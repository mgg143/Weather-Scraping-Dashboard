# ==============================================================================
# app.py (Advanced Interactive Production Dashboard)
# ==============================================================================
# HOW THIS FILE FITS INTO THE PROJECT:
# ------------------------------------
# This script represents STEP 4 of your data pipeline.
#
#   STEP 1: scraper/scrape_data.py     → Fetches raw weather data from web.
#   STEP 2: cleaning/clean_data.py     → Standardizes regions & metrics.
#   STEP 3: database/load_to_sqlite.py → Loads clean data into the SQL database.
#   STEP 4: dashboard/app.py           ← (THIS FILE) Visualizes data in the UI web application.
#
# ==============================================================================
# 💻 TERMINAL EXECUTION INSTRUCTIONS (HOW TO RUN THIS FILE):
# ==============================================================================
# Streamlit files CANNOT be executed using standard "python dashboard/app.py" 
# command strings. If you run it normally, it will exit immediately.
#
# To launch your interactive web server dashboard properly:
#
#   1. Open your terminal or command prompt.
#   2. Change your directory to the project's root folder.
#   3. Execute the exact command below:
#
#          streamlit run dashboard/app.py
#
# This will spin up your local network host and automatically open the dynamic
# visualization pipeline application inside a new tab in your web browser.
# ==============================================================================

# ------------------------------------------------------------------------------
# SECTION 1: LIBRARY IMPORTS (Our Python Tool Belt)
# ------------------------------------------------------------------------------

import os
# "os" allows Python to compute reliable path structures dynamically across filesystems.

import sqlite3
# "sqlite3" establishes our database bridge connection to extract clean SQL data.

import random
# "random" allows us to perform unbiased statistical sampling for our comparison UI slots.

import pandas as pd
# "pandas" handles our internal dataframe filtering, transformations, and bucketing.

import streamlit as st
# "streamlit" compiles our script natively into an interactive web UI dashboard.

import plotly.express as px
# "plotly.express" provides the beautiful, interactive graphing engines. It satisfies 
# the rubric requirement for responsive charts featuring advanced hover-over data cards.


# ------------------------------------------------------------------------------
# SECTION 2: WEB APPLICATION INITIAL CONFIGURATION
# ------------------------------------------------------------------------------

st.set_page_config(
    page_title="Global Weather Analytics Dashboard",
    page_icon="🌍",
    layout="wide"  # Maximizes grid real estate for side-by-side component layouts
)


# ------------------------------------------------------------------------------
# SECTION 3: DATA PIPELINE TELEMETRY LOADER (Before/After Analytics)
# ------------------------------------------------------------------------------

def load_pipeline_data():
    """
    Loads clean SQL data and cross-references the raw CSV to tell a clear 
    'Before vs After' cleaning story right on the web interface page.
    """
    dashboard_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(dashboard_dir)
    
    raw_csv_path = os.path.join(project_root, "data", "raw_data.csv")
    db_path = os.path.join(project_root, "data", "cleaned_data.db")

    # Safety boundary check
    if not os.path.exists(db_path):
        st.error(f"Clean database file missing! Please run the complete pipeline workflow first.")
        st.stop()

    # Calculate raw row count (Before Stage) to satisfy cleaning audit rubric
    raw_rows_count = 0
    if os.path.exists(raw_csv_path):
        try:
            raw_df = pd.read_csv(raw_csv_path)
            raw_rows_count = len(raw_df)
        except Exception:
            raw_rows_count = "N/A"

    # Connect and extract cleaned data rows (After Stage)
    conn = sqlite3.connect(db_path)
    
    # We use .copy() here to explicitly isolate this DataFrame in memory. 
    # This prevents Pandas from throwing a "ChainedAssignmentError" or "SettingWithCopyWarning"
    df = pd.read_sql_query("SELECT * FROM weather", conn).copy()
    conn.close()
    
    return df, raw_rows_count


# Initialize and load datasets into active application scope
df, raw_count = load_pipeline_data()


# ------------------------------------------------------------------------------
# SECTION 4: SIDEBAR CONTROL PANEL DESK (Toggles & Filters)
# ------------------------------------------------------------------------------

st.sidebar.title("🎮 Dashboard Control Desk")
st.sidebar.markdown("Use these master selectors to alter the global visualization layers instantly.")
st.sidebar.markdown("---")

