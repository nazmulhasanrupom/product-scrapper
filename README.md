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



## Documentation

Below is a simple, kid-friendly documentation that explains what the tool does and how to use it. You can share this with anyone—even a 10‑year‑old!

---

# Product Scraper Tool – User Guide

## What Does It Do?

This tool is like a smart robot that visits websites and collects important information about products. It finds details like the product’s name, what it is about (description), its price, and a picture (image URL). Then it saves all this information in a special file called a CSV (which you can open in a program like Excel).

## How Can It Get Product Information?

You have **4 different ways** to tell the robot where to look:

1. **Sitemap Mode:**  
   - A sitemap is like a treasure map for a website. It tells the robot where all the products are.
   - You can either type in the sitemap addresses yourself or give the robot a file (a text file) that has a list of sitemap addresses.

2. **Home URL Mode (Crawl Mode):**  
   - You give the robot a website’s main page (home page).  
   - The robot will start there, follow links on the site, and look for product pages.

3. **Single Page Mode:**  
   - You give the robot one page that has several products listed.
   - The robot will look at that page and collect the product information it finds there.

4. **Product URL File Mode:**  
   - You create a file with a list of product page addresses (URLs).  
   - The robot reads the file and visits each page to get the product details.

## Special Feature: Resume Your Work!

Sometimes, if the power goes out or the internet stops working, the robot can “remember” what it has done so far. When you run the tool again, you can tell it to continue from where it left off. This means you won’t lose all the work that was already done!

## What You Need Before You Start

- **A computer with the internet.**
- **Python 3.6 or higher installed.**
- **A few extra packages installed:**  
  You can install them by opening your command prompt (or terminal) and typing:
  ```bash
  pip install requests beautifulsoup4 lxml
  ```
  These packages help the robot talk to websites and understand the pages.

## How to Use the Tool – Step by Step

1. **Open Your Command Prompt or Terminal:**
   - This is where you will run the robot (the code).

2. **Run the Tool:**
   - Type `python your_script_name.py` and press Enter. (Replace “your_script_name.py” with the name of the file that has the code.)

3. **Choose a Mode:**
   - The tool will ask you which mode you want to use:
     - Type **1** for Sitemap Mode.
     - Type **2** for Home URL Mode.
     - Type **3** for Single Page Mode.
     - Type **4** for Product URL File Mode.
   - Press Enter.

4. **Follow the Instructions for Your Mode:**
   - **If you choose Sitemap Mode:**  
     The robot will ask you if you want to type the sitemap addresses by hand (manual) or use a text file that has them.  
     Follow the simple questions.  
   - **If you choose Home URL Mode:**  
     Just type in the home page address (for example, `https://example.com`).
   - **If you choose Single Page Mode:**  
     Type the URL of the page that shows many products.
   - **If you choose Product URL File Mode:**  
     Give the full location (path) of the file on your computer that has the list of product URLs.

5. **Set a Product Limit:**
   - The tool will ask how many products you want to collect. Type a number (for example, 50) and press Enter.

6. **Let the Robot Work:**
   - The tool will now visit all the links, grab the product details, and save them in a file called **products.csv**.
   - It shows you messages like “Scraped products: 10” so you know it’s working.

7. **Resume If Needed:**
   - If something stops the tool (like a power cut), when you run it again, it will ask if you want to resume.  
     Type **y** for yes, and it will continue where it left off.

## What’s in the CSV File?

After the tool finishes:
- Open **products.csv**.
- You will see columns for:
  - **URL**: The address of the product page.
  - **Title**: The name of the product.
  - **Description**: A short explanation of what the product is.
  - **Price**: How much it costs.
  - **Image URL**: A link to a picture of the product.

## Extra Fun Features

- **Multi-threading:**  
  The robot can work on many pages at the same time, which makes it faster!

- **Resume Feature:**  
  Even if something goes wrong, you can restart and continue from where you stopped.

---

That’s it! Now you have a complete guide that explains how the tool works and how to use it in a very simple way. Happy scraping!


