import pandas as pd
import folium
from folium.plugins import FastMarkerCluster
from dash import Dash, dcc, html, Input, Output

# Load your data
df = pd.read_csv("df.csv")

# Initialize the Dash app
app = Dash(__name__)

# Layout of the app
app.layout = html.Div([
    html.H1("Australia Charities Map Dashboard"),

    html.Label("Select the Main Activity Types of the Charity:"),
    dcc.Dropdown(
        options=[{'label': 'All', 'value': 'All'}] + 
                [{'label': activity, 'value': activity} for activity in df['main_activity'].unique()],
        id='charity-type',
        value='All' 
    ),

    html.Label("Select the State:"),
    dcc.Dropdown(
        options=[{'label': 'All', 'value': 'All'}] + 
                [{'label': state, 'value': state} for state in df['state'].unique()],
        id='state-dropdown',
        value='All'
    ),

    html.Iframe(id='map', srcDoc=None, width='35%', height='500'),
])

# Callback to update the map and charity list based on filters
@app.callback(
    Output('map', 'srcDoc'),
    Input('charity-type', 'value'),
    Input('state-dropdown', 'value')
)
def update_map_and_list(selected_activity, selected_state):
    # Filter based on selected activity
    if selected_activity == 'All':
        filtered_df = df
    else:
        filtered_df = df[df['main_activity'] == selected_activity]

    # Further filter based on selected state
    if selected_state != 'All':
        filtered_df = filtered_df[filtered_df['state'] == selected_state]

    # Create the map
    latitude = filtered_df['latitude'].tolist()
    longitude = filtered_df['longitude'].tolist()
    locations = list(zip(latitude, longitude))

    map = folium.Map(location=[-25.2744, 133.7751], zoom_start=5)  # Centered on Australia
    FastMarkerCluster(data=locations).add_to(map)
    map.save("map.html")

    return open("map.html", "r").read()

# Run the server
if __name__ == '__main__':
    app.run_server(debug=True)

