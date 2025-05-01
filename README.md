# College Timetable Management System

A web application built with Python, Flask, and SQLite to manage college timetable data and automatically generate schedules for specific sections based on defined constraints.

## Features

*   **Web-Based UI:** Clean interface built with Flask and basic CSS for managing data and viewing timetables.
*   **Data Management:** Add, list, and delete Faculty, Subjects (with codes), Rooms, and Semester/Section/Subject/Faculty assignments.
*   **Targeted Timetable Generation:** Automatically generate a timetable for a specific selected Semester and Section using a backtracking algorithm.
*   **Constraint Checking:** The generator avoids conflicts (Faculty, Room, Section) within the same time slot by checking against previously generated entries for other sections *within the same shift* (Shift 1: Sem 5-10, 9am-1pm; Shift 2: Sem 1-4, 1pm-5pm).
*   **Faculty Load Constraint:** Enforces a maximum of 2 lectures per faculty per day *within their assigned shift* during generation.
*   **PDF Export:** Download generated timetables as formatted PDF documents.
*   **PDF Preview:** View generated PDFs directly within the web interface using an iframe.
*   **Generated Timetable List:** View a list of all semester/section combinations for which a timetable has been successfully generated.
*   **Admin Login:** Simple authentication (`admin`/`password`) protects data management and generation functions.
*   **Database Reset:** Option to reset the database to the initial sample data state.

## Prerequisites

*   Python 3.x
*   `pip` (Python package installer)
*   Ability to create Python virtual environments (`venv` module)

## Setup and Installation

1.  **Clone the Repository:**
    ```bash
    git clone <your-repository-url>
    cd timetablegenerationsystem
    ```
    *(Replace `<your-repository-url>` with the actual URL of your GitHub repository)*

2.  **Create and Activate Virtual Environment:**
    *   It's highly recommended to use a virtual environment.
    ```bash
    # Create the environment (e.g., named .venv)
    python -m venv .venv

    # Activate it:
    # On Linux/macOS:
    source .venv/bin/activate
    # On Windows (Command Prompt):
    # .venv\Scripts\activate.bat
    # On Windows (PowerShell):
    # .venv\Scripts\Activate.ps1
    ```
    *(You should see `(.venv)` at the beginning of your terminal prompt)*

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Initialize the Database:**
    *   This creates the `timetable_data.db` SQLite file with the necessary tables and populates it with sample data for all 10 semesters.
    ```bash
    python database_setup.py
    ```

## Running the Application

1.  **Ensure Virtual Environment is Active:** If not already active, run `source .venv/bin/activate` (or the Windows equivalent).
2.  **Start the Flask Development Server:**
    ```bash
    flask run
    ```
3.  **Access the Application:** Open your web browser and navigate to `http://127.0.0.1:5000` (or the URL provided in the terminal output).

## Usage

1.  **Login:** You will be redirected to the login page. Use the default credentials:
    *   Username: `admin`
    *   Password: `password`
2.  **Main Page (Generate/View):** After login, you'll see the main dashboard.
    *   Select a **Semester** and **Section**.
    *   Click the **"Generate/View Timetable"** button.
    *   The system will attempt to generate the timetable for that specific section, checking for conflicts with other sections in the same shift. Monitor the terminal where `flask run` is active for progress messages (`Attempting generation...`, `Solution found!`, `Failed...`, etc.).
    *   If successful, the page will reload, displaying the generated timetable grid. If it fails, an error message will be shown.
3.  **View Generated List:** Click the "View Generated" link in the navigation bar to see a list of all semester/section combinations that have a timetable saved in the database. You can click "View" or "Download" from this list.
4.  **Manage Data:** (Requires Login) Click the "Manage Data" link in the navigation bar. Here you can:
    *   Add/View Faculty.
    *   Add/View Subjects (including Subject Codes).
    *   Add/View Rooms.
    *   Add/View/Delete Semester/Section/Subject/Faculty assignments (this is the input data for the generator).
    *   Reset the entire database back to the initial sample data (use with caution!).
5.  **Download PDF:** On the timetable view page (after generating or clicking "View" from the list), click the "Download PDF" button.
6.  **Logout:** Click the "Logout" link in the navigation bar.

## Configuration (Optional)

For better security, especially if deploying, you can set the admin credentials and Flask secret key using environment variables *before* running `flask run`:

*   `ADMIN_USERNAME`: Set the desired admin username.
*   `ADMIN_PASSWORD`: Set the desired admin password.
*   `FLASK_SECRET_KEY`: Set a long, random string for session security.

**Example (Linux/macOS):**
```bash
export ADMIN_USERNAME='myadmin'
export ADMIN_PASSWORD='mysecretpassword'
export FLASK_SECRET_KEY='a_very_long_random_secure_string'
source .venv/bin/activate
flask run
```

## Note on `Minor_Project` Folder

This repository may contain a subfolder named `Minor_Project`. This folder contains a separate PHP project that was used for analysis and reference during the development of this Python/Flask application. The PHP project itself is **not** part of the running Python application and is not required for its operation.
