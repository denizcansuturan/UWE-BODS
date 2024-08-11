import folium
import pandas as pd
import matplotlib.pyplot as plt
import contextily as ctx
import geopandas as gpd
import matplotlib.cm as cm
import matplotlib.colors as colors
from folium.plugins import HeatMap
import matplotlib.dates as mdates

# --------------------------------  Severity Analysis  ---------------------------------------------

# Load your data
df = pd.read_csv('Data/final.csv')

# Create a map centered around the average latitude and longitude
m = folium.Map(location=[df['Latitude'].mean(), df['Longitude'].mean()], zoom_start=6)

# Define a color map for consequence severity
severity_color_map = {'Unknown': 'gray', 'Normal': 'green', 'Slight': 'yellow', 'Severe': 'red'}

# Add points to the map
for idx, row in df.iterrows():
    folium.CircleMarker(
        [row['Latitude'], row['Longitude']],
        radius=5,
        popup=row['Consequence Severity'],
        color=severity_color_map.get(row['Consequence Severity'], 'blue'),
        fill=True,
        fill_color=severity_color_map.get(row['Consequence Severity'], 'blue')
    ).add_to(m)

# Save the map to an HTML file
# m.save('consequence_severity_map.html')

# Group the data by location (Latitude and Longitude) and Consequence Severity
location_severity = df.groupby(['Latitude', 'Longitude', 'Consequence Severity']).size().unstack(fill_value=0)

# Determine the most common severity at each location
location_severity['Most Common Severity'] = location_severity.idxmax(axis=1)

# Convert to GeoDataFrame
gdf = gpd.GeoDataFrame(
    location_severity.reset_index(),
    geometry=gpd.points_from_xy(location_severity.index.get_level_values('Longitude'), location_severity.index.get_level_values('Latitude'))
)

# Set the coordinate reference system to WGS84
gdf = gdf.set_crs("EPSG:4326")

# Convert to Web Mercator for mapping
gdf = gdf.to_crs(epsg=3857)

# Map the most common severity at each location
severity_color_map = {'Unknown': 'gray', 'Normal': 'green', 'Slight': 'yellow', 'Severe': 'red'}
gdf['color'] = gdf['Most Common Severity'].map(severity_color_map)

fig, ax = plt.subplots(figsize=(10, 10))
gdf.plot(ax=ax, marker='o', color=gdf['color'], markersize=50, alpha=0.6)

# Add a basemap
ctx.add_basemap(ax, crs=gdf.crs.to_string(), source=ctx.providers.Stamen.TonerLite)

plt.title('Most Common Disruption Severity by Location')
plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.show(block=True)

# --------------------------------  Time-Space Scatter Plot Of Disruptions  ---------------------------------------------

# Load the data
df = pd.read_csv('Data/final.csv')  # Ensure this path is correct on your local machine

# Convert 'Start Time' to datetime
df['Start Time'] = pd.to_datetime(df['Start Time'])

# Set the 'Start Time' as the index
df.set_index('Start Time', inplace=True)

# Resample the data to daily counts of disruptions
daily_disruptions = df.resample('D').size()

# Plot the time series of daily disruptions with larger text and paler grids
plt.figure(figsize=(14, 7))
daily_disruptions.plot()

# Customize the plot
plt.title('Daily Disruptions Over Time', fontsize=18)
plt.xlabel('Date', fontsize=14)
plt.ylabel('Number of Disruptions', fontsize=14)
plt.xticks(fontsize=20)
plt.yticks(fontsize=20)
plt.grid(True, which='major', linestyle='-', linewidth='0.5', color='gray', alpha=0.3)
plt.grid(True, which='minor', linestyle=':', linewidth='0.5', color='gray', alpha=0.3)
plt.show(block=True)

# Load the data
df = pd.read_csv('Data/final.csv')  # Ensure this path is correct on your local machine

# Convert 'Start Time' to datetime
df['Start Time'] = pd.to_datetime(df['Start Time'])

# Extract the hour from the 'Start Time'
df['Hour'] = df['Start Time'].dt.hour

# Group the data by hour
hourly_disruptions = df.groupby('Hour').size()

# Plot the hourly disruptions with larger text and paler grids
plt.figure(figsize=(14, 7))
hourly_disruptions.plot(kind='bar', color='skyblue')

# Customize the plot
plt.title('Disruptions by Hour of the Day', fontsize=18)
plt.xlabel('Hour of the Day', fontsize=14)
plt.ylabel('Number of Disruptions', fontsize=14)
plt.xticks(fontsize=12)
plt.yticks(fontsize=12)
plt.grid(True, which='major', linestyle='-', linewidth='0.5', color='gray', alpha=0.3)

