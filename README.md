# Weather-Scraping-Dashboard
This project uses Selenium to scrape data from a live website, clean and structure it with Pandas, save it to CSV and SQLite, and later visualize insights through an interactive Streamlit dashboard. It builds a full pipeline from raw web data to an explorable web app.

=====

This project builds a complete, end‑to‑end data pipeline using real‑world web scraping, data cleaning, database storage, and interactive visualization. The goal is to extract structured information from a live website (such as Weather Around the World or another approved source), transform it into a clean dataset, store it in a SQLite database, and present insights through an interactive Streamlit dashboard.

The final result is a fully functional application that demonstrates the entire lifecycle of data: collection → cleaning → storage → analysis → visualization.

### PROJECT COMPONENTS

1. Web Scraping (Selenium)
  * Automates a browser to retrieve dynamic web content
  * Handles missing tags, pagination, and inconsistent HTML
  * Extracts structured fields from each result
  * Saves raw scraped data to a CSV file

2. Data Cleaning and Transformation (Pandas)
  * Loads the raw CSV into a DataFrame
  * Removes duplicates, fixes malformed entries, and fills missing values
  * Applies transformations, grouping, or filtering
  * Saves the cleaned dataset into a SQLite database

3. Database Storage (SQLite)
  * Stores cleaned data in a relational database
  * Allows efficient querying and filtering
  * Supports both command‑line and programmatic access

4. Interactive Dashboard (Streamlit)
  * Displays the cleaned dataset and insights
  * Includes at least three interactive visualizations
  * Provides dropdowns, sliders, and filters for user exploration
  * Updates visualizations dynamically based on user input

======

### REPOSITORY STRUCTURE
```
project/
├── scraper/
│   └── scrape_data.py
├── cleaning/
│   └── clean_data.py
├── database/
│   └── load_to_sqlite.py
├── dashboard/
│   └── app.py
├── data/
│   ├── raw_data.csv
│   └── cleaned_data.db
├── README.md
└── requirements.txt
```
====

### SETUP INSTRUCTIONS

1) Clone the repository:
```
git clone https://github.com/mgg143/weather-scraping-dashboard.git
cd weather-scraping-dashboard
```

2) Create and activate a virtual environment:
```
python -m venv venv
source venv/bin/activate        (macOS/Linux)
venv\Scripts\activate           (Windows)
```
3) Install dependencies:
```
pip install -r requirements.txt
```
====

### RUNNING THE PROJECT

1) Run the web scraper:
```
python scraper/scrape_data.py
```
2) Run the cleaning script:
```
python cleaning/clean_data.py
```
3) Load cleaned data into SQLite:
```
python database/load_to_sqlite.py
```
4) Launch the Streamlit dashboard:
```
streamlit run dashboard/app.py
```
====

### PROJECT GOALS

This project demonstrates the ability to:
  * Automate data collection from dynamic websites
  * Clean and structure messy real-world data
  * Build and query a SQLite database
  * Create interactive, web-based visualizations
  * Organize code into logical modules
  * Use GitHub branches and pull requests for version control
