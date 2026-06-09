# ==============================================================================
# scrape_data.py
# ==============================================================================
# HOW THIS FILE FITS INTO THE PROJECT:
# ------------------------------------
# This script represents STEP 1 of your data pipeline.
#
#   STEP 1: scraper/scrape_data.py     ← (THIS FILE) Fetches raw data from the web.
#   STEP 2: cleaning/clean_data.py     → Standardizes regions & metrics.
#   STEP 3: database/load_to_sqlite.py → Loads clean data into the SQL database.
#   STEP 4: dashboard/app.py           → Visualizes data in the UI web application.
# ==============================================================================

# ------------------------------------------------------------------------------
# SECTION 1: LIBRARY IMPORTS (Our Python Tool Belt)
# ------------------------------------------------------------------------------

import os
# "os" stands for Operating System. This library allows Python to interact with
# your computer's files and folders. We use it to calculate file paths dynamically 
# and build output data directories without breaking across Windows, Mac, or Linux.

import csv
# This built-in library manages standard comma-separated value spreadsheets. 
# We use its "DictWriter" engine to cleanly save our harvested data records array 
# straight into a tabular data text file.

import time
# This module deals with time tracking. We use it inside our data loop to 
# capture the exact second a row is parsed, appending a structured verification 
# timestamp ("Scraped_Timestamp") onto our records.

from selenium import webdriver
# "Selenium" is an advanced browser automation framework. Instead of merely requesting 
# static text, it boots up a real web browser instance programmatically, allowing 
# Python to click buttons, wait for animations, and interact with complex dynamic web layouts.

from selenium.webdriver.common.by import By
# The "By" class supplies standardized flag locators. It tells Selenium precisely 
# how to scan a webpage's underlying code structure (e.g., search by CSS Selector, 
# search by HTML Tag Name, or search by element ID).

from selenium.webdriver.support.ui import WebDriverWait
# This tool allows us to construct "Smart Waits". Instead of hardcoding arbitrary 
# pauses that waste time, it forces Python to pause and monitor the webpage, moving 
# forward the millisecond an item finishes loading.

from selenium.webdriver.support import expected_conditions as EC
# Often abbreviated as "EC", this library holds a collection of preset rules. 
# We combine it with WebDriverWait to say things like: "Wait until this header 
# element is physically visible on the screen before parsing its text."

from selenium.webdriver.firefox.service import Service as FirefoxService
# This service manager establishes the background communication link between 
# Python and the underlying Firefox web browser binary program on your computer drive.


# ------------------------------------------------------------------------------
# SECTION 2: METRIC UNIFICATION (Defensive Data Normalization)
# ------------------------------------------------------------------------------

def normalize_temperature(temp_text):
    """
    Takes any scraped temperature string and uniformly forces it into a standardized 
    Celsius string format (e.g., converts "70°F" or raw text numbers cleanly into "21 °C").

    WHY WE NEED IT:
    Websites frequently swap display settings based on global regional traffic. If 
    a server randomly serves us a Fahrenheit reading, this function converts the 
    underlying value programmatically so our downstream files don't mix up scale units.
    """
    # If the text block is completely blank or holds no reading data, exit immediately
    if not temp_text or temp_text == "N/A":
        return "N/A"
    
    clean_text = temp_text.strip()
    
    # Isolate numeric digits and mathematical minus signs, stripping away symbols/spaces
    digits = "".join([c for c in clean_text if c.isdigit() or c == '-'])
    if not digits:
        return temp_text
        
    try:
        value = int(digits)
        # CONVERSION RULE: If the scraped text contains an "F", or if it has no unit marker 
        # but the raw numeric value exceeds 45 (an impossible ambient Celsius reading), 
        # convert it to Celsius using the standard formula: (Fahrenheit - 32) * 5/9
        if "F" in clean_text or ("C" not in clean_text and value > 45):
            celsius_val = round((value - 32) * 5 / 9)
            return f"{celsius_val} °C"
        
        # If it was already a valid Celsius number, return it with our standard text suffix
        return f"{value} °C"
    except Exception:
        # If anything unexpected goes wrong during conversions, return the original text as a safety backup
        return temp_text


# ------------------------------------------------------------------------------
# SECTION 3: AUTOMATION ENGINE INITIALIZATION
# ------------------------------------------------------------------------------