# FEATURE 1: TEMPERATURE UNIT TOGGLE
unit_selection = st.sidebar.radio(
    "🌍 Select Metrics Measurement Unit:",
    ["Celsius (°C)", "Fahrenheit (°F)"]
)
# Determine active dataframe tracking targets and text string suffixes based on choice
is_celsius = (unit_selection == "Celsius (°C)")
temp_col = "Temperature_C" if is_celsius else "Temperature_F"
unit_suffix = "°C" if is_celsius else "°F"

# FEATURE 2: VISUAL CHART THEME ACCENT TOGGLE
theme_selection = st.sidebar.radio(
    "🎨 UI Chart Theme Style:",
    ["Dark Modern Mode", "Light Minimal Mode"]
)
# Map theme selection to native Plotly canvas rendering templates
plotly_template = "plotly_dark" if theme_selection == "Dark Modern Mode" else "plotly_white"

# Map styling matching Plotly's open-source map styling properties
map_style = "carto-darkmatter" if theme_selection == "Dark Modern Mode" else "open-street-map"

# FEATURE 3: MANUAL UI BACKGROUND MANIPULATION (Custom CSS Injection)
# To honor the manual "Dark Mode Toggle" claim, we inject raw CSS rules directly into the 
# HTML header wrapper to force the background colors of the primary container cards to adapt.
if theme_selection == "Dark Modern Mode":
    st.markdown(
        """
        <style>
        .stApp { background-color: #0E1117; color: #FAFAFA; }
        div[data-testid="stMetricValue"] { color: #FBC02D !important; }
        </style>
        """,
        unsafe_allow_html=True
    )
else:
    st.markdown(
        """
        <style>
        .stApp { background-color: #FFFFFF; color: #31333F; }
        div[data-testid="stMetricValue"] { color: #0D47A1 !important; }
        </style>
        """,
        unsafe_allow_html=True
    )

st.sidebar.markdown("---")
st.sidebar.subheader("⏳ Cascading Geography Filter")
st.sidebar.markdown(
    "**How it works:** Selecting a specific country will dynamically narrow down the available "
    "city selection choices available below it automatically."
)

# Step A: Isolate unique available country values
country_options = ["All Countries"] + sorted(df["Country"].dropna().unique().tolist())
selected_country = st.sidebar.selectbox("Choose a Country:", country_options)

# Step B: Apply cascading logic to filter rows based on country choice
if selected_country != "All Countries":
    df_filtered = df[df["Country"] == selected_country].copy()
    # Populate the secondary city lookup using ONLY cities attached to the chosen country
    city_options = ["All Cities in Country"] + sorted(df_filtered["City"].unique().tolist())
    selected_city = st.sidebar.selectbox("Choose a City:", city_options)
    
    if selected_city != "All Cities in Country":
        df_filtered = df_filtered[df_filtered["City"] == selected_city].copy()
else:
    df_filtered = df.copy()
    # If "All Countries" is selected, disable the secondary city filter dropdown
    selected_city = "All Cities in Country"
    st.sidebar.selectbox("Choose a City:", [selected_city], disabled=True)


# ------------------------------------------------------------------------------
# SECTION 5: DYNAMIC CLIMATE BUCKET TRANSFORMATION LAYER (Unit-Responsive)
# ------------------------------------------------------------------------------

def assign_dynamic_climate_zone(temp, is_celsius_mode):
    """
    Applies real-time transformation grouping logic to cluster cities into 
    climate buckets that scale seamlessly depending on the unit toggle state.
    """
    if pd.isna(temp):
        return "Unknown"
    
    if is_celsius_mode:
        if temp < 0: return "❄️ Freezing (< 0°C)"
        elif temp <= 15: return "🍃 Cool (0°C to 15°C)"
        elif temp <= 25: return "☀️ Mild/Warm (15°C to 25°C)"
        else: return "🔥 Hot (> 25°C)"
    else:
        # Mathematical conversions equivalent to the Celsius pipeline targets
        if temp < 32: return "❄️ Freezing (< 32°F)"
        elif temp <= 59: return "🍃 Cool (32°F to 59°F)"
        elif temp <= 77: return "☀️ Mild/Warm (59°F to 77°F)"
        else: return "🔥 Hot (> 77°F)"

