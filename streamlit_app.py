import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Set page config
st.set_page_config(page_title="Accessible Excellence Explorer", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv('accessible_excellence.csv')
    
    # Rename columns for clarity
    column_mapping = {
        'Institution Name': 'Name',
        'City location of institution (HD2022)': 'City',
        'State abbreviation (HD2022)': 'State',
        'Control of institution (IPEDS)': 'Control',
        'Fit Rating for Accessible Excellence List': 'Fit Rating'
    }
    
    df = df.rename(columns={old: new for old, new in column_mapping.items() if old in df.columns})
    
    # Create Public/Private column
    df['Institution Type'] = df['Control'].map({1: 'Public', 2: 'Private'})
    
    return df

# Load the data
try:
    df = load_data()
except Exception as e:
    st.error(f"Error loading data: {str(e)}")
    st.stop()

# Main layout
st.title('Accessible Excellence Explorer')
st.write('Explore institutions based on their Fit Rating for Accessible Excellence')

# Sidebar for filters
st.sidebar.header('Filters')

# Fit Rating filter
fit_ratings = df['Fit Rating'].unique()
selected_ratings = st.sidebar.multiselect('Select Fit Ratings', fit_ratings, default=fit_ratings)

# Institution Type filter
institution_types = df['Institution Type'].unique()
selected_types = st.sidebar.multiselect('Select Institution Types', institution_types, default=institution_types)

# State filter
states = sorted(df['State'].unique())
selected_states = st.sidebar.multiselect('Select States', states, default=[])

# Search box
search_term = st.sidebar.text_input('Search for an institution')

# Filter the dataframe
filtered_df = df[
    (df['Fit Rating'].isin(selected_ratings)) &
    (df['Institution Type'].isin(selected_types)) &
    (df['Name'].str.contains(search_term, case=False, na=False))
]

if selected_states:
    filtered_df = filtered_df[filtered_df['State'].isin(selected_states)]

# Map visualization
st.subheader('Institution Locations')

# Create a color map for fit ratings
color_map = {'★★★': 'green', '★★☆': 'orange', '★☆☆': 'red'}

# Filter out rows with missing lat/long
map_df = filtered_df.dropna(subset=['Latitude', 'Longitude'])

# Create the figure
fig = go.Figure()

# Add traces for each fit rating
for rating in map_df['Fit Rating'].unique():
    df_rating = map_df[map_df['Fit Rating'] == rating]
    
    fig.add_trace(go.Scattermapbox(
        lat=df_rating['Latitude'],
        lon=df_rating['Longitude'],
        mode='markers',
        marker=go.scattermapbox.Marker(
            size=10,
            color=color_map.get(rating, 'gray'),
        ),
        text=df_rating['Name'],
        hoverinfo='text',
        customdata=df_rating[['City', 'State', 'Institution Type', 'Fit Rating']],
        hovertemplate=(
            "<b>%{text}</b><br>" +
            "%{customdata[0]}, %{customdata[1]}<br>" +
            "%{customdata[2]}<br>" +
            "Fit Rating: %{customdata[3]}<br>" +
            "<extra></extra>"
        )
    ))

# Update the layout
fig.update_layout(
    mapbox_style="open-street-map",
    mapbox=dict(
        center=dict(lat=map_df['Latitude'].mean(), lon=map_df['Longitude'].mean()),
        zoom=3
    ),
    showlegend=False,
    height=600,
    margin={"r":0,"t":0,"l":0,"b":0}
)

st.plotly_chart(fig, use_container_width=True)

# Data table
st.subheader('Institution Data')

# Main table with key metrics
main_columns = ['Name', 'City', 'State', 'Institution Type', 'Fit Rating']
st.dataframe(filtered_df[main_columns])

# Add debug information
st.sidebar.write("Debug Information:")
st.sidebar.write(f"Total institutions: {len(df)}")
st.sidebar.write(f"Displayed institutions: {len(filtered_df)}")
st.sidebar.write(f"Filtered out institutions: {len(df) - len(filtered_df)}")
