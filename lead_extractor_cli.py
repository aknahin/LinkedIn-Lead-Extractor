# =============================================================================
# LinkedIn Lead Extractor (CLI Version)
#
# Author: AK Nahin
# Website: https://aknahin.com
#
# Description: This script uses the Google Custom Search API to find public
#              contact information associated with LinkedIn profiles. It
#              extracts data from Google's search snippets, not by scraping
#              LinkedIn directly.
# =============================================================================

import requests
import os
import json
import re
import time
import pandas as pd
from datetime import datetime

# --- Configuration ---
CONFIG_FILE = 'google_search_config.json'
HISTORY_FILE = 'search_history.json'
OUTPUT_FOLDER = 'extracted_leads'

def display_linkedin_logo():
    # Displays a minimal "in" logo for LinkedIn-Lead-Extractor
    logo = r"""
  _                                 _ _     
 (_)                               (_) |    
  _ _ __ ______ ___ _ __ ___   __ _ _| |___ 
 | | '_ \______/ _ \ '_ ` _ \ / _` | | / __|
 | | | | |    |  __/ | | | | | (_| | | \__ \
 |_|_| |_|     \___|_| |_| |_|\__,_|_|_|___/
                                            
                                            
    """
    print(logo)

def load_or_create_config():
    """Loads API configuration from a file or prompts the user to create it."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    else:
        print("--- Google API Configuration (First-time setup) ---")
        api_key = input("Enter your Google Custom Search API key: ")
        cx = input("Enter your Google Custom Search Engine ID (cx): ")
        config = {"api_key": api_key, "cx": cx}
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f)
        print("✅ Configuration saved to google_search_config.json\n")
        return config

def google_search(query, api_key, cx, start_index=1, max_retries=3):
    """Performs a Google search and handles retries and quota errors."""
    for attempt in range(max_retries):
        try:
            url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={api_key}&cx={cx}&start={start_index}"
            res = requests.get(url, timeout=15)
            if res.status_code == 200:
                return res.json().get('items', [])
            elif "quota" in res.text.lower():
                print("🚫 Google API quota limit reached. Cannot continue.")
                return []
            else:
                print(f"⚠️ API Error: {res.status_code} - {res.text}")
        except requests.exceptions.RequestException as e:
            print(f"Network error on attempt {attempt + 1}/{max_retries}: {e}")
        
        if attempt < max_retries - 1:
            print(f"Retrying in 3 seconds...")
            time.sleep(3)
            
    print("❌ Failed to fetch results after multiple retries.")
    return []

def extract_emails(text):
    """Uses regex to find unique email addresses from a block of text."""
    return list(set(re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b', text)))

def extract_phones(text):
    """Uses a flexible regex to find unique phone numbers."""
    return list(set(re.findall(r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}', text)))

def save_history(entry):
    """Saves a record of the search to a history file."""
    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            try:
                history = json.load(f)
            except json.JSONDecodeError:
                history = [] # Overwrite if corrupted
    history.append(entry)
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

def ensure_output_folder():
    """Creates the output folder if it doesn't exist"""
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

def main():
    """Main function to run the command-line interface."""
    display_linkedin_logo()
    config = load_or_create_config()
    api_key, cx = config["api_key"], config["cx"]
    ensure_output_folder()

    print("--- LinkedIn Lead Extractor ---")
    title_input = input("Enter the title you're looking for (e.g. realtor): ").strip()
    area = input("Enter the area or city (e.g. Phoenix): ").strip()
    target_count = int(input("How many contacts do you want to extract? ").strip())
    email_provider = input("Enter an email provider to search for (e.g. gmail.com): ").strip()

    collected = []
    seen_links = set()
    query = f'site:linkedin.com/in/ "{title_input}" "{area}" "{email_provider}"'
    print(f"\nSearching Google with query: {query}\n")
    start_index = 1
    
    while len(collected) < target_count:
        print(f"Searching... Found {len(collected)}/{target_count} contacts so far.")
        results = google_search(query, api_key, cx, start_index=start_index)
        if not results:
            print("No more Google results found.")
            break

        for item in results:
            link = item.get('link')
            if not link or link in seen_links:
                continue
            seen_links.add(link)

            name = item.get('title', '').split(' - ')[0].strip()
            snippet = item.get('snippet', '')
            search_text = name + " " + snippet

            emails = extract_emails(search_text)
            phones = extract_phones(search_text)
            
            if emails:
                collected.append({
                    "Name": name,
                    "Email": emails[0],
                    "Phone": phones[0] if phones else "N/A",
                    "LinkedIn": link
                })
                print(f"  -> Found: {name} | Email: {emails[0]}")

            if len(collected) >= target_count:
                break
        
        start_index += 10
        if len(collected) < target_count:
            time.sleep(2)

    if collected:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        base_filename = f"{title_input}_{area}_{timestamp}".replace(" ", "_")

        df = pd.DataFrame(collected)
        excel_file = os.path.join(OUTPUT_FOLDER, base_filename + ".xlsx")
        csv_file = os.path.join(OUTPUT_FOLDER, base_filename + ".csv")
        df.to_excel(excel_file, index=False)
        df.to_csv(csv_file, index=False)

        print(f"\n✅ Success! Saved {len(collected)} contacts:")
        print(f"   - Excel file: {excel_file}")
        print(f"   - CSV file:   {csv_file}")

        save_history({
            "title": title_input,
            "area": area,
            "timestamp": timestamp,
            "count": len(collected),
            "files": [excel_file, csv_file]
        })

    else:
        print("\n❌ No data was collected. Try a broader search (e.g., different title or area).")

if __name__ == "__main__":
    main()