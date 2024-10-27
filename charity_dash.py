from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import folium
from folium.plugins import FastMarkerCluster

df_2018 = pd.read_excel('final_data.xlsx', sheet_name='18-year')
df_2019 = pd.read_excel('final_data.xlsx', sheet_name='19-year')
df_2020 = pd.read_excel('final_data.xlsx', sheet_name='20-year')
df_2021 = pd.read_excel('final_data.xlsx', sheet_name='21-year')
df_2022 = pd.read_excel('final_data.xlsx', sheet_name='22-year')

df_2018['year'] = 2018
df_2019['year'] = 2019
df_2020['year'] = 2020
df_2021['year'] = 2021
df_2022['year'] = 2022

df = pd.concat([df_2018, df_2019, df_2020, df_2021, df_2022])

year_options = df['year'].unique().tolist()
staff_types = {
    'Full Time': 'staff_full_time',
    'Part Time': 'staff_part_time',
    'Casual': 'staff_casual',
    'Volunteers': 'staff_volunteers'
}

app = Dash(__name__)

app.layout = html.Div([
    html.H1("Australia Charities Dashboard", style={'textAlign': 'center', 'fontSize': '32px'}),
    html.Label("Select the Main Activity Types of the Charity:"),
    dcc.Dropdown(
        id='main_activity',
        options=[{'label':'All','value':'All'}]+[{'label': main_activity, 'value': main_activity} for main_activity in sorted(df['main_activity'].dropna().unique())],
        value='All', 
        multi=False, 
        clearable=False,
        placeholder="Select Main Activity"
    ),
    html.Label("Select the State:"),
    dcc.Dropdown(
        id='state',
        options=[{'label':'All','value':'All'}]+[{'label': state, 'value': state} for state in sorted(df['state'].dropna().unique())],
        value='All', 
        multi=False, 
        clearable=False,
        placeholder="Select State"
    ),
    html.Div(
        html.Iframe(id='map', srcDoc=None, width='70%', height='500'), 
        style={'display': 'flex', 'justifyContent': 'center'} 
    ),
    html.Label("Select Charities:"),
    dcc.Dropdown(
        id='charity_name',
        multi=True,
        clearable=False,
        placeholder="Select Charity Name",
        maxHeight=300
    ),
    html.Label("Select the Year:"),
    dcc.Dropdown(
        id='year',
        options=[{'label': str(year), 'value': year} for year in sorted(df['year'].unique())],
        value=2022,
        clearable=False,
        placeholder="Select Year"
    ),
    dcc.Checklist(
        id='staff-type-checklist',
        options=[{'label': label, 'value': value} for label, value in staff_types.items()],
        value=list(staff_types.values()), 
        inline=True
    ),
    html.Div([
        dcc.Graph(id='multi-line-chart'),
    ], style={'width': '100%', 'display': 'inline-block', 'padding-bottom': '20px'}),

    html.Label("Charities Staff Components:", style={'fontSize': '18px', 'display': 'block'}),
    html.Div(id='pie-charts-container', style={'display': 'flex', 'flex-wrap': 'wrap'}),

    html.Div([
        dcc.Graph(id='revenue_line_graph', style={'width': '50%', 'display': 'inline-block'}),
        dcc.Graph(id='revenue_graph', style={'width': '50%', 'display': 'inline-block'}),
    ], style={'display': 'flex', 'flex-direction': 'row'}),

    html.Div([
        dcc.Graph(id='expense_line_graph', style={'width': '50%', 'display': 'inline-block'}),
        dcc.Graph(id='expense_components_graph', style={'width': '50%', 'display': 'inline-block'}),
    ], style={'display': 'flex', 'flex-direction': 'row'}),
    html.Label("Charities Gauge:", style={'fontSize': '18px', 'display': 'block'} ),
    html.Div(id='gauge_charts', style={'display': 'flex', 'flex-wrap': 'wrap'})
])


@app.callback(
    Output('charity_name', 'options'),
    [Input('main_activity', 'value'), Input('state', 'value'), Input('year', 'value')]
)
def update_charity_options(selected_main_activity, selected_state, selected_year):
    if selected_main_activity and selected_state and selected_year:

        filtered_df = df[(df['main_activity'] == selected_main_activity) &
                         (df['state'] == selected_state) &
                         (df['year'] == selected_year)]
        return [{'label': name, 'value': name} for name in sorted(filtered_df['charity_name'].unique())]
    return []

