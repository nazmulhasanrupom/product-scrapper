
**Product Scraper Tool – User Guide**
---

### What Does It Do?

This tool is like a smart robot that visits websites and collects important information about products. It finds details like the product’s name, what it is about (description), its price, and a picture (image URL). Then it saves all this information in a special file called a CSV (which you can open in a program like Excel).

---

### How Can It Get Product Information?

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

---

### Special Feature: Resume Your Work!

Sometimes, if the power goes out or the internet stops working, the robot can “remember” what it has done so far. When you run the tool again, you can tell it to continue from where it left off. This means you won’t lose all the work that was already done!

---

### What You Need Before You Start

- **A computer with the internet.**
- **Python 3.6 or higher installed.**
- **A few extra packages installed:**  
  You can install them by opening your command prompt (or terminal) and typing:

  ```
  pip install requests beautifulsoup4 lxml
  ```

  These packages help the robot talk to websites and understand the pages.

---

### How to Use the Tool – Step by Step

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

---

### Changing HTML Tags and Classes

Websites can look different from each other. Sometimes, the names of the classes or the structure of the website can be different from one site to another. So, the tool needs to know where to find the product details on the page. 

For each of the product details (like title, description, price, etc.), the robot looks for specific HTML tags and class names. Here's how you can change these for different websites:

- **Title of the Product:**  
   Usually found in `<h1>` or `<h2>` tags.  
   Example:  
   ```html
   <h1 class="product-title">Product Name</h1>
   ```
   Change the tag or class based on the website you're scraping.

- **Price of the Product:**  
   Typically in a `<span>` or `<div>` tag with a class like `"price"` or `"product-price"`.  
   Example:  
   ```html
   <span class="price">29.99</span>
   ```
   Update the tag or class name to match the site you’re scraping.

- **Description of the Product:**  
   Often in a `<div>` or `<p>` tag with a class like `"product-description"`.  
   Example:  
   ```html
   <div class="product-description">This is a great product.</div>
   ```
   Make sure to update the class name if it's different on the website you are scraping.

- **Image URL:**  
   The image is usually inside an `<img>` tag.  
   Example:  
   ```html
   <img src="image_url.jpg" class="product-image"/>
   ```
   The class name or the tag might vary, so adjust accordingly.

**How to Change the Code for a New Website:**
- Look at the website you want to scrape and find the **HTML structure** (use your browser's "Inspect Element" tool to view the page’s HTML).
- Identify the tags and classes where the information you want (product name, price, description, image) is located.
- Go to the script and **update the code** with the correct tags and classes for the site you’re working with.

**Example Update:**
If the product name is inside a `<span>` with the class `product-name`, and the price is inside a `<div>` with the class `product-cost`, you would change the code to:

```python
title = soup.find('span', {'class': 'product-name'}).get_text()
price = soup.find('div', {'class': 'product-cost'}).get_text()
```

---

### What’s in the CSV File?

After the tool finishes:
- Open **products.csv**.
- You will see columns for:
  - **URL**: The address of the product page.
  - **Title**: The name of the product.
  - **Description**: A short explanation of what the product is.
  - **Price**: How much it costs.
  - **Image URL**: A link to a picture of the product.

---

### Extra Fun Features

- **Multi-threading:**  
  The robot can work on many pages at the same time, which makes it faster!

- **Resume Feature:**  
  Even if something goes wrong, you can restart and continue from where you stopped.

---

That’s it! Now you have a complete guide that explains how the tool works and how to use it in a very simple way. Happy scraping!

---