# Show the plot
plt.show(block=True)


# --------------------------------  Heat Map  -----------------------------------


# Load your data
df = pd.read_csv('Data/final.csv')

# Create a map centered around the average latitude and longitude
m = folium.Map(location=[df['Latitude'].mean(), df['Longitude'].mean()], zoom_start=6)

# Prepare data for the heatmap
heat_data = [[row['Latitude'], row['Longitude']] for index, row in df.iterrows()]

# Add heatmap to the map
HeatMap(heat_data).add_to(m)

# Save the map to an HTML file
m.save('disruption_heatmap.html')

# --------------------------------  Point Map  -----------------------------------
# Load your data
df = pd.read_csv('Data/final.csv')

# Create a map centered around the average latitude and longitude
m = folium.Map(location=[df['Latitude'].mean(), df['Longitude'].mean()], zoom_start=6)

# Add points to the map
for idx, row in df.iterrows():
    folium.CircleMarker(
        [row['Latitude'], row['Longitude']],
        radius=3,
        color='blue',
        fill=True,
        fill_color='blue'
    ).add_to(m)

# Save the map to an HTML file
m.save('disruption_points_map.html')

# --------------------------------  Comparative Analysis: Operator Comparison  -----------------------------------

# Load your data
df = pd.read_csv('Data/final.csv')  # Ensure this path is correct on your local machine

# Filter the dataframe to include only disruptions where the operator is responsible, specifically for 'Service Diversion'
df_filtered = df[df['Efficient Disruption Category'] == 'Service Changes']

# Counting disruptions by Operator and Consequence Severity
operator_severity_counts = df_filtered.groupby(['Operator_name', 'Consequence Severity']).size().unstack(fill_value=0)

# Selecting the top 7 companies by total number of disruptions
top_operators = operator_severity_counts.sum(axis=1).nlargest(7).index
top_operator_severity_counts = operator_severity_counts.loc[top_operators]

# Plotting the comparison of the top 7 operators by disruption severity
plt.figure(figsize=(16, 10))
top_operator_severity_counts.plot(kind='bar', stacked=True, colormap='tab20', figsize=(16, 10))

# Customize the plot
plt.title('Top 7 Operators Comparison by Disruption Severity', fontsize=20)
plt.xlabel('Operator Name', fontsize=16)
plt.ylabel('Number of Disruptions', fontsize=16)
plt.xticks(rotation=45, ha='right', fontsize=14)
plt.yticks(fontsize=14)
plt.grid(True, which='major', linestyle='-', linewidth='0.5', color='gray', alpha=0.3)
plt.grid(True, which='minor', linestyle=':', linewidth='0.5', color='gray', alpha=0.3)
plt.legend(title='Consequence Severity', fontsize=14)

# Show the plot
plt.show(block=True)

# --------------------------------  Comparative Analysis: Geographical Comparison  -----------------------------------

# Counting disruptions by County and Consequence Severity
county_severity_counts = df.groupby(['County', 'Consequence Severity']).size().unstack(fill_value=0)

plt.figure(figsize=(18, 12))
county_severity_counts.plot(kind='bar', stacked=True, colormap='tab20', figsize=(18, 12))

# Customize the plot
plt.title('Geographical Comparison by Disruption Severity', fontsize=18)
plt.xlabel('County', fontsize=14)
plt.ylabel('Number of Disruptions', fontsize=14)
plt.xticks(rotation=45, ha='right', fontsize=12)
plt.yticks(fontsize=12)
plt.grid(True, which='major', linestyle='-', linewidth='0.5', color='gray', alpha=0.3)
plt.grid(True, which='minor', linestyle=':', linewidth='0.5', color='gray', alpha=0.3)
plt.legend(title='Consequence Severity', fontsize=12)

plt.show(block=True)

# --------------------------------  Severity - Reason  -----------------------------------
# Load your data
df = pd.read_csv('Data/final.csv')  # Ensure this path is correct on your local machine

# Group the data by Detailed Disruption Category and Consequence Severity
severity_vs_reason = df.groupby(['Detailed Disruption Category', 'Consequence Severity']).size().unstack(fill_value=0)

# Plotting the data with larger texts and paler grids
plt.figure(figsize=(16, 10))
severity_vs_reason.plot(kind='bar', stacked=True, figsize=(16, 10), colormap='tab20')

