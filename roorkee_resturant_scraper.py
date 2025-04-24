
import time
import re
import os
import json
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from IPython.display import HTML, display
import matplotlib.pyplot as plt

os.makedirs("menu_data", exist_ok=True)

def scrape_restaurant_menu(url, restaurant_key):
    """
    Scrapes a Zomato restaurant page and extracts menu information
    
    Args:
        url (str): The Zomato restaurant URL
        restaurant_key (str): A key/name to identify the restaurant
        
    Returns:
        dict: Restaurant and menu information
    """
    print(f"🔍 Scraping {restaurant_key}...")
    
    # Configure Chrome browser
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
    
    # Initialize the browser
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.get(url)
    
    time.sleep(4)
    
    try:
        expand_attempts = 0
        max_attempts = 5
        
        while expand_attempts < max_attempts:
            read_more_buttons = driver.find_elements(By.XPATH, "//span[contains(translate(text(), 'READ MORE', 'read more'), 'read more')]")
            if not read_more_buttons:
                break
                
            for btn in read_more_buttons:
                try:
                    driver.execute_script("arguments[0].click();", btn)
                except Exception:
                    pass
                    
            time.sleep(0.5)
            expand_attempts += 1
    except Exception as e:
        print(f"Warning during expansion: {e}")
    
    # Parse the page with BeautifulSoup
    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()
    
    # Extract restaurant information
    restaurant_info = {}
    
    rest_name = soup.find("h1")
    restaurant_info["name"] = rest_name.get_text(strip=True) if rest_name else "Unknown Restaurant"
    
    # Get restaurant location
    location = ""
    loc_tag = soup.find("div", class_=re.compile("sc-clNaTc"))
    if loc_tag:
        location = loc_tag.get_text(strip=True)
    restaurant_info["location"] = location
    
    # Get contact information
    contact = ""
    phone_tag = soup.find("a", href=re.compile(r"tel:"))
    if phone_tag:
        contact = phone_tag.get_text(strip=True)
    restaurant_info["contact"] = contact
    
    # Extract menu data
    menu_data = []
    menu_sections = soup.find_all("section", class_=re.compile("sc-bZVNgQ"))
    
    for section in menu_sections:
        # Get category name
        cat_tag = section.find("h4")
        category = cat_tag.get_text(strip=True) if cat_tag else "Uncategorized"
        
        # Initialize category data
        category_data = {"category": category, "items": []}
        
        # Find all items in this category
        item_blocks = section.find_all("div", class_=re.compile("sc-jhLVlY"))
        
        for item in item_blocks:
            # Determine veg/non-veg status
            veg_type = "Unknown"
            veg_div = item.find("div", class_=re.compile("sc-gcpVEs"))
            if veg_div and veg_div.has_attr("type"):
                if veg_div["type"] == "veg":
                    veg_type = "Veg"
                elif veg_div["type"] == "non-veg":
                    veg_type = "Non-Veg"
            
            # Get item name
            name_tag = item.find("h4", class_=re.compile("sc-cGCqpu"))
            name = name_tag.get_text(strip=True) if name_tag else ""
            
            # Get item price
            price_tag = item.find("span", class_=re.compile("sc-17hyc2s-1"))
            price = price_tag.get_text(strip=True) if price_tag else ""
            
            # Get item description
            desc_tag = item.find("p", class_=re.compile("sc-gsxalj"))
            desc = ""
            if desc_tag:
                # Remove any remaining "read more" text
                for rm in desc_tag.find_all("span", string=re.compile("read more", re.I)):
                    rm.extract()
                desc = desc_tag.get_text(" ", strip=True)
            
            # Determine spice level from description
            spice_level = "Spicy" if re.search(r"spicy|fiery|peri peri|chilli|hot", desc, re.I) else "Normal"
            
            # Add item to category if it has a name
            if name:
                category_data["items"].append({
                    "name": name,
                    "price": price,
                    "description": desc,
                    "veg_nonveg": veg_type,
                    "spice_level": spice_level
                })
        
        # Add category to menu if it has items
        if category_data["items"]:
            menu_data.append(category_data)
    
    # Create final data structure
    final_data = {
        "restaurant": restaurant_info,
        "menu": menu_data
    }
    
    # Save data to JSON file
    filename = f"{restaurant_key}_menu.json"
    filepath = os.path.join("menu_data", filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, indent=4, ensure_ascii=False)
    
    print(f" Saved {restaurant_info['name']} menu to {filepath}")
    
    return final_data

