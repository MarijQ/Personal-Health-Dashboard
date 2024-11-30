import os
import pandas as pd
from django.shortcuts import render
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from .dashapp import create_dash_app  # Import the Dash app creation function

def upload_csv(request):
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
    return render(request, "upload.html", {
        'column_names': column_names,
        'dash_app_url': "/dash_app/",  # Corrected dash app URL
    })

def dash_app_view(request):
    """
    Renders the Dash app with selected columns from the CSV.
    """
    # Retrieve the file path from the session or URL parameters
    file_path = request.session.get('csv_file_path', None)

    # If file path isn't available, redirect back to the upload page
    if not file_path:
        return HttpResponseRedirect(reverse('upload_csv'))

    # Create the Flask app
    app = create_dash_app(file_path=file_path)  # Pass the file path to the Dash app

    # Render Dash app inside the Django view
    return HttpResponse(app.index(), content_type="text/html")