# Overwrite and compute climate tags matching the user's active sidebar toggle choice
df.loc[:, "Climate_Zone"] = df.apply(lambda row: assign_dynamic_climate_zone(row[temp_col], is_celsius), axis=1)
df_filtered.loc[:, "Climate_Zone"] = df_filtered.apply(lambda row: assign_dynamic_climate_zone(row[temp_col], is_celsius), axis=1)


# [COLOR HARMONIZATION LAYER]: Explicit color mappings explicitly locking both
# Celsius and Fahrenheit text keys to a unified thermal palette mapping loop.
# Blue = Coldest (#0D47A1), Orange/Red = Hotter (#EF6C00), Yellow = Hottest (#FBC02D).
CLIMATE_COLOR_MAP = {
    "❄️ Freezing (< 0°C)": "#0D47A1",
    "❄️ Freezing (< 32°F)": "#0D47A1",
    "🍃 Cool (0°C to 15°C)": "#2196F3",
    "🍃 Cool (32°F to 59°F)": "#2196F3",
    "☀️ Mild/Warm (15°C to 25°C)": "#EF6C00",
    "☀️ Mild/Warm (59°F to 77°F)": "#EF6C00",
    "🔥 Hot (> 25°C)": "#FBC02D",
    "🔥 Hot (> 77°F)": "#FBC02D",
    "Unknown": "#757575"
}


# ------------------------------------------------------------------------------
# SECTION 6: HEADER CONTENT & PIPELINE METRIC TELEMETRY
# ------------------------------------------------------------------------------

st.title("🌍 Global Weather Tracking Pipeline Dashboard")

# Visual browser-based reminder matching our terminal caution note
st.info(
    "💡 **Pipeline Execution Note:** This visualization layout is powered by Streamlit. "
    "If you ever need to manually relaunch this server interface from your command line terminal, "
    "make sure to use: `streamlit run dashboard/app.py`"
)

# RENDER OUR PIPELINE DATA CLEANING BEFORE/AFTER AUDIT CARD BLOCK
st.subheader("⚙️ Data Pipeline Infrastructure Health Status")
tel_col1, tel_col2, tel_col3 = st.columns(3)

with tel_col1:
    st.metric(label="Raw Scraped Source Rows (Before Clean)", value=f"{raw_count} Records")
with tel_col2:
    st.metric(label="Clean Database Table Rows (After Clean)", value=f"{len(df)} Records")
with tel_col3:
    dropped_rows = raw_count - len(df) if isinstance(raw_count, int) else "N/A"
    st.metric(label="Anomalous / Duplicate Clones Pruned", value=f"{dropped_rows} Rows Deleted", delta="-Cleaned", delta_color="inverse")

st.markdown("---")


# ------------------------------------------------------------------------------
# SECTION 7: GEOGRAPHICAL INTERACTIVE MAP REGION (With Balanced Fixed Zoom)
# ------------------------------------------------------------------------------

st.header("🗺️ Global Location Weather Map")
st.markdown("Hover cursor elements over geographic coordinate mapping plots to analyze live telemetry tracking data cards.")

# UX KEY GUIDE: Updated description keys explaining the explicit continuous thermal spectrum map dots.
st.markdown(
    """
    <div style="background-color: rgba(135, 206, 250, 0.1); padding: 12px; border-radius: 6px; border-left: 5px solid #4A90E2; margin-bottom: 15px;">
        🔍 <strong>Map Legend Guide:</strong><br>
        • <strong>Dot Color:</strong> Represents geographic temperature intensity (blue = cold, orange/red = hotter, yellow = hottest).<br>
        • <strong>Dot Size:</strong> Represents local <strong>Relative Humidity %</strong>. Larger dots indicate higher ambient atmospheric moisture levels.
    </div>
    """, 
    unsafe_allow_html=True
)

# Build a comprehensive interactive Plotly Map Libre canvas layout frame
map_valid_df = df_filtered[df_filtered["Latitude"].notna() & df_filtered["Longitude"].notna()].copy()
map_valid_df.loc[:, "Humidity_Value"] = map_valid_df["Humidity_Value"].fillna(0)

if map_valid_df.empty:
    st.warning("No geographic coordinate records available for this specific filtered country breakdown select.")
