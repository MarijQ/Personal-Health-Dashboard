# Use the official Python image from Docker Hub
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Install dependencies and wget/curl
RUN apt-get update && apt-get install -y wget curl

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy the rest of the application code
COPY . /app/

# Ensure the static directories exist
RUN mkdir -p /app/static/dash/component/plotly/package_data/

# Check if the directories are created
RUN ls -l /app/static/dash/component/plotly/

# Download the plotly.min.js file into the correct directory
RUN curl -v -L https://cdn.plot.ly/plotly-latest.min.js -o /app/static/dash/component/plotly/package_data/plotly.min.js

# Verify if the file has been downloaded
RUN ls -l /app/static/dash/component/plotly/package_data/

# Expose necessary ports
EXPOSE 8000 8050

# Collect static files (so they can be served by Django)
RUN python manage.py collectstatic --noinput

# Command to run the application
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]


