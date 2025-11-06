#!/usr/bin/env python3
"""
Dice.com Job Scraper
Reads filters from Google Sheets and saves jobs to queue
"""

import os
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
GOOGLE_CREDS_JSON = os.getenv("GOOGLE_CREDENTIALS")

def get_sheets_client():
    creds_dict = json.loads(GOOGLE_CREDS_JSON)
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

def read_job_filters():
    gc = get_sheets_client()
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    sheet = spreadsheet.worksheet("JOB_FILTERS")
    records = sheet.get_all_records()
    print(f"[Filters] 📋 Found {len(records)} filters")
    return records

def scrape_dice_jobs(keyword, location, posted_date="ONE", max_pages=5):
    print(f"\n[Scrape] 🔍 {keyword} in {location}")
    all_jobs = []
    
    for page in range(1, max_pages + 1):
        url = f'https://www.dice.com/jobs?q="{keyword}"&location={location}&filters.postedDate={posted_date}&filters.easyApply=true&page={page}'
        
        try:
            print(f"[Page {page}]...", end=" ")
            response = requests.get(url, timeout=30)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_links = soup.find_all('a', {'data-testid': 'job-search-job-card-link'})
            
            for link in job_links:
                href = link.get('href')
                if href and '/job-detail/' in href:
                    full_url = f"https://www.dice.com{href}" if not href.startswith('http') else href
                    
                    title_elem = link.find('span', {'data-testid': 'job-title'})
                    title = title_elem.get_text(strip=True) if title_elem else "Unknown"
                    
                    all_jobs.append({
                        'job_url': full_url,
                        'job_title': title,
                        'keyword': keyword,
                        'discovered_at': datetime.now().isoformat(),
                        'status': 'Pending'
                    })
            
            print(f"Found {len(job_links)} jobs")
            
        except Exception as e:
            print(f"Error: {e}")
    
    return all_jobs

def save_to_job_queue(jobs):
    if not jobs:
        print("[Queue] No jobs to save")
        return
    
    gc = get_sheets_client()
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    sheet = spreadsheet.worksheet("JOB_QUEUE")
    
    existing_data = sheet.get_all_records()
    existing_urls = {row['job_url'] for row in existing_data if 'job_url' in row}
    
    new_jobs = [job for job in jobs if job['job_url'] not in existing_urls]
    
    if not new_jobs:
        print(f"[Queue] ✅ All jobs already queued")
        return
    
    for job in new_jobs:
        sheet.append_row([job['job_url'], job['job_title'], job['keyword'], job['discovered_at'], job['status']])
    
    print(f"[Queue] ✅ Added {len(new_jobs)} new jobs")

def main():
    print("=" * 70)
    print("🔍 Dice Job Scraper")
    print("=" * 70)
    
    filters = read_job_filters()
    all_jobs = []
    
    for filter_row in filters:
        keyword = filter_row.get('Keyword', '')
        location = filter_row.get('Location', 'Remote')
        posted_date = filter_row.get('PostedDate', 'ONE')
        
        if keyword:
            jobs = scrape_dice_jobs(keyword, location, posted_date, max_pages=5)
            all_jobs.extend(jobs)
    
    unique_jobs = {job['job_url']: job for job in all_jobs}.values()
    
    print(f"\n{'='*70}")
    print(f"[Summary] 📊 Total: {len(unique_jobs)} unique jobs")
    print(f"{'='*70}\n")
    
    save_to_job_queue(list(unique_jobs))
    print("✅ Done!")

if __name__ == "__main__":
    main()