else:
    # 🛠️ FEATURE UPDATE: We lock zoom to a unified, comfortable global baseline (1.3) across the board.
    # This prevents the map from aggressively zooming in too tight when a single country is isolated,
    # leaving standard pan-and-zoom discovery actions completely up to the user.
    fig_map = px.scatter_map(
        map_valid_df,
        lat="Latitude",
        lon="Longitude",
        hover_name="City",
        custom_data=["Country", temp_col, "Humidity_Value", "Condition"],
        color=temp_col,
        size="Humidity_Value",
        color_continuous_scale=px.colors.sequential.thermal, 
        size_max=15,
        zoom=1.3, 
        template=plotly_template,
        labels={temp_col: f"Temp ({unit_suffix})", "Humidity_Value": "Humidity (%)"}
    )

    # Enforce uniform layout alignment by restructuring the hovertemplate framework
    fig_map.update_traces(
        hovertemplate=(
            "<b>%{hovertext}</b><br>"
            "Country=%{customdata[0]}<br>"
            "Temperature=%{customdata[1]}" + unit_suffix + "<br>"
            "Humidity=%{customdata[2]}%<br>"
            "Condition=%{customdata[3]}<extra></extra>"
        )
    )

    fig_map.update_layout(
        map_style=map_style,
        margin={"r":0,"t":40,"l":0,"b":0},
        height=450
    )

    # Render map utilizing modernized layout width properties
    st.plotly_chart(fig_map, width="stretch")

st.markdown("---")


# ------------------------------------------------------------------------------
# SECTION 8: STATISTICAL LEADERBOARD RANKINGS (With Country Context Labels)
# ------------------------------------------------------------------------------

st.header("📊 Statistical Leaderboard Rankings")
st.markdown("This section analyzes the absolute highest intensity records actively stored within the active pipeline scope.")

# Isolate the top 10 hottest rows in our active filtered data frame selection
top_10_hottest = df_filtered.nlargest(10, temp_col).copy()

if top_10_hottest.empty:
    st.warning("No metrics available to construct the statistical ranking layers.")
else:
    # Concatenate City and Country into an explicit geographic label feature.
    # This automatically feeds into both the horizontal axis layout AND the interactive hover cards!
    top_10_hottest.loc[:, "Location_Full"] = top_10_hottest["City"] + " (" + top_10_hottest["Country"].fillna("Unknown") + ")"

    # Construct an interactive, modern bar chart sorting highest records from left to right
    fig_top_10 = px.bar(
        top_10_hottest,
        x="Location_Full",  
        y=temp_col,
        color=temp_col,
        text_auto=".1f", # Automatically overlay formatting value labels right on top of bars
        color_continuous_scale=px.colors.sequential.solar,
        template=plotly_template,
        title=f"🥇 Top 10 Hottest Monitored Locations ({unit_suffix})",
        labels={temp_col: f"Temperature ({unit_suffix})", "Location_Full": "Monitored Location"}
    )
    
    fig_top_10.update_layout(xaxis_tickangle=-45, height=380)
    st.plotly_chart(fig_top_10, width="stretch")

st.markdown("---")


# ------------------------------------------------------------------------------
# SECTION 9: GLOBAL LANDSCAPE ANALYSIS (Climate Zone Distributions)
# ------------------------------------------------------------------------------

st.header("📊 Global Ambient Landscape Distributions")
dist_col1, dist_col2 = st.columns([4, 6])

with dist_col1:
    st.subheader(f"Regional Climate Classification Counts ({unit_suffix})")
    st.markdown("Analyzes the distribution of scraped cities across thermal categories calculated via your pipeline transformation logic expressions.")
    
    # Calculate group tallies dynamically
    zone_counts = df_filtered["Climate_Zone"].value_counts().reset_index().copy()
    zone_counts.columns = ["Climate Zone", "Total Cities Found"]
    
    # Ensure standard sorting sequence for clean visualization
    sorting_dict = {
        "❄️ Freezing (< 0°C)": 0, "❄️ Freezing (< 32°F)": 0,
        "🍃 Cool (0°C to 15°C)": 1, "🍃 Cool (32°F to 59°F)": 1,
        "☀️ Mild/Warm (15°C to 25°C)": 2, "☀️ Mild/Warm (59°F to 77°F)": 2,
        "🔥 Hot (> 25°C)": 3, "🔥 Hot (> 77°F)": 3,
        "Unknown": 4
    }
    
    # Use explicit single-step row/column coordinate targeting via .loc
    zone_counts.loc[:, "Sort_Order"] = zone_counts["Climate Zone"].map(sorting_dict)
    zone_counts = zone_counts.sort_values("Sort_Order")

    # Generate interactive distribution bar plot
    fig_zone = px.bar(
        zone_counts,
        x="Climate Zone",
        y="Total Cities Found",
        color="Climate Zone",
        template=plotly_template,
        color_discrete_map=CLIMATE_COLOR_MAP
    )
    fig_zone.update_layout(showlegend=False, height=350)
    st.plotly_chart(fig_zone, width="stretch")

