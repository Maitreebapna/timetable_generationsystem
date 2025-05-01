import os
import sqlite3
import uuid
# Removed threading import
from functools import wraps
from flask import (Flask, render_template, request, redirect, url_for,
                   flash, send_file, abort, session, Response)
from collections import defaultdict

# Import functions from our modules
import db_utils
# Import the specific generator function we will create
from timetable_generator import generate_for_single_section # Assuming this function name
from pdf_generator import generate_timetable_pdf
from database_setup import setup_database # Import setup function

# --- Flask App Setup ---
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'a_default_secret_key_for_dev')
PDF_TEMP_DIR = os.path.join(app.root_path, 'temp_pdfs')
os.makedirs(PDF_TEMP_DIR, exist_ok=True)

# --- Simple Authentication ---
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'password')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != ADMIN_USERNAME or \
           request.form['password'] != ADMIN_PASSWORD:
            error = 'Invalid Credentials. Please try again.'
            flash(error, 'error')
        else:
            session['logged_in'] = True
            flash('You were successfully logged in.', 'success')
            next_url = request.args.get('next') or url_for('generate_view_timetable') # Redirect to main page
            return redirect(next_url)
    # If already logged in, redirect away from login page
    if 'logged_in' in session:
        return redirect(url_for('generate_view_timetable'))
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out.', 'info')
    return redirect(url_for('login')) # Redirect to login page after logout

# --- List Generated Timetables Route ---
@app.route('/generated')
@login_required
def list_generated_timetables():
    """Lists the semester/section combinations for which timetable data exists."""
    query = "SELECT DISTINCT semester, section FROM Timetable ORDER BY semester, section"
    generated_list = db_utils.fetch_data(query)
    return render_template('generated_list.html', generated_list=generated_list)

# --- Main Generate/View Route ---

