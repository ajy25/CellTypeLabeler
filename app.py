import dash
from dash import dcc, html, Input, Output, State
from dash import dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pathlib
import numpy as np

curr_dir_path = pathlib.Path(__file__).resolve().parent

locations_df: pd.DataFrame = pd.read_pickle(curr_dir_path / ".." / ".." / "splage_analysis_scripts" / "results" / "062724" / "Visium_FFPE_Human_Breast_Cancer" / "locations.pkl")
locations_df = locations_df.reset_index(drop=False)
locations_df = locations_df[['barcode', 'x', 'y']]
locations_df['temp'] = locations_df['x']
locations_df['x'] = locations_df['y']
locations_df['y'] = -locations_df['temp']
locations_df.drop(columns=['temp'], inplace=True)

# Sample DataFrame
data = locations_df
df = pd.DataFrame(data)
df['label'] = 0  # Initializing the label column

# Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

color_discrete_map = {
    0: 'lightblue',
    1: 'black',
    2: 'red',
    3: 'green',
    4: 'purple',
    5: 'orange'
}

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            dcc.Graph(id='scatter-plot'),
            html.Div(id='label-output'),
            dcc.RadioItems(
                id='label-selector',
                options=[{'label': str(i), 'value': i} for i in range(6)],
                value=0,
                inline=True
            ),
        ], width=6),
        dbc.Col([
            dash_table.DataTable(
                id='table',
                columns=[
                    {'name': 'barcode', 'id': 'barcode'},
                    {'name': 'x', 'id': 'x', 'type': 'numeric'},
                    {'name': 'y', 'id': 'y', 'type': 'numeric'},
                    {'name': 'label', 'id': 'label', 'presentation': 'dropdown'}
                ],
                data=df.to_dict('records'),
                editable=True,
                page_size=10,
                filter_action="native",
                dropdown={
                    'label': {
                        'options': [{'label': str(i), 'value': i} for i in range(6)]
                    }
                }
            ),
            html.Br(),
            html.Button('Download Mask', id='download-button', className='btn btn-primary'),
            dcc.Download(id='download-mask')
        ], width=6)
    ])
], fluid=True)

@app.callback(
    Output('scatter-plot', 'figure'),
    Output('table', 'data'),
    Input('table', 'data_timestamp'),
    Input('scatter-plot', 'clickData'),
    Input('label-selector', 'value'),
    State('table', 'data')
)
def update_labels(timestamp, click_data, selected_label, rows):
    df_updated = pd.DataFrame(rows)
    
    if click_data:
        click_x = click_data['points'][0]['x']
        click_y = click_data['points'][0]['y']
        
        # Find the exact point that was clicked
        clicked_point = df_updated[(df_updated['x'] == click_x) & (df_updated['y'] == click_y)]
        
        if not clicked_point.empty:
            # Update the label of the clicked point
            index = clicked_point.index[0]
            df_updated.loc[index, 'label'] = selected_label
    
    fig = px.scatter(
        df_updated, x='x', y='y', color=df_updated['label'].astype(str), 
        color_discrete_map=color_discrete_map,
    )
    fig.update_traces(marker=dict(size=5))
    fig.update_layout(
        yaxis=dict(scaleanchor="x", scaleratio=1.6),
        xaxis_title='X',
        yaxis_title='Y'
    )
    
    return fig, df_updated.to_dict('records')

@app.callback(
    Output('download-mask', 'data'),
    Input('download-button', 'n_clicks'),
    State('table', 'data'),
    prevent_initial_call=True
)
def download_mask(n_clicks, rows):
    df_updated = pd.DataFrame(rows)
    return dcc.send_data_frame(df_updated.to_csv, 'mask.csv')

if __name__ == '__main__':
    app.run_server(debug=True)