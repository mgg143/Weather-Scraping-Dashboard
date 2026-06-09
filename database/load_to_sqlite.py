# ==============================================================================
# load_to_sqlite.py
# ==============================================================================
# HOW THIS FILE FITS INTO THE PROJECT:
# ------------------------------------
# This script represents STEP 3 of your data pipeline.
#
#   STEP 1: scraper/scrape_data.py     → Fetches raw weather data from web.
#   STEP 2: cleaning/clean_data.py     → Standardizes regions & metrics.
#   STEP 3: database/load_to_sqlite.py ← (THIS FILE) Hydrates the local database.
#   STEP 4: dashboard/app.py           → Visualizes data in the UI web application.
# ==============================================================================

# ------------------------------------------------------------------------------
# SECTION 1: LIBRARY IMPORTS (Our Python Tool Belt)
# ------------------------------------------------------------------------------

import os
# "os" stands for Operating System. This library allows Python to talk to your
# computer's file system. We use it to calculate file paths dynamically, ensuring 
# the script works perfectly whether it runs on a Mac, Windows, or Linux machine.

import sys
# "sys" stands for System. It handles system-specific parameters and functions.
# Here, we use "sys.exit(1)" to stop the entire script immediately if a critical 
# file is missing, preventing downstream components from crashing silently.

import sqlite3
# "sqlite3" is a built-in Python library for working with SQLite databases.
# SQLite is perfect for small projects because it stores the entire database in a 
# single file on your hard drive, requires zero server installations, and works 
# instantly anywhere Python can run.

import pandas as pd
# "pandas" is our data manipulation engine. Here, we use it to read our polished 
# clean_data.csv file into memory and natively translate it directly into an 
# optimized SQL table structure.


# ------------------------------------------------------------------------------
# SECTION 2: MAIN LOADING CORE
# ------------------------------------------------------------------------------

def main():
    """
    The orchestrator function containing the structured line-by-line pipeline sequence.
    """

    # --------------------------------------------------------------------------
    # Step 2.1: Compute Dynamic Project File Paths
    # --------------------------------------------------------------------------
    # Find out exactly where this specific load_to_sqlite.py file lives on the drive
    database_dir = os.path.dirname(os.path.abspath(__file__))
    # Step out one folder layer up to find the root workspace directory
    project_root = os.path.dirname(database_dir)
    # Target the "data" subfolder where our files are organized
    data_dir = os.path.join(project_root, "data")

    # Construct explicit paths to our target input and output files
    clean_file = os.path.join(data_dir, "clean_data.csv")
    db_path = os.path.join(data_dir, "cleaned_data.db")

    # --------------------------------------------------------------------------
    # Step 2.2: Verify Input Files & Load Data
    # --------------------------------------------------------------------------
    # Check if clean_data.csv exists on the computer disk. If missing, sound an alarm.
    if not os.path.exists(clean_file):
        print(
            "[ERROR] clean_data.csv not found.\n"
            f"Expected location: {clean_file}\n"
            "Please run 'python cleaning/clean_data.py' first to generate it."
        )
        sys.exit(1)

    # Attempt to load our polished clean CSV data into an active Pandas DataFrame
    try:
        df = pd.read_csv(clean_file)
    except Exception as e:
        print(f"[ERROR] Failed to read clean_data.csv: {e}")
        sys.exit(1)

    # --------------------------------------------------------------------------
    # Step 2.3: Establish Database Connection
    # --------------------------------------------------------------------------
    # Open a connection bridge to the SQLite file. If the 'cleaned_data.db' file 
    # doesn't exist yet, SQLite will automatically create it from scratch!
    try:
        conn = sqlite3.connect(db_path)
    except Exception as e:
        print(f"[ERROR] Failed to connect to SQLite database: {e}")
        sys.exit(1)

    # --------------------------------------------------------------------------
    # Step 2.4: Stream DataFrame to SQLite Table
    # --------------------------------------------------------------------------
    try:
        # WHY YOUR USERS ARE SAFE FROM MANUAL DELETIONS:
        # ----------------------------------------------
        # By utilizing 'if_exists="replace"', Pandas runs an explicit SQL command 
        # behind the scenes: "DROP TABLE IF EXISTS weather;". 
        # This completely vaporizes the old table structure and old data rows 
        # before building a brand-new table. No historical data remnants can survive!
        df.to_sql("weather", conn, if_exists="replace", index=False)
        
    except Exception as e:
        print(f"[ERROR] Failed to write data to SQLite table 'weather': {e}")
        # If writing fails, close the connection cleanly before exiting to avoid memory leaks
        conn.close()
        sys.exit(1)

    # Close the database connection to release the memory lock safely
    conn.close()

    # --------------------------------------------------------------------------
    # Step 2.5: User Feedback Logs
    # --------------------------------------------------------------------------
    # Print out clear confirmations and absolute file paths so beginners can 
    # track down exactly where their files are located.
    print(f"[SUCCESS] Data loaded into SQLite database successfully!")
    print(f"[INFO] Absolute DB Path: {os.path.abspath(db_path)}")
    print("[INFO] Target Table Name: weather")
    print(f"[INFO] Total Clean Rows Hydrated: {len(df)}")


# ------------------------------------------------------------------------------
# SECTION 3: SCRIPT BOOTSTRAPPER (The Python Execution Guard)
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    # This statement guarantees that code blocks execute only if someone runs this 
    # file directly from a terminal window via "python database/load_to_sqlite.py".
    main()