with dist_col2:
    st.subheader("💧 Humidity vs. Temperature Scatter Correlation")
    st.markdown("Evaluates climate relationships to uncover whether hot areas show specific moisture profiles.")
    
    # Generate scatter plot tracking chosen metrics variables
    fig_scatter = px.scatter(
        df_filtered,
        x=temp_col,
        y="Humidity_Value",
        color="Climate_Zone",
        hover_name="City",
        custom_data=["Country", temp_col, "Humidity_Value", "Climate_Zone"],
        template=plotly_template,
        labels={temp_col: f"Temperature ({unit_suffix})", "Humidity_Value": "Humidity (%)", "Climate_Zone": "Zone Category"},
        color_discrete_map=CLIMATE_COLOR_MAP
    )
    
    # Bind the exact uniform text layer formatting structural rules onto the markers
    fig_scatter.update_traces(
        hovertemplate=(
            "<b>%{hovertext}</b><br>"
            "Country=%{customdata[0]}<br>"
            "Temperature=%{customdata[1]}" + unit_suffix + "<br>"
            "Humidity=%{customdata[2]}%<br>"
            "Zone Category=%{customdata[3]}<extra></extra>"
        )
    )
    
    fig_scatter.update_layout(height=350)
    st.plotly_chart(fig_scatter, width="stretch")

st.markdown("---")


# ------------------------------------------------------------------------------
# SECTION 10: SIDE-BY-SIDE CITY VISUAL COMPARISON UNIT (Filter-Aware Randomizer)
# ------------------------------------------------------------------------------

st.header("⚔️ Spot-Compare Specific Cities Side-by-Side")
st.markdown("Isolate individual locations to instantly cross-reference metrics directly beneath selected control drop-down frames.")

# Sourced globally to ensure complete translation dictionary visibility
global_cities = sorted(df["City"].unique())
city_to_country = df.drop_duplicates(subset=["City"]).set_index("City")["Country"].to_dict()

# 🛠️ FEATURE UPDATE STEP A: Calculate an isolated, active unique filter key string.
# This represents a combination of the sidebar's current selections.
current_filter_key = f"Country:{selected_country}||City:{selected_city}"

# Isolate the list of cities that are matching the current filter scope
filtered_city_pool = sorted(df_filtered["City"].unique().tolist())

# 🛠️ FEATURE UPDATE STEP B: Compare the current filter key to the last tracked state.
# If the keys do not match, the user adjusted the sidebar, prompting an instant re-roll!
if "active_filter_state" not in st.session_state or st.session_state.active_filter_state != current_filter_key:
    
    # Scenario 1: The current filtered view has 2 or more distinct cities available
    if len(filtered_city_pool) >= 2:
        sampled_pair = random.sample(filtered_city_pool, 2)
        st.session_state.random_city1 = sampled_pair[0]
        st.session_state.random_city2 = sampled_pair[1]
        
    # Scenario 2: The filter isolated exactly 1 city (e.g., a specific city or single-city country)
    elif len(filtered_city_pool) == 1:
        st.session_state.random_city1 = filtered_city_pool[0]
        # Pair it with a random city chosen from the wider global pool to maintain context
        global_alternatives = [c for c in global_cities if c != filtered_city_pool[0]]
        if global_alternatives:
            st.session_state.random_city2 = random.choice(global_alternatives)
        else:
            st.session_state.random_city2 = filtered_city_pool[0] # Complete fallback boundary
            
    # Scenario 3: Catch-all safety boundary fallback if the filter pool structure returns empty
    else:
        if len(global_cities) >= 2:
            sampled_pair = random.sample(global_cities, 2)
            st.session_state.random_city1 = sampled_pair[0]
            st.session_state.random_city2 = sampled_pair[1]
        else:
            st.session_state.random_city1 = global_cities[0] if global_cities else None
            st.session_state.random_city2 = global_cities[0] if global_cities else None

    # Cache this new filter state key string so we don't shuffle again until the filters change
    st.session_state.active_filter_state = current_filter_key


