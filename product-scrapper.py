import requests
from bs4 import BeautifulSoup
import csv
from urllib.parse import urljoin, urlparse
import time
import threading
import queue
import xml.etree.ElementTree as ET
import json
import os

# -----------------------------
# Global Variables and Session
# -----------------------------
visited = set()                   # To track processed URLs
visited_lock = threading.Lock()   # Lock for visited set
scraped_count = 0                 # Count of scraped products
scraped_lock = threading.Lock()   # Lock for updating scraped_count
stop_crawl = False                # Flag to signal threads to stop
work_queue = queue.Queue()        # Queue for URLs to process
session = requests.Session()      # Global session for HTTP requests

# For resume functionality:
resume_file = "resume_state.json"
resume_lock = threading.Lock()    # Lock for writing resume state
scraped_products = []             # List of scraped product URLs (for resume)

# -----------------------------
# Resume State Functions
# -----------------------------
def update_resume_state():
    """
    Save current state (visited, pending URLs, and scraped product URLs) to a JSON file.
    """
    with resume_lock:
        state = {
            "scraped": scraped_products,              # Already scraped product URLs
            "visited": list(visited),                 # Visited URLs
            "pending": list(work_queue.queue)         # Pending URLs (from the queue)
        }
        with open(resume_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=4)

def load_resume_state():
    """
    Load state from the resume file.
    Returns a tuple: (visited_set, scraped_list, pending_list)
    """
    try:
        with open(resume_file, "r", encoding="utf-8") as f:
            state = json.load(f)
        return set(state.get("visited", [])), state.get("scraped", []), state.get("pending", [])
    except Exception as e:
        print(f"Error loading resume state: {e}")
        return set(), [], []

# -----------------------------
# Helper Functions
# -----------------------------

def is_internal_url(url, base_netloc):
    """Check if the URL belongs to the same domain."""
    parsed = urlparse(url)
    return parsed.netloc == base_netloc or parsed.netloc == ""

def is_product_page(url):
    """
    Determine if the URL is likely a product page.
    We assume product pages contain '/product/' in the path.
    """
    parsed = urlparse(url)
    return '/product/' in parsed.path

def scrape_product(url):
    """
    Scrape a product page for:
      - Title: primary in an <h1> tag with class "product_title entry-title"
               fallback: meta tag "og:title"
      - Description: primary in a <div> tag with class "e-n-tabs-content"
                     fallback: <div> with id "tab-description"
                     fallback: <div> with class "woocommerce-Tabs-panel woocommerce-Tabs-panel--description"
      - Price: primary in a <span> tag with class "woocommerce-Price-amount amount"
               fallback: <p> tag with class "price"
      - Image: primary in an <img> tag inside a <figure> tag with class "woocommerce-product-gallery__image"
               fallback: meta tag "og:image"
    Returns a dictionary with the product details (using "N/A" for missing fields).
    """
    print(f"Scraping product: {url}")
    try:
        response = session.get(url, timeout=10)
        if response.status_code != 200:
            print(f"Failed to retrieve {url}")
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        
        # --- Title Extraction ---
        title = "N/A"
        title_tag = soup.find("h1", class_="product_title entry-title")
        if title_tag:
            title = title_tag.get_text(strip=True)
        else:
            meta_title = soup.find("meta", property="og:title")
            if meta_title and meta_title.get("content"):
                title = meta_title["content"].strip()
        
        # --- Description Extraction ---
        description = "N/A"
        desc_tag = soup.find("div", class_="e-n-tabs-content")
        if desc_tag:
            description = desc_tag.get_text(strip=True)
        else:
            alt_desc_tag = soup.find("div", id="tab-description")
            if alt_desc_tag:
                description = alt_desc_tag.get_text(strip=True)
            else:
                alt_desc_tag = soup.find("div", class_="woocommerce-Tabs-panel woocommerce-Tabs-panel--description")
                if alt_desc_tag:
                    description = alt_desc_tag.get_text(strip=True)
        
        # --- Price Extraction ---
        price = "N/A"
        price_tag = soup.find("span", class_="woocommerce-Price-amount amount")
        if price_tag:
            price = price_tag.get_text(strip=True)
        else:
            p_price = soup.find("p", class_="price")
            if p_price:
                price = p_price.get_text(strip=True)
        
        # --- Image Extraction ---
        image_url = "N/A"
        figure_tag = soup.find("figure", class_="woocommerce-product-gallery__image")
        if figure_tag:
            img_tag = figure_tag.find("img")
            if img_tag and img_tag.has_attr("src"):
                image_url = img_tag["src"]
        else:
            meta_img = soup.find("meta", property="og:image")
            if meta_img and meta_img.get("content"):
                image_url = meta_img["content"].strip()
        
        if title == "N/A" and description == "N/A" and price == "N/A" and image_url == "N/A":
            print("No product info found on page, skipping.")
            return None

        return {
            "url": url,
            "title": title,
            "description": description,
            "price": price,
            "image_url": image_url
        }
    except Exception as e:
        print(f"Error scraping product at {url}: {e}")
        return None

