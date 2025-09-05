<<<<<<< HEAD
AI Art Mood App
A Flask web application built for a university dissertation project. This application generates AI-powered art based on user-selected emotions and collects feedback for analysis. It features a comprehensive admin panel for data monitoring and application management.

Live Application
The application is deployed on Render and can be accessed here: [Your Live Render App URL] (Note: You will need to replace this with the actual URL from your Render dashboard.)

Features
User-Facing Art Generation: Users can select an emotion, provide a text prompt, and receive a unique, AI-generated image that reflects their mood.

Admin Panel: A secure, multi-page dashboard for administrators to:

View key statistics (total users, images generated, etc.).

Review and filter all user feedback and logs.

Visualize data with interactive charts.

Manage application settings, including API keys.

View detailed activity for individual users.

Data Export: Admins can export feedback data in CSV, Excel, or PDF formats for analysis.

Secure User System: The app uses pre-defined user accounts for anonymous participation and a separate, secure login for the administrator.

Technology Stack
Backend: Python 3, Flask

Database: PostgreSQL (hosted on Supabase)

Image Generation: ClipDrop API (by Stability AI)

Frontend: HTML5, CSS3, JavaScript

Data Visualization: Chart.js

Deployment: Render, Gunicorn

Local Development Setup
To run this project on your local machine, follow these steps.

1. Prerequisites
Python 3.10+

A free Supabase account for the PostgreSQL database.

A free ClipDrop account for the image generation API key.

2. Clone the Repository
git clone [https://github.com/scarcelsland/ai-mood-art-app.git](https://github.com/scarcelsland/ai-mood-art-app.git)
cd ai-mood-art-app

3. Create and Activate Virtual Environment
Windows:

python -m venv venv
.\venv\Scripts\activate

macOS / Linux:

python3 -m venv venv
source venv/bin/activate

4. Install Dependencies
Install all the required Python libraries from the requirements.txt file.

pip install -r requirements.txt

5. Set Up the Database
This project requires a PostgreSQL database.

Log in to your Supabase account and create a new project.

In your project's dashboard, navigate to the SQL Editor.

Create a new query and paste the following SQL commands to create the necessary tables. Click RUN.

-- Create the 'feedback' table
CREATE TABLE IF NOT EXISTS feedback (
    id SERIAL PRIMARY KEY,
    username TEXT,
    emotion TEXT,
    prompt TEXT,
    image_url TEXT,
    advice TEXT,
    predicted_correct INTEGER,
    advice_ok INTEGER,
    comments TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create the 'logs' table
CREATE TABLE IF NOT EXISTS logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    event TEXT,
    "user" TEXT,
    source TEXT,
    data JSONB
);

-- Create the 'settings' table
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY NOT NULL,
    value TEXT
);

6. Set Environment Variables
The application requires secret keys to be set as environment variables.

In the root directory of your project, create a new file named .env.

Copy the contents of .env.sample into your new .env file.

Fill in the values for the following variables:

SECRET_KEY: A long, random string for securing sessions.

CLIPDROP_API_KEY: Your API key from your ClipDrop account.

DATABASE_URL: Your database connection string (URI) from your Supabase project settings.

7. Run the Application
You can now start the Flask development server.

python run.py

The application will be available at http://127.0.0.1:5000.

Project Structure
/
├── app/                  # Core application source code
│   ├── models/           # User authentication logic
│   ├── static/           # CSS stylesheets
│   └── templates/        # HTML templates
├── data/                 # (For local SQLite, now unused)
├── .gitignore            # Files to be ignored by Git
├── README.md             # This file
├── requirements.txt      # Python dependencies
└── run.py                # Application entry point
=======
# AI Art Mood App

This web application is a full-stack project developed for a university dissertation. It allows users to generate AI-powered art based on their current mood, view tailored advice, and provide feedback on the results. The application includes a comprehensive admin panel for monitoring activity, viewing feedback, and managing application settings.

# Features
# User Features

- **Mood-Based Art Generation:** 
Select an emotion and provide an optional text prompt to generate a unique piece of AI art.

- **Contextual Advice:** 
Receive helpful advice tailored to the selected emotion.

- **Anonymous Feedback:** 
Users can provide feedback on whether the generated image matched their mood and if the advice was helpful.

- **Ethical Consent:** 
A clear consent form is presented to all participants before they can use the application, ensuring compliance with research ethics.

# Admin Features

- **Interactive Dashboard:** 
An at-a-glance view of key metrics like total users, images generated, feedback submissions, and active sessions.

- **User Management:** 
View a list of all users and drill down into a detailed view of a specific user's activity, including all their feedback and log entries.

- **User Data Deletion:** 
Anonymously delete all data associated with a user, including their feedback and logs.

- **Feedback Viewer:** 
A detailed table of all feedback submitted, with a modal to view full prompt and comment text. Includes data visualization charts for emotion distribution and feedback ratings.

- **Log Viewer:** 
A comprehensive log of all system events, with client-side generated charts for visual insights and the ability to download chart data.

- **Application Settings:** 
A secure page to manage the application's API keys.

# Tech Stack

- **Backend:** 
Python, Flask

- **Database:** 
SQLite

- **Frontend:** 
HTML, CSS, JavaScript

- **AI Image Generation:** 
ClipDrop API (Stable Diffusion)

- **Charting Library:** 
Chart.js

- **Deployment Server:** 
Gunicorn

# Local Setup and Installation

To run this project on your local machine, please follow these steps.

# 1. Clone the Repository

Clone this repository to your local machine.

_git clone <your-repository-url>_
_cd <your-project-folder>_

# 2. Create and Activate Virtual Environment

It is highly recommended to use a virtual environment.

_# Create the virtual environment_

_python -m venv venv_

_# Activate it (Windows PowerShell)_

_.\venv\Scripts\Activate.ps1_

_# Activate it (macOS/Linux)_

_source venv/bin/activate_

# 3. Install Dependencies

Install all the required Python libraries from the _requirements.txt_ file.

_pip install -r requirements.txt_

# 4. Set Environment Variables

The application requires the ClipDrop API key to be set as an environment variable.

_# In Windows PowerShell_

_$env:CLIPDROP_API_KEY="your_clipdrop_api_key_here"_

# 5. Initialize the Database

Before running the app for the first time, you need to create the database schema.

_python init_db.py_

This will create a _mood_app.db_ file in the _/data_ directory with all the necessary tables.

# 6. Run the Application

You can now start the Flask development server.

_python run.py_

The application will be available at _http://127.0.0.1:5000_.

# Deployment

This application is configured for deployment on a service like Render. The key files for deployment are:

- _requirements.txt:_ 

Defines the Python dependencies.

- _run.py:_

The entry point for the application.

The recommended start command for a production environment is: 

_gunicorn run:app_

>>>>>>> f4647915052fa6d15d51b6f9ac70774040319bb4
