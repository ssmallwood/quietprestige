import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# Set page config
st.set_page_config(page_title="Hidden Gems Finder", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv('gems_with_coordinates.csv')
    
    # Function to convert percentage strings to floats
    def convert_percentage(value):
        if isinstance(value, str):
            return float(value.strip('%')) / 100
        return value

    # Function to convert to float, handling non-numeric strings
    def safe_float(value):
        if pd.isna(value):
            return np.nan
        try:
            return float(value.replace('$', '').replace(',', ''))
        except (ValueError, AttributeError):
            return np.nan

    # Convert percentages to floats and handle potential string values
    percentage_columns = ['Acceptance Rate 2022 (IPEDS)', '6 Year Grad Rate 2022 (IPEDS)', 'FTFT Grad Rate (6 Years) 2015-2016 Cohort (Bain)', 'Yield Rate 2022 (IPEDS)']
    for col in percentage_columns:
        if col in df.columns:
            df[col] = df[col].apply(convert_percentage)
    
    # Handle 'Average net price over four years (Itkowitz)' separately
    if 'Average net price over four years (Itkowitz)' in df.columns:
        df['Average net price over four years (Itkowitz)'] = df['Average net price over four years (Itkowitz)'].apply(safe_float)
    
    # Ensure 'Earnings-to-Price Ratio (Itzkowitz)' is float without modifying its format
    if 'Earnings-to-Price Ratio (Itzkowitz)' in df.columns:
        df['Earnings-to-Price Ratio (Itzkowitz)'] = pd.to_numeric(df['Earnings-to-Price Ratio (Itzkowitz)'], errors='coerce')
    
    # Rename columns for clarity
    column_mapping = {
        'Institution Name': 'Name',
        'Acceptance Rate 2022 (IPEDS)': 'Admission Rate',
        'Earnings-to-Price Ratio (Itzkowitz)': 'Earnings to Price Ratio',
        '6 Year Grad Rate 2022 (IPEDS)': 'Graduation Rate',
        'Control of institution (IPEDS)': 'Control',
        'City location of institution (HD2022)': 'City',
        'State abbreviation (HD2022)': 'State',
        'Average net price over four years (Itkowitz)': 'Four Year Cost',
        'Yield Rate 2022 (IPEDS)': 'Yield Rate'
    }
    
    df = df.rename(columns={old: new for old, new in column_mapping.items() if old in df.columns})
    
    # Create Public/Private column
    df['Institution Type'] = df['Control'].map({1: 'Public', 2: 'Private'})
    
    # Print data types and some statistics for debugging
    print(df.dtypes)
    print(df['Earnings to Price Ratio'].describe())
    
    return df

# Load the data
try:
    df = load_data()
except Exception as e:
    st.error(f"Error loading data: {str(e)}")
    st.stop()

# Main layout
st.title('Hidden Gems Finder')
st.write('Discover potential gem colleges across the United States.')

# Sidebar for filters
st.sidebar.header('Filters')

# Sliders for filtering
admission_rate = st.sidebar.slider('Admission Rate', 0.0, 1.0, (0.0, 1.0))
graduation_rate = st.sidebar.slider('Graduation Rate', 0.0, 1.0, (0.0, 1.0))

# Handle Earnings to Price Ratio
earnings_ratio_values = df['Earnings to Price Ratio'].dropna()
if len(earnings_ratio_values) > 0:
    earnings_ratio_min = float(earnings_ratio_values.min())
    earnings_ratio_max = min(float(earnings_ratio_values.max()), 10.0)  # Cap at 2.0
    earnings_ratio = st.sidebar.slider('Earnings to Price Ratio', 
                                       earnings_ratio_min, 
                                       earnings_ratio_max, 
                                       (earnings_ratio_min, earnings_ratio_max))
else:
    st.sidebar.warning("No valid Earnings to Price Ratio data available.")
    earnings_ratio = (0, 2)  # Default range if no valid data

# Search box
search_term = st.sidebar.text_input('Search for an institution')

# Filter the dataframe
filtered_df = df[
    (df['Admission Rate'].between(admission_rate[0], admission_rate[1], inclusive='both')) &
    (df['Graduation Rate'].between(graduation_rate[0], graduation_rate[1], inclusive='both')) &
    (
        (df['Earnings to Price Ratio'].between(earnings_ratio[0], earnings_ratio[1], inclusive='both')) |
        (df['Earnings to Price Ratio'].isna())  # Include NaN values
    ) &
    (df['Name'].str.contains(search_term, case=False, na=False))
]


# Add a debug print statement
st.sidebar.write(f"Number of colleges after filtering: {len(filtered_df)}")

# Toggle for map visibility
show_map = st.checkbox('Show Map', value=True)

if show_map and not filtered_df.empty:
    # Map visualization
    st.subheader('College Locations')

    # Create a color map for public/private institutions
    color_map = {'Public': 'orange', 'Private': 'green'}

    # Filter out rows with missing lat/long
    map_df = filtered_df.dropna(subset=['Latitude', 'Longitude'])

    fig = px.scatter_mapbox(map_df, 
                            lat='Latitude', 
                            lon='Longitude', 
                            hover_name='Name', 
                            color='Institution Type',
                            color_discrete_map=color_map,
                            zoom=3, 
                            height=600)

    fig.update_traces(marker=dict(size=10))  # Increase marker size

    fig.update_layout(mapbox_style="open-street-map")
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

    # Custom hover template
    hovertemplate = "<b>%{hovertext}</b><br>" + \
                    "%{customdata[0]}, %{customdata[1]}<br>" + \
                    "%{customdata[2]}<br>" + \
                    "Admission Rate: %{customdata[3]:.0%}<br>" + \
                    "Earnings to Price Ratio: %{customdata[4]:.1f}<br>" + \
                    "Graduation Rate: %{customdata[5]:.0%}<br>" + \
                    "Four Year Cost: $%{customdata[6]:,.0f}<br>" + \
                    "Yield Rate: %{customdata[7]:.0%}<br>" + \
                    "<extra></extra>"

    fig.update_traces(
        hovertemplate=hovertemplate,
        customdata=map_df[['City', 'State', 'Institution Type', 'Admission Rate', 
                           'Earnings to Price Ratio', 'Graduation Rate', 'Four Year Cost', 'Yield Rate']]
    )

    st.plotly_chart(fig, use_container_width=True)
elif show_map:
    st.warning("No colleges to display on the map based on current filters.")

# Data table
st.subheader('College Data')

# Main table with all metrics
main_columns = ['Name', 'City', 'State', 'Institution Type', 'Admission Rate', 'Earnings to Price Ratio', 
                'Graduation Rate', 'Four Year Cost', 'Yield Rate']
st.dataframe(filtered_df[main_columns].style.format({
    'Admission Rate': '{:.0%}',
    'Graduation Rate': '{:.0%}',
    'Earnings to Price Ratio': '{:.2f}',
    'Four Year Cost': '${:,.0f}',
    'Yield Rate': '{:.0%}'
}))

# Display filtered out colleges
filtered_out_df = df[~df.index.isin(filtered_df.index)]
with st.expander("Filtered Out Colleges"):
    st.dataframe(filtered_out_df[main_columns].style.format({
        'Admission Rate': '{:.0%}',
        'Graduation Rate': '{:.0%}',
        'Earnings to Price Ratio': '{:.2f}',
        'Four Year Cost': '${:,.0f}',
        'Yield Rate': '{:.0%}'
    }))

# Add debug information
st.sidebar.write("Debug Information:")
st.sidebar.write(f"Total colleges: {len(df)}")
st.sidebar.write(f"Displayed colleges: {len(filtered_df)}")
st.sidebar.write(f"Filtered out colleges: {len(filtered_out_df)}")