@app.callback(
    Output('map', 'srcDoc'),
    Input('main_activity', 'value'),
    Input('state', 'value')
)
def update_map_and_list(selected_main_activity, selected_state):

    if selected_main_activity == 'All':
        filtered_df = df
    else:
        filtered_df = df[df['main_activity'] == selected_main_activity]

    if selected_state != 'All':
        filtered_df = filtered_df[filtered_df['state'] == selected_state]

    latitude = filtered_df['latitude'].tolist()
    longitude = filtered_df['longitude'].tolist()
    locations = list(zip(latitude, longitude))

    num_to_display = max(1, len(locations) // 5)  
    reduced_locations = locations[:num_to_display]  

    map = folium.Map(location=[-25.2744, 133.7751], zoom_start=5) 
    FastMarkerCluster(data=reduced_locations).add_to(map)
    map.save("map.html")

    return open("map.html", "r").read()


@app.callback(
    Output('multi-line-chart', 'figure'),
    [Input('charity_name', 'value'),
     Input('staff-type-checklist', 'value')]
)
def update_multi_line(selected_charity_name, selected_staff_types):
    if not selected_charity_name:
        return {}

    filtered_df = df[df['charity_name'].isin(selected_charity_name)]
    filtered_df['total_selected_staff'] = filtered_df[selected_staff_types].sum(axis=1)
    
    fig = px.line(
        filtered_df,
        x='year',
        y='total_selected_staff',
        color='charity_name',
        title="Staff Trends over Years (2018-2022)",
        markers=True
    )
    fig.update_layout(legend=dict(
        orientation="h",
        yanchor="bottom",
        y=-0.4,
        xanchor="center",
        x=0.5
    ))
    fig.update_xaxes(type='category')
    return fig


@app.callback(
    Output('pie-charts-container', 'children'),
    [Input('charity_name', 'value'),
     Input('year', 'value'),
     Input('staff-type-checklist', 'value')]
)
def update_pie_charts(selected_charity_name, selected_year, selected_staff_types):
    if not selected_charity_name or not selected_year:
        return []

    selected_charity_name = selected_charity_name[:4]

    pie_charts = []

    for i, charity in enumerate(selected_charity_name):
        charity_df = df[(df['charity_name'] == charity) & (df['year'] == int(selected_year))]

        if charity_df.empty:
            continue

        charity_df['total_selected_staff'] = charity_df[selected_staff_types].sum(axis=1)
        staff_distribution = charity_df[selected_staff_types].sum().reset_index()
        staff_distribution.columns = ['staff_type', 'count']

        fig = px.pie(
            staff_distribution,
            values='count',
            names='staff_type',
            title=f"{selected_year} {charity}",
            hole=0.4 
        )

        if i < len(selected_charity_name) - 1:
            fig.update_layout(showlegend=False)
        else:
            fig.update_layout(showlegend=True, legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5
            ))

        pie_charts.append(
            html.Div(
                dcc.Graph(figure=fig),
                style={'width': '25%', 'display': 'inline-block', 'vertical-align':'top'}
            )
        )

    return pie_charts


@app.callback(
    Output('revenue_graph', 'figure'),
    [Input('main_activity', 'value'), Input('state', 'value'), Input('charity_name', 'value'), Input('year', 'value')]
)
def update_revenue_graph(selected_main_activity, selected_state, selected_charity_name, selected_year):
    if not selected_main_activity or not selected_state or not selected_charity_name or not selected_year:
        return {}

    filtered_df = df[(df['main_activity'] == selected_main_activity) &
                     (df['state'] == selected_state) &
                     (df['charity_name'].isin(selected_charity_name)) &
                     (df['year'] == selected_year)]

    fig = px.bar(
        filtered_df,
        x='charity_name',
        y=['revenue_from_government', 'donations_and_bequests', 'revenue_from_goods_and_services', 
           'revenue_from_investments', 'all_other_revenue'],
        title=f"Revenue Components for {selected_year}",
        barmode='stack',
    )
    fig.update_layout(
        xaxis_title="Charity Name",
        yaxis_title="Revenue Components",
        legend_title="Revenue Types"
    )
    return fig


@app.callback(
    Output('revenue_line_graph', 'figure'),
    [Input('main_activity', 'value'), Input('state', 'value'), Input('charity_name', 'value')]
)
def update_revenue_line_graph(selected_main_activity, selected_state, selected_charity_name):
    if not selected_main_activity or not selected_state or not selected_charity_name:
        return {}

    filtered_df = df[(df['main_activity'] == selected_main_activity) &
                     (df['state'] == selected_state) &
                     (df['charity_name'].isin(selected_charity_name))]

    fig = px.line(
        filtered_df,
        x='year',
        y='total_revenue',
        color='charity_name',
        title="Total Revenue Across Years",
        markers=True
    )
    fig.update_layout(
        xaxis_title="Year",
        yaxis_title="Total Revenue",
        xaxis_type='category',
        legend_title="Charity"
    )
    fig.update_layout(legend=dict(
        orientation="h",
        yanchor="bottom",
        y=-0.4,
        xanchor="center",
        x=0.5
    ))
    return fig


