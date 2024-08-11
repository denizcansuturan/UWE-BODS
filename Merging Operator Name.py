import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

# Set Pandas display options to show all columns and rows
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.max_colwidth', None)  # Show full column width

# Load the datasets
causes_df = pd.read_csv('Data/Causes_all_disruption_data.csv')
operators_df = pd.read_csv('Data/bods data catalogue overall/operator_noc_data_catalogue.csv')

# Standardize 'Consequence Severity' values by replacing variations with uniform terms
severity_mapping = {
    'unknown': 'Unknown',
    'normal': 'Normal',
    'severe': 'Severe',
    'slight': 'Slight',
    'verySevere': 'Very Severe',
    'verySlight': 'Very Slight'
}
causes_df['Consequence Severity'] = causes_df['Consequence Severity'].replace(severity_mapping)


# List of ceremonial counties in England
counties = [
    "Bedfordshire", "Berkshire", "Bristol", "Buckinghamshire", "Cambridgeshire", "Cheshire",
    "City of London", "Cornwall", "Cumbria", "Derbyshire", "Devon", "Dorset", "Durham",
    "East Riding of Yorkshire", "East Sussex", "Essex", "Gloucestershire", "Greater London",
    "Greater Manchester", "Hampshire", "Herefordshire", "Hertfordshire", "Isle of Wight",
    "Kent", "Lancashire", "Leicestershire", "Lincolnshire", "Merseyside", "Norfolk",
    "North Yorkshire", "Northamptonshire", "Northumberland", "Nottinghamshire", "Oxfordshire",
    "Rutland", "Shropshire", "Somerset", "South Yorkshire", "Staffordshire", "Suffolk",
    "Surrey", "Tyne and Wear", "Warwickshire", "West Midlands", "West Sussex", "West Yorkshire",
    "Wiltshire", "Worcestershire"
]

# Rename columns in operators_df for clarity
operators_df.columns = ['Operator_name', 'Operator']

# Merge the causes and operators dataframes on the 'Operator' column
merged_df = pd.merge(causes_df, operators_df, on='Operator', how='left')

# Replace missing Operator names with 'Unknown'
merged_df['Operator_name'].fillna('unknown', inplace=True)

# Handle operators that doesn't have full names by using the code itself as the operator name
special_codes = ['SYFT', 'METL', 'SPCT']
merged_df.loc[merged_df['Operator'].isin(special_codes), 'Operator_name'] = merged_df['Operator']

# merged_df[merged_df['Operator_name'] == 'unknown'][['Operator', 'Operator_name']]


# Function to get location name from coordinates using geopy
def get_location_name(lat, lon):
    geolocator = Nominatim(user_agent="geoapiExercises")
    location = geolocator.reverse((lat, lon), exactly_one=True)
    return location.address if location else "Unknown Location"


# Function to determine the county from a location name
def determine_county(location_name):
    for county in counties:
        if county in location_name:
            return county
    return "Unknown"


# Initialize geolocator with rate limiter to avoid exceeding API limits
geolocator = Nominatim(user_agent="geoapiExercises")
reverse = RateLimiter(geolocator.reverse, min_delay_seconds=1, return_value_on_exception=None)

# Apply the function to determine the county for each row based on latitude and longitude
merged_df['County'] = merged_df.apply(lambda row: determine_county(get_location_name(row['Latitude'], row['Longitude'])), axis=1)

# Replace 'Unknown' in the 'County' column with 'Liverpool'
merged_df.loc[merged_df['County'] == 'Unknown', 'County'] = 'Liverpool'
# merged_df.columns
merged_df['Operator_name'] = merged_df['Operator_name'].replace('unknown', 'Unknown')
# Save the final dataframe to a CSV file
# merged_df.to_csv('final.csv', index=False)
