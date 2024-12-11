import os
import pandas as pd
from django.shortcuts import render
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponseRedirect
from django.urls import reverse
from dash import dcc, html
import plotly.express as px
from django_plotly_dash import DjangoDash
from dash.dependencies import Input, Output
from urllib.parse import parse_qs


def create_dash_app(file_path, x_column=None, y_column=None):
    """
    Creates and returns a Dash app that integrates with Django.
    """
    app = DjangoDash("CSVPlotApp")  # Initialize the Dash app

    # Load the CSV data
    if file_path and os.path.exists(file_path):
        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            df = pd.DataFrame()
    else:
        df = pd.DataFrame()

    column_names = df.columns.tolist() if not df.empty else []
    if not column_names:
        print("WARNING: No columns found in the dataset.")

    # Define the layout
    app.layout = html.Div([
    html.H1("Dynamic Data Plot"),
    dcc.Location(id='url', refresh=False),
    dcc.Graph(id="graph"),
    html.Div(id="error-message", style={"color": "red", "margin-top": "10px"})
])

    # Define the callback for updating the graph
    @app.callback(
    [Output("graph", "figure"), Output("error-message", "children")],
    [Input("url", "search")]  # Get query parameters from the URL
)
    def update_graph(url):
        # Parse query parameters
        params = parse_qs(url[1:])  # Get query parameters from the URL search string
        selected_x_column = params.get("x_column", [None])[0]
        selected_y_column = params.get("y_column", [None])[0]

        # Handle empty DataFrame
        if df.empty:
            return {}, "No data available. Please upload a valid CSV file."

        # Handle missing or incomplete column selections
        if not selected_x_column or not selected_y_column:
            print("ERROR: Column selection is incomplete.")
            return {}, "Please select both X-axis and Y-axis columns."

        # Handle invalid column selections
        if selected_x_column not in df.columns or selected_y_column not in df.columns:
            print(f"ERROR: Invalid columns selected - X: {selected_x_column}, Y: {selected_y_column}")
            return {}, f"Invalid columns: {selected_x_column} or {selected_y_column} not found in the dataset."

        # Generate the plot
        try:
            fig = px.scatter(df, x=selected_x_column, y=selected_y_column, title="Scatter Plot")
            return fig, ""
        except Exception as e:
            return {}, f"Error generating plot: {e}"



# Handle the file upload
def home(request):
    """
    Handles the CSV upload and displays available columns for user selection.
    """
    column_names = []
    if request.method == 'POST' and request.FILES.get("csv_file"):
        # Save the uploaded CSV file
        csv_file = request.FILES['csv_file']
        fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'uploads'))
        filename = fs.save(csv_file.name, csv_file)
        filepath = fs.path(filename)

        # Read the CSV to get column names
        df = pd.read_csv(filepath)
        column_names = df.columns.tolist()

        # Store file path in session for later access by the Dash app
        request.session['csv_file_path'] = filepath

    # Render the upload page with the column names
    return render(request, "stats/upload.html", {
        'column_names': column_names,
    })


# Handle the Dash app view
def dash_app_view(request):
    """
    Renders the Dash app with selected columns from the CSV.
    """
    # Retrieve the uploaded CSV file path from the session
    file_path = request.session.get('csv_file_path', None)

    if not file_path:
        print("ERROR: File path not found in session. Redirecting to home.")
        return HttpResponseRedirect(reverse('home'))

    # Get selected x_column and y_column from the request parameters
    x_column = request.GET.get('x_column')
    y_column = request.GET.get('y_column')

    if not x_column or not y_column:
        print("ERROR: X or Y column not selected. Redirecting to home.")
        return HttpResponseRedirect(reverse('home'))
    
    # Read the CSV to get the column names dynamically
    df = pd.read_csv(file_path)
    column_names = df.columns.tolist()

    # Initialize the Dash app
    app = create_dash_app(file_path, x_column, y_column)  # Store the app instance

    # Render the template with the Dash app URL and pass the selected columns
    return render(request, "stats/upload.html", {
        'dash_app_url': f'/django_plotly_dash/app/CSVPlotApp/',  # Make sure URL doesn't include query params here
        'x_column': x_column,
        'y_column': y_column,
        'column_names': column_names,  # Update with actual column names from CSV
    })



