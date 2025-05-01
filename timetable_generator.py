import sqlite3
import random
from collections import defaultdict
import db_utils # Import the whole module

# --- Constants ---
LECTURES_PER_SUBJECT_PER_WEEK = 4
MAX_FACULTY_LECTURES_PER_DAY_PER_SHIFT = 3
# MAX_FACULTY_LECTURES_PER_WEEK_PER_SHIFT = 8 # Weekly check is hard with targeted generation
SHIFT1_SEMESTERS = {5, 6, 7, 8, 9, 10}
SHIFT2_SEMESTERS = {1, 2, 3, 4}
DAYS_OF_WEEK = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday','Saturday']

# --- Helper: Fetch Existing Schedule for Shift ---
def get_existing_schedule_for_shift(target_shift):
    """ Fetches current Timetable entries ONLY for the target shift. """
    faculty_bookings = defaultdict(set) # {slot_id: {faculty_id, ...}}
    room_bookings = defaultdict(set)    # {slot_id: {room_id, ...}}
    faculty_daily_load = defaultdict(lambda: defaultdict(int)) # {faculty_id: {day: count}}

    # Determine which semesters belong to the target shift
    relevant_semesters = SHIFT1_SEMESTERS if target_shift == 1 else SHIFT2_SEMESTERS

    # Construct semester placeholders for the query
    sem_placeholders = ','.join('?' * len(relevant_semesters))
    params = tuple(relevant_semesters)

    # Ensure we only query if there are relevant semesters
    if not relevant_semesters:
        return faculty_bookings, room_bookings, faculty_daily_load

    query = f"""
        SELECT t.slot_id, t.faculty_id, t.room_id, ts.day_of_week
        FROM Timetable t
        JOIN TimeSlots ts ON t.slot_id = ts.slot_id
        WHERE t.semester IN ({sem_placeholders})
    """
    entries = db_utils.fetch_data(query, params)

    for entry in entries:
        slot_id = entry['slot_id']
        fac_id = entry['faculty_id']
        room_id = entry['room_id']
        day = entry['day_of_week']

        faculty_bookings[slot_id].add(fac_id)
        room_bookings[slot_id].add(room_id)
        if day in DAYS_OF_WEEK:
            faculty_daily_load[fac_id][day] += 1

    return faculty_bookings, room_bookings, faculty_daily_load

# --- Targeted Backtracking Generator ---

# Global vars to store existing schedule info for the relevant shift
existing_faculty_bookings_shift = defaultdict(set)
existing_room_bookings_shift = defaultdict(set)
existing_faculty_daily_load_shift = defaultdict(lambda: defaultdict(int))
# Global var for slot details (day, time) - fetched once per generation call
slot_details_map = {}

