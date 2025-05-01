import sqlite3
import os

# Define the name for your database file
DATABASE_NAME = 'timetable_data.db'

# --- SQL Script ---
sql_script = """
-- =============================================
-- Temporarily Disable Foreign Key Support for Dropping
-- =============================================
PRAGMA foreign_keys = OFF;

-- =============================================
-- Drop Tables if they exist (Order matters, but FK check disabled)
-- =============================================
DROP TABLE IF EXISTS Timetable;
DROP TABLE IF EXISTS SemesterSubjects;
DROP TABLE IF EXISTS Faculty;
DROP TABLE IF EXISTS Subjects;
DROP TABLE IF EXISTS Rooms;
DROP TABLE IF EXISTS TimeSlots;

-- =============================================
-- Re-Enable Foreign Key Support Before Creating
-- =============================================
PRAGMA foreign_keys = ON;

-- =============================================
-- Create Faculty Table
-- =============================================
CREATE TABLE Faculty (
    faculty_id INTEGER PRIMARY KEY AUTOINCREMENT,
    faculty_name TEXT NOT NULL UNIQUE
);

-- =============================================
-- Create Subjects Table
-- =============================================
CREATE TABLE Subjects (
    subject_id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_code TEXT NOT NULL UNIQUE,
    subject_name TEXT NOT NULL
);

-- =============================================
-- Create Rooms Table
-- =============================================
CREATE TABLE Rooms (
    room_id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_number TEXT NOT NULL UNIQUE
);

-- =============================================
-- Create TimeSlots Table
-- =============================================
CREATE TABLE TimeSlots (
    slot_id INTEGER PRIMARY KEY AUTOINCREMENT,
    day_of_week TEXT NOT NULL CHECK(day_of_week IN ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday')),
    start_time TEXT NOT NULL, -- Format 'HH:MM'
    end_time TEXT NOT NULL,   -- Format 'HH:MM'
    UNIQUE(day_of_week, start_time)
);

-- =============================================
-- Create SemesterSubjects Table (Input Mapping)
-- =============================================
CREATE TABLE SemesterSubjects (
    assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    semester INTEGER NOT NULL, -- e.g., 1, 2, 3...
    section TEXT NOT NULL CHECK(section IN ('A', 'B')), -- e.g., 'A', 'B'
    subject_id INTEGER NOT NULL,
    faculty_id INTEGER NOT NULL,
    FOREIGN KEY (subject_id) REFERENCES Subjects(subject_id) ON DELETE CASCADE,
    FOREIGN KEY (faculty_id) REFERENCES Faculty(faculty_id) ON DELETE CASCADE,
    UNIQUE(semester, section, subject_id) -- Ensure a subject is assigned only once per section
);

-- =============================================
-- Create Timetable Table (Output Storage)
-- =============================================
CREATE TABLE Timetable (
    timetable_id INTEGER PRIMARY KEY AUTOINCREMENT,
    semester INTEGER NOT NULL,
    section TEXT NOT NULL,
    slot_id INTEGER NOT NULL,
    subject_id INTEGER NOT NULL,
    faculty_id INTEGER NOT NULL,
    room_id INTEGER NOT NULL,
    -- created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Optional timestamp
    FOREIGN KEY (slot_id) REFERENCES TimeSlots(slot_id) ON DELETE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES Subjects(subject_id) ON DELETE CASCADE,
    FOREIGN KEY (faculty_id) REFERENCES Faculty(faculty_id) ON DELETE CASCADE,
    FOREIGN KEY (room_id) REFERENCES Rooms(room_id) ON DELETE CASCADE,
    UNIQUE(semester, section, slot_id), -- Section constraint: Only one class per section per slot
    UNIQUE(faculty_id, slot_id),        -- Faculty constraint: Faculty teaches only one class per slot
    UNIQUE(room_id, slot_id)            -- Room constraint: Room occupied by only one class per slot
);

CREATE TABLE FacultySubjectMapping (
    mapping_id INTEGER PRIMARY KEY AUTOINCREMENT,
    faculty_id INTEGER NOT NULL,
    subject_id INTEGER NOT NULL,
    FOREIGN KEY (faculty_id) REFERENCES Faculty(faculty_id) ON DELETE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES Subjects(subject_id) ON DELETE CASCADE,
    UNIQUE(faculty_id, subject_id) -- Ensure a faculty is mapped to a subject only once
);
-- =============================================
-- Populate TimeSlots Table (Mon-Fri, Shifts 1 & 2)
-- =============================================
INSERT INTO TimeSlots (day_of_week, start_time, end_time) VALUES
-- Shift 1 (Sem 5-10)
('Monday', '09:00', '10:00'), ('Monday', '10:00', '11:00'), ('Monday', '11:00', '12:00'), ('Monday', '12:00', '13:00'),
('Tuesday', '09:00', '10:00'), ('Tuesday', '10:00', '11:00'), ('Tuesday', '11:00', '12:00'), ('Tuesday', '12:00', '13:00'),
('Wednesday', '09:00', '10:00'), ('Wednesday', '10:00', '11:00'), ('Wednesday', '11:00', '12:00'), ('Wednesday', '12:00', '13:00'),
('Thursday', '09:00', '10:00'), ('Thursday', '10:00', '11:00'), ('Thursday', '11:00', '12:00'), ('Thursday', '12:00', '13:00'),
('Friday', '09:00', '10:00'), ('Friday', '10:00', '11:00'), ('Friday', '11:00', '12:00'), ('Friday', '12:00', '13:00'),
-- Shift 2 (Sem 1-4)
('Monday', '13:00', '14:00'), ('Monday', '14:00', '15:00'), ('Monday', '15:00', '16:00'), ('Monday', '16:00', '17:00'),
('Tuesday', '13:00', '14:00'), ('Tuesday', '14:00', '15:00'), ('Tuesday', '15:00', '16:00'), ('Tuesday', '16:00', '17:00'),
('Wednesday', '13:00', '14:00'), ('Wednesday', '14:00', '15:00'), ('Wednesday', '15:00', '16:00'), ('Wednesday', '16:00', '17:00'),
('Thursday', '13:00', '14:00'), ('Thursday', '14:00', '15:00'), ('Thursday', '15:00', '16:00'), ('Thursday', '16:00', '17:00'),
('Friday', '13:00', '14:00'), ('Friday', '14:00', '15:00'), ('Friday', '15:00', '16:00'), ('Friday', '16:00', '17:00');

-- =============================================
-- Populate Faculty Table
-- =============================================
INSERT INTO Faculty (faculty_name) VALUES 
('Dr. Basant Namdeo'), ('Dr. Jugendra Dongre'), ('Mr.Rajesh Verma'), ('Dr. Kirti Mathur'),
('Dr.Nitin Nagar'), ('Dr. Pradeep Jatav'), ('Dr. Rahul Singhai'), ('Dr. Ramesh Thakur'),
('Dr. Rupesh Sendre'), ('Dr. Shaligram Prajapat') , ('Dr. Vivek Shrivastava'), ('Dr. Yasmin Sheikh'), 
('Ms.Kirti Vijayvargiya'), ('Ms. Manju Sachdeo'),('Ms. Poonam Mangwani'), ('Ms.Shraddha Soni'),
('Mr.Sanjay Katiyal'), ('Dr. Pushpendra Dubey'),('Dr. Naresh Patel'), ('Dr. Monalisa Khatre') , ('Visting 1'),('visting 2'), ('Dr.Jyoti Jain'); -- Added more faculty

-- =============================================
-- Populate Subjects Table
-- =============================================

INSERT INTO Subjects (subject_code, subject_name) VALUES ('CS101', 'Maths 1');
INSERT INTO Subjects (subject_code, subject_name) VALUES ('CS102', 'PC Software');
INSERT INTO Subjects (subject_code, subject_name) VALUES ('CS103', 'C');
INSERT INTO Subjects (subject_code, subject_name) VALUES ('CS104', 'digital Electronics');
INSERT INTO Subjects (subject_code, subject_name) VALUES ('CS105', 'English & Communication');
INSERT INTO Subjects (subject_code, subject_name) VALUES ('CS201', 'C++');
INSERT INTO Subjects (subject_code, subject_name) VALUES ('CS202', 'Digital Computer Org.');
INSERT INTO Subjects (subject_code, subject_name) VALUES ('CS203', 'Web Programming');
INSERT INTO Subjects (subject_code, subject_name) VALUES ('CS204', 'Maths 2');
INSERT INTO Subjects (subject_code, subject_name) VALUES ('CS205', 'Hindi');
INSERT INTO Subjects (subject_code, subject_name) VALUES ('CS301', 'Data Structure & Algorithm ');
INSERT INTO Subjects (subject_code, subject_name) VALUES ('CS302', 'Database Management Systems');
INSERT INTO Subjects (subject_code, subject_name) VALUES ('CS303', 'Financial Acoounting');
INSERT INTO Subjects (subject_code, subject_name) VALUES ('CS304', 'Statistics And Probability');
INSERT INTO Subjects (subject_code, subject_name) VALUES ('CS305', 'Environmental Chemistry');
INSERT INTO Subjects (subject_code, subject_name) VALUES ('CS401', 'Discrete Maths');
INSERT INTO Subjects (subject_code, subject_name) VALUES ('CS402', 'Java');
INSERT INTO Subjects (subject_code, subject_name) VALUES ('CS403', 'Unix OS');
INSERT INTO Subjects (subject_code, subject_name) VALUES ('CS404', 'Data & Computer Communication');
INSERT INTO Subjects (subject_code, subject_name) VALUES ('CS405', 'Entrepreneurship');
INSERT INTO Subjects (subject_code, subject_name) VALUES ('CS501', 'Introduction to Data Science');
INSERT INTO Subjects (subject_code, subject_name) VALUES ('CS502', 'Python');
INSERT INTO Subjects (subject_code, subject_name) VALUES ('CS503', 'System Programming');
INSERT INTO Subjects (subject_code, subject_name) VALUES ('CS504', 'Computer Graphics & Multimedia');
INSERT INTO Subjects (subject_code, subject_name) VALUES ('CS505', 'Computer Oriented Numerical Methods');
INSERT INTO Subjects (subject_code, subject_name) VALUES ('CS601', 'Operating System');
INSERT INTO Subjects (subject_code, subject_name) VALUES ('CS602', 'Cloud Computing');
INSERT INTO Subjects (subject_code, subject_name) VALUES ('CS603', 'System Analysis & Design');
INSERT INTO Subjects (subject_code, subject_name) VALUES ('CS604', 'Human Computer Interaction');
INSERT INTO Subjects (subject_code, subject_name) VALUES ('CS701', 'Software Engineering');
INSERT INTO Subjects (subject_code, subject_name) VALUES ('CS702', 'Computer Networks');
INSERT INTO Subjects (subject_code, subject_name) VALUES ('CS703', 'Computer Architecture');
INSERT INTO Subjects (subject_code, subject_name) VALUES ('CS704', 'Design & Analysis of Algorithm');
INSERT INTO Subjects (subject_code, subject_name) VALUES ('CS705', 'Artificial Intelligence');
INSERT INTO Subjects (subject_code, subject_name) VALUES ('CS801', 'Data Mining & Warehousing');
INSERT INTO Subjects (subject_code, subject_name) VALUES ('CS802', 'Enterprise Computer Techniques');
INSERT INTO Subjects (subject_code, subject_name) VALUES ('CS803', 'Mobile & Wireless computing');
INSERT INTO Subjects (subject_code, subject_name) VALUES ('CS804', 'Theory of Computation');
INSERT INTO Subjects (subject_code, subject_name) VALUES ('CS805', 'Soft Computing');

-- =============================================
-- Faculty Subject Mappping Table
-- =============================================
INSERT INTO FacultySubjectMapping (faculty_id, subject_id) VALUES (19, 1); 
INSERT INTO FacultySubjectMapping (faculty_id, subject_id) VALUES (9, 2); 
INSERT INTO FacultySubjectMapping (faculty_id, subject_id) VALUES (7, 3); 
INSERT INTO FacultySubjectMapping (faculty_id, subject_id) VALUES (3, 4);
INSERT INTO FacultySubjectMapping (faculty_id, subject_id) VALUES (20, 5); 
INSERT INTO FacultySubjectMapping (faculty_id, subject_id) VALUES (16, 6); 
INSERT INTO FacultySubjectMapping (faculty_id, subject_id) VALUES (9, 7); 
INSERT INTO FacultySubjectMapping (faculty_id, subject_id) VALUES (13, 8); 
INSERT INTO FacultySubjectMapping (faculty_id, subject_id) VALUES (19, 9); 
INSERT INTO FacultySubjectMapping (faculty_id, subject_id) VALUES (18, 10); 
INSERT INTO FacultySubjectMapping (faculty_id, subject_id) VALUES (14, 11); 
INSERT INTO FacultySubjectMapping (faculty_id, subject_id) VALUES (5, 12); 
INSERT INTO FacultySubjectMapping (faculty_id, subject_id) VALUES (17, 13);
INSERT INTO FacultySubjectMapping (faculty_id, subject_id) VALUES (6, 14); 
INSERT INTO FacultySubjectMapping (faculty_id, subject_id) VALUES (21, 15);
INSERT INTO FacultySubjectMapping (faculty_id, subject_id) VALUES (5, 16); 
INSERT INTO FacultySubjectMapping (faculty_id, subject_id) VALUES (1, 17); 
INSERT INTO FacultySubjectMapping (faculty_id, subject_id) VALUES (9, 18); 
INSERT INTO FacultySubjectMapping (faculty_id, subject_id) VALUES (3, 19); 
INSERT INTO FacultySubjectMapping (faculty_id, subject_id) VALUES (23, 20); 
INSERT INTO FacultySubjectMapping (faculty_id, subject_id) VALUES (10, 21); 
INSERT INTO FacultySubjectMapping (faculty_id, subject_id) VALUES (22, 22); 
INSERT INTO FacultySubjectMapping (faculty_id, subject_id) VALUES (13, 23);
INSERT INTO FacultySubjectMapping (faculty_id, subject_id) VALUES (1, 24);
INSERT INTO FacultySubjectMapping (faculty_id, subject_id) VALUES (9, 25); 
INSERT INTO FacultySubjectMapping (faculty_id, subject_id) VALUES (4, 26); 
INSERT INTO FacultySubjectMapping (faculty_id, subject_id) VALUES (11, 27); 
INSERT INTO FacultySubjectMapping (faculty_id, subject_id) VALUES (7, 28);
INSERT INTO FacultySubjectMapping (faculty_id, subject_id) VALUES (6, 29); 
INSERT INTO FacultySubjectMapping (faculty_id, subject_id) VALUES (22, 30); 
INSERT INTO FacultySubjectMapping (faculty_id, subject_id) VALUES (15, 31); 
INSERT INTO FacultySubjectMapping (faculty_id, subject_id) VALUES (16, 32); 
INSERT INTO FacultySubjectMapping (faculty_id, subject_id) VALUES (8, 33);
INSERT INTO FacultySubjectMapping (faculty_id, subject_id) VALUES (6, 34);
INSERT INTO FacultySubjectMapping (faculty_id, subject_id) VALUES (10, 35); 
INSERT INTO FacultySubjectMapping (faculty_id, subject_id) VALUES (8, 36); 
INSERT INTO FacultySubjectMapping (faculty_id, subject_id) VALUES (14, 37);
INSERT INTO FacultySubjectMapping (faculty_id, subject_id) VALUES (12, 38); 
INSERT INTO FacultySubjectMapping (faculty_id, subject_id) VALUES (2, 39);

-- =============================================
-- Populate Rooms Table
-- =============================================
INSERT INTO Rooms (room_number) VALUES
('Room 101'), ('Room 102'), ('Room 103'), ('Room 104'),
('Room 201'), ('Room 202'), ('Room 203'), ('Room 204'),
('Room 301'), ('Room 302'), ('Room 303'), ('Room 304'),
('Lab 1'), ('Lab 2'), ('Lab 3'), ('Lab 4'), ('Seminar Hall');

-- =============================================
-- Populate SemesterSubjects Table (Input Mapping - SAMPLE DATA)
-- Assign faculty_id and subject_id based on above inserts
-- =============================================
-- Semester 1, Section A
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (1, 'A', 3, 7); -- Maths I by Sharma
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (1, 'A', 2, 9); -- Prog Fundamentals by Sharma
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (1, 'A', 1, 19); -- Digital Logic by Mehta
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (1, 'A', 4, 3); -- Prog Fundamentals by Sharma
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (1, 'A', 5, 20); -- Digital Logic by Mehta

-- Semester 1, Section B
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (1, 'B', 1, 19); -- Maths I by Sharma
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (1, 'B', 2, 9); -- Prog Fundamentals by Rao
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (1, 'B', 3, 7); -- Digital Logic by Mehta
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (1, 'B', 4, 3); -- Prog Fundamentals by Sharma
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (1, 'B', 5, 20); -- Digital Logic by Mehta

-- Semester 2, Section A
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (2, 'A', 6, 16); -- Maths I by Sharma
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (2, 'A', 7, 9); -- Prog Fundamentals by Sharma
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (2, 'A', 8, 13); -- Digital Logic by Mehta
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (2, 'A', 9, 19); -- Prog Fundamentals by Sharma
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (2, 'A', 10, 18); -- Digital Logic by Mehta

-- Semester 2, Section B
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (2, 'B', 6, 16); -- Maths I by Sharma
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (2, 'B', 7, 9); -- Prog Fundamentals by Rao
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (2, 'B', 8, 13); -- Digital Logic by Mehta
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (2, 'B', 9, 19); -- Prog Fundamentals by Sharma
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (2, 'B', 10, 18); -- Digital Logic by Mehta

-- Semester 3, Section A
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (3, 'A', 11, 14); -- Maths I by Sharma
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (3, 'A', 12, 5); -- Prog Fundamentals by Sharma
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (3, 'A', 13, 17); -- Digital Logic by Mehta
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (3, 'A', 14, 6); -- Prog Fundamentals by Sharma
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (3, 'A', 15, 21); -- Digital Logic by Mehta

-- Semester 3, Section B
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (3, 'B', 11, 14); -- Maths I by Sharma
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (3, 'B', 12, 5); -- Prog Fundamentals by Rao
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (3, 'B', 13, 17); -- Digital Logic by Mehta
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (3, 'B', 14, 6); -- Prog Fundamentals by Sharma
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (3, 'B', 15, 21); -- Digital Logic by Mehta

-- Semester 4, Section A
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (4, 'A', 16, 5); -- Maths I by Sharma
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (4, 'A', 17, 1); -- Prog Fundamentals by Sharma
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (4, 'A', 18, 9); -- Digital Logic by Mehta
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (4, 'A', 19, 3); -- Prog Fundamentals by Sharma


-- Semester 4, Section B
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (4, 'B', 16, 5); -- Maths I by Sharma
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (4, 'B', 17, 1); -- Prog Fundamentals by Rao
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (4, 'B', 18, 9); -- Digital Logic by Mehta
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (4, 'B', 19, 3); -- Prog Fundamentals by Sharma

-- Semester 5, Section A
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (5, 'A', 20, 23); -- Maths I by Sharma
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (5, 'A', 21, 10); -- Prog Fundamentals by Sharma
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (5, 'A', 22, 22); -- Digital Logic by Mehta
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (5, 'A', 23, 13); -- Prog Fundamentals by Sharma
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (5, 'A', 24, 1); -- Digital Logic by Mehta

-- Semester 5, Section B
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (5, 'B', 20, 23); -- Maths I by Sharma
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (5, 'B', 21, 10); -- Prog Fundamentals by Rao
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (5, 'B', 22, 22); -- Digital Logic by Mehta
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (5, 'B', 23, 13); -- Prog Fundamentals by Sharma
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (5, 'B', 24, 1); -- Digital Logic by Mehta

-- Semester 6, Section A
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (6, 'A', 25, 9); -- Maths I by Sharma
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (6, 'A', 26, 4); -- Prog Fundamentals by Sharma
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (6, 'A', 27, 11); -- Digital Logic by Mehta
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (6, 'A', 28, 7); -- Prog Fundamentals by Sharma
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (6, 'A', 29, 6); -- Digital Logic by Mehta

-- Semester 6, Section B
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (6, 'B', 25, 9); -- Maths I by Sharma
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (6, 'B', 26, 4); -- Prog Fundamentals by Rao
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (6, 'B', 27, 11); -- Digital Logic by Mehta
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (6, 'B', 28, 7); -- Prog Fundamentals by Sharma
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (6, 'B', 29, 6); -- Digital Logic by Mehta

-- Semester 7, Section A
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (7, 'A', 30, 22); -- Maths I by Sharma
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (7, 'A', 31, 15); -- Prog Fundamentals by Sharma
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (7, 'A', 32, 16); -- Digital Logic by Mehta
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (7, 'A', 33, 8); -- Prog Fundamentals by Sharma
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (7, 'A', 34, 16); -- Digital Logic by Mehta

-- Semester 7, Section B
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (7, 'B', 30, 22); -- Maths I by Sharma
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (7, 'B', 31, 15); -- Prog Fundamentals by Rao
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (7, 'B', 32, 16); -- Digital Logic by Mehta
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (7, 'B', 33, 8); -- Prog Fundamentals by Sharma
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (7, 'B', 34, 6); -- Digital Logic by Mehta

-- Semester 8, Section A
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (8, 'A', 35, 10); -- Maths I by Sharma
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (8, 'A', 36, 8); -- Prog Fundamentals by Sharma
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (8, 'A', 37, 14); -- Digital Logic by Mehta
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (8, 'A', 38, 12); -- Prog Fundamentals by Sharma
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (8, 'A', 39, 2); -- Digital Logic by Mehta

-- Semester 8, Section B
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (8, 'B', 35, 10); -- Maths I by Sharma
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (8, 'B', 36, 8); -- Prog Fundamentals by Rao
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (8, 'B', 37, 14); -- Digital Logic by Mehta
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (8, 'B', 38, 12); -- Prog Fundamentals by Sharma
INSERT INTO SemesterSubjects (semester, section, subject_id, faculty_id) VALUES (8, 'B', 39, 2); -- Digital Logic by Mehta

"""

# --- Function to setup the database ---
def setup_database():
    """Connects to the SQLite database, executes the setup script."""
    conn = None
    try:
        print(f"Connecting to database: {DATABASE_NAME}...")
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        print("Executing SQL setup script...")
        cursor.executescript(sql_script)
        conn.commit()
        print("Database setup successful.")
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        if conn:
            conn.rollback()
            print("Changes rolled back due to error.")
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")

# --- Main execution block ---
if __name__ == "__main__":
    setup_database()