def initialize_driver():
    """
    Locates and boots an isolated, self-contained Portable Firefox browser instance 
    without needing a traditional global system installation on your local machine.
    """
    # Define our workspace folder paths for our localized portable environments
    portable_root = "FirefoxPortable"
    gecko_driver = "geckodriver.exe"
    
    # Check both potential internal structural paths where the Portable executable may sit
    firefox_binary = os.path.join(portable_root, "App", "Firefox64", "firefox.exe")
    if not os.path.exists(firefox_binary):
        firefox_binary = os.path.join(portable_root, "App", "Firefox", "firefox.exe")

    # Configure advanced operational settings flags for the automation engine
    options = webdriver.FirefoxOptions()
    
    # "--headless" commands the browser to run invisibly in the computer's background memory. 
    # This prevents pop-up browser windows from interrupting you while you work.
    options.add_argument("--headless")
    
    # "eager" tells the driver to start scraping text layouts immediately once the main text 
    # structure lands, skipping slow, heavy external video/image file downloads.
    options.page_load_strategy = 'eager' 
    
    # Bind the calculated paths straight into our engine initialization settings
    options.binary_location = firefox_binary
    service = FirefoxService(executable_path=gecko_driver)
    
    # Launch and return the fully ready background browser control manager object
    return webdriver.Firefox(service=service, options=options)


# ------------------------------------------------------------------------------
# SECTION 4: NODE DECONSTRUCTION (Target Page Scraper)
# ------------------------------------------------------------------------------

