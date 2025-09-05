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
#Tech Stack
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
#Local Setup and Installation
To run this project on your local machine, please follow these steps.
#**1. Clone the Repository**
Clone this repository to your local machine.
git clone <your-repository-url>
cd <your-project-folder>

#**2. Create and Activate Virtual Environment**
It is highly recommended to use a virtual environment.
#** Create the virtual environment**
python -m venv venv

# Activate it (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Activate it (macOS/Linux)
source venv/bin/activate

**3. Install Dependencies**
Install all the required Python libraries from the requirements.txt file.
pip install -r requirements.txt

**4. Set Environment Variables**
The application requires the ClipDrop API key to be set as an environment variable.
# In Windows PowerShell
$env:CLIPDROP_API_KEY="your_clipdrop_api_key_here"

**5. Initialize the Database**
Before running the app for the first time, you need to create the database schema.
python init_db.py

This will create a mood_app.db file in the /data directory with all the necessary tables.
#6. Run the Application
You can now start the Flask development server.
python run.py

The application will be available at http://127.0.0.1:5000.
Deployment
This application is configured for deployment on a service like Render. The key files for deployment are:
•	requirements.txt: Defines the Python dependencies.
•	run.py: The entry point for the application.
The recommended start command for a production environment is: gunicorn run:app