# Customize the plot
plt.title('Severity vs. Reason Category Analysis', fontsize=20)
plt.xlabel('Detailed Disruption Category', fontsize=16)
plt.ylabel('Number of Disruptions', fontsize=16)
plt.xticks(rotation=45, ha='right', fontsize=14)
plt.yticks(fontsize=14)
plt.grid(True, which='major', linestyle='-', linewidth='0.5', color='gray', alpha=0.3)
plt.grid(True, which='minor', linestyle=':', linewidth='0.5', color='gray', alpha=0.3)
plt.legend(title='Consequence Severity', fontsize=14)
plt.show(block=True)


# --------------------------------  Unknown Severity - Planned or not  -----------------------------------
# Load your data
df = pd.read_csv('Data/final.csv')  # Ensure this path is correct on your local machine

# Filter the data to get only the disruptions with 'Unknown' severity
unknown_severity = df[df['Consequence Severity'] == 'Unknown']

# Group the filtered data by the 'Planned' column
planned_vs_unplanned = unknown_severity.groupby('Planned').size()

# Plotting the comparison
plt.figure(figsize=(10, 6))
planned_vs_unplanned.plot(kind='bar', color='skyblue')

# Customize the plot
plt.title('Comparison of Unknown Severities: Planned vs Unplanned Disruptions', fontsize=16)
plt.xlabel('Disruption was Planned?', fontsize=14)
plt.ylabel('Number of Unknown Severities', fontsize=14)
plt.xticks(rotation=0, fontsize=12)
plt.yticks(fontsize=12)
plt.grid(True, which='major', linestyle='-', linewidth='0.5', color='gray', alpha=0.3)

# Show the plot
plt.show(block=True)

unknown_severity_count = df[df['Consequence Severity'] == 'Unknown'].shape[0]
total_disruptions = df.shape[0]
unknown_severity_percentage = (unknown_severity_count / total_disruptions) * 100
print(f"Unknown severities account for {unknown_severity_percentage:.2f}% of total disruptions.")

# Example: Check the distribution of 'Unknown' severities by operator
unknown_by_operator = df[df['Consequence Severity'] == 'Unknown'].groupby('Operator_name').size()
print(unknown_by_operator)

# Load your data
df = pd.read_csv('Data/final.csv')
# Group by 'Operator_name' and count unknown severities
unknown_by_operator = unknown_severity.groupby('Operator_name').size()

# Plotting the comparison
plt.figure(figsize=(12, 8))
unknown_by_operator.plot(kind='bar', color='salmon')

# Customize the plot
plt.title('Comparison of Unknown Severities by Operator', fontsize=16)
plt.xlabel('Operator Name', fontsize=14)
plt.ylabel('Number of Unknown Severities', fontsize=14)
plt.xticks(rotation=45, ha='right', fontsize=12)
plt.yticks(fontsize=12)
plt.grid(True, which='major', linestyle='-', linewidth='0.5', color='gray', alpha=0.3)
plt.show(block=True)
# --------------------------------------------
# Group by 'County' and count unknown severities
unknown_by_region = unknown_severity.groupby('County').size()

# Plotting the comparison
plt.figure(figsize=(12, 8))
unknown_by_region.plot(kind='bar', color='lightgreen')

# Customize the plot
plt.title('Comparison of Unknown Severities by Geographic Region', fontsize=16)
plt.xlabel('County', fontsize=14)
plt.ylabel('Number of Unknown Severities', fontsize=14)
plt.xticks(rotation=45, ha='right', fontsize=12)
plt.yticks(fontsize=12)
plt.grid(True, which='major', linestyle='-', linewidth='0.5', color='gray', alpha=0.3)
plt.show(block=True)
#  ---------------------------------------------------------

# Load your data
df = pd.read_csv('Data/final.csv')
# Convert 'Start Time' to datetime
df['Start Time'] = pd.to_datetime(df['Start Time'])

# Set the 'Start Time' as the index
df.set_index('Start Time', inplace=True)

# Filter for unknown severities
unknown_severity = df[df['Consequence Severity'] == 'Unknown']

# Resample the data to monthly counts of unknown severities
monthly_unknown_severities = unknown_severity.resample('M').size()

# Plotting the monthly unknown severities
plt.figure(figsize=(10, 6))
monthly_unknown_severities.plot(kind='bar', color='skyblue')

# Customize the plot
plt.title('Monthly Unknown Severities Over Time', fontsize=16)
plt.xlabel('Month', fontsize=14)
plt.ylabel('Number of Unknown Severities', fontsize=14)

# Format the x-axis for better readability
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
plt.xticks(rotation=45, ha='right', fontsize=12)
plt.yticks(fontsize=12)
plt.grid(True, which='major', linestyle='-', linewidth='0.5', color='gray', alpha=0.3)

plt.show(block=True)