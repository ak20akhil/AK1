#!/usr/bin/env python3
"""
Dice.com Job Application Script
Runs on GitHub Actions
"""

import os
import sys
import time
import random
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

def simulate_typing(element, text):
    """Type like a human"""
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(0.05, 0.15))

def human_pause(min_sec=1, max_sec=3):
    """Human-like pause"""
    time.sleep(random.uniform(min_sec, max_sec))

def init_driver():
    """Initialize Chrome for GitHub Actions"""
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    print("[Driver] 🖥️  Chrome initialized")
    return driver

def login(driver, email, password):
    """Login to Dice.com"""
    print(f"[Login] 🔐 Logging in as {email}...")
    driver.get("https://www.dice.com/dashboard/login")
    wait = WebDriverWait(driver, 15)
    
    try:
        # Email
        email_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "input[type='email']")))
        email_input.clear()
        simulate_typing(email_input, email)
        human_pause(1, 2)
        
        continue_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Continue')]")))
        driver.execute_script("arguments[0].click();", continue_btn)
        human_pause(2, 3)
        
        # Password
        password_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "input[type='password']")))
        password_input.clear()
        simulate_typing(password_input, password)
        human_pause(1, 2)
        
        signin_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Sign In')]")))
        driver.execute_script("arguments[0].click();", signin_btn)
        human_pause(5, 7)
        
        if "dashboard" in driver.current_url or "jobs" in driver.current_url:
            print("[Login] ✅ Success")
            return True
        
        print(f"[Login] ❌ Failed")
        driver.save_screenshot("login_error.png")
        return False
        
    except Exception as e:
        print(f"[Login] ❌ Error: {e}")
        return False

def get_overview_text(driver):
    """Get job overview"""
    try:
        section = driver.find_element(By.XPATH, "//section[@aria-label='Job Details']")
        return section.text.strip().lower()
    except:
        return ""

def check_eligibility(driver):
    """Check if job is eligible (C2C/Contract)"""
    overview = get_overview_text(driver)
    overview_lines = [line.strip() for line in overview.splitlines()]
    
    has_c2c = any("corp to corp" in line for line in overview_lines)
    
    valid_terms = ["contract - 3", "contract - 6", "contract - 9", "contract - 12", "contract - independent"]
    has_valid_term = any(term in overview_lines for term in valid_terms)
    
    strict_skip = ["w2", "contract - w2", "full time", "full-time"]
    is_w2_only = any(skip in overview_lines for skip in strict_skip)
    
    if is_w2_only and not (has_c2c or has_valid_term):
        print("[Eligibility] ❌ W2/FT only")
        return False
    
    print("[Eligibility] ✅ Eligible")
    return True

def apply_easy(driver):
    """Apply using Easy Apply"""
    try:
        apply_btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "applyButton")))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", apply_btn)
        human_pause(1, 2)
        apply_btn.click()
        
        WebDriverWait(driver, 10).until(EC.url_contains("/apply"))
        human_pause(2, 3)
        
        try:
            next_btn = WebDriverWait(driver, 8).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Next')]")))
            next_btn.click()
            human_pause(2, 3)
        except:
            pass
        
        WebDriverWait(driver, 10).until(EC.url_contains("/apply/submit"))
        human_pause(2, 3)
        
        submit_btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Submit')]")))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_btn)
        human_pause(1, 2)
        submit_btn.click()
        human_pause(2, 3)
        
        print("[Apply] ✅ Success")
        return True
        
    except Exception as e:
        print(f"[Apply] ❌ Failed: {e}")
        return False

def main():
    if len(sys.argv) < 4:
        print("Usage: python apply_job.py <job_url> <job_title> <email> <password>")
        sys.exit(1)
    
    job_url = sys.argv[1]
    job_title = sys.argv[2]
    email = sys.argv[3]
    password = sys.argv[4]
    
    print(f"\n{'='*70}")
    print(f"[Start] 🚀 Applying to: {job_title}")
    print(f"{'='*70}\n")
    
    driver = None
    
    try:
        driver = init_driver()
        
        if not login(driver, email, password):
            print("FAILED: Login failed")
            sys.exit(1)
        
        print(f"[Job] 📝 Opening job...")
        driver.get(job_url)
        human_pause(3, 5)
        
        driver.execute_script("window.scrollBy(0, 400)")
        human_pause(2, 3)
        
        if not check_eligibility(driver):
            print("SKIPPED: Not eligible")
            sys.exit(2)
        
        if apply_easy(driver):
            print("\nSUCCESS: Applied")
            sys.exit(0)
        else:
            print("\nFAILED: Could not apply")
            sys.exit(1)
            
    except Exception as e:
        print(f"\nFAILED: {e}")
        sys.exit(1)
        
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()
