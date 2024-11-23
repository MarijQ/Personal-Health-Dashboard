from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from django.conf import settings
import pandas as pd
import os

def home(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']

        if not csv_file.name.endswith('.csv'):
            return render(request, 'stats/upload.html', {'error': 'This is not a CSV file.'})

        fs = FileSystemStorage()
        filename = fs.save(csv_file.name, csv_file)
        file_path = fs.path(filename)

        # Read the CSV file into a Pandas DataFrame
        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            return render(request, 'stats/upload.html', {'error': f'Error reading CSV file: {e}'})

        fs.delete(filename)  # Clean up the uploaded file

        # Check if the DataFrame is empty
        if df.empty:
            return render(request, 'stats/upload.html', {'error': 'The CSV file is empty.'})

        # Calculate basic statistics for numerical columns
        numerical_data = df.describe().transpose()  # Get statistics for each column
        numerical_data.reset_index(inplace=True)  # Reset index to convert it to a DataFrame for rendering

        # Prepare the data for display
        formatted_data = []
        for index, row in numerical_data.iterrows():
            formatted_data.append({
                'header': row['index'],
                'mean': row['mean'],
                'median': df[row['index']].median(),  # Calculate median separately from describe
                'std_dev': row['std'],
            })

        return render(request, 'stats/upload.html', {'numerical_data': formatted_data})

    return render(request, 'stats/upload.html')