def scrape_city_detail(driver, detail_url):
    """
    Navigates the background browser to a specific city URL, parses individual 
    HTML text blocks, and assembles a dictionary of current weather measurements.
    """
    # Tell the browser engine to load the city page link
    driver.get(detail_url)
    
    # Try to locate the main title heading to parse out geographical identities
    try:
        # Wait up to 4 seconds for the "h1" page title element to officially load
        header_element = WebDriverWait(driver, 4).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h1"))
        )
        # Strip away standard template prefix labels to isolate location names
        header_text = header_element.text.replace("Weather in ", "").strip()
    except Exception:
        # If the page completely fails to load or change layouts, cancel this row gracefully
        return {"City": None}

    # If the layout title contains a comma separator, split it into structural [City, Country] cells
    if "," in header_text:
        city = header_text.split(",")[0].strip()
        country = header_text.split(",")[1].strip()
    else:
        city = header_text
        country = "Global"

    # EXTRACTING TEMPERATURE VALUE
    try:
        # Target alternative web layout elements that host primary temperature markers
        raw_temp = driver.find_element(By.CSS_SELECTOR, "#qlook .h2, .bk-focus__qlook .h2").text
        temperature = normalize_temperature(raw_temp)
    except Exception:
        temperature = "N/A"

    # EXTRACTING CURRENT WEATHER CONDITION TEXT
    try:
        condition = driver.find_element(By.CSS_SELECTOR, "#qlook p, .bk-focus__qlook p").text.strip()
    except Exception:
        condition = "N/A"

    # Set up safe structural text fallback metrics in case tables differ across pages
    local_time, humidity, wind = "N/A", "N/A", "N/A"

    # RESILIENCE PASS 1: Isolate side-by-side summary tables for Time and Humidity
    try:
        # Locate all generic tables on the page
        tables = driver.find_elements(By.TAG_NAME, "table")
        for table in tables:
            table_text = table.text
            # Identify if this specific table holds text variables we need, skipping forecasts
            if ("Humidity" in table_text or "Time" in table_text) and "Forecast" not in table_text:
                rows = table.find_elements(By.TAG_NAME, "tr")
                for row in rows:
                    rt = row.text
                    # Extract the exact reading segment located next to data labels
                    if "Time" in rt and local_time == "N/A":
                        local_time = rt.replace("Current Time:", "").replace("Local Time:", "").replace("Time:", "").strip()
                    elif "Humidity" in rt and humidity == "N/A":
                        humidity = rt.replace("Humidity:", "").replace("Humidity", "").strip()
    except Exception:
        pass  # Quietly bypass errors to ensure minor table mutations don't crash our script

    # RESILIENCE PASS 2: Scan text strings for unstructured native Wind layouts
    try:
        # Search parent container paragraph layout blocks where unstructured raw text lists wind data
        text_elements = driver.find_elements(By.CSS_SELECTOR, "#qlook p, .bk-focus__qlook p, #qlook, .bk-focus__qlook")
        for element in text_elements:
            raw_text = element.text.strip()
            if "Wind:" in raw_text:
                # Isolate the exact wind speed text segment located immediately behind the "Wind:" tag
                after_wind = raw_text.split("Wind:")[1].strip()
                # Split off downstream lines or location data blocks to extract only the pure wind metric string
                clean_wind = after_wind.split("\n")[0].split("Location:")[0].strip()
                if clean_wind:
                    wind = clean_wind
                    break  # Exit row loop immediately once found
    except Exception:
        pass

    # GLOBAL BACKUP: If table logic missed the time string, target the site's live digital clock element ID
    if local_time == "N/A":
        try:
            clock_el = driver.find_element(By.ID, "bclt")
            if clock_el:
                local_time = clock_el.text.strip()
        except Exception:
            pass

    # Package our clean dataset variables into a structured dictionary object mapping pipeline specs
    return {
        "City": city,
        "Country": country,
        "Local_Time": local_time,
        "Condition": condition,
        "Temperature": temperature,
        "Humidity": humidity,
        "Wind": wind,
        "Short_Forecast": condition,
        "Scraped_Timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }


# ------------------------------------------------------------------------------
# SECTION 5: PIPELINE ORCHESTRATION LAYER (Main Crawler Core)
# ------------------------------------------------------------------------------

def scrape_weather_data():
    """
    The orchestrator function containing the structured line-by-line pipeline sequence.
    """
    base_url = "https://www.timeanddate.com/weather/"
    driver = initialize_driver()
    records = []

    try:
        print(f"[INFO] Connecting to local Firefox engine container: {base_url}")
        driver.get(base_url)
        
        # Gather all regional anchor links displayed inside the main directory index spreadsheet table
        city_links = WebDriverWait(driver, 6).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "table.zebra.fw.tb-theme tbody tr td a"))
        )
        
        # Loop through found elements and harvest their clean routing URLs
        detail_urls = []
        for link in city_links:
            href = link.get_attribute("href")
            if href and "/weather/" in href:
                # Split off trailing URL query tracking parameters to keep paths uniform
                detail_urls.append(href.split("?")[0])

        # Drop duplicate links by routing values through a Python dictionary key catalog
        unique_urls = list(dict.fromkeys(detail_urls))
        print(f"[INFO] Successfully cataloged {len(unique_urls)} unique system layout pathways.")

        active_batch = unique_urls

        # CRAWLER PROCESSING LOOP: Process every targeted city link systematically
        for index, url in enumerate(active_batch, start=1):
            print(f"[PROCESSING] [{index}/{len(active_batch)}] Target Node -> {url}")
            
            # Route our browser engine directly into individual city page layouts
            record = scrape_city_detail(driver, url)
            
            # If data extraction succeeded and a city was parsed, save it to our memory storage list
            if record["City"]:
                records.append(record)

    except Exception as e:
        print(f"[ERROR] Engine process runtime error: {e}")
        
    finally:
        # Crucial clean-up step. This kills background processes inside your computer memory 
        # so you don't accumulate dozens of frozen, hidden browser tasks.
        print("[INFO] Terminating isolated background browser instance...")
        driver.quit()

    # COMPUTE DYNAMIC PROJECT FOLDER EXPORT LOCATION Paths
    # Step up one layer from our script path folder to locate our primary database project data container
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(project_root, "data")
    
    # If the workspace 'data/' folder doesn't exist on disk, create it programmatically from scratch
    os.makedirs(data_dir, exist_ok=True)
    output_file = os.path.join(data_dir, "raw_data.csv")

    # CSV DATA SINK STREAM: If we harvested valid data lines, dump them onto disk
    if records:
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            # Tell CSV writer engine to use the dictionary keys of our first element as our column column headers
            writer = csv.DictWriter(f, fieldnames=records[0].keys())
            writer.writeheader()
            writer.writerows(records)
            
        print(f"\n[SUCCESS] Pipeline extraction complete! File generated at: {output_file}")
    
    return records


# ------------------------------------------------------------------------------
# SECTION 6: SCRIPT BOOTSTRAPPER (The Python Execution Guard)
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    # This statement guarantees that code blocks execute only if someone runs this 
    # file directly from a terminal window via "python scraper/scrape_data.py".
    scrape_weather_data()