import logging
from argparse import PARSER
from datetime import datetime

import requests
from bs4 import BeautifulSoup
import time
import json
import random
import re
import csv
from urllib.parse import urljoin
import os

from elkhelper import ElasticsearchHelper

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

# Thiết lập logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

es_helper = ElasticsearchHelper()
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
    """
    Parse a single ingredient page and extract required data.
    """
    logger.info(f"Scraping: {url}")
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise exception for HTTP errors

    except Exception as e:
        logger.error(f"Failed to access {url}: {str(e)}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract all text content first - this helps with debugging
    page_text = soup.get_text("\n", strip=True)

    # Initialize result dictionary
    result = {
        "name": "N/A",
        "aliases": [],
        "what_it_does": [],
        "irritancy": "N/A",
        "comedogenicity": "N/A",
        "hazard_level": "N/A",
        "ewg_rating": "N/A",
        "description": "",
        "functions": [],
        "url": url,
        "scrape_date": datetime.now().strftime("%Y-%m-%d"),
    }

    # Extract name - directly from h1 elements
    h1_elements = soup.find_all('h1')
    for h1 in h1_elements:
        if h1.text.strip() and len(h1.text.strip()) < 100:  # Avoid too long texts
            result["name"] = h1.text.strip()
            break

    # Extract aliases using regex
    alias_match = re.search(r'Also-called-like-this:\s*(.*?)(?:\n|What-it-does)', page_text, re.DOTALL)
    if alias_match:
        aliases_text = alias_match.group(1).strip()
        result["aliases"] = [alias.strip() for alias in re.split(r'[;,]', aliases_text) if alias.strip()]

    # Extract what-it-does using regex
    what_it_does_match = re.search(r'What-it-does:\s*(.*?)(?:\n|Irritancy)', page_text, re.DOTALL)
    if what_it_does_match:
        what_it_does_text = what_it_does_match.group(1).strip()
        # Split by commas, slashes, or specific separator
        result["what_it_does"] = [func.strip() for func in re.split(r'[,;/]', what_it_does_text) if func.strip()]
        result["functions"] = result["what_it_does"].copy()  # Copy to functions as well

    # Extract irritancy using regex
    irritancy_match = re.search(r'Irritancy:\s*(\d+|N/A)', page_text)
    if irritancy_match:
        result["irritancy"] = irritancy_match.group(1).strip()

    # Extract comedogenicity using regex
    comedogenicity_match = re.search(r'Comedogenicity:\s*(\d+|N/A)', page_text)
    if comedogenicity_match:
        result["comedogenicity"] = comedogenicity_match.group(1).strip()

    # Extract EWG/hazard rating - try multiple approaches
    # Method 1: Via regex from text
    ewg_match = re.search(r'EWG.*?(\d+)', page_text, re.IGNORECASE)
    if ewg_match:
        result["ewg_rating"] = ewg_match.group(1).strip()
        result["hazard_level"] = result["ewg_rating"]

    # Method 2: Try to find via DOM
    ewg_elements = soup.select('.ewg-rating, .ewg .rating-value, .ewg-value')
    for element in ewg_elements:
        text = element.get_text(strip=True)
        if text:
            # Try to extract number
            number_match = re.search(r'\d+', text)
            if number_match:
                result["ewg_rating"] = number_match.group(0)
                result["hazard_level"] = result["ewg_rating"]
                break

    # Extract description - approach via grey boxes or specific description blocks
    description_blocks = []

    # Method 1: Find paragraphs in specific classes
    desc_elements = soup.select('.ingredient-description p, .description p, .gray-box p')
    if desc_elements:
        for p in desc_elements:
            text = p.get_text(strip=True)
            if len(text) > 50:  # Only significant paragraphs
                description_blocks.append(text)

    # Method 2: Look for longer text blocks in the content
    if not description_blocks:
        content_blocks = soup.select('.content p, .main-content p')
        for p in content_blocks:
            text = p.get_text(strip=True)
            if len(text) > 100:  # Longer threshold for general content
                description_blocks.append(text)

    # Combine description blocks
    if description_blocks:
        result["description"] = ' '.join(description_blocks)
    else:
        # Attempt to find description in the text content
        desc_section = re.search(r'We have (better news|info|data|research).*?(\.).*', page_text)
        if desc_section:
            result["description"] = desc_section.group(0).strip()

    # Extract all functions - try to find "All Functions:" section
    all_functions_match = re.search(r'All Functions:\s*(.*?)(?:\n\*\*|\Z)', page_text, re.DOTALL)
    if all_functions_match:
        functions_text = all_functions_match.group(1).strip()
        all_functions = [func.strip() for func in re.split(r'[,;]', functions_text) if func.strip()]

        # Only update if we found something and the existing list is empty
        if all_functions and not result["functions"]:
            result["functions"] = all_functions

            # Also update what_it_does if empty
            if not result["what_it_does"]:
                result["what_it_does"] = all_functions

    # Add ID field for Elasticsearch - using name in lowercase and hyphenated
    result["id"] = url.split("/")[-1].lower() if "/" in url else re.sub(r'[^a-z0-9]', '-', result["name"].lower())

    logger.info(f"Extracted data for {result['name']}:")
    logger.info(f"- Aliases: {result['aliases']}")
    logger.info(f"- What it does: {result['what_it_does']}")
    logger.info(
        f"- Ratings: Irritancy={result['irritancy']}, Comedogenicity={result['comedogenicity']}, EWG={result['ewg_rating']}")

    return result

def main():
    if not os.path.exists("debug"):
        os.makedirs("debug")

    ingredient_links = extract_ingredient_links()
    print(f"Found {len(ingredient_links)} ingredient links.")

    all_ingredients = []
    start_index = 0

    if os.path.exists('ingredient_data_progress.json'):
        with open('ingredient_data_progress.json', 'r', encoding='utf-8') as f:
            all_ingredients = json.load(f)
            existing_urls = [item['url'] for item in all_ingredients]
            for i, link in enumerate(ingredient_links):
                if link in existing_urls:
                    start_index = i + 1
            print(f"Resuming from index {start_index}")

    max_ingredients = 5  # For testing
    for i, link in enumerate(ingredient_links[start_index:start_index + max_ingredients]):
        print(f"Parsing {i + start_index + 1}/{len(ingredient_links)}: {link}")
        time.sleep(random.uniform(3, 6))
        data = parse_ingredient_page(link)
        if data:
            all_ingredients.append(data)
            with open('ingredient_data_progress.json', 'w', encoding='utf-8') as f:
                json.dump(all_ingredients, f, ensure_ascii=False, indent=2)
        else:
            print(f"Failed to parse {link}")

    if all_ingredients:
        with open('ingredient_data_final.json', 'w', encoding='utf-8') as f:
            json.dump(all_ingredients, f, ensure_ascii=False, indent=2)
        with open('ingredient_data_final.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=all_ingredients[0].keys())
            writer.writeheader()
            for row in all_ingredients:
                row_copy = row.copy()
                for key, value in row_copy.items():
                    if isinstance(value, list):
                        row_copy[key] = '|'.join(value)
                writer.writerow(row_copy)
        print(f"Saved {len(all_ingredients)} ingredients.")
        inserted = es_helper.bulk_insert(all_ingredients)
        print(f"Inserted {inserted} ingredients into Elasticsearch.")
    else:
        print("No data collected.")

if __name__ == "__main__":
    main()

