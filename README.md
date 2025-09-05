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
