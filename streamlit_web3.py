import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import folium
from streamlit_folium import folium_static
from folium.plugins import MarkerCluster
from geopy.geocoders import Nominatim
import plotly.graph_objects as go
from streamlit_tags import st_tags
from folium.plugins import HeatMap
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.ops import unary_union
from shapely.geometry import Point
import contextily as ctx  # for adding basemaps
from streamlit_folium import folium_static

# Load the dataset
file_path = 'Data/final.csv'
data = pd.read_csv(file_path)
data['Start Time'] = pd.to_datetime(data['Start Time'], utc=True)
data['End Time'] = pd.to_datetime(data['End Time'], utc=True)

# Add Duration in hours
data['Duration (hours)'] = data['Duration'].apply(pd.to_numeric, errors='coerce')


# Function to get location name from latitude and longitude
def get_location_name(lat, lon):
    geolocator = Nominatim(user_agent="geoapiExercises")
    location = geolocator.reverse((lat, lon), exactly_one=True)
    return location.address if location else "Unknown Location"


# Function to perform buffer analysis on geospatial data
def buffer_analysis(gdf, buffer_distance):
    # Re-project to a projected CRS (e.g., UTM zone 30N)
    gdf = gdf.to_crs(epsg=32630)
    # Create buffer zones
    gdf['buffer'] = gdf.geometry.buffer(buffer_distance)
    # Re-project back to the original CRS
    gdf = gdf.to_crs(epsg=4326)
    return gdf


# Function to format datetime for display
def format_datetime(dt):
    if pd.isna(dt):
        return "Unknown"
    return dt.strftime("%d.%m.%Y %H:%M")


# Sidebar for navigation
st.sidebar.title("Navigation")
pages = ["Home", "Map View", "Disruption Details", "Analytics", "User Dashboard"]
selected_page = st.sidebar.radio("Go to", pages)

# Homepage
if selected_page == "Home":
    st.title("Public Transport Disruptions")
    st.write(
        "Welcome to the public transport disruption information website. Use the navigation bar to explore disruptions, view details, and analyze data.")
    st.write("### Current Major Disruptions")
    st.dataframe(data[['Summary', 'Start Time', 'End Time', 'Stop Name', 'Planned', 'Consequence Severity']].head(10))

# Map View
elif selected_page == "Map View":
    st.title("Disruption Map")
    # Create a Folium map centered on the average latitude and longitude
    m = folium.Map(location=[data['Latitude'].mean(), data['Longitude'].mean()], zoom_start=10)
    marker_cluster = MarkerCluster().add_to(m)

    # Add markers for each disruption
    for idx, row in data.iterrows():
        folium.Marker(
            location=[row['Latitude'], row['Longitude']],
            popup=(
                f"{row['Summary']}<br>"
                f"Planned: {row['Planned']}<br>Consequence Severity: {row['Consequence Severity']}"
            ),
            icon=folium.Icon(color="red" if row['Consequence Severity'] == 'Very Severe' else "blue")
        ).add_to(marker_cluster)

    # Display the map
    folium_static(m)

# Disruption Details
elif selected_page == "Disruption Details":
    st.title("Disruption Details")

    # County selection
    selected_county = st.selectbox("Select County", data['County'].unique())

    # Filter disruptions by selected county
    county_disruptions = data[data['County'] == selected_county]

    # Disruption selection by summary
    selected_summary = st.selectbox("Select Disruption Summary", county_disruptions['Summary'].unique())
    disruption_details = county_disruptions[county_disruptions['Summary'] == selected_summary]

    # Display disruption details if available
    if len(disruption_details) > 0:
        disruption_details = disruption_details.iloc[0]  # Get the first row
    else:
        st.write("No details available for the selected disruption.")
        st.stop()

    # try:
    #     location_name = get_location_name(disruption_details['Latitude'], disruption_details['Longitude'])
    # except Exception as e:
    #     location_name = "Unknown Location"
    #     st.error(f"Error getting location name: {e}")

    stop_names = disruption_details['Stop Name'].split(', ')

    reason = disruption_details['Efficient Disruption Category']
    if disruption_details['Efficient Disruption Category'] != disruption_details['Detailed Disruption Category']:
        reason += f": {disruption_details['Detailed Disruption Category']}"

    st.write(f"### {disruption_details['Summary']}")
    st.write(f"**Description:** {disruption_details['Description']}")
    st.write(f"**Start Time:** {format_datetime(disruption_details['Start Time'])}")
    st.write(f"**End Time:** {format_datetime(disruption_details['End Time'])}")
    # st.write(f"**Location:** {location_name}")
    st.write(f"**Operator:** {disruption_details['Operator_name']}")
    st.write(f"**Planned:** {disruption_details['Planned']}")
    st.write(f"**Consequence Severity:** {disruption_details['Consequence Severity']}")
    st.write(f"**Reason:** {reason}")
    st.write("**Affected Stop Names:**")
    for stop_name in stop_names:
        st.write(f"- {stop_name}")

