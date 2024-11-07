import dash
from dash import dcc, html, Input, Output, State, ctx
from dash import dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
import pathlib
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

# initialize app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# load and prepare data
curr_dir_path = pathlib.Path(__file__).resolve().parent
locations_df: pd.DataFrame = pd.read_pickle(curr_dir_path / "location.pkl")

# force the index to be a column named 'barcode'
locations_df.reset_index(inplace=True)
locations_df.rename(columns={'index': 'barcode'}, inplace=True)
locations_df = locations_df[['barcode', 'x', 'y']]

# flip the y-axis to match the plotly coordinate system
locations_df['temp'] = locations_df['x']
locations_df['x'] = locations_df['y']
locations_df['y'] = -locations_df['temp']
locations_df.drop(columns=['temp'], inplace=True)
df = pd.DataFrame(locations_df)
df['label'] = 0

x_min, x_max = df['x'].min(), df['x'].max()
y_min, y_max = df['y'].min(), df['y'].max()
data_width = x_max - x_min
data_height = y_max - y_min

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            dcc.Graph(
                id='scatter-plot',
                config={
                    'modeBarButtonsToAdd': ['lasso2d'],
                    'displayModeBar': True,
                    'scrollZoom': True
                },
                style={'height': '800px'},
                figure=go.Figure(
                    data=[
                        go.Scatter(
                            x=df['x'],
                            y=df['y'],
                            mode='markers',
                            marker=dict(
                                size=5,
                                color='lightblue',
                                opacity=1
                            ),
                            name='Unlabeled'
                        )
                    ],
                    layout=dict(
                        yaxis=dict(scaleanchor="x", scaleratio=1.6),
                        xaxis_title='X',
                        yaxis_title='Y',
                        dragmode='lasso',
                        uirevision=True
                    )
                )
            ),
            dbc.Card([
                dbc.CardHeader("Label Management", className="p-2"),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Label("Label Name", className="small"),
                            dbc.Input(
                                id='new-label-name',
                                type='text',
                                placeholder='Enter label name',
                                size="sm"
                            ),
                        ], width=6),
                        dbc.Col([
                            html.Label("Label Color", className="small"),
                            dcc.Dropdown(
                                id='new-label-color',
                                options=[
                                    {'label': color, 'value': color}
                                    for color in ['red', 'green', 'blue', 'purple', 'orange', 
                                                'yellow', 'pink', 'cyan', 'brown', 'gray']
                                ],
                                placeholder='Select color',
                                className="small"
                            ),
                        ], width=6),
                    ]),
                    dbc.Button(
                        "Add Label",
                        id='add-label-button',
                        color='primary',
                        className='mt-2 btn-sm'
                    ),
                    html.Div(id='label-management-output', className="small mt-2"),
                    html.Hr(className="my-2"),
                    dcc.RadioItems(
                        id='label-selector',
                        options=label_manager.get_label_options(),
                        value=0,
                        inline=True,
                        className='mt-2'
                    )
                ], className="p-2")
            ], className="mb-3"),
            dbc.Card([
                dbc.CardHeader("Point Controls", className="p-2"),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Label("Point Size", className="mb-0 small"),
                            dcc.Slider(
                                id='point-size-slider',
                                min=1,
                                max=20,
                                value=5,
                                step=0.5,
                                marks=None,
                                tooltip={"placement": "bottom", "always_visible": True},
                                className="mb-2"
                            ),
                        ], width=6),
                        dbc.Col([
                            html.Label("Point Opacity", className="mb-0 small"),
                            dcc.Slider(
                                id='point-opacity-slider',
                                min=0,
                                max=1,
                                value=1,
                                step=0.05,
                                marks=None,
                                tooltip={"placement": "bottom", "always_visible": True},
                                className="mb-2"
                            ),
                        ], width=6),
                    ]),
                ], className="p-2")
            ], className="mb-3"),
            dbc.Card([
                dbc.CardHeader("Background Image", className="p-2"),
                dbc.CardBody([
                    dcc.Upload(
                        id='upload-image',
                        children=html.Div([
                            'Drag and Drop or ',
                            html.A('Select Background Image')
                        ]),
                        style={
                            'width': '100%',
                            'height': '40px',
                            'lineHeight': '40px',
                            'borderWidth': '1px',
                            'borderStyle': 'dashed',
                            'borderRadius': '5px',
                            'textAlign': 'center',
                            'marginBottom': '10px'
                        }
                    ),
                    dbc.Row([
                        dbc.Col([
                            html.Label("Position X", className="mb-0 small"),
                            dcc.Slider(
                                id='image-x-slider',
                                min=x_min - data_width,
                                max=x_max + data_width,
                                value=x_min,
                                marks=None,
                                tooltip={"placement": "bottom", "always_visible": True},
                                className="mb-2"
                            ),
                        ], width=6),
                        dbc.Col([
                            html.Label("Position Y", className="mb-0 small"),
                            dcc.Slider(
                                id='image-y-slider',
                                min=y_min - data_height,
                                max=y_max + data_height,
                                value=y_max,
                                marks=None,
                                tooltip={"placement": "bottom", "always_visible": True},
                                className="mb-2"
                            ),
                        ], width=6),
                    ]),
                    dbc.Row([
                        dbc.Col([
                            html.Label("Width", className="mb-0 small"),
                            dcc.Slider(
                                id='image-width-slider',
                                min=data_width * 0.1,
                                max=data_width * 3,
                                value=data_width,
                                marks=None,
                                tooltip={"placement": "bottom", "always_visible": True},
                                className="mb-2"
                            ),
                        ], width=4),
                        dbc.Col([
                            html.Label("Height", className="mb-0 small"),
                            dcc.Slider(
                                id='image-height-slider',
                                min=data_height * 0.1,
                                max=data_height * 3,
                                value=data_height,
                                marks=None,
                                tooltip={"placement": "bottom", "always_visible": True},
                                className="mb-2"
                            ),
                        ], width=4),
                        dbc.Col([
                            html.Label("Opacity", className="mb-0 small"),
                            dcc.Slider(
                                id='image-opacity-slider',
                                min=0,
                                max=1,
                                value=0.5,
                                step=0.1,
                                marks=None,
                                tooltip={"placement": "bottom", "always_visible": True},
                                className="mb-2"
                            ),
                        ], width=4),
                    ]),
                ], className="p-2")
            ], className="mb-3"),
            dcc.Store(id='selected-points-store', data=[]),
            html.Div(id='label-output'),
        ], width=7),
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
                },
                style_table={'height': '800px', 'overflowY': 'auto'}
            ),
            html.Br(),
            dbc.Button(
                'Download Labels',
                id='download-button',
                color='success',
                className="btn-sm"
            ),
            dcc.Download(id='download-mask')
        ], width=5),
    ])
], fluid=True, style={'maxWidth': '2000px'})

