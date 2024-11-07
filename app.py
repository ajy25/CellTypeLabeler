import dash
from dash import dcc, html, Input, Output, State, ctx
from dash import dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pathlib
import numpy as np
from PIL import Image
import base64
import io

class LabelManager:
    def __init__(self):
        self.labels = {0: {'name': 'Unlabeled', 'color': 'lightblue'}}
        self.next_id = 1
    
    def add_label(self, name, color):
        self.labels[self.next_id] = {'name': name, 'color': color}
        self.next_id += 1
        return self.next_id - 1
    
    def get_color_map(self):
        return {k: v['color'] for k, v in self.labels.items()}
    
    def get_label_options(self):
        return [{'label': f"{v['name']} ({k})", 'value': k} for k, v in self.labels.items()]

label_manager = LabelManager()

# Initialize app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Load and prepare data
curr_dir_path = pathlib.Path(__file__).resolve().parent
locations_df: pd.DataFrame = pd.read_pickle(curr_dir_path / "location.pkl")

# force the index to be a column named 'barcode'
locations_df.reset_index(inplace=True)
locations_df.rename(columns={'index': 'barcode'}, inplace=True)
locations_df = locations_df[['barcode', 'x', 'y']]
locations_df = locations_df[['x', 'y']]
locations_df['temp'] = locations_df['x']
locations_df['x'] = locations_df['y']
locations_df['y'] = -locations_df['temp']
locations_df.drop(columns=['temp'], inplace=True)
df = pd.DataFrame(locations_df)
df['label'] = 0

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            # Image upload
            dcc.Upload(
                id='upload-image',
                children=html.Div([
                    'Drag and Drop or ',
                    html.A('Select Background Image')
                ]),
                style={
                    'width': '100%',
                    'height': '60px',
                    'lineHeight': '60px',
                    'borderWidth': '1px',
                    'borderStyle': 'dashed',
                    'borderRadius': '5px',
                    'textAlign': 'center',
                    'margin': '10px'
                }
            ),
            # Main plot
            dcc.Graph(
                id='scatter-plot',
                config={
                    'modeBarButtonsToAdd': ['lasso2d'],
                    'displayModeBar': True,
                    'scrollZoom': True
                }
            ),
            # Store for selected points
            dcc.Store(id='selected-points-store', data=[]),
            html.Div(id='label-output'),
            
            # Label management
            dbc.Card([
                dbc.CardHeader("Label Management"),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Label("Label Name"),
                            dbc.Input(id='new-label-name', type='text', placeholder='Enter label name'),
                        ], width=6),
                        dbc.Col([
                            html.Label("Label Color"),
                            dcc.Dropdown(
                                id='new-label-color',
                                options=[
                                    {'label': color, 'value': color}
                                    for color in ['red', 'green', 'blue', 'purple', 'orange', 
                                                'yellow', 'pink', 'cyan', 'brown', 'gray']
                                ],
                                placeholder='Select color'
                            ),
                        ], width=6),
                    ]),
                    dbc.Button("Add Label", id='add-label-button', color='primary', className='mt-2'),
                    html.Div(id='label-management-output'),
                    html.Hr(),
                    dcc.RadioItems(
                        id='label-selector',
                        options=label_manager.get_label_options(),
                        value=0,
                        inline=True,
                        className='mt-2'
                    )
                ])
            ], className='mt-3'),
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
                        'options': label_manager.get_label_options()
                    }
                }
            ),
            html.Br(),
            dbc.Button('Download Labels', id='download-button', color='success'),
            dcc.Download(id='download-mask')
        ], width=6)
    ])
], fluid=True)

def parse_image_contents(contents):
    if contents is None:
        return None
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    img = Image.open(io.BytesIO(decoded))
    return img

# Separate callback for handling selections
@app.callback(
    Output('selected-points-store', 'data'),
    Input('scatter-plot', 'selectedData'),
    prevent_initial_call=True
)
def store_selected_points(selectedData):
    if selectedData:
        return selectedData['points']
    return []

@app.callback(
    Output('scatter-plot', 'figure'),
    Output('table', 'data'),
    Output('label-management-output', 'children'),
    Output('label-selector', 'options'),
    Input('selected-points-store', 'data'),
    Input('scatter-plot', 'clickData'),
    Input('label-selector', 'value'),
    Input('add-label-button', 'n_clicks'),
    Input('upload-image', 'contents'),
    State('new-label-name', 'value'),
    State('new-label-color', 'value'),
    State('table', 'data'),
    prevent_initial_call=True
)
def update_data(selected_points, click_data, selected_label, add_label_clicks, 
                image_contents, new_label_name, new_label_color, rows):
    triggered_id = ctx.triggered_id if ctx.triggered_id else 'No clicks yet'
    df_updated = pd.DataFrame(rows)
    management_output = None
    
    if triggered_id == 'add-label-button' and new_label_name and new_label_color:
        label_id = label_manager.add_label(new_label_name, new_label_color)
        management_output = f"Added new label: {new_label_name} (ID: {label_id})"
    
    # Handle lasso selection
    if selected_points and triggered_id == 'selected-points-store':
        for point in selected_points:
            mask = (df_updated['x'] == point['x']) & (df_updated['y'] == point['y'])
            df_updated.loc[mask, 'label'] = selected_label
    
    # Handle single click
    elif click_data and triggered_id == 'scatter-plot':
        click_x = click_data['points'][0]['x']
        click_y = click_data['points'][0]['y']
        mask = (df_updated['x'] == click_x) & (df_updated['y'] == click_y)
        df_updated.loc[mask, 'label'] = selected_label
    
    # Create figure
    fig = go.Figure()
    
    # Add background image if available
    if image_contents:
        img = parse_image_contents(image_contents)
        if img:
            fig.add_layout_image(
                dict(
                    source=image_contents,
                    xref="x",
                    yref="y",
                    x=df_updated['x'].min(),
                    y=df_updated['y'].max(),
                    sizex=df_updated['x'].max() - df_updated['x'].min(),
                    sizey=df_updated['y'].max() - df_updated['y'].min(),
                    sizing="stretch",
                    opacity=0.5,
                    layer="below"
                )
            )
    
    # Add scatter points
    for label_id, label_info in label_manager.labels.items():
        mask = df_updated['label'] == label_id
        fig.add_trace(go.Scatter(
            x=df_updated[mask]['x'],
            y=df_updated[mask]['y'],
            mode='markers',
            name=f"{label_info['name']} ({label_id})",
            marker=dict(size=5, color=label_info['color'])
        ))
    
    fig.update_layout(
        yaxis=dict(scaleanchor="x", scaleratio=1.6),
        xaxis_title='X',
        yaxis_title='Y',
        dragmode='lasso',
        uirevision=True  # This helps maintain zoom/pan state
    )
    
    return fig, df_updated.to_dict('records'), management_output, label_manager.get_label_options()

@app.callback(
    Output('download-mask', 'data'),
    Input('download-button', 'n_clicks'),
    State('table', 'data'),
    prevent_initial_call=True
)
def download_mask(n_clicks, rows):
    df_updated = pd.DataFrame(rows)
    return dcc.send_data_frame(df_updated.to_csv, 'labeled_data.csv')

if __name__ == '__main__':
    app.run_server(debug=True)