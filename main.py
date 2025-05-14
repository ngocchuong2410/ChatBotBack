import requests
from bs4 import BeautifulSoup
import time
import json
import random
import re
import csv
from urllib.parse import urljoin
import os

BASE_URL = "https://incidecoder.com"
INGREDIENTS_URL = f"{BASE_URL}/ingredients"

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/119.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": BASE_URL,
    "Connection": "keep-alive"
})

def get_soup(url, retries=3):
    for attempt in range(retries):
        try:
            time.sleep(random.uniform(2, 5))
            print(f"Fetching: {url}")
            response = session.get(url, timeout=30)
            if response.status_code == 200:
                return BeautifulSoup(response.text, 'html.parser')
            else:
                print(f"Error status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt+1}/{retries} failed: {e}")
            time.sleep(5)
    return None

def extract_text_if_exists(element):
    return element.get_text(strip=True) if element else ""

def extract_ingredient_links(max_pages=3):
    ingredient_links = []
    for page_num in range(1, max_pages + 1):
        url = INGREDIENTS_URL if page_num == 1 else f"{INGREDIENTS_URL}/p{page_num}"
        soup = get_soup(url)
        if not soup:
            break

        ingredients = []
        selectors = [
            '.detailpage-link', 'a.ingred-link', 'a.ingred-showinfo',
            '.ingred-showinfo', '.ingredname', 'li.main-list-item a'
        ]

        for selector in selectors:
            ingredients = soup.select(selector)
            if ingredients:
                break

        if not ingredients:
            ingredients = [a for a in soup.find_all('a') if '/ingredients/' in a.get('href', '')]

        for ingredient in ingredients:
            href = ingredient.get('href')
            if href and '/ingredients/' in href:
                full_url = urljoin(BASE_URL, href)
                if full_url not in ingredient_links:
                    ingredient_links.append(full_url)

    with open('ingredient_links.json', 'w', encoding='utf-8') as f:
        json.dump(ingredient_links, f, indent=2)
    return ingredient_links

def parse_ingredient_page(url):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch page: {response.status_code}")

    soup = BeautifulSoup(response.text, 'html.parser')

    # Tên thành phần
    name_tag = soup.find("h1", class_="css-1k1bwi")
    name = name_tag.text.strip() if name_tag else ""

    # Aliases
    aliases = []
    also_called = soup.find("div", class_="css-1s8pjh")
    if also_called and "Also-called-as" in also_called.text:
        alias_text = also_called.text.split("Also-called-as")[-1].strip()
        aliases = [a.strip() for a in alias_text.split(",")]

    # Description (from Details section)
    description = ""
    detail_div = soup.find("div", class_="css-9l3uo3")
    if detail_div:
        p_tag = detail_div.find("p")
        if p_tag:
            description = p_tag.get_text(strip=True)

    # What-it-does / Functions (under image)
    what_it_does = []
    functions_div = soup.find("div", class_="css-1ldok1t")
    if functions_div:
        function_tags = functions_div.find_all("a")
        what_it_does = [tag.get_text(strip=True) for tag in function_tags]

    # Ratings: Irritancy, Comedogenicity, Safety, EWG
    ratings = {
        "irritancy": None,
        "comedogenicity": None,
        "hazard_level": None,
        "ewg_rating": None,
    }
    box_divs = soup.find_all("div", class_="css-v03m4z")
    for div in box_divs:
        label = div.find("div", class_="css-1ij2v2b")
        value = div.find("div", class_="css-1jjc3lj")
        if label and value:
            label_text = label.text.strip().lower()
            value_text = value.text.strip()
            number = int(value_text) if value_text.isdigit() else None
            if "irritancy" in label_text:
                ratings["irritancy"] = number
            elif "comedogenicity" in label_text:
                ratings["comedogenicity"] = number
            elif "safety" in label_text or "hazard" in label_text:
                ratings["hazard_level"] = number
            elif "ewg" in label_text:
                ratings["ewg_rating"] = number

    return {
        "name": name,
        "aliases": aliases,
        "what_it_does": what_it_does,
        "irritancy": ratings["irritancy"],
        "comedogenicity": ratings["comedogenicity"],
        "hazard_level": ratings["hazard_level"],
        "ewg_rating": ratings["ewg_rating"],
        "description": description,
        "functions": what_it_does,
        "url": url,
        "last_updated": time.strftime('%Y-%m-%dT%H:%M:%S')
    }


def main():
    data = parse_ingredient_page("https://incidecoder.com/ingredients/panthenol")
    print(data)
    # if not os.path.exists("debug"):
    #     os.makedirs("debug")
    #
    # ingredient_links = extract_ingredient_links()
    # print(f"Found {len(ingredient_links)} ingredient links.")
    #
    # all_ingredients = []
    # start_index = 0
    #
    # if os.path.exists('ingredient_data_progress.json'):
    #     with open('ingredient_data_progress.json', 'r', encoding='utf-8') as f:
    #         all_ingredients = json.load(f)
    #         existing_urls = [item['url'] for item in all_ingredients]
    #         for i, link in enumerate(ingredient_links):
    #             if link in existing_urls:
    #                 start_index = i + 1
    #         print(f"Resuming from index {start_index}")
    #
    # max_ingredients = 5  # For testing
    # for i, link in enumerate(ingredient_links[start_index:start_index + max_ingredients]):
    #     print(f"Parsing {i + start_index + 1}/{len(ingredient_links)}: {link}")
    #     time.sleep(random.uniform(3, 6))
    #     data = parse_ingredient_page(link)
    #     if data:
    #         all_ingredients.append(data)
    #         with open('ingredient_data_progress.json', 'w', encoding='utf-8') as f:
    #             json.dump(all_ingredients, f, ensure_ascii=False, indent=2)
    #     else:
    #         print(f"Failed to parse {link}")
    #
    # if all_ingredients:
    #     print(all_ingredients)
    #     with open('ingredient_data_final.json', 'w', encoding='utf-8') as f:
    #         json.dump(all_ingredients, f, ensure_ascii=False, indent=2)
    #     with open('ingredient_data_final.csv', 'w', newline='', encoding='utf-8') as f:
    #         writer = csv.DictWriter(f, fieldnames=all_ingredients[0].keys())
    #         writer.writeheader()
    #         for row in all_ingredients:
    #             row_copy = row.copy()
    #             for key, value in row_copy.items():
    #                 if isinstance(value, list):
    #                     row_copy[key] = '|'.join(value)
    #             writer.writerow(row_copy)
    #     print(f"Saved {len(all_ingredients)} ingredients.")
    # else:
    #     print("No data collected.")

if __name__ == "__main__":
    main()