@app.route('/', methods=['GET', 'POST'])
@login_required
def generate_view_timetable():
    """Handles timetable generation for a specific section and displays it."""
    selected_semester = None
    selected_section = None
    timetable_data_formatted = None
    days = []
    time_intervals = []
    generation_attempted = False # Flag to know if generation was tried

    if request.method == 'POST':
        try:
            selected_semester = int(request.form['semester'])
            selected_section = request.form['section']
            generation_attempted = True # Mark that we tried generating

            if selected_section not in ['A', 'B'] or not 1 <= selected_semester <= 10:
                raise ValueError("Invalid semester or section selected.")

            print(f"Attempting generation for Sem {selected_semester}, Sec {selected_section}...")
            # Call the new targeted generator function
            # This function should handle clearing old data for this section and saving new data
            generated_dict = generate_for_single_section(selected_semester, selected_section)

            if generated_dict:
                flash(f"Timetable generated successfully for Semester {selected_semester} Section {selected_section}.", 'success')
                # Fetch the newly saved data for display
                # (Query needs to join tables to get names and room numbers)
                query = """
                    SELECT
                        ts.day_of_week, ts.start_time, ts.end_time,
                        s.subject_name, f.faculty_name, r.room_number
                    FROM Timetable t
                    JOIN TimeSlots ts ON t.slot_id = ts.slot_id
                    JOIN Subjects s ON t.subject_id = s.subject_id
                    JOIN Faculty f ON t.faculty_id = f.faculty_id
                    JOIN Rooms r ON t.room_id = r.room_id
                    WHERE t.semester = ? AND t.section = ?
                    ORDER BY ts.day_of_week, ts.start_time
                """
                timetable_entries = db_utils.fetch_data(query, (selected_semester, selected_section))

                if timetable_entries:
                    # Format data for the template grid
                    days = sorted(list(set(entry['day_of_week'] for entry in timetable_entries)), key=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'].index)
                    time_intervals = sorted(list(set(f"{entry['start_time']}-{entry['end_time']}" for entry in timetable_entries)))
                    timetable_data_formatted = defaultdict(str)
                    for entry in timetable_entries:
                        interval = f"{entry['start_time']}-{entry['end_time']}"
                        timetable_data_formatted[(entry['day_of_week'], interval)] = f"{entry['subject_name']}<br>({entry['faculty_name']})<br>[{entry['room_number']}]"
                else:
                     flash("Successfully generated but failed to fetch data for display.", "error") # Should not happen if save worked

            else:
                flash(f"Failed to generate timetable for Semester {selected_semester} Section {selected_section}. No valid schedule found.", 'error')
                # timetable_data_formatted remains None

        except ValueError as e:
            flash(str(e), 'error')
        except Exception as e:
            flash(f"An unexpected error occurred during generation: {e}", 'error')
            print(f"Generation Error: {e}") # Log the full error

    # Render the template for both GET and POST requests
    # Pass necessary data for dropdowns and potentially the generated timetable
    return render_template('generate_view_timetable.html',
                           selected_semester=selected_semester,
                           selected_section=selected_section,
                           timetable_data=timetable_data_formatted, # Pass formatted data
                           days=days,
                           time_intervals=time_intervals,
                           generation_attempted=generation_attempted)


# --- Data Management Routes (Protected) ---

@app.route('/manage')
@login_required
def manage_data():
    """Displays the main data management page."""
    faculty = db_utils.list_faculty()
    subjects = db_utils.list_subjects()
    rooms = db_utils.list_rooms()
    assignments = db_utils.list_semester_subjects()
    return render_template('manage_data.html',
                           faculty=faculty,
                           subjects=subjects,
                           rooms=rooms,
                           assignments=assignments)

@app.route('/add_faculty', methods=['POST'])
@login_required
def add_faculty_route():
    name = request.form.get('faculty_name')
    if name:
        if db_utils.add_faculty(name): flash(f"Faculty '{name}' added.", 'success')
        else: flash(f"Error adding faculty '{name}'.", 'error')
    else: flash("Faculty name cannot be empty.", 'error')
    return redirect(url_for('manage_data'))

@app.route('/add_subject', methods=['POST'])
@login_required
def add_subject_route():
    code = request.form.get('subject_code')
    name = request.form.get('subject_name')
    if code and name:
         if db_utils.add_subject(code, name):
             flash(f"Subject '{code} - {name}' added.", 'success')
         else:
             flash(f"Error adding subject '{code}'. It might already exist (unique code).", 'error')
    else:
        flash("Subject code and name cannot be empty.", 'error')
    return redirect(url_for('manage_data'))

@app.route('/add_assignment', methods=['POST'])
@login_required
def add_assignment_route():
    try:
        semester = int(request.form['semester'])
        section = request.form['section']
        subject_id = int(request.form['subject_id'])
        faculty_id = int(request.form['faculty_id'])
        if section not in ['A', 'B'] or not 1 <= semester <= 10: raise ValueError("Invalid semester/section.")
        if db_utils.add_semester_subject(semester, section, subject_id, faculty_id): flash("Assignment added.", 'success')
        else: flash("Error adding assignment. Already exists?", 'error')
    except (KeyError, ValueError, TypeError) as e: flash(f"Invalid input: {e}", 'error')
    return redirect(url_for('manage_data'))

@app.route('/delete_assignment/<int:assignment_id>', methods=['POST'])
@login_required
def delete_assignment_route(assignment_id):
     if db_utils.delete_semester_subject(assignment_id): flash("Assignment deleted.", 'success')
     else: flash("Error deleting assignment.", 'error')
     return redirect(url_for('manage_data'))

@app.route('/add_room', methods=['POST'])
@login_required
def add_room_route():
    room_number = request.form.get('room_number')
    if room_number:
        if db_utils.add_room(room_number): flash(f"Room '{room_number}' added.", 'success')
        else: flash(f"Error adding room '{room_number}'. Already exists?", 'error')
    else: flash("Room number cannot be empty.", 'error')
    return redirect(url_for('manage_data'))

# --- Specific Timetable View Route ---
@app.route('/view/<int:semester>/<string:section>', endpoint='display_single_timetable') # Explicit endpoint
@login_required # Add login required here too
def display_single_timetable(semester, section): # Renamed function
    """Displays the timetable for a specific semester and section."""
    if section not in ['A', 'B'] or not 1 <= semester <= 10:
        abort(404)

    # Fetch data for the specific timetable view
    query = """
        SELECT
            ts.day_of_week, ts.start_time, ts.end_time,
            s.subject_name, f.faculty_name, r.room_number
        FROM Timetable t
        JOIN TimeSlots ts ON t.slot_id = ts.slot_id
        JOIN Subjects s ON t.subject_id = s.subject_id
        JOIN Faculty f ON t.faculty_id = f.faculty_id
        JOIN Rooms r ON t.room_id = r.room_id
        WHERE t.semester = ? AND t.section = ?
        ORDER BY ts.day_of_week, ts.start_time
    """
    timetable_entries = db_utils.fetch_data(query, (semester, section))

    schedule_map = {}
    days = []
    time_intervals = []
    pdf_exists = False

    if not timetable_entries:
        flash(f"No generated timetable data found for Semester {semester}, Section {section}.", 'warning')
    else:
        pdf_exists = True
        days = sorted(list(set(entry['day_of_week'] for entry in timetable_entries)), key=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'].index)
        time_intervals = sorted(list(set(f"{entry['start_time']}-{entry['end_time']}" for entry in timetable_entries)))
        schedule_map = defaultdict(str)
        for entry in timetable_entries:
            interval = f"{entry['start_time']}-{entry['end_time']}"
            schedule_map[(entry['day_of_week'], interval)] = f"{entry['subject_name']}<br>({entry['faculty_name']})<br>[{entry['room_number']}]"

    # Generate a temporary PDF filename for potential iframe use
    temp_pdf_filename = f"preview_sem{semester}_sec{section}_{uuid.uuid4()}.pdf"
    temp_pdf_filepath = os.path.join(PDF_TEMP_DIR, temp_pdf_filename)
    pdf_preview_url = None

    if pdf_exists:
        if generate_timetable_pdf(semester, section, temp_pdf_filepath):
             pdf_preview_url = url_for('serve_pdf', filename=temp_pdf_filename)
        else:
             flash("Could not generate PDF preview.", "error")
             if os.path.exists(temp_pdf_filepath): os.remove(temp_pdf_filepath)

    return render_template('timetable_view.html',
                           semester=semester,
                           section=section,
                           days=days,
                           time_intervals=time_intervals,
                           schedule=schedule_map,
                           pdf_preview_url=pdf_preview_url,
                           pdf_exists=pdf_exists)

# --- PDF Routes ---

@app.route('/serve_pdf/<filename>')
def serve_pdf(filename):
    """Serves the generated PDF for the iframe."""
    if '..' in filename or filename.startswith('/'): abort(403)
    filepath = os.path.join(PDF_TEMP_DIR, filename)
    if os.path.exists(filepath):
        response = send_file(filepath, mimetype='application/pdf')
        @response.call_on_close
        def cleanup_file():
            try: os.remove(filepath); print(f"Cleaned up preview PDF: {filepath}")
            except Exception as e: print(f"Error cleaning up preview PDF {filepath}: {e}")
        return response
    else: abort(404)

@app.route('/download/<int:semester>/<string:section>')
@login_required
def download_timetable(semester, section):
    """Generates and serves the PDF timetable for download."""
    if section not in ['A', 'B'] or not 1 <= semester <= 10: abort(404)
    temp_filename = f"timetable_sem{semester}_sec{section}_{uuid.uuid4()}.pdf"
    temp_filepath = os.path.join(PDF_TEMP_DIR, temp_filename)
    success = generate_timetable_pdf(semester, section, temp_filepath)
    if success and os.path.exists(temp_filepath):
        try:
            response = send_file(temp_filepath, as_attachment=True, download_name=f"Timetable_Sem{semester}_Sec{section}.pdf")
            @response.call_on_close
            def cleanup_file():
                 try: os.remove(temp_filepath); print(f"Cleaned up download PDF: {temp_filepath}")
                 except Exception as e: print(f"Error cleaning up download PDF {temp_filepath}: {e}")
            return response
        except Exception as e:
             print(f"Error sending file {temp_filepath}: {e}")
             if os.path.exists(temp_filepath): os.remove(temp_filepath)
             abort(500)
    else:
        flash(f"Could not generate PDF for Semester {semester}, Section {section}.", 'error')
        # Redirect back to the main page or a specific error page?
        return redirect(url_for('generate_view_timetable')) # Redirect back to main page

# --- Database Reset Route ---
@app.route('/reset_db', methods=['POST'])
@login_required
def reset_database_route():
    """Resets and reseeds the database."""
    try:
        print("Attempting to reset database...")
        if os.path.exists(db_utils.DATABASE_NAME): os.remove(db_utils.DATABASE_NAME)
        setup_database()
        flash("Database has been reset and reseeded.", 'success')
    except Exception as e:
        flash(f"An error occurred during database reset: {e}", 'error')
        print(f"Database reset error: {e}")
    return redirect(url_for('manage_data'))

# --- Run the App ---
if __name__ == '__main__':
    db_exists, _ = db_utils.check_db_and_data() # Use check from db_utils if it exists there now
    if not db_exists:
        print(f"Database file '{db_utils.DATABASE_NAME}' not found. Creating...")
        try: setup_database()
        except Exception as e: print(f"Failed to create database: {e}")
    app.run(debug=True)
