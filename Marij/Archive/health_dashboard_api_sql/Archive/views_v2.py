from django.http import HttpResponse
from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
import csv
import os
from django.conf import settings


def home(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']

        if not csv_file.name.endswith('.csv'):
            return render(request, 'stats/upload.html', {'error': 'This is not a CSV file.'})

        fs = FileSystemStorage()
        filename = fs.save(csv_file.name, csv_file)
        file_path = fs.path(filename)

        # Read and process the CSV file
        data = []
        with open(file_path, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                data.append(row)

        # Clean up and delete the file after processing
        fs.delete(filename)

        return render(request, 'stats/upload.html', {'data': data})

    return render(request, 'stats/upload.html')