def parse_sitemap(sitemap_url):
    """
    Given a sitemap.xml URL, fetch it and parse out all product links (from <loc> tags).
    Returns a set of URLs that appear to be product pages.
    """
    product_urls = set()
    try:
        print(f"Fetching sitemap: {sitemap_url}")
        response = requests.get(sitemap_url, timeout=10)
        if response.status_code != 200:
            print(f"Failed to fetch sitemap: {sitemap_url}")
            return product_urls
        root = ET.fromstring(response.content)
        ns = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        for url_element in root.findall("ns:url", ns):
            loc = url_element.find("ns:loc", ns)
            if loc is not None and loc.text:
                url_text = loc.text.strip()
                if is_product_page(url_text):
                    product_urls.add(url_text)
    except Exception as e:
        print(f"Error parsing sitemap {sitemap_url}: {e}")
    return product_urls

def extract_product_urls_from_page(page_url):
    """
    Given a single page URL, fetch it and extract product links.
    Returns a set of URLs that appear to be product pages.
    """
    product_urls = set()
    try:
        print(f"Fetching single page: {page_url}")
        response = requests.get(page_url, timeout=10)
        if response.status_code != 200:
            print(f"Failed to fetch page: {page_url}")
            return product_urls
        soup = BeautifulSoup(response.text, "html.parser")
        for a_tag in soup.find_all("a", href=True):
            full_url = urljoin(page_url, a_tag["href"]).split("#")[0]
            if is_product_page(full_url):
                product_urls.add(full_url)
    except Exception as e:
        print(f"Error extracting products from {page_url}: {e}")
    return product_urls

# -----------------------------
# Worker Functions
# -----------------------------
def worker_product(product_limit, csv_writer, num_threads):
    """
    Worker for modes where a pre-populated list of product URLs is processed.
    """
    global scraped_count, stop_crawl, scraped_products
    while True:
        try:
            current_url = work_queue.get(timeout=3)
        except queue.Empty:
            break
        if current_url is None:
            work_queue.task_done()
            break
        with scraped_lock:
            if stop_crawl:
                work_queue.task_done()
                break
        with visited_lock:
            if current_url in visited:
                work_queue.task_done()
                continue
            visited.add(current_url)
        product = scrape_product(current_url)
        if product:
            with scraped_lock:
                if scraped_count < product_limit:
                    csv_writer.writerow(product)
                    scraped_count += 1
                    scraped_products.append(product["url"])
                    print(f"Scraped products: {scraped_count}")
                    if scraped_count % 10 == 0:
                        print(f"Batch complete: {scraped_count} products scraped so far.")
                    update_resume_state()
                    if scraped_count >= product_limit and not stop_crawl:
                        stop_crawl = True
                        for _ in range(num_threads):
                            work_queue.put(None)
        time.sleep(0.1)
        work_queue.task_done()

def worker_crawl(base_netloc, product_limit, csv_writer, num_threads):
    """
    Worker for Home URL mode: Crawl starting from the given URL,
    follow internal links, and scrape product pages.
    """
    global scraped_count, stop_crawl, scraped_products
    while True:
        try:
            current_url = work_queue.get(timeout=3)
        except queue.Empty:
            break
        if current_url is None:
            work_queue.task_done()
            break
        with scraped_lock:
            if stop_crawl:
                work_queue.task_done()
                break
        with visited_lock:
            if current_url in visited:
                work_queue.task_done()
                continue
            visited.add(current_url)
        try:
            response = session.get(current_url, timeout=10)
        except Exception as e:
            print(f"Error fetching {current_url}: {e}")
            work_queue.task_done()
            continue
        if response.status_code != 200:
            work_queue.task_done()
            continue
        soup = BeautifulSoup(response.text, "html.parser")
        if is_product_page(current_url):
            product = scrape_product(current_url)
            if product:
                with scraped_lock:
                    if scraped_count < product_limit:
                        csv_writer.writerow(product)
                        scraped_count += 1
                        scraped_products.append(product["url"])
                        print(f"Scraped products: {scraped_count}")
                        if scraped_count % 10 == 0:
                            print(f"Batch complete: {scraped_count} products scraped so far.")
                        update_resume_state()
                        if scraped_count >= product_limit and not stop_crawl:
                            stop_crawl = True
                            for _ in range(num_threads):
                                work_queue.put(None)
        # Enqueue internal links
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            full_url = urljoin(current_url, href).split("#")[0]
            with visited_lock:
                if full_url not in visited and is_internal_url(full_url, base_netloc):
                    work_queue.put(full_url)
        time.sleep(0.1)
        work_queue.task_done()

