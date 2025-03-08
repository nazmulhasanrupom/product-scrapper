import os
import json
import time
import threading
import queue
import csv
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import xml.etree.ElementTree as ET

# -----------------------------
# Global Variables
# -----------------------------
visited = set()               # URLs that have been processed
scraped_count = 0             # Count of products scraped
scraped_products = []         # List of product URLs that have been scraped
stop_crawl = False            # Flag to signal threads to stop
work_queue = queue.Queue()    # Thread-safe queue for URLs to process
session = requests.Session()  # Reuse HTTP connections

# Additional globals for resume functionality and crawl mode
resume_file = "resume_state.json"
crawl_mode = False            # True if using Home URL mode (crawling internal links)
base_netloc = None            # The base domain (used in crawling mode)

# Lock objects
visited_lock = threading.Lock()
scraped_lock = threading.Lock()
resume_lock = threading.Lock()

# -----------------------------
# Resume Functions
# -----------------------------
def update_resume_state():
    """Save current state (visited URLs, scraped product URLs, pending queue, crawl_mode and base_netloc)"""
    with resume_lock:
        state = {
            "visited": list(visited),
            "scraped": scraped_products,
            "pending": list(work_queue.queue),
            "crawl_mode": crawl_mode,
            "base_netloc": base_netloc
        }
        with open(resume_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=4)

def load_resume_state():
    """Load state from resume file and return the components."""
    try:
        with open(resume_file, "r", encoding="utf-8") as f:
            state = json.load(f)
        return (set(state.get("visited", [])),
                state.get("scraped", []),
                state.get("pending", []),
                state.get("crawl_mode", False),
                state.get("base_netloc", None))
    except Exception as e:
        print(f"Error loading resume state: {e}")
        return set(), [], [], False, None

# -----------------------------
# Helper Functions
# -----------------------------
def is_internal_url(url, base_netloc):
    """Return True if the URL is on the same domain as base_netloc."""
    parsed = urlparse(url)
    return (parsed.netloc == base_netloc) or (parsed.netloc == "")

def is_product_page(url):
    """Return True if the URL looks like a product page (contains '/product/')."""
    parsed = urlparse(url)
    return '/product/' in parsed.path

def scrape_product(url):
    """Scrape a product page for title, description, price, and image URL."""
    print(f"Scraping product: {url}")
    try:
        response = session.get(url, timeout=10)
        if response.status_code != 200:
            print(f"Failed to retrieve {url}")
            return None
        soup = BeautifulSoup(response.text, "html.parser")
        # --- Title ---
        title = "N/A"
        title_tag = soup.find("h1", class_="product_title entry-title")
        if title_tag:
            title = title_tag.get_text(strip=True)
        else:
            meta_title = soup.find("meta", property="og:title")
            if meta_title and meta_title.get("content"):
                title = meta_title["content"].strip()
        # --- Description ---
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
        # --- Price ---
        price = "N/A"
        price_tag = soup.find("span", class_="woocommerce-Price-amount amount")
        if price_tag:
            price = price_tag.get_text(strip=True)
        else:
            p_price = soup.find("p", class_="price")
            if p_price:
                price = p_price.get_text(strip=True)
        # --- Image URL ---
        image_url = "N/A"
        figure_tag = soup.find("figure", class_="woocommerce-product-gallery__image")
        if figure_tag:
            img_tag = figure_tag.find("img")
            if img_tag and img_tag.get("src"):
                image_url = img_tag["src"]
        else:
            meta_img = soup.find("meta", property="og:image")
            if meta_img and meta_img.get("content"):
                image_url = meta_img["content"].strip()
        # If nothing found, skip the page.
        if title == "N/A" and description == "N/A" and price == "N/A" and image_url == "N/A":
            print("No product info found, skipping.")
            return None
        return {
            "url": url,
            "title": title,
            "description": description,
            "price": price,
            "image_url": image_url
        }
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

def parse_sitemap(sitemap_url):
    """Parse a sitemap.xml and return a set of product URLs."""
    product_urls = set()
    try:
        print(f"Fetching sitemap: {sitemap_url}")
        response = requests.get(sitemap_url, timeout=10)
        if response.status_code != 200:
            print(f"Failed to fetch sitemap: {sitemap_url}")
            return product_urls
        root = ET.fromstring(response.content)
        ns = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        for url_elem in root.findall("ns:url", ns):
            loc = url_elem.find("ns:loc", ns)
            if loc is not None and loc.text:
                url_text = loc.text.strip()
                if is_product_page(url_text):
                    product_urls.add(url_text)
    except Exception as e:
        print(f"Error parsing sitemap {sitemap_url}: {e}")
    return product_urls

