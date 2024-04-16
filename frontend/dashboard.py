import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash
from dash import dcc
from dash import html
import plotly.graph_objects as go

#import raw revenue data
df_2016 = pd.read_csv("../raw_data/orders2016.csv", sep=";")
df_2017 = pd.read_csv("../raw_data/orders2017.csv", sep=";")
df_2018 = pd.read_csv("../raw_data/orders2018.csv", sep=";")
df_2019 = pd.read_csv("../raw_data/orders2019.csv", sep=";")
df_2020 = pd.read_csv("../raw_data/orders2020.csv", sep=";")
df_2021 = pd.read_csv("../raw_data/orders2021.csv", sep=";")
df_2022 = pd.read_csv("../raw_data/orders2022.csv", sep=";")

df_list = [df_2016, df_2017, df_2018, df_2019, df_2020, df_2021, df_2022]

#Dropping unnecessary columns, grouping by "date", summing "item_price" to get daily revenues

for i, df in enumerate(df_list):
    df_list[i] = pd.DataFrame(df.groupby(by="date")["item_price"].sum()/100)

#Concat all data in one dataframe, rename the columns for prophet

df = pd.concat(df_list, ignore_index=False)
df = df.rename(columns={"date": "ds", "item_price": "y"})
df["ds"] = df.index
df = df.reset_index(drop=True)
df = df[["ds","y"]]
df

#turning the ds (date) column into datetime

df['ds']=pd.to_datetime(df['ds'])

# Expanding dates for complete dates
min_date = pd.to_datetime("2016-01-01")
max_date = pd.to_datetime("2022-12-31")
all_dates = pd.date_range(min_date, max_date, freq='D')
df = df.set_index('ds').reindex(all_dates).reset_index().rename(columns={'index': 'ds'})

# Reset index to start from 0
df = df.reset_index(drop=True)

#Fill missing values with zeros
df['y'] = df['y'].fillna(0)

#Creating seasonal columns
df['Year'] = df['ds'].dt.year
df['Season'] = df['ds'].dt.quarter.map({1: 'Winter', 2: 'Spring', 3: 'Summer', 4: 'Fall'})
df['Month'] = df['ds'].dt.month_name()
df['Week'] = df['ds'].dt.week
df['Weekday'] = df['ds'].dt.strftime('%A')

# Compute total revenue and fill missing values with zeros
total_revenue = df['y'].sum()

# Prepare the data
df_hierarchy = df.groupby(['Year', 'Season', 'Month', 'Week', 'Weekday'], as_index=False)['y'].sum()

# Filter out rows with zero revenue
df_hierarchy = df_hierarchy[df_hierarchy['y'] != 0]

# Calculate average yearly revenue
avg_yearly_revenue = df_hierarchy.groupby('Year')['y'].mean().reset_index()
avg_yearly_revenue.rename(columns={'y': 'Average Revenue'}, inplace=True)

# Create the Sunburst chart
fig = px.sunburst(df_hierarchy, path=['Year', 'Season', 'Month', 'Week', 'Weekday'], values='y', color='y')
fig.update_traces(sort=False, customdata=df_hierarchy[['Year','Season', 'Month', 'Week']], selector=dict(type='sunburst'))

fig.show()

# Create the Dash app
app = dash.Dash(__name__)

bar_fig = go.Figure()
bar_chart = dcc.Graph(id='bar-chart', figure=bar_fig)

@app.callback(
    dash.dependencies.Output('bar-chart', 'figure'),
    dash.dependencies.Input('sunburst-chart', 'clickData')
)
def update_bar_chart(clickData):
    if clickData and 'label' in clickData['points'][0]:
        selected_label = clickData['points'][0]['label']
        if selected_label in df_hierarchy['Year'].values:
            selected_data = df_hierarchy[df_hierarchy['Year'] == selected_label]
            bar_fig = go.Figure(data=go.Bar(x=selected_data['Season'], y=selected_data['Season'].mean()))
            bar_fig.update_layout(title=f"Average Revenues for {selected_label}")
            return bar_fig
        elif selected_label in df_hierarchy['Season'].values:
            selected_data = df_hierarchy[df_hierarchy['Season'] == selected_label]
            bar_fig = go.Figure(data=go.Bar(x=selected_data['Month'], y=selected_data['Season'].mean()))
            bar_fig.update_layout(title=f"Average Revenues for {selected_label}")
            return bar_fig
    return go.Figure()

app.layout = html.Div([
    html.Div([
        dcc.Graph(
            id='sunburst-chart',
            figure=fig
        )
    ], style={'width': '50%', 'display': 'inline-block'}),
    html.Div([
        bar_chart
    ], style={'width': '50%', 'display': 'inline-block'}),
    html.Div(id='selected-year-output', style={'margin-top': '20px'})
])

# Run the Dash app
if __name__ == '__main__':
    app.run_server(debug=True)
