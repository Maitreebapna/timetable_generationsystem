# Example in timetable_generator.py or db_utils.py
import sqlite3

DATABASE_NAME = 'timetable_data.db'

def connect_db():
    """Establishes connection to the SQLite database."""
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        conn.row_factory = sqlite3.Row # Access columns by name
        # Enforce foreign key constraints
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
        return None

def fetch_data(query, params=()):
    """Fetches multiple rows from the database."""
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            # Convert rows to list of dictionaries
            data = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return data
        except sqlite3.Error as e:
            print(f"Database fetch error: {e}")
            conn.close()
    return [] # Return empty list on error or no connection

def fetch_one(query, params=()):
    """Fetches a single row from the database."""
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            row = cursor.fetchone()
            data = dict(row) if row else None
            conn.close()
            return data
        except sqlite3.Error as e:
            print(f"Database fetch one error: {e}")
            conn.close()
    return None

def execute_query(query, params=()):
    """Executes INSERT, UPDATE, or DELETE queries."""
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            conn.close()
            return True # Indicate success
        except sqlite3.Error as e:
            print(f"Database execute error: {e}")
            conn.rollback() # Roll back changes on error
            conn.close()
    return False # Indicate failure

# --- Functions for Data Management ---

def add_faculty(name):
    """Adds a new faculty member."""
    query = "INSERT INTO Faculty (faculty_name) VALUES (?)"
    return execute_query(query, (name,))

def list_faculty():
    """Lists all faculty members."""
    query = "SELECT faculty_id, faculty_name FROM Faculty ORDER BY faculty_name"
    return fetch_data(query)

def add_subject(code, name):
    """Adds a new subject with code and name."""
    query = "INSERT INTO Subjects (subject_code, subject_name) VALUES (?, ?)"
    # Check for unique constraint violation (subject_code)
    try:
        return execute_query(query, (code, name))
    except sqlite3.IntegrityError as e:
        # Handle unique constraint violation specifically if needed
        print(f"Integrity error adding subject {code}: {e}")
        return False

def list_subjects():
    """Lists all subjects with their codes."""
    query = "SELECT subject_id, subject_code, subject_name FROM Subjects ORDER BY subject_name"
    return fetch_data(query)

def add_semester_subject(semester, section, subject_id, faculty_id):
    """Assigns a faculty to a subject for a specific semester/section."""
    query = """
        INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id)
        VALUES (?, ?, ?, ?)
    """
    return execute_query(query, (semester, section, subject_id, faculty_id))

def list_semester_subjects(semester=None, section=None):
    """Lists semester subject assignments, optionally filtered."""
    base_query = """
        SELECT ss.assignment_id, ss.semester, ss.section,
               s.subject_name, f.faculty_name, ss.subject_id, ss.faculty_id
        FROM SemesterSubjects ss
        JOIN Subjects s ON ss.subject_id = s.subject_id
        JOIN Faculty f ON ss.faculty_id = f.faculty_id
    """
    conditions = []
    params = []
    if semester:
        conditions.append("ss.semester = ?")
        params.append(semester)
    if section:
        conditions.append("ss.section = ?")
        params.append(section)

    if conditions:
        base_query += " WHERE " + " AND ".join(conditions)

    base_query += " ORDER BY ss.semester, ss.section, s.subject_name"
    return fetch_data(base_query, tuple(params))

def delete_semester_subject(assignment_id):
    """Deletes a specific semester subject assignment."""
    query = "DELETE FROM SemesterSubjects WHERE assignment_id = ?"
    return execute_query(query, (assignment_id,))

def add_room(room_number):
    """Adds a new room."""
    query = "INSERT INTO Rooms (room_number) VALUES (?)"
    return execute_query(query, (room_number,))

def list_rooms():
    """Lists all rooms."""
    query = "SELECT room_id, room_number FROM Rooms ORDER BY room_number"
    return fetch_data(query)

def clear_timetable_section(semester, section):
    """Deletes all timetable entries for a specific semester and section."""
    query = "DELETE FROM Timetable WHERE semester = ? AND section = ?"
    return execute_query(query, (semester, section))

# Add delete functions for faculty/subjects/rooms if needed, considering cascade deletes