def extract_product_urls_from_page(page_url):
    """Extract product URLs from a single page that lists products."""
    product_urls = set()
    try:
        print(f"Fetching page: {page_url}")
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
# Worker Function (Unified)
# -----------------------------
def worker(num_threads, product_limit):
    global scraped_count, stop_crawl, crawl_mode
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
        # If URL is a product page, scrape it
        if is_product_page(current_url):
            product = scrape_product(current_url)
            if product:
                with scraped_lock:
                    if scraped_count < product_limit:
                        # Write the product data
                        csv_writer.writerow(product)
                        scraped_count += 1
                        scraped_products.append(product["url"])
                        print(f"Scraped products: {scraped_count}")
                        update_resume_state()
                        if scraped_count >= product_limit and not stop_crawl:
                            stop_crawl = True
                            for _ in range(num_threads):
                                work_queue.put(None)
        # If crawl_mode is enabled (Home URL mode), then find and enqueue internal links
        if crawl_mode:
            try:
                resp = session.get(current_url, timeout=10)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    for a_tag in soup.find_all("a", href=True):
                        full_url = urljoin(current_url, a_tag["href"]).split("#")[0]
                        with visited_lock:
                            if full_url not in visited and is_internal_url(full_url, base_netloc):
                                work_queue.put(full_url)
            except Exception as e:
                print(f"Error crawling {current_url}: {e}")
        time.sleep(0.1)
        work_queue.task_done()

# -----------------------------
# Main Execution
# -----------------------------
if __name__ == "__main__":
    NUM_THREADS = 10  # Number of threads to use

    resume_mode = False
    # Check if a resume file exists
    if os.path.exists(resume_file):
        choice = input("Found a resume state. Do you want to resume? (y/n): ").strip().lower()
        if choice == "y":
            resume_mode = True
            loaded_visited, loaded_scraped, loaded_pending, loaded_crawl_mode, loaded_base_netloc = load_resume_state()
            visited = loaded_visited
            scraped_products = loaded_scraped
            scraped_count = len(scraped_products)
            for url in loaded_pending:
                work_queue.put(url)
            crawl_mode = loaded_crawl_mode
            base_netloc = loaded_base_netloc
            print(f"Resuming: {scraped_count} products scraped; {len(loaded_pending)} URLs pending.")
        else:
            os.remove(resume_file)

    if not resume_mode:
        # Mode Selection:
        print("Select scraping mode:")
        print("1: Sitemap Mode")
        print("2: Home URL Mode (crawl the site)")
        print("3: Single Page Mode (scrape products from one page)")
        print("4: Product URL File Mode (list product URLs from a text file)")
        mode = input("Enter option (1/2/3/4): ").strip()

        product_urls = set()

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
                    more = input("Another sitemap? (yes/no): ").strip().lower()
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
                print("No product URLs found. Exiting.")
                exit(1)
            # For sitemap mode, we do not crawl further.
            crawl_mode = False
            # Set base_netloc from the first sitemap URL
            base_netloc = urlparse(sitemap_urls[0]).netloc

        elif mode == "2":
            # Home URL Mode (Crawl)
            home_url = input("Enter the home URL: ").strip()
            if not home_url:
                print("No URL provided. Exiting.")
                exit(1)
            crawl_mode = True
            base_netloc = urlparse(home_url).netloc
            work_queue.put(home_url)

        elif mode == "3":
            # Single Page Mode
            page_url = input("Enter the page URL that lists products: ").strip()
            if not page_url:
                print("No URL provided. Exiting.")
                exit(1)
            product_urls = extract_product_urls_from_page(page_url)
            if not product_urls:
                print("No product URLs found on the page. Exiting.")
                exit(1)
            crawl_mode = False
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
            crawl_mode = False
            base_netloc = urlparse(next(iter(product_urls))).netloc

        else:
            print("Invalid mode selected. Exiting.")
            exit(1)

        # If using modes 1, 3, or 4, pre-populate the queue with the product URLs.
        if mode in ["1", "3", "4"]:
            for url in product_urls:
                work_queue.put(url)

        # Ask for product limit
        try:
            product_limit = int(input("Enter how many products to scrape: "))
        except ValueError:
            print("Invalid number. Exiting.")
            exit(1)

    # Open CSV file (append if resuming, else write new)
    output_mode = "a" if resume_mode else "w"
    with open("products.csv", output_mode, newline="", encoding="utf-8") as csvfile:
        fieldnames = ["url", "title", "description", "price", "image_url"]
        global csv_writer
        csv_writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not resume_mode:
            csv_writer.writeheader()

        # Start worker threads
        threads = []
        for _ in range(NUM_THREADS):
            t = threading.Thread(target=worker, args=(NUM_THREADS, product_limit))
            t.daemon = True
            t.start()
            threads.append(t)

        work_queue.join()
        for t in threads:
            t.join()

    print(f"Scraping complete. Total products scraped: {scraped_count}")
    # If scraping finished, remove the resume state file.
    if os.path.exists(resume_file):
        os.remove(resume_file)