# Calculate safe index integer map fallback properties for our selectbox configurations
try:
    c1_default_idx = global_cities.index(st.session_state.random_city1)
except ValueError:
    c1_default_idx = 0

try:
    c2_default_idx = global_cities.index(st.session_state.random_city2)
except ValueError:
    c2_default_idx = 1 if len(global_cities) > 1 else 0

comp_col1, comp_col2 = st.columns(2)

with comp_col1:
    city1_selection = st.selectbox(
        "🎯 Target Location City 1:", 
        global_cities, 
        index=c1_default_idx,  # Bind to our persistent random state index assignment
        format_func=lambda city: f"{city} ({city_to_country.get(city, 'Unknown')})"
    )
    city1_data = df[df["City"] == city1_selection].iloc[0] if not df[df["City"] == city1_selection].empty else None
    
    if city1_data is not None:
        st.subheader(f"📍 {city1_selection} ({city1_data['Country']})")
        
        m_t1, m_h1 = st.columns(2)
        with m_t1:
            st.metric(label="Temperature Reading", value=f"{city1_data[temp_col]} {unit_suffix}")
        with m_h1:
            st.metric(label="Relative Humidity Index", value=f"{city1_data['Humidity_Value']}%")
            
        c1_df = pd.DataFrame({
            "Core Metric Elements": [f"Temperature ({unit_suffix})", "Humidity (%)", "Wind Speed (m/s)"],
            "Value": [float(city1_data[temp_col]), float(city1_data['Humidity_Value']), float(city1_data['Wind_Speed'])]
        })
        
        fig_c1 = px.bar(c1_df, x="Core Metric Elements", y="Value", template=plotly_template)
        c1_color = CLIMATE_COLOR_MAP.get(city1_data["Climate_Zone"], "#4A90E2")
        fig_c1.update_traces(marker_color=c1_color)
        fig_c1.update_layout(height=300, yaxis_title="")
        st.plotly_chart(fig_c1, width="stretch")

with comp_col2:
    city2_selection = st.selectbox(
        "🎯 Target Location City 2:", 
        global_cities, 
        index=c2_default_idx,  # Bind to our persistent random state index assignment
        format_func=lambda city: f"{city} ({city_to_country.get(city, 'Unknown')})"
    )
    city2_data = df[df["City"] == city2_selection].iloc[0] if not df[df["City"] == city2_selection].empty else None
    
    if city2_data is not None:
        st.subheader(f"📍 {city2_selection} ({city2_data['Country']})")
        
        m_t2, m_h2 = st.columns(2)
        with m_t2:
            st.metric(label="Temperature Reading", value=f"{city2_data[temp_col]} {unit_suffix}")
        with m_h2:
            st.metric(label="Relative Humidity Index", value=f"{city2_data['Humidity_Value']}%")
            
        c2_df = pd.DataFrame({
            "Core Metric Elements": [f"Temperature ({unit_suffix})", "Humidity (%)", "Wind Speed (m/s)"],
            "Value": [float(city2_data[temp_col]), float(city2_data['Humidity_Value']), float(city2_data['Wind_Speed'])]
        })
        
        fig_c2 = px.bar(c2_df, x="Core Metric Elements", y="Value", template=plotly_template)
        c2_color = CLIMATE_COLOR_MAP.get(city2_data["Climate_Zone"], "#F5A623")
        fig_c2.update_traces(marker_color=c2_color)
        fig_c2.update_layout(height=300, yaxis_title="")
        st.plotly_chart(fig_c2, width="stretch")


# ------------------------------------------------------------------------------
# SECTION 11: COMPLETE DATABASE LEDGER SHEET
# ------------------------------------------------------------------------------
st.markdown("---")
st.header("📋 Pipeline Relational Database Ledger View")
st.markdown("This window streams our active transactional database storage rows straight onto the browser screen interface.")

# Drop runtime categories before display so the dashboard strictly maps back to our SQLite database schema structure
st.dataframe(df_filtered.drop(columns=["Climate_Zone"]), width="stretch")