def analyze_menu(menu_data):
    """
    Analyzes menu data and displays insights
    
    Args:
        menu_data (dict): Restaurant and menu information
    """
    # Extract restaurant name
    restaurant_name = menu_data["restaurant"]["name"]
    
    # Count items by category
    categories = {}
    veg_count = 0
    nonveg_count = 0
    spicy_count = 0
    
    for category in menu_data["menu"]:
        cat_name = category["category"]
        categories[cat_name] = len(category["items"])
        
        for item in category["items"]:
            if item["veg_nonveg"] == "Veg":
                veg_count += 1
            elif item["veg_nonveg"] == "Non-Veg":
                nonveg_count += 1
                
            if item["spice_level"] == "Spicy":
                spicy_count += 1
    
    # Display restaurant info
    display(HTML(f"<h3>Restaurant: {restaurant_name}</h3>"))
    display(HTML(f"<p><b>Location:</b> {menu_data['restaurant']['location']}</p>"))
    if menu_data['restaurant']['contact']:
        display(HTML(f"<p><b>Contact:</b> {menu_data['restaurant']['contact']}</p>"))
    
    # Display menu stats
    total_items = sum(categories.values())
    display(HTML(f"<p><b>Total menu items:</b> {total_items}</p>"))
    
    # Create and display category distribution
    plt.figure(figsize=(10, 6))
    plt.bar(categories.keys(), categories.values())
    plt.title(f"Menu Categories for {restaurant_name}")
    plt.xlabel("Category")
    plt.ylabel("Number of Items")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.show()
    
    # Display veg/non-veg distribution
    if veg_count + nonveg_count > 0:
        plt.figure(figsize=(8, 8))
        plt.pie([veg_count, nonveg_count], 
                labels=["Vegetarian", "Non-Vegetarian"], 
                autopct='%1.1f%%',
                colors=['green', 'red'])
        plt.title(f"Vegetarian vs Non-Vegetarian Items for {restaurant_name}")
        plt.tight_layout()
        plt.show()

    # Sample menu items from first category
    if menu_data["menu"] and menu_data["menu"][0]["items"]:
        display(HTML(f"<h4>Sample items from {menu_data['menu'][0]['category']}:</h4>"))
        sample_items = menu_data["menu"][0]["items"][:3]
        for item in sample_items:
            display(HTML(f"""
                <div style="margin-bottom: 10px; padding: 10px; border: 1px solid #ddd; border-radius: 5px;">
                    <h5>{item['name']} - {item['price']}</h5>
                    <p><span style="color: {'green' if item['veg_nonveg'] == 'Veg' else 'red'}">
                        {item['veg_nonveg']}
                    </span> | Spice Level: {item['spice_level']}</p>
                    <p><i>{item['description']}</i></p>
                </div>
            """))

# Restaurant URLs to scrape
restaurant_urls = {
    "prakash_hotel": "https://www.zomato.com/roorkee/hotel-prakash-restaurant-roorkee-locality/order",
    "pizza_hut": "https://www.zomato.com/roorkee/pizza-hut-roorkee-locality/order",
    "foodbay": "https://www.zomato.com/roorkee/foodbay-roorkee-locality/order",
    "desi_tadka": "https://www.zomato.com/roorkee/desi-tadka-2-roorkee-locality/order",
    "baap_of_rolls": "https://www.zomato.com/roorkee/baap-of-rolls-roorkee-locality/order"
}

# Example: Run the scraper on a single restaurant for demonstration
# Uncomment this cell to run for a single restaurant
"""
restaurant_key = "dominos"  # Change this to any key from restaurant_urls
url = restaurant_urls[restaurant_key]
menu_data = scrape_restaurant_menu(url, restaurant_key)
analyze_menu(menu_data)
"""

# To scrape all restaurants (this will take some time)
# Uncomment this cell to run for all restaurants
"""
collected_data = {}
for restaurant_key, url in restaurant_urls.items():
    try:
        menu_data = scrape_restaurant_menu(url, restaurant_key)
        collected_data[restaurant_key] = menu_data
        # Basic analysis for each restaurant
        analyze_menu(menu_data)
    except Exception as e:
        print(f" Failed to scrape {restaurant_key}: {str(e)}")
"""

# Function to compare vegetarian options across restaurants
def compare_veg_options(collected_data):
    """
    Compares vegetarian options across restaurants
    
    Args:
        collected_data (dict): Dictionary of restaurant menu data
    """
    restaurants = []
    veg_counts = []
    nonveg_counts = []
    
    for restaurant_key, data in collected_data.items():
        rest_name = data["restaurant"]["name"]
        restaurants.append(rest_name)
        
        veg = 0
        nonveg = 0
        for category in data["menu"]:
            for item in category["items"]:
                if item["veg_nonveg"] == "Veg":
                    veg += 1
                elif item["veg_nonveg"] == "Non-Veg":
                    nonveg += 1
        
        veg_counts.append(veg)
        nonveg_counts.append(nonveg)
    
    # Create grouped bar chart
    x = range(len(restaurants))
    width = 0.35
    
    plt.figure(figsize=(12, 8))
    plt.bar(x, veg_counts, width, label='Vegetarian', color='green')
    plt.bar([i + width for i in x], nonveg_counts, width, label='Non-Vegetarian', color='red')
    
    plt.xlabel('Restaurant')
    plt.ylabel('Number of Items')
    plt.title('Vegetarian vs Non-Vegetarian Menu Items by Restaurant')
    plt.xticks([i + width/2 for i in x], restaurants, rotation=45, ha='right')
    plt.legend()
    plt.tight_layout()
    plt.show()

# Load and analyze saved data (use this if you already saved the data)
def load_and_analyze():
    """
    Loads previously saved JSON data files and performs analysis
    """
    collected_data = {}
    for restaurant_key in restaurant_urls.keys():
        filepath = os.path.join("menu_data", f"{restaurant_key}_menu.json")
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                menu_data = json.load(f)
                collected_data[restaurant_key] = menu_data
                print(f"Loaded data for {menu_data['restaurant']['name']}")
    
    if collected_data:
        # Analyze a specific restaurant
        sample_key = list(collected_data.keys())[0]
        analyze_menu(collected_data[sample_key])
        
        # Compare across restaurants
        compare_veg_options(collected_data)
    else:
        print("No saved data found. Run the scraper first.")
