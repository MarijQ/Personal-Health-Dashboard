# Medical Personal Health Dashboard

**Authors:**   Marij Qureshi, Het Suhagiya, Georgios Gkakos

## Overview

This repository contains a **Medical Personal Health Dashboard** — a user-centric web app built with **Django** and integrated with **Plotly Dash** for real-time health data visualization. It aims to consolidate data from multiple health sources (Google Fit, manual inputs, and more) into a single, intuitive dashboard. Through the integrated **Generative AI** assistant, users can also query their data in natural language and receive insights or recommendations.

This project was created as part of a collaborative initiative to demonstrate a broad range of data science and software engineering skills, including:
- **Web App Development** (Django, Flask, Plotly Dash)
- **Containerization & Deployment** (Docker)
- **Data Visualization**
- **Generative AI / LLM Integration** (Langchain-like flow, OpenRouter, GPT-based models)
- **Data Structures & Algorithms** (Ingesting data efficiently, handling concurrency, etc.)

> **Health Dashboard Screenshots:** 
>![image](https://github.com/user-attachments/assets/6d91bd6c-8ed2-4734-9f30-a45f17bb5e09)
>![image](https://github.com/user-attachments/assets/c63e2d6b-900d-49b7-a38b-398c37e77f64)


## Table of Contents

1. [Features](#features)  
2. [Architecture](#architecture)  
3. [Directory Structure](#directory-structure)  
4. [Getting Started](#getting-started)  
5. [Running the Application](#running-the-application)  
6. [Usage Guide](#usage-guide)  
7. [Technologies Used](#technologies-used)  
8. [Future Improvements](#future-improvements)  
9. [Team and Contact](#team-and-contact)

---

## Features

1. **Centralized Health Data**  
   - Aggregate data from **Google Fit** and other sources via CSV uploads or manual input.
   - Visualize your steps, heart rate, calories, sleep patterns, and more in a single place.

2. **Interactive Dashboards**  
   - Real-time plots and charts built with **Plotly** and embedded via **Django Plotly Dash**.
   - Interactively explore or filter data, enabling quick insights into daily and long-term trends.

3. **AI Assistant**  
   - Powered by GPT-based models through **OpenRouter**.
   - Ask natural language questions about your stored health metrics, table structures, or summaries, and receive relevant insights.

4. **Modular & Containerized**  
   - Fully containerized with Docker, ensuring consistent behavior across development, staging, and production environments.
   - Potential for scaling with Docker Compose or Kubernetes.

5. **Manual Input & CSV Table Creation**  
   - Quickly add custom health metrics (e.g., weight, mood, custom biomarkers) with a single-line input format.
   - Upload any CSV to automatically create (or update) a table in the integrated SQLite database.

---

## Architecture

Below is the high-level data flow:

1. **Data Ingestion**  
   - Users either manually enter health data, upload CSV files, or connect their Google Fit account via OAuth.
2. **Django Backend**  
   - Handles ingestion, transforms data, and stores it in an SQLite database.
3. **Plotly Dash**  
   - Dynamically queries the database to create interactive charts.
4. **Generative AI / LLM**  
   - Upon a user query, the relevant database context is fetched and combined with the query prompt.  
   - Request is sent to the GPT-based model via **OpenRouter**, and the result is displayed back in the web app.
5. **Docker**  
   - All services (Django, Plotly Dash, any microservices) run within Docker containers for portability.

---

## Directory Structure

Below is a summarized tree of the repository’s essential files and folders.  

```
├── requirements.txt          # Python dependencies
├── runfile.txt               # Shell commands to build & run the Docker container
├── Dockerfile                # Docker build instructions
├── .dockerignore             # Files/folders ignored by Docker
├── manage.py                 # Django management script
├── db.sqlite3                # SQLite database (auto-generated)
├── media/
│   ├── ...                   # CSV data, user file uploads, logo, etc.
│   └── api_key.txt           # (Encrypted or hidden in production)
├── stats/
│   ├── tests.py
│   ├── views.py              # Main Django views (Google Fit OAuth, CSV upload, AI queries, etc.)
│   ├── urls.py
│   ├── dash_apps.py          # Plotly Dash application definitions
│   ├── models.py             # Django ORM models (UserSteps, UserHR, etc.)
│   ├── templates/
│   │   └── stats/
│   │       └── dashboard.html
│   └── migrations/
│       └── ...
├── Archive/                  # Legacy or experimental code
├── health_dashboard/         # Django project settings, URLs, WSGI, etc.
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── ...
└── README.md                 # This file!
```

---

## Getting Started

### Prerequisites

1. **Python 3.10+**  
2. **Docker** (recommended for container-based deployment)  
3. **(Optional) Virtual Environment**  
   - If running locally without Docker.

### Installation

1. **Clone this repo**:  
   ```bash
   git clone https://github.com/YourUserName/medical-personal-health-dashboard.git
   cd medical-personal-health-dashboard
   ```
2. **Install Python Dependencies (Local-Only Setup)**  
   ```bash
   pip install -r requirements.txt
   ```

---

## Running the Application

### Option A: Docker

1. **Build the Docker image**:  
   ```bash
   docker build -t health-dashboard .
   ```

2. **Run the container**:  
   ```bash
   docker run -p 8000:8000 -v "$(pwd):/app" health-dashboard # Linux, MacOS
   docker run -p 8000:8000 -v "'your_path_to_health_dashboard_project':/app" django-app # Windows
   
   ```
   - Access the app at `http://localhost:8000`.

3. **Docker Commands** (reference in `runfile.txt`):
   ```bash
   # Enter Docker container terminal
   docker exec -it <container_name_or_id> /bin/sh

   # Access SQLite shell from within container
   python manage.py dbshell
   ```

### Option B: Local Python Environment

1. **Run Migrations**:  
   ```bash
   python manage.py migrate
   ```
2. **Start Server**:  
   ```bash
   python manage.py runserver
   ```
   - Access at `http://127.0.0.1:8000`.

---

## Usage Guide

1. **Sync with Google Fit**  
   - Obtain a Google OAuth client JSON file and upload it via the “Sync” button.  
   - Grant permissions to read steps, HR, sleep data, etc.  
   - The application will fetch your data and create or update the corresponding tables.

2. **Add Manual Data**  
   - In the “Manual Data Entry” panel, use the format: `YYYY-MM-DD, metric, value`.  
   - Example: `2024-12-01, Weight, 70`

3. **CSV Upload**  
   - Upload a `.csv` file to automatically create or update a table in SQLite.  
   - Table name is derived from the file name (e.g., `sleep_data.csv` => table `sleep_data`).

4. **AI Assistant**  
   - Enter your **OpenRouter** API Key (or another GPT-based key if integrated).  
   - Ask questions like “What’s my average step count over the last 7 days?” or “Summarize my heart rate trends.”  
   - The system sends relevant DB context plus your prompt to the LLM, returning a natural language answer.

5. **Database Management**  
   - View all user-created tables and row counts in the “Database Settings” panel.  
   - Optionally drop all user-created tables (excluding core Django tables) to start fresh.

---

## Technologies Used

- **Django 5.1.2**  
- **Plotly Dash** + **django-plotly-dash**  
- **Docker**  
- **SQLite** (development DB)  
- **OpenRouter** or GPT-based API  
- **Google Fitness APIs**  

---

## Future Improvements

1. **Apple Health & Fitbit Integrations**  
   - Extend OAuth integrations to other popular health platforms.
2. **LangChain-Style Pipelines**  
   - Deeper context or chain-of-thought enhancements for advanced health insights.
3. **User Authentication**  
   - Add login/registration to store data per user in the DB more securely.
4. **Kubernetes Deployment**  
   - Option to orchestrate multiple containers & scale horizontally.
5. **Improve UI/Visualisations**
   - Prompt LLM to adjust the charts' features(eg. x/y axes, colours, ranges)
   - Add dynamically loaded plots for the major concerns on the users' health data

---

## Team and Contact

- **Marij**: MEng Aeronautical (Imperial), MSc Data Science (Brunel), ex-EY Parthenon
- **Het**: MSc Data Science (Brunel), BSc Information Technology 
- **George**: MSc Data Science (Brunel), BSc Economics (AUTH)

For questions, feel free to reach out via GitHub issues or email any of us.

---

## License
This project is licensed under the MIT License. See the [LICENSE](License) file for more details.

---

> **Thank you for checking out our Medical Personal Health Dashboard!** If you have any questions or suggestions, please open an issue or contact us directly.
