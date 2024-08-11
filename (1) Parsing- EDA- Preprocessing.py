import xml.etree.ElementTree as ET
import pandas as pd
import matplotlib.pyplot as plt
import geopandas as gpd

# Set pandas display options
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.max_colwidth', None)  # Show full column width

# Load and parse the XML file
tree = ET.parse('Data/all disruption data/sirisx_2024-07-31_145644/sirisx.xml')
root = tree.getroot()

# Define the namespace to correctly parse the XML
ns = {'siri': 'http://www.siri.org.uk/siri'}

# Extract data from the XML file with additional fields
data = []
for situation in root.findall('.//siri:PtSituationElement', ns):
    situation_number = situation.find('siri:SituationNumber', ns).text if situation.find('siri:SituationNumber', ns) is not None else 'Unknown'
    operator_name = situation.find('.//siri:OperatorRef', ns).text if situation.find('.//siri:OperatorRef', ns) is not None else 'Unknown'
    summary = situation.find('siri:Summary', ns).text if situation.find('siri:Summary', ns) is not None else 'Unknown'
    description = situation.find('siri:Description', ns)
    start_time = situation.find('.//siri:StartTime', ns).text if situation.find('.//siri:StartTime', ns) is not None else 'Unknown'
    end_time = situation.find('.//siri:EndTime', ns).text if situation.find('.//siri:EndTime', ns) is not None else 'Unknown'
    planned = situation.find('siri:Planned', ns).text if situation.find('siri:Planned', ns) is not None else 'Unknown'
    consequence_severity = situation.find('.//siri:Severity', ns).text if situation.find('.//siri:Severity', ns) is not None else 'Unknown'

    # Iterate through affected stops
    for stop in situation.findall('.//siri:AffectedStopPoint', ns):
        stop_name = stop.find('siri:StopPointName', ns).text if stop.find('siri:StopPointName', ns) is not None else 'Unknown'
        lat = stop.find('.//siri:Latitude', ns).text if stop.find('.//siri:Latitude', ns) is not None else 'Unknown'
        lon = stop.find('.//siri:Longitude', ns).text if stop.find('.//siri:Longitude', ns) is not None else 'Unknown'

        # Append extracted data to the list
        data.append([
            situation_number, operator_name, summary, description.text if description is not None else '',
            start_time, end_time, stop_name, lat, lon,
            planned, consequence_severity
        ])

# Convert to DataFrame
df = pd.DataFrame(data, columns=[
    'Situation Number', 'Operator', 'Summary', 'Description', 'Start Time', 'End Time',
    'Stop Name', 'Latitude', 'Longitude', 'Planned', 'Consequence Severity'
])

# Display the DataFrame
# print(df.head())

# Convert Start Time and End Time to datetime
df['Start Time'] = pd.to_datetime(df['Start Time'], errors='coerce')
df['End Time'] = pd.to_datetime(df['End Time'], errors='coerce')

# Convert Latitude and Longitude to numeric
df['Latitude'] = pd.to_numeric(df['Latitude'], errors='coerce')
df['Longitude'] = pd.to_numeric(df['Longitude'], errors='coerce')

# Check for missing values in the DataFrame
missing_values = df.isnull().sum()
print("Missing values in each column:\n", missing_values)

# Handle missing End Time by marking them as 'Unknown'
df['Unknown'] = df['End Time'].isna()

# Calculate the duration (in hours) of each disruption; if End Time is missing, mark it as 'Unknown'
df['Duration'] = df.apply(lambda row: 'Unknown' if row['Unknown'] else (row['End Time'] - row['Start Time']).total_seconds() / 3600, axis=1)

# Aggregate duplicate information by 'Situation Number' to consolidate data
df_aggregated = df.groupby('Situation Number').agg({
    'Operator': 'first',
    'Summary': 'first',
    'Description': 'first',
    'Start Time': 'first',
    'End Time': 'first',
    'Stop Name': lambda x: ', '.join(x.unique()),
    'Latitude': 'mean',
    'Longitude': 'mean',
    'Planned': 'first',
    'Consequence Severity': 'first',
    'Duration': 'first',
    'Unknown': 'first'
}).reset_index()

print(f"Shape of DataFrame after aggregating duplicates: {df_aggregated.shape}")

x = df_aggregated