# Analytics
elif selected_page == "Analytics":

    st.title("Analytics")

    # Filters section
    with st.expander("Select Filters", expanded=True):

        col1, col2 = st.columns(2)

        with col1:
            operators = st.multiselect(
                'Select Operators',
                options=data['Operator_name'].unique(),
                default=['First Bus'],  # Default value
                help="Select the bus operators to include in the analysis."
            )

        with col2:
            severities = st.multiselect(
                'Select Severities',
                options=data['Consequence Severity'].unique(),
                default=['Normal'],  # Default value
                help="Select the severity levels to include in the analysis."
            )

        col3, col4 = st.columns(2)

        with col3:
            start_date = st.date_input(
                "Start Date",
                value=pd.to_datetime(data['Start Time']).min(),
                help="Select the start date for the analysis."
            )

        with col4:
            end_date = st.date_input(
                "End Date",
                value=pd.to_datetime(data['End Time']).max(),
                help="Select the end date for the analysis."
            )

        # Convert date inputs to timezone-aware datetime
        start_date = pd.to_datetime(start_date).tz_localize('UTC')
        end_date = pd.to_datetime(end_date).tz_localize('UTC')

    # Filter data based on selections
    filtered_data = data[(data['Operator_name'].isin(operators)) &
                         (data['Consequence Severity'].isin(severities)) &
                         (data['Start Time'] >= start_date) &
                         (data['End Time'] <= end_date)]


    # Sidebar for analysis type selection
    st.sidebar.header("Select Analysis:")
    analysis_options = [
        "Mapping Disruption Hotspots",
        "Impact Analysis on Commuters",
        "Temporal Analysis",
        "Severity and Consequence Analysis",
        "Route-Based Analysis",
        "Correlation with External Factors",
        "Impact on Different Demographic Groups",
        "Comparative Analysis",
        "Severity vs. Reason Category"
    ]
    selected_analysis = st.sidebar.radio("Analysis Type", analysis_options)

    # 1. Mapping Disruption Hotspots
    if selected_analysis == "Mapping Disruption Hotspots":
        st.header("Mapping Disruption Hotspots")

        # Create a base map
        m = folium.Map(location=[53.480759, -2.242631], zoom_start=10)

        # Heatmap
        st.subheader("Heatmap of Disruptions")
        heat_data = [[row['Latitude'], row['Longitude']] for index, row in filtered_data.iterrows()]
        HeatMap(heat_data).add_to(m)
        folium_static(m)

    # 2. Impact Analysis on Commuters
    elif selected_analysis == "Impact Analysis on Commuters":
        st.header("Impact Analysis on Commuters")

        st.subheader("Service Coverage Analysis")
        # Service coverage analysis logic
        st.write("Service coverage analysis not implemented yet.")

        st.subheader("Accessibility Analysis")
        # Accessibility analysis logic
        st.write("Accessibility analysis not implemented yet.")

    # 3. Temporal Analysis
    elif selected_analysis == "Temporal Analysis":
        st.header("Temporal Analysis")

        st.subheader("Time Series Analysis")
        filtered_data['Start Time'] = pd.to_datetime(filtered_data['Start Time'])
        filtered_data['End Time'] = pd.to_datetime(filtered_data['End Time'])
        filtered_data['Duration'] = (filtered_data['End Time'] - filtered_data['Start Time']).dt.total_seconds() / (3600 * 24)
        time_series = filtered_data.set_index('Start Time').resample('D').size()
        st.line_chart(time_series)

        st.subheader("Duration Impact")
        fig = px.histogram(filtered_data, x='Duration')
        st.plotly_chart(fig)

    # 4. Severity and Consequence Analysis
    elif selected_analysis == "Severity and Consequence Analysis":
        st.header("Severity and Consequence Analysis")

        st.subheader("Severity Mapping")
        severity_map = folium.Map(location=[53.480759, -2.242631], zoom_start=10)
        severity_colors = {
            'Unknown': 'gray',
            'Normal': 'green',
            'Slight': 'blue',
            'Severe': 'red',
            'Very Severe': 'darkred',
            'Very Slight': 'lightblue'
        }

        for i, row in filtered_data.iterrows():
            folium.Marker(
                location=[row['Latitude'], row['Longitude']],
                popup=f"Severity: {row['Consequence Severity']}",
                icon=folium.Icon(color=severity_colors.get(row['Consequence Severity'], 'blue'))
            ).add_to(severity_map)
        folium_static(severity_map)

        st.subheader("Planned vs. Unplanned")
        planned_data = filtered_data[filtered_data['Planned'] == True]
        planned_data = planned_data.rename(columns={"Latitude": "lat", "Longitude": "lon"})
        unplanned_data = filtered_data[filtered_data['Planned'] == False]
        unplanned_data = unplanned_data.rename(columns={"Latitude": "lat", "Longitude": "lon"})
        st.map(planned_data[['lat', 'lon']])
        st.map(unplanned_data[['lat', 'lon']])

    # 5. Route-Based Analysis
    elif selected_analysis == "Route-Based Analysis":
        st.header("Route-Based Analysis")

        st.subheader("Route Disruption Analysis")
        route_analysis = filtered_data['Stop Name'].value_counts()
        st.bar_chart(route_analysis)

        st.subheader("Alternative Route Analysis")
        st.write("Alternative route analysis not implemented yet.")

    # 6. Correlation with External Factors
    elif selected_analysis == "Correlation with External Factors":
        st.header("Correlation with External Factors")

        st.subheader("Weather Conditions")
        st.write("Weather correlation analysis not implemented yet.")

        st.subheader("Construction Activities")
        st.write("Construction correlation analysis not implemented yet.")

    # 7. Impact on Different Demographic Groups
    elif selected_analysis == "Impact on Different Demographic Groups":
        st.header("Impact on Different Demographic Groups")

        st.subheader("Socioeconomic Impact")
        st.write("Socioeconomic impact analysis not implemented yet.")

        st.subheader("Vulnerable Populations")
        st.write("Vulnerable populations analysis not implemented yet.")

    # 8. Comparative Analysis
    elif selected_analysis == "Comparative Analysis":
        st.header("Comparative Analysis")

        st.subheader("Inter-Operator Comparison")
        operator_comparison = filtered_data['Operator'].value_counts()
        st.bar_chart(operator_comparison)

        st.subheader("Regional Comparison")
        regional_comparison = filtered_data['County'].value_counts()
        st.bar_chart(regional_comparison)
    # 9. Severity vs. Reason Category Analysis
    elif selected_analysis == "Severity vs. Reason Category":
        st.header("Severity vs. Reason Category Analysis")

        # Create a stacked bar chart for severity vs reason category
        st.subheader("Severity Distribution by Reason Category")
        fig = px.bar(filtered_data,
                     x='Detailed Disruption Category',
                     color='Consequence Severity',
                     title='Severity Distribution by Reason Category',
                     category_orders={"Consequence Severity": ["Unknown", "Normal", "Very Slight", "Slight", "Severe",
                                                               "Very Severe"]},
                     barmode='stack')
        st.plotly_chart(fig)

        st.subheader("Count of Severities by Reason Category")
        severity_reason_counts = filtered_data.groupby(
            ['Detailed Disruption Category', 'Consequence Severity']).size().reset_index(name='Counts')
        fig2 = px.bar(severity_reason_counts,
                      x='Detailed Disruption Category',
                      y='Counts',
                      color='Consequence Severity',
                      title='Count of Severities by Reason Category',
                      category_orders={"Consequence Severity": ["Unknown", "Normal", "Very Slight", "Slight", "Severe",
                                                                "Very Severe"]},
                      barmode='group')
        st.plotly_chart(fig2)
    # Data Table
    st.header('Data Table')
    st.dataframe(filtered_data)

    # Save filtered data
    st.download_button('Download Filtered Data', data=filtered_data.to_csv(), file_name='filtered_disruptions.csv')


# User Dashboard
elif selected_page == "User Dashboard":
    st.title("User Dashboard")
    st.write("Customize your dashboard by selecting your preferences.")


# General layout and footer
st.sidebar.title("About")
st.sidebar.info("This is a demo website for public transport disruption information, built using Streamlit.")
