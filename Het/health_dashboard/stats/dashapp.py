import dash
from dash import dcc, html
import plotly.express as px
import pandas as pd
from dash.dependencies import Input, Output
from flask import request
import os
from urllib.parse import parse_qs

def create_dash_app(file_path=None):
    """
    Creates and returns a Dash app.
    """
    # Initialize Dash app
    app = dash.Dash(__name__, routes_pathname_prefix="/dash_app/")

    def load_data():
        """Utility function to load CSV data from the given file path."""
        if file_path and os.path.exists(file_path):
            return pd.read_csv(file_path)
        return pd.DataFrame()  # Return empty DataFrame if the file does not exist

    app.layout = html.Div([
        html.H1("CSV Data Plot"),
        dcc.Location(id="url", refresh=False),  # For capturing query parameters
        dcc.Graph(id="graph"),
        html.Div(id="error-message", style={"color": "red"})
    ])

    @app.callback(
        [Output("graph", "figure"),
         Output("error-message", "children")],
        [Input("url", "search")]  # Capture query parameters
    )
    def update_graph(search):
        # Parse query parameters
        params = parse_qs(search[1:] if search else "")  # Remove "?" at the start
        x_column = params.get('x_column', [None])[0]
        y_column = params.get('y_column', [None])[0]

        # Load data
        df = load_data()
        if df.empty:
            return {}, "No data loaded. Please upload a valid CSV file."

        if x_column not in df.columns or y_column not in df.columns:
            return {}, f"Invalid column names: {x_column} or {y_column} not found in CSV."

        # Create the plot
        fig = px.scatter(df, x=x_column, y=y_column, title=f"Graph of {x_column} vs {y_column}")
        return fig, ""

    return app