# Define the keyword categories in a dictionary
keyword_categories = {
    'Service Withdrawal': ['withdrawal'],
    'Bus Stop Closure': ['stop closure', 'bus stop closure', 'stop closed', 'bus stop suspension', 'bus station'],
    'Road Closure': ['road closure', 'road will be closed', 'lane is closed', 'road closed', 'drive will be closed',
                     'road east will be closed', 'lane will be closed', 'street in leeds city centre closed'],
    'Service Diversion': ['diversion', 'service', 'divert'],
    'Roadworks': ['roadworks', 'road works', 'line works', 'road conditions', 'surface dressing', 'installation'],
    'Emergency Closure': ['emergency'],
    'Special Events': ['event', 'march'],
    'Maintenance/Repair': ['maintenance', 'repair', 'replacement', 'upgrade', 'water', 'resurfacing', 'renewal', 'junction', 'gas works', 'waterpipe'],
    'Construction/Demolition': ['construction', 'demolition'],
    'Incident': ['incident'],
    'Security Issue': ['police', 'security', 'safety'],
    'Staff Shortage': ['staff', 'shortage'],
    'Bridge Issue': ['bridge'],
    'Traffic': ['traffic'],
    'Tram Works/Disruption': ['tram'],
    'Service Change': ['service change']
}


# Function to categorize based on keywords
def categorize(text, categories):
    text_lower = text.lower()
    for category, keywords in categories.items():
        if any(keyword in text_lower for keyword in keywords):
            return category
    return 'Others'


# Apply the categorization function to the "Description" field
x['Detailed Disruption Category'] = x['Description'].apply(lambda x: categorize(x, keyword_categories))

# Identify rows categorized as "Others"
others_rows = x[x['Detailed Disruption Category'] == 'Others']

# Re-categorize "Others" using the "Summary" field for more accurate categorization
others_rows['Detailed Disruption Category'] = others_rows['Summary'].apply(lambda x: categorize(x, keyword_categories))

# Update the original dataset with the re-categorized rows
x.loc[others_rows.index, 'Detailed Disruption Category'] = others_rows['Detailed Disruption Category']

# Display the distribution of categories
category_counts = x['Detailed Disruption Category'].value_counts()
print("Distribution of Detailed Disruption Categories:\n", category_counts)


# Efficient re-categorization function to group similar categories into broader ones
def efficient_recategorize(category):
    if category in ['Bus Stop Closure']:
        return 'Bus Stop Closure'
    elif category in ['Road Closure']:
        return 'Road Closure'
    elif category in ['Maintenance/Repair', 'Roadworks', 'Construction/Demolition', 'Tram Works/Disruption']:
        return 'Infrastructure Work'
    elif category in ['Service Diversion', 'Service Withdrawal', 'Service Change']:
        return 'Service Changes'
    elif category in ['Special Events', 'Emergency Closure', 'Security Issue']:
        return 'Events and Emergency Circumstances'
    elif category in ['Incident', 'Traffic', 'Bridge Issue']:
        return 'Incidents'
    else:
        return 'Others'


# Apply the final categorization function to the existing "Disruption Category"
x['Efficient Disruption Category'] = x['Detailed Disruption Category'].apply(efficient_recategorize)

# Display the distribution of categories
efficient_category_counts = x['Efficient Disruption Category'].value_counts()
print("Distribution of Efficient Disruption Categories:\n", efficient_category_counts)

x.to_csv('Causes_all_disruption_data.csv', index=False)
print(x.head())

# Convert the DataFrame to a GeoDataFrame for geospatial analysis
gdf = gpd.GeoDataFrame(x, geometry=gpd.points_from_xy(x.Longitude, x.Latitude))

# Plot the top 10 disruption hotspots based on location frequency
hotspots = gdf['geometry'].value_counts().head(10)
hotspots.plot(kind='bar')
plt.title('Top 10 Disruption Hotspots')
plt.xlabel('Location')
plt.ylabel('Number of Disruptions')
plt.show(block=True)

x['hour'] = x['Start Time'].dt.hour
temporal_patterns = x['hour'].value_counts().sort_index()
temporal_patterns.plot(kind='bar')
plt.title('Disruptions by Hour')
plt.xlabel('Hour of the Day')
plt.ylabel('Number of Disruptions')
plt.show(block=True)

































