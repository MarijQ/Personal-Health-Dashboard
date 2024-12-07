import dash
from dash import dcc, html
import plotly.express as px
import pandas as pd
from dash.dependencies import Input, Output
from dash import dash_table
import os
from django_plotly_dash import DjangoDash

def create_dash_app(file_path=None, x_column=None, y_column=None):
    """
    Creates and returns a Dash app that integrates with Django.
    """
    # Initialize Dash app
    app = DjangoDash("CSVPlotApp", routes_pathname_prefix="/dash_app/")

    def load_data():
        """Utility function to load CSV data from the given file path."""
        if file_path and os.path.exists(file_path):
            return pd.read_csv(file_path)
        return pd.DataFrame()  # Return empty DataFrame if the file does not exist

    # Load the data once and extract column names
    df = load_data()
    column_names = df.columns.tolist() if not df.empty else []

    app.layout = html.Div([
        html.H1("CSV Data Plot"),

        # Dropdown for X and Y selection based on column names
        html.Div([
            html.Label("Select X-axis Column:"),
            dcc.Dropdown(
                id="x-column-dropdown",
                options=[{'label': col, 'value': col} for col in column_names],
                value=x_column if x_column else (column_names[0] if column_names else None)  # Default if no x_column provided
            ),
            html.Label("Select Y-axis Column:"),
            dcc.Dropdown(
                id="y-column-dropdown",
                options=[{'label': col, 'value': col} for col in column_names],
                value=y_column if y_column else (column_names[1] if len(column_names) > 1 else None)  # Default if no y_column provided
            ),
        ]),

        # Graph that will display the plot
        dcc.Graph(id="graph"),
        html.Div(id="error-message", style={"color": "red"})
    ])

    @app.callback(
        [Output("graph", "figure"),
         Output("error-message", "children")],
        [Input("x-column-dropdown", "value"),
         Input("y-column-dropdown", "value")]
    )
    def update_graph(x_column, y_column):
        # Load data
        df = load_data()
        if df.empty:
            return {}, "No data loaded. Please upload a valid CSV file."

        # If no columns are selected, display a default plot
        if not x_column or not y_column:
            return {}, "Please select both X and Y axis columns."

        if x_column not in df.columns or y_column not in df.columns:
            return {}, f"Invalid column names: {x_column} or {y_column} not found in CSV."

        # Create the plot
        fig = px.scatter(df, x=x_column, y=y_column, title=f"Graph of {x_column} vs {y_column}")
        return fig, ""

    # Ensure Dash app is bound to all network interfaces and on port 8050
    app.run_server(debug=True, host='0.0.0.0', port=8050)

    return app