import os
import pandas as pd
from django.shortcuts import render
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponseRedirect
from django.urls import reverse
from .dash_app import create_dash_app  # Import the Dash app creation function
import os

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

def dash_app_view(request):
    """
    Renders the Dash app with selected columns from the CSV.
    """
    # Retrieve the file path from the session or URL parameters
    file_path = request.session.get('csv_file_path', None)

    # If file path isn't available, redirect back to the upload page
    if not file_path:
        return HttpResponseRedirect(reverse('home'))

    # Get selected x_column and y_column from the request parameters
    x_column = request.GET.get('x_column')
    y_column = request.GET.get('y_column')

    # If no columns are selected, redirect to the CSV upload page to select columns
    if not x_column or not y_column:
        return HttpResponseRedirect(reverse('home'))

    # Create the Dash app
    app = create_dash_app(file_path=file_path, x_column=x_column, y_column=y_column)  # Pass the file path and columns to Dash app

    # Return the URL of the Dash app in the context, but typically it's hosted on a different port (e.g., 8050)
    return render(request, 'stats/dash_template.html', {
        'dash_app_url': 'http://localhost:8050/dash_app/',  # Point to the Dash app URL (running on port 8050)
    })