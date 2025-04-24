import time
import re
import os
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

def scrape_zomato(url, filename="zomato_menu.json"):
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.7049.115 Safari/537.36")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.get(url)
    time.sleep(4)
    try:
        while True:
            read_more_buttons = driver.find_elements(By.XPATH, "//span[contains(translate(text(), 'READ MORE', 'read more'), 'read more')]")
            if not read_more_buttons:
                break
            for btn in read_more_buttons:
                try:
                    driver.execute_script("arguments[0].click();", btn)
                except Exception:
                    pass
            time.sleep(0.5)
    except Exception:
        pass

    soup = BeautifulSoup(driver.page_source, "lxml")
    driver.quit()

    restaurant_info = {}
    rest_name = soup.find("h1")
    restaurant_info["name"] = rest_name.get_text(strip=True) if rest_name else ""

    location = ""
    loc_tag = soup.find("div", class_=re.compile("sc-clNaTc"))
    if loc_tag:
        location = loc_tag.get_text(strip=True)
    restaurant_info["location"] = location

    contact = ""
    phone_tag = soup.find("a", href=re.compile(r"tel:"))
    if phone_tag:
        contact = phone_tag.get_text(strip=True)
    restaurant_info["contact"] = contact

    menu_data = []
    menu_sections = soup.find_all("section", class_=re.compile("sc-bZVNgQ"))
    for section in menu_sections:
        cat_tag = section.find("h4")
        category = cat_tag.get_text(strip=True) if cat_tag else ""
        category_data = {"category": category, "items": []}
        item_blocks = section.find_all("div", class_=re.compile("sc-jhLVlY"))
        for item in item_blocks:
            veg_type = "Unknown"
            veg_div = item.find("div", class_=re.compile("sc-gcpVEs"))
            if veg_div and veg_div.has_attr("type"):
                if veg_div["type"] == "veg":
                    veg_type = "Veg"
                elif veg_div["type"] == "non-veg":
                    veg_type = "Non-Veg"
            name_tag = item.find("h4", class_=re.compile("sc-cGCqpu"))
            name = name_tag.get_text(strip=True) if name_tag else ""
            price_tag = item.find("span", class_=re.compile("sc-17hyc2s-1"))
            price = price_tag.get_text(strip=True) if price_tag else ""
            desc_tag = item.find("p", class_=re.compile("sc-gsxalj"))
            desc = ""
            if desc_tag:
                for rm in desc_tag.find_all("span", string=re.compile("read more", re.I)):
                    rm.extract()
                desc = desc_tag.get_text(" ", strip=True)
            spice_level = "Spicy" if re.search(r"spicy|fiery|peri peri|chilli|hot", desc, re.I) else "Normal"
            if name:
                category_data["items"].append({
                    "name": name,
                    "price": price,
                    "description": desc,
                    "veg_nonveg": veg_type,
                    "spice_level": spice_level
                })
        if category_data["items"]:
            menu_data.append(category_data)

    print("Restaurant:", restaurant_info["name"])
    print("Location:", restaurant_info["location"])
    print("Contact:", restaurant_info["contact"])
    if menu_data:
        print("Sample menu items:", menu_data[0]["items"][:3])
    else:
        print("No menu items found.")

    os.makedirs("menu", exist_ok=True)
    filepath = os.path.join("menu", filename)
    final_data = {
        "restaurant": restaurant_info,
        "menu": menu_data
    }
    with open(filepath, 'w') as f:
        json.dump(final_data, f, indent=4)
    print(f"Saved to {filepath}")

urls = {
    "prakash_hotel": "https://www.zomato.com/roorkee/hotel-prakash-restaurant-roorkee-locality/order",
    "pizza_hut": "https://www.zomato.com/roorkee/pizza-hut-roorkee-locality/order",
    "foodbay": "https://www.zomato.com/roorkee/foodbay-roorkee-locality/order",
    "desi_tadka": "https://www.zomato.com/roorkee/desi-tadka-2-roorkee-locality/order",
    "baap_of_rolls": "https://www.zomato.com/roorkee/baap-of-rolls-roorkee-locality/order"
}

for name, url in urls.items():
    print(f"\n==> Scraping {name} from {url}")
    filename = f"{name}_menu.json"
    try:
        scrape_zomato(url, filename)
    except Exception as e:
        print(f" Failed to scrape {name}: {e}")