def generate_for_single_section(target_semester, target_section):
    """
    Generates timetable for a single semester/section using backtracking,
    checking against existing schedule *within the same shift* for conflicts.
    Enforces max daily load per shift for faculty.
    """
    print(f"Starting generation for Sem {target_semester}, Sec {target_section}...")
    global existing_faculty_bookings_shift, existing_room_bookings_shift
    global existing_faculty_daily_load_shift, slot_details_map

    # 1. Determine Shift and Fetch Data
    try:
        target_shift = 1 if target_semester in SHIFT1_SEMESTERS else (2 if target_semester in SHIFT2_SEMESTERS else 0)
        if target_shift == 0: raise ValueError(f"Semester {target_semester} not in defined shifts.")

        all_slots = db_utils.fetch_data("SELECT * FROM TimeSlots ORDER BY slot_id")
        if not all_slots: raise ValueError("No time slots found.")
        slot_details_map = {s['slot_id']: s for s in all_slots} # Populate global map

        shift_slots = [s['slot_id'] for s in all_slots if (9 <= int(s['start_time'].split(':')[0]) < 13 and target_shift == 1) or \
                                                          (13 <= int(s['start_time'].split(':')[0]) < 17 and target_shift == 2)]
        print(f"Target Shift: {target_shift}, Available Shift Slots: {len(shift_slots)} → {shift_slots}")

        if not shift_slots: raise ValueError(f"No time slots found for Shift {target_shift}.")

        all_rooms = db_utils.list_rooms()
        if not all_rooms: raise ValueError("No rooms found.")
        room_ids = [r['room_id'] for r in all_rooms]

        assignments = db_utils.list_semester_subjects(semester=target_semester, section=target_section)
        if not assignments: raise ValueError(f"No assignments found for Sem {target_semester}, Sec {target_section}.")

        # Fetch existing schedule ONLY for the target shift
        existing_faculty_bookings_shift, existing_room_bookings_shift, existing_faculty_daily_load_shift = get_existing_schedule_for_shift(target_shift)
        print(f"- Existing faculty bookings (Shift {target_shift}): {len(existing_faculty_bookings_shift)} slots")
        print(f"- Existing room bookings (Shift {target_shift}): {len(existing_room_bookings_shift)} slots")
        print(f"- Existing faculty daily load (Shift {target_shift}): {len(existing_faculty_daily_load_shift)} faculty")

    except ValueError as e:
        print(f"Error preparing data: {e}")
        return None
    except Exception as e: # Catch other potential errors during setup
        print(f"Unexpected error preparing data: {e}")
        return None


    # 2. Prepare lecture instances
    lectures_to_schedule = []
    lecture_info = {}
    for assign in assignments:
        subj_id = assign['subject_id']
        fac_id = assign['faculty_id']
        for i in range(1, LECTURES_PER_SUBJECT_PER_WEEK + 1):
            instance = (target_semester, target_section, subj_id, i)
            lectures_to_schedule.append(instance)
            lecture_info[instance] = {'faculty_id': fac_id}

    print(f"Attempting to schedule {len(lectures_to_schedule)} lecture instances...")

    # 3. Start backtracking
    solution_found, generated_schedule = backtrack_solver_targeted(
        lectures_to_schedule,
        lecture_info,
        shift_slots,
        room_ids,
        {} # Start with empty current schedule for this section
    )

    # 4. Process and Save Result
    if solution_found:
        print("Solution found!")
        timetable_to_save = {}
        for lecture_var, (slot_id, room_id) in generated_schedule.items():
            sem, sec, subj_id, _ = lecture_var
            fac_id = lecture_info[lecture_var]['faculty_id']
            timetable_to_save[(sem, sec, slot_id)] = (subj_id, fac_id, room_id)

        print(f"Clearing old timetable entries for Sem {target_semester}, Sec {target_section}...")
        if db_utils.clear_timetable_section(target_semester, target_section):
             if save_timetable_to_db(timetable_to_save):
                 print("Timetable saved successfully.")
                 return timetable_to_save
             else:
                 print("Error: Failed to save generated timetable.")
                 return None
        else:
             print("Error: Failed to clear old timetable entries.")
             return None
    else:
        print("Failed to find a valid schedule for this section.")
        return None


