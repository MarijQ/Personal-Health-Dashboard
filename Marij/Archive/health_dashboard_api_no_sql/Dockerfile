# Use the official Python image from Docker Hub
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file
COPY requirements.txt /app/

# Install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy the rest of the application code
COPY . /app/

# Expose port 8000 to the host
EXPOSE 8000

# Set an environment variable to allow OAuth over HTTP for local development
ENV OAUTHLIB_INSECURE_TRANSPORT 1

# Run the development server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]