# -----------------------------
# Main Function and Mode Selection
# -----------------------------
if __name__ == "__main__":
    # Check for resume state
    resume_mode = False
    if os.path.exists(resume_file):
        choice = input("A resume state was found. Do you want to resume the previous session? (y/n): ").strip().lower()
        if choice == "y":
            resume_mode = True
            loaded_visited, loaded_scraped, loaded_pending = load_resume_state()
            visited = loaded_visited
            scraped_products = loaded_scraped
            scraped_count = len(scraped_products)
            for url in loaded_pending:
                work_queue.put(url)
            print(f"Resuming session: {scraped_count} products already scraped, {len(loaded_pending)} URLs pending.")
        else:
            os.remove(resume_file)
    
    # If not resuming, choose scraping mode.
    if not resume_mode:
        print("Select scraping mode:")
        print("1: Sitemap Mode")
        print("2: Home URL Mode (crawl the site)")
        print("3: Single Page Mode (scrape products from one page)")
        print("4: Product URL File Mode (list of product URLs in a text file)")
        mode = input("Enter option (1/2/3/4): ").strip()

        product_urls = set()  # Will hold product URLs for modes 1, 3, and 4
        base_netloc = None

        if mode == "1":
            # Sitemap Mode
            sitemap_urls = []
            print("Choose sitemap input method:")
            print("a: Manual entry")
            print("b: Read from a text file")
            sub_option = input("Enter option (a/b): ").strip().lower()
            if sub_option == "a":
                while True:
                    sitemap_url = input("Enter a sitemap URL: ").strip()
                    if sitemap_url:
                        sitemap_urls.append(sitemap_url)
                    more = input("Do you have another sitemap? (yes/no): ").strip().lower()
                    if more != "yes":
                        break
            elif sub_option == "b":
                file_path = input("Enter the full path to your sitemap text file: ").strip()
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if line:
                                sitemap_urls.append(line)
                except Exception as e:
                    print(f"Error reading file: {e}")
                    exit(1)
            else:
                print("Invalid option. Exiting.")
                exit(1)
            if not sitemap_urls:
                print("No sitemap URLs provided. Exiting.")
                exit(1)
            for sitemap in sitemap_urls:
                urls = parse_sitemap(sitemap)
                print(f"Found {len(urls)} product URLs in sitemap: {sitemap}")
                product_urls.update(urls)
            if not product_urls:
                print("No product URLs found in the provided sitemaps. Exiting.")
                exit(1)
            base_netloc = urlparse(sitemap_urls[0]).netloc

        elif mode == "2":
            # Home URL Mode
            home_url = input("Enter the home URL: ").strip()
            if not home_url:
                print("No URL provided. Exiting.")
                exit(1)
            base_netloc = urlparse(home_url).netloc
            work_queue.put(home_url)

        elif mode == "3":
            # Single Page Mode
            page_url = input("Enter the single page URL: ").strip()
            if not page_url:
                print("No URL provided. Exiting.")
                exit(1)
            product_urls = extract_product_urls_from_page(page_url)
            if not product_urls:
                print("No product URLs found on the page. Exiting.")
                exit(1)
            base_netloc = urlparse(page_url).netloc

        elif mode == "4":
            # Product URL File Mode
            file_path = input("Enter the full path to your product URL text file: ").strip()
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            product_urls.add(line)
            except Exception as e:
                print(f"Error reading file: {e}")
                exit(1)
            if not product_urls:
                print("No product URLs found in the file. Exiting.")
                exit(1)
            base_netloc = urlparse(next(iter(product_urls))).netloc

        else:
            print("Invalid mode selected. Exiting.")
            exit(1)

        print(f"Total unique product URLs collected: {len(product_urls)}")
        # Pre-populate the work queue for modes 1, 3, and 4.
        if mode in ["1", "3", "4"]:
            for url in product_urls:
                work_queue.put(url)

        # Ask for the product limit.
        try:
            product_limit = int(input("Enter how many products you want to scrape: "))
        except ValueError:
            print("Invalid number entered. Exiting.")
            exit(1)
    
    # If resuming, ask for (or confirm) product limit.
    if resume_mode:
        try:
            product_limit = int(input("Enter the total product limit for this session (including already scraped): "))
        except ValueError:
            print("Invalid number entered. Exiting.")
            exit(1)
        print(f"Resuming with product limit: {product_limit}")

    output_file = "products.csv"
    NUM_THREADS = 10  # Number of concurrent threads

    with open(output_file, "a" if resume_mode else "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["url", "title", "description", "price", "image_url"]
        csv_writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not resume_mode:
            csv_writer.writeheader()

        threads = []
        if (not resume_mode and mode == "2") or (resume_mode and work_queue.empty() == False and any("http" in url for url in list(work_queue.queue)) and base_netloc):
            # Home URL mode: use worker_crawl
            for _ in range(NUM_THREADS):
                t = threading.Thread(target=worker_crawl, args=(base_netloc, product_limit, csv_writer, NUM_THREADS))
                t.daemon = True
                t.start()
                threads.append(t)
        else:
            # Modes 1, 3, 4 or resume with pre-populated product URLs: use worker_product
            for _ in range(NUM_THREADS):
                t = threading.Thread(target=worker_product, args=(product_limit, csv_writer, NUM_THREADS))
                t.daemon = True
                t.start()
                threads.append(t)

        work_queue.join()
        for t in threads:
            t.join()

    print(f"Scraping complete. Total products scraped: {scraped_count}")
    # On successful completion, remove resume state.
    if os.path.exists(resume_file):
        os.remove(resume_file)
