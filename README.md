
## Assalamualaikum

`(this is totally for educational purpose , i or my work will not be responsible for any missuse)`

## Try it on different sites and see where it works and it doesnt . And me know the results :)
Most of the woocommerce site should work without any changes.
Also check if your ip is getting blocked or not due to scraping. 

## The code will only work if it is able to visit the website(means it is not blocked by any defender like cloudflare) and it is able to fetch the product informations(like title tag, description tag, img tag e.t.c)

If its not able to fetch any product at all try to change the ip.
(i shall try to implement proxy feature in future updates in sha allah)




# product-scrapper

MINIMUM SYSTEM REQ TO RUN THIS : 

CPU: Dual-core processor (Intel i3 or equivalent)

RAM: 4 GB (recommended 8 GB or more)

Storage: 1 GB available disk space (5 GB or more recommended for large scraping jobs)

Network: Stable internet connection (10 Mbps or higher)

OS: Windows 10/11, macOS 10.13+, Linux (Ubuntu 18.04+)

Python: Python 3.6+ (3.8+ recommended)

Libraries: requests, beautifulsoup4, lxml, csv

# How to run?

Before you run the .py file create a virtual environment and intall the following libraries : 

requests: For sending HTTP requests.

beautifulsoup4: For parsing HTML and extracting data.

lxml: An optional parser used by BeautifulSoup for faster parsing (if needed).

csv: For writing data to CSV files (this is part of Python's standard library).

os: For interacting with the operating system (also part of the standard library).

pickle: For saving and loading Python objects (part of the standard library).

time: For time delays and managing sleep times (part of the standard library).

queue: For using a thread-safe queue (part of the standard library).

threading: For handling multiple threads (part of the standard library).

urllib.parse: For parsing URLs (part of the standard library).

` pip install requests `
` pip install beautifulsoup4 `
` pip install lxml `


## Now update the HTML Classes in the code**
First run the code as it is if doesnt work then try to update the classes.

## If the code doesnt stop automatically , press `ctrl+c`

## Features : 

Here’s a list of the overall features of the code I’ve been working on:

1. **Scraping Methods**:
   - **Sitemap-based Scraping**: Allows scraping product links from sitemap.xml files.
   - **Home URL Scraping**: Scrapes product links starting from the home URL and follows internal links.
   - **Single Page Scraping**: Scrapes product links from a single page specified by the user.

2. **Customizable Input Options**:
   - The user can choose from different scraping methods (sitemap, home URL, or single page).
   - Ability to manually input multiple sitemaps.
   - Option to provide a text file containing a list of sitemap URLs for automatic scraping.

3. **Product Data Collection**:
   - Scrapes essential product details: title, description, price, and image URL.
   - Fallback methods in case some product details are missing (e.g., using `meta` tags for missing content).

4. **Multi-threading for Faster Scraping**:
   - Uses **multi-threading** to scrape product pages concurrently for faster data collection.
   - Worker threads process URLs concurrently, improving performance.

5. **Queue Management**:
   - A thread-safe queue to store URLs that need to be scraped.
   - URL visits are tracked to avoid re-scraping the same URLs.

6. **Resumption After Interruption**:
   - **Resumes scraping from where it left off** in case of interruptions (power cut, internet failure, etc.).
   - **Persistent storage** of visited URLs and scraped data using **pickle**.

7. **CSV Output**:
   - Scraped product data is stored in a CSV file.
   - The CSV file contains columns for URL, title, description, price, and image URL.
   - Automatically appends each product’s details to the CSV file and shows a count of how many products have been scraped.

8. **Dynamic Sitemap Parsing**:
   - Can handle multiple sitemap URLs and gather products from all listed URLs.
   - Automatically follows links from a sitemap to scrape products.

9. **Error Handling**:
   - Handles exceptions gracefully and skips problematic pages without halting the scraping process.
   - Logs errors when a product page fails to load or cannot be scraped.

10. **Configuration and Control**:
   - Allows the user to define how many products to scrape (product limit).
   - Allows pausing and resuming scraping when the product limit is reached.

11. **Efficiency Improvements**:
   - Implements **rate limiting** (with a short delay) between requests to avoid overwhelming the server.
   - **Session reuse** for HTTP requests to speed up the process and reduce the overhead of new connections.

12. **File Input for Sitemaps**:
   - Allows reading multiple sitemaps from a text file, making it easy to scrape from a list of sitemaps without manual input.
