import sqlite3
from collections import defaultdict
from db_utils import fetch_data, DATABASE_NAME
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
import os

def generate_timetable_pdf(semester, section, output_filepath):
    """
    Generates a PDF timetable for a specific semester and section.

    Args:
        semester (int): The semester number.
        section (str): The section ('A' or 'B').
        output_filepath (str): The full path where the PDF should be saved.
    """
    print(f"Generating PDF for Semester {semester}, Section {section} at {output_filepath}...")

    # Fetch timetable data for the specific semester and section
    query = """
        SELECT
            t.slot_id,
            ts.day_of_week,
            ts.start_time,
            ts.end_time,
            s.subject_name,
            f.faculty_name,
            r.room_number -- Added room_number
        FROM Timetable t
        JOIN TimeSlots ts ON t.slot_id = ts.slot_id
        JOIN Subjects s ON t.subject_id = s.subject_id
        JOIN Faculty f ON t.faculty_id = f.faculty_id
        JOIN Rooms r ON t.room_id = r.room_id -- Join with Rooms table
        WHERE t.semester = ? AND t.section = ?
        ORDER BY ts.day_of_week, ts.start_time
    """
    timetable_entries = fetch_data(query, (semester, section))

    if not timetable_entries:
        print(f"No timetable data found for Semester {semester}, Section {section}.")
        # Create an empty PDF or return an error indicator? For now, just print.
        # Optionally, create a PDF saying "No data available"
        doc = SimpleDocTemplate(output_filepath)
        styles = getSampleStyleSheet()
        story = [Paragraph(f"Timetable - Semester {semester} Section {section}", styles['h1']),
                 Spacer(1, 0.2*inch),
                 Paragraph("No timetable data found in the database for this selection.", styles['Normal'])]
        try:
            doc.build(story)
            print("Generated PDF indicating no data.")
            return True # Indicate PDF was created (even if empty)
        except Exception as e:
            print(f"Error generating empty PDF: {e}")
            return False


    # --- Prepare data for the table ---
    # Get unique days and time intervals present in the fetched data
    days = sorted(list(set(entry['day_of_week'] for entry in timetable_entries)), key=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'].index)
    time_intervals = sorted(list(set(f"{entry['start_time']}-{entry['end_time']}" for entry in timetable_entries)))

    # Create a mapping: (day, time_interval) -> "Subject (Faculty)"
    schedule_map = defaultdict(str)
    for entry in timetable_entries:
        interval = f"{entry['start_time']}-{entry['end_time']}"
        # Format cell content for PDF (using newline characters)
        schedule_map[(entry['day_of_week'], interval)] = f"{entry['subject_name']}\n({entry['faculty_name']})\n[{entry['room_number']}]"

    # --- Build the table data structure ---
    # Header row
    header = ['Time'] + days
    table_data = [header]

    # Data rows
    for interval in time_intervals:
        row = [interval] # First column is the time interval
        for day in days:
            row.append(schedule_map.get((day, interval), "")) # Get data or empty string
        table_data.append(row)

    # --- Create PDF Document ---
    doc = SimpleDocTemplate(output_filepath)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title = f"Timetable - Semester {semester} Section {section}"
    story.append(Paragraph(title, styles['h1']))
    story.append(Spacer(1, 0.2*inch))

    # Create Table and Style
    timetable_table = Table(table_data, repeatRows=1) # Repeat header row if table spans pages
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey), # Header background
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke), # Header text color
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'), # Center alignment for all cells
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), # Middle vertical alignment
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), # Header font bold
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12), # Header bottom padding
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige), # Body background
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black), # Body text color
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'), # Body font
        ('GRID', (0, 0), (-1, -1), 1, colors.black) # Grid lines
    ])
    timetable_table.setStyle(style)

    story.append(timetable_table)

    # Build the PDF
    try:
        # Ensure the output directory exists
        os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
        doc.build(story)
        print(f"PDF successfully generated: {output_filepath}")
        return True
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return False

# --- Example Usage (for testing) ---
if __name__ == '__main__':
    # Ensure the database exists and has generated data
    # Example: Generate PDF for Semester 1, Section A
    TEST_SEMESTER = 1
    TEST_SECTION = 'A'
    OUTPUT_DIR = 'generated_pdfs' # Create this directory if it doesn't exist
    # Make output path relative to the script location or CWD
    output_file = os.path.join(OUTPUT_DIR, f'timetable_sem{TEST_SEMESTER}_sec{TEST_SECTION}.pdf')

    # Check if DB exists
    try:
        conn = sqlite3.connect(f'file:{DATABASE_NAME}?mode=rw', uri=True)
        print("Database found.")
        conn.close()

        # Check if Timetable table has data (simple check)
        if fetch_data("SELECT 1 FROM Timetable LIMIT 1"):
             print("Timetable data found. Attempting PDF generation...")
             generate_timetable_pdf(TEST_SEMESTER, TEST_SECTION, output_file)
        else:
             print("Timetable table is empty. Run the generator first.")

    except sqlite3.OperationalError:
        print(f"Database '{DATABASE_NAME}' not found. Run database_setup.py first.")