@app.callback(
    Output('expense_components_graph', 'figure'),
    [Input('main_activity', 'value'), Input('state', 'value'), Input('charity_name', 'value'), Input('year', 'value')]
)
def update_expense_components_graph(selected_main_activity, selected_state, selected_charity_name, selected_year):
    if not selected_main_activity or not selected_state or not selected_charity_name or not selected_year:
        return {}

    filtered_df = df[(df['main_activity'] == selected_main_activity) &
                     (df['state'] == selected_state) &
                     (df['charity_name'].isin(selected_charity_name)) &
                     (df['year'] == selected_year)]

    fig = px.bar(
        filtered_df,
        x='charity_name',
        y=['employee_expenses', 'interest_expenses', 'grants_and_donations_made_for_use_in_Australia', 
           'grants_and_donations_made_for_use_outside_Australia', 'all_other_expenses'],
        title=f"Expense Components for {selected_year}",
        barmode='stack',
    )
    fig.update_layout(
        xaxis_title="Charity Name",
        yaxis_title="Expense Components",
        legend_title="Expense Types"
    )
    return fig


@app.callback(
    Output('expense_line_graph', 'figure'),
    [Input('main_activity', 'value'), Input('state', 'value'), Input('charity_name', 'value')]
)
def update_expense_line_graph(selected_main_activity, selected_state, selected_charity_name):
    if not selected_main_activity or not selected_state or not selected_charity_name:
        return {}

    filtered_df = df[(df['main_activity'] == selected_main_activity) &
                     (df['state'] == selected_state) &
                     (df['charity_name'].isin(selected_charity_name))]

    fig = px.line(
        filtered_df,
        x='year',
        y='total_expenses',
        color='charity_name',
        title="Total Expenses Across Years",
        markers=True
    )
    fig.update_layout(
        xaxis_title="Year",
        yaxis_title="Total Expenses",
        xaxis_type='category',
        legend_title="Charity"
    )
    fig.update_layout(legend=dict(
        orientation="h",
        yanchor="bottom",
        y=-0.4,
        xanchor="center",
        x=0.5
    ))
    return fig


@app.callback(
    Output('gauge_charts', 'children'),
    [Input('main_activity', 'value'), Input('state', 'value'), Input('charity_name', 'value'), Input('year', 'value')]
)
def update_gauge_charts(selected_main_activity, selected_state, selected_charity_name, selected_year):
    if not selected_main_activity or not selected_state or not selected_charity_name or not selected_year:
        return []

    filtered_df = df[(df['main_activity'] == selected_main_activity) &
                     (df['state'] == selected_state) &
                     (df['charity_name'].isin(selected_charity_name)) &
                     (df['year'] == selected_year)].head(4)

    gauges = []
    for index, row in filtered_df.iterrows():
        net_deficit = row['net_surplus_deficit'] / 1000 
        min_value = df['net_surplus_deficit'].min() / 1000 
        max_value = -min_value 

        fig = go.Figure(go.Indicator(
            mode="gauge+number", 
            value=net_deficit, 
            title={'text': row['charity_name'], 'font': {'size': 14}}, 
            gauge={
                'axis': {'range': [min_value, max_value], 'tickwidth': 1, 'tickcolor': "darkblue"},
                'bar': {'color': "black", 'thickness': 0.2}, 
                'steps': [
                    {'range': [min_value, min_value / 2], 'color': "red"},
                    {'range': [min_value / 2, 0], 'color': "orange"},
                    {'range': [0, max_value / 2], 'color': "yellow"},
                    {'range': [max_value / 2, max_value], 'color': "green"},
                ],
                'threshold': {
                    'line': {'color': "black", 'width': 6}, 
                    'thickness': 0.75, 
                    'value': net_deficit 
                },
            },
            number={
                'prefix': "$",  
                'suffix': "K", 
                'valueformat': ",.1f" 
            }
        ))

        gauges.append(dcc.Graph(figure=fig, style={'width': '24%', 'display': 'inline-block'}))
    
    return gauges

if __name__ == '__main__':
    app.run_server(debug=True)