@app.callback(
    Output('scatter-plot', 'figure'),
    Output('table', 'data'),
    Output('table', 'dropdown'),
    Output('label-management-output', 'children'),
    Output('label-selector', 'options'),
    Input('selected-points-store', 'data'),
    Input('scatter-plot', 'clickData'),
    Input('label-selector', 'value'),
    Input('add-label-button', 'n_clicks'),
    Input('upload-image', 'contents'),
    Input('image-x-slider', 'value'),
    Input('image-y-slider', 'value'),
    Input('image-width-slider', 'value'),
    Input('image-height-slider', 'value'),
    Input('image-opacity-slider', 'value'),
    Input('point-size-slider', 'value'),  # New input
    Input('point-opacity-slider', 'value'),  # New input
    Input('table', 'data_timestamp'),
    State('new-label-name', 'value'),
    State('new-label-color', 'value'),
    State('table', 'data'),
    prevent_initial_call=True
)
def update_data(selected_points, click_data, selected_label, add_label_clicks, 
                image_contents, img_x, img_y, img_width, img_height, img_opacity,
                point_size, point_opacity, table_timestamp, 
                new_label_name, new_label_color, rows):
    triggered_id = ctx.triggered_id if ctx.triggered_id else 'No clicks yet'
    df_updated = pd.DataFrame(rows)
    management_output = None
    
    if triggered_id == 'add-label-button' and new_label_name and new_label_color:
        label_id = label_manager.add_label(new_label_name, new_label_color)
        management_output = f"Added new label: {new_label_name} (ID: {label_id})"

    if selected_points and triggered_id == 'selected-points-store':
        for point in selected_points:
            mask = (df_updated['x'] == point['x']) & (df_updated['y'] == point['y'])
            df_updated.loc[mask, 'label'] = selected_label
    elif click_data and triggered_id == 'scatter-plot':
        click_x = click_data['points'][0]['x']
        click_y = click_data['points'][0]['y']
        mask = (df_updated['x'] == click_x) & (df_updated['y'] == click_y)
        df_updated.loc[mask, 'label'] = selected_label

    dropdown_options = {'label': {'options': label_manager.get_label_options()}}
    
    fig = go.Figure()

    if image_contents:
        img = parse_image_contents(image_contents)
        if img:
            fig.add_layout_image(
                dict(
                    source=image_contents,
                    xref="x",
                    yref="y",
                    x=img_x,
                    y=img_y,
                    sizex=img_width,
                    sizey=img_height,
                    sizing="stretch",
                    opacity=img_opacity,
                    layer="below"
                )
            )

    for label_id, label_info in label_manager.labels.items():
        mask = df_updated['label'] == label_id
        fig.add_trace(go.Scatter(
            x=df_updated[mask]['x'],
            y=df_updated[mask]['y'],
            mode='markers',
            name=f"{label_info['name']} ({label_id})",
            marker=dict(
                size=point_size,  # Use the slider value
                color=label_info['color'],
                opacity=point_opacity  # Use the slider value
            )
        ))
    
    fig.update_layout(
        yaxis=dict(scaleanchor="x", scaleratio=1.6),
        xaxis_title='X',
        yaxis_title='Y',
        dragmode='lasso',
        uirevision=True
    )
    
    return fig, df_updated.to_dict('records'), dropdown_options, management_output, label_manager.get_label_options()

def parse_image_contents(contents):
    if contents is None:
        return None
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    img = Image.open(io.BytesIO(decoded))
    return img

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