def backtrack_solver_targeted(lectures_to_schedule, lecture_info, available_slots, available_rooms, current_schedule):
    """ Recursive backtracking function for targeted generation with refined checks. """
    # current_schedule format: {lecture_instance: (slot_id, room_id)}
    # Uses global existing_*_shift variables for conflict checking

    if not lectures_to_schedule:
        return True, current_schedule

    lecture = lectures_to_schedule[0]
    remaining_lectures = lectures_to_schedule[1:]
    faculty_id = lecture_info[lecture]['faculty_id']
    semester, section, _, _ = lecture

    possible_assignments = [(slot, room) for slot in available_slots for room in available_rooms]
    random.shuffle(possible_assignments)

    for slot_id, room_id in possible_assignments:
        valid = True
        # Ensure slot_id is valid before accessing slot_details_map
        if slot_id not in slot_details_map:
            # print(f"Warning: Invalid slot_id {slot_id} encountered during assignment.")
            continue # Skip this invalid assignment
        day_of_week = slot_details_map[slot_id]['day_of_week']

        # --- Constraint Checking ---

        # 1. Check Section-Slot clash (within current generation for this section)
        for assigned_lecture, (assigned_slot, _) in current_schedule.items():
            if assigned_slot == slot_id:
                valid = False
                break
        if not valid:
            continue

        # 2. Check Faculty-Slot clash (against existing shift schedule AND current generation)
        if faculty_id in existing_faculty_bookings_shift.get(slot_id, set()):
            valid = False
        if valid:
            for assigned_lecture, (assigned_slot, _) in current_schedule.items():
                 if assigned_slot == slot_id and lecture_info[assigned_lecture]['faculty_id'] == faculty_id:
                    valid = False
                    break
        if not valid: 
            continue

        # 3. Check Room-Slot clash (against existing shift schedule AND current generation)
        if room_id in existing_room_bookings_shift.get(slot_id, set()):
            valid = False
        if valid:
             # Check against currently assigned slots in this run
            for assigned_lecture, (assigned_slot, assigned_room) in current_schedule.items():
                if assigned_slot == slot_id and assigned_room == room_id:
                    valid = False
                    break
        if not valid: 
            continue


        # 4. Check Faculty Daily Load (Max 2 per day per shift)
        # Count existing + currently assigned for this faculty on this day
        current_day_count = existing_faculty_daily_load_shift[faculty_id].get(day_of_week, 0)
        for assigned_lecture, (assigned_slot, _) in current_schedule.items():
            # Ensure assigned_slot is valid before checking its day
            if assigned_slot in slot_details_map and \
               lecture_info[assigned_lecture]['faculty_id'] == faculty_id and \
               slot_details_map[assigned_slot]['day_of_week'] == day_of_week:
                current_day_count += 1

        subject_count = len(set([lec[2] for lec in lecture_info if lecture_info[lec]['faculty_id'] == faculty_id]))
        adjusted_limit = MAX_FACULTY_LECTURES_PER_DAY_PER_SHIFT + (subject_count // 2)  # dynamic load        
                
        # If assigning this lecture exceeds the limit
        if current_day_count >= adjusted_limit:
             valid = False
        if not valid: 
            continue

        # --- Assign and Recurse ---
        current_schedule[lecture] = (slot_id, room_id)
        success, final_schedule = backtrack_solver_targeted(
            remaining_lectures, lecture_info, available_slots, available_rooms, current_schedule
        )
        if success: 
            return True, final_schedule

        # --- Backtrack ---
        del current_schedule[lecture]

    return False, None


# --- Database Saving (Keep existing function) ---
def save_timetable_to_db(timetable_data):
    """Saves the generated timetable dictionary to the database."""
    print("Saving timetable to database...")
    insert_query = """
        INSERT INTO Timetable (semester, section, slot_id, subject_id, faculty_id, room_id)
        VALUES (?, ?, ?, ?, ?, ?)
    """
    saved_count = 0
    error_count = 0
    for (semester, section, slot_id), (subject_id, faculty_id, room_id) in timetable_data.items():
        if db_utils.execute_query(insert_query, (semester, section, slot_id, subject_id, faculty_id, room_id)):
            saved_count += 1
        else:
            print(f"Error saving entry: Sem {semester}, Sec {section}, Slot {slot_id}")
            error_count += 1
    if error_count == 0:
        print(f"Successfully saved {saved_count} timetable entries.")
        return True
    else:
        print(f"Saved {saved_count} entries, but encountered {error_count} errors.")
        return False

# --- Main Execution Block (for testing targeted generation) ---
if __name__ == "__main__":
    TEST_SEMESTER = 6
    TEST_SECTION = 'A'
    try:
        conn = sqlite3.connect(f'file:{db_utils.DATABASE_NAME}?mode=rw', uri=True)
        print("Database found.")
        conn.close()
        final_schedule = generate_for_single_section(TEST_SEMESTER, TEST_SECTION)
        if final_schedule:
            print(f"\n--- Generation Complete for Sem {TEST_SEMESTER} Sec {TEST_SECTION} ---")
        else:
            print(f"\n--- Generation Failed for Sem {TEST_SEMESTER} Sec {TEST_SECTION} ---")
    except sqlite3.OperationalError:
        print(f"Database '{db_utils.DATABASE_NAME}' not found. Run database_setup.py first.")
    except Exception as e:
        print(f"An error occurred: {e}")


