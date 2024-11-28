from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from django.conf import settings
import pandas as pd
import os

def home(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']

        # Validate the file extension
        if not csv_file.name.endswith('.csv'):
            return render(request, 'stats/upload.html', {'error': 'This is not a CSV file.'})

        fs = FileSystemStorage()
        filename = fs.save(csv_file.name, csv_file)
        file_path = fs.path(filename)

        # Read the file and handle errors
        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            return render(request, 'stats/upload.html', {'error': f'Error reading CSV file: {e}'})

        fs.delete(filename)  # Clean up the file on the server

        return render(request, 'stats/upload.html', {'data': df.head().to_html()})

    return render(request, 'stats/upload.html')
