# upgraded_attendance_ui.py
# Full upgraded UI wrapper around your existing attendance logic.
# Preserves all original scan / registration / attendance functions unchanged.

import pandas as pd
import datetime
import json
import os
import time
import tkinter as tk
from tkinter import messagebox, scrolledtext, simpledialog, ttk
import threading

# --- Bluetooth import & flags (same as original) ---
try:
    import bluetooth
    BLUETOOTH_AVAILABLE = True
except ImportError:
    bluetooth = None
    BLUETOOTH_AVAILABLE = False
    print("Warning: 'pybluez' is not installed. Bluetooth functionality will be simulated.")

# --- Configuration (kept original values; modify if needed) ---
SCAN_DURATION_SECONDS = 5
SCAN_INTERVAL_SECONDS = 5
REGISTRATION_FILE = "registered_students.json"
ATTENDANCE_THRESHOLD = 0.8

# --- Default UI / Auth settings (change here if you wish) ---
DEFAULT_TEACHER_ID = "teacher"
DEFAULT_TEACHER_PASSWORD = "1234"
STUDENT_ADMIN_PASSWORD = "admin123"

BATCHES = ["CSE A", "CSE B", "IT A", "ECE 1"]
PERIODS = [f"Period {i}" for i in range(1, 7)]  # 6 periods by default
SEMESTERS = [str(i) for i in range(1, 9)]

# --- Data stores (same as original) ---
registered_students = {}
attendance_data = {}
attendance_records = {}

# --- Global UI / State placeholders ---
app = None
log_box = None
current_teacher_context = {"batch": None, "period": None, "semester": None}
is_scanning = False
stop_scan_flag = threading.Event()

# ---------- Original helper & logic functions (kept intact, slightly adapted to reference globals) ----------

def log(message):
    """Console + UI log helper."""
    print(message)
    if log_box:
        log_box.after(0, lambda: log_box.insert(tk.END, message + "\n"))
        log_box.after(0, lambda: log_box.see(tk.END))

def scan_for_devices(duration):
    """Scans for Bluetooth devices or simulates when pybluez not present."""
    devices_found = {}
    if not BLUETOOTH_AVAILABLE:
        log("\n⚠️ SIMULATION MODE: Bluetooth module not found.")
        simulated_macs = list(registered_students.keys())
        if len(simulated_macs) < 2:
            simulated_macs.append("AA:BB:CC:DD:EE:01")
            simulated_macs.append("AA:BB:CC:DD:EE:02")
        for mac in simulated_macs:
            name = registered_students.get(mac, {}).get('name', 'Unknown Device')
            # slight randomness in simulated detection to mimic real world
            if threading.current_thread().name == "MainThread" or (time.time() * 1000) % 4 != 0:
                devices_found[mac] = {'name': name, 'rssi': 'N/A'}
        time.sleep(duration / 2)
        return devices_found

    try:
        nearby_devices = bluetooth.discover_devices(duration=duration, lookup_names=True, flush_cache=True, lookup_class=False)
        for addr, name in nearby_devices:
            devices_found[addr] = {'name': name if name else "Unknown Device", 'rssi': 'N/A'}
    except Exception as e:
        log(f"An unexpected error occurred during scanning: {e}")
        return {}
    return devices_found

def load_registered_students():
    """Load from JSON if exists."""
    global registered_students
    if os.path.exists(REGISTRATION_FILE):
        try:
            with open(REGISTRATION_FILE, 'r') as f:
                registered_students = json.load(f)
                log(f"✅ Loaded {len(registered_students)} registered students from {REGISTRATION_FILE}.")
        except (IOError, json.JSONDecodeError) as e:
            log(f"❌ Error loading student data from file: {e}. Starting with an empty list.")
            registered_students = {}
    else:
        log("No existing registration file found. Starting a new registration.")

def save_registered_students():
    """Save to JSON."""
    try:
        with open(REGISTRATION_FILE, 'w') as f:
            json.dump(registered_students, f, indent=4)
        log(f"✅ Registered students saved to {REGISTRATION_FILE}.")
    except IOError as e:
        log(f"❌ Error saving student data to file: {e}")

# --- Registration popup (reused from original) ---
def registration_process_popup():
    """Handles student registration flow (reuses original logic)."""
    def register_selected():
        selected_index = listbox.curselection()
        if not selected_index:
            messagebox.showerror("Error", "Please select a device to register.")
            return
        index = selected_index[0]
        selected_mac, selected_data = device_list[index]
        name = name_entry.get().strip()
        if not name:
            messagebox.showerror("Error", "Student name cannot be empty.")
            return
        if selected_mac in registered_students:
            messagebox.showwarning("Warning", f"This device is already registered to {registered_students[selected_mac]['name']}.")
            devices_window.destroy()
            return
        registered_students[selected_mac] = {"name": name, "beacon_id": selected_mac}
        log(f"✅ Registered {name} with MAC Address {selected_mac}")
        save_registered_students()
        devices_window.destroy()

    log("\n--- 📝 Starting Student Registration Scan (Blocking) ---")
    app.config(cursor="wait")
    app.update_idletasks()
    nearby_devices = scan_for_devices(SCAN_DURATION_SECONDS)
    app.config(cursor="")
    app.update_idletasks()

    if not nearby_devices:
        log("⚠️ No Bluetooth devices found. Registration aborted.")
        messagebox.showinfo("Registration Status", "No Bluetooth devices found.")
        return

    device_list = list(nearby_devices.items())
    devices_window = tk.Toplevel(app)
    devices_window.title("Register Student")
    devices_window.geometry("520x380")
    devices_window.resizable(False, False)

    tk.Label(devices_window, text="Found Devices:", font=('Segoe UI', 10, 'bold')).pack(pady=8)
    listbox = tk.Listbox(devices_window, width=70, height=10, font=('Consolas', 10))
    for mac, data in device_list:
        status = "(Registered)" if mac in registered_students else ""
        listbox.insert(tk.END, f"{data['name']} | MAC: {mac} {status}")
    listbox.pack(pady=4, padx=8)

    tk.Label(devices_window, text="Student Name:", font=('Segoe UI', 10)).pack(pady=(8, 2))
    name_entry = tk.Entry(devices_window, width=40, font=('Segoe UI', 10))
    name_entry.pack(pady=4)

    btn_frame = tk.Frame(devices_window)
    btn_frame.pack(pady=12)
    tk.Button(btn_frame, text="Register Selected Device", command=register_selected, bg='#00C853', fg='white', width=22, height=1, relief=tk.FLAT).pack(side=tk.LEFT, padx=8)
    tk.Button(btn_frame, text="Cancel", command=devices_window.destroy, bg='#9E9E9E', fg='white', width=12, height=1, relief=tk.FLAT).pack(side=tk.LEFT)

    devices_window.transient(app)
    devices_window.grab_set()
    app.wait_window(devices_window)

# --- Attendance core logic (unchanged - only small refactor so UI can call it) ---
def attendance_process_logic():
    global is_scanning, attendance_data, attendance_records, stop_scan_flag
    is_scanning = True
    stop_scan_flag.clear()
    if not registered_students:
        log("\n⚠️ No students are registered. Please run registration first.")
        is_scanning = False
        app.after(0, lambda: update_ui_state(True))
        return

    log(f"\n--- ⏳ Starting Continuous Attendance Session ---")
    log(f"System will scan every {SCAN_INTERVAL_SECONDS} seconds until stopped.")
    attendance_records = {mac: 0 for mac in registered_students.keys()}
    scan_count = 0

    while not stop_scan_flag.is_set():
        scan_count += 1
        log(f"\n[SCAN {scan_count}] Scanning for {SCAN_DURATION_SECONDS} seconds...")
        nearby_devices = scan_for_devices(SCAN_DURATION_SECONDS)
        detected_macs = set(nearby_devices.keys())

        for mac in registered_students.keys():
            student_name = registered_students[mac]['name']
            if mac in detected_macs:
                attendance_records[mac] += 1
                log(f"  ✅ Detected: {student_name} (Total Detections: {attendance_records[mac]})")
            else:
                log(f"  ❌ Not Found: {student_name}")

        log(f"Waiting for {SCAN_INTERVAL_SECONDS} seconds...")
        if stop_scan_flag.wait(SCAN_INTERVAL_SECONDS):
            break

    log("\n\n--- 🛑 Attendance Session Stopped ---")
    current_date = datetime.date.today().isoformat()
    required_detections = round(scan_count * ATTENDANCE_THRESHOLD)

    for mac, data in registered_students.items():
        total_detections = attendance_records.get(mac, 0)
        status = "Present" if total_detections >= required_detections else "Absent"
        attendance_data[data['name']] = {
            "Name": data['name'],
            "Beacon ID": data['beacon_id'],
            "Date": current_date,
            "Status": status,
            "Total Detections": total_detections,
            "Total Scans": scan_count,
            "Required Detections": required_detections
        }

    log(f"Attendance finalized. Total Scans: {scan_count}. Threshold: {ATTENDANCE_THRESHOLD*100:.0f}% ({required_detections} detections required).")
    app.after(0, lambda: update_ui_state(True))
    app.after(0, display_and_export_results)
    is_scanning = False

def start_attendance_session_thread():
    global is_scanning
    if is_scanning:
        messagebox.showwarning("Warning", "Attendance scan is already running.")
        return
    if not BLUETOOTH_AVAILABLE:
        if not messagebox.askyesno("Warning: Simulation Mode", "Bluetooth module (pybluez) not found. The system will run in simulation mode. Continue?"):
            return
    update_ui_state(False)
    scan_thread = threading.Thread(target=attendance_process_logic, name="AttendanceThread")
    scan_thread.daemon = True
    scan_thread.start()

def stop_attendance_session():
    global is_scanning
    if is_scanning:
        log("\n--- User requested to stop scanning. Finalizing results... ---")
        stop_scan_flag.set()
    else:
        messagebox.showinfo("Status", "No attendance session is currently running.")

def display_and_export_results():
    if not attendance_data:
        log("No attendance data to display.")
        return
    df = pd.DataFrame(list(attendance_data.values()))
    df = df[['Name', 'Beacon ID', 'Date', 'Status', 'Total Detections', 'Total Scans', 'Required Detections']]
    log("\n--- 📊 Final Attendance Report ---")
    log(df.to_string(index=False))
    filename = f"attendance_{datetime.date.today().isoformat()}.csv"
    try:
        df.to_csv(filename, index=False)
        log(f"\n✅ Attendance data saved to {filename}")
    except IOError as e:
        log(f"❌ Error saving attendance file: {e}")

# ---------- UI helpers & flows for app-like interface ----------

def center_window(win, w=900, h=650):
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    x = int((sw - w) / 2)
    y = int((sh - h) / 2)
    win.geometry(f"{w}x{h}+{x}+{y}")

def make_hover(widget, bg_normal, bg_hover):
    def on_enter(e):
        widget.configure(bg=bg_hover)
    def on_leave(e):
        widget.configure(bg=bg_normal)
    widget.bind("<Enter>", on_enter)
    widget.bind("<Leave>", on_leave)

def clear_main_area():
    for child in main_area.winfo_children():
        child.destroy()

# --- Authentication flows ---

def student_admin_auth_and_open_register():
    """Show a simple password prompt for student admin, then open register if correct."""
    pwd = simpledialog.askstring("Student Admin Auth", "Enter Admin Password:", show='*', parent=app)
    if pwd is None:
        return
    if pwd == STUDENT_ADMIN_PASSWORD:
        registration_process_popup()
    else:
        messagebox.showerror("Auth Failed", "Incorrect admin password for registration.")

def teacher_login_flow():
    """Open teacher login modal (ID + password). On success, open semester -> batch -> period flow."""
    login_win = tk.Toplevel(app)
    login_win.title("Teacher Login")
    login_win.resizable(False, False)
    login_win.grab_set()
    login_win.geometry("380x220")
    login_win.transient(app)

    tk.Label(login_win, text="Teacher Login", font=('Segoe UI', 12, 'bold')).pack(pady=(12,6))
    frm = tk.Frame(login_win)
    frm.pack(pady=6)

    tk.Label(frm, text="Teacher ID:", font=('Segoe UI', 10)).grid(row=0, column=0, sticky='e', padx=6, pady=6)
    id_entry = tk.Entry(frm, width=22, font=('Segoe UI', 10))
    id_entry.grid(row=0, column=1, padx=6, pady=6)
    tk.Label(frm, text="Password:", font=('Segoe UI', 10)).grid(row=1, column=0, sticky='e', padx=6, pady=6)
    pwd_entry = tk.Entry(frm, show='*', width=22, font=('Segoe UI', 10))
    pwd_entry.grid(row=1, column=1, padx=6, pady=6)

    def attempt_login():
        tid = id_entry.get().strip()
        tpwd = pwd_entry.get().strip()
        if not tid or not tpwd:
            messagebox.showwarning("Missing", "Please enter ID and password.")
            return
        if tid == DEFAULT_TEACHER_ID and tpwd == DEFAULT_TEACHER_PASSWORD:
            login_win.destroy()
            show_teacher_selections()
        else:
            messagebox.showerror("Auth Failed", "Invalid Teacher ID or Password.")

    btn_frame = tk.Frame(login_win)
    btn_frame.pack(pady=10)
    tk.Button(btn_frame, text="Login", command=attempt_login, bg='#2979FF', fg='white', width=12, relief=tk.FLAT).pack(side=tk.LEFT, padx=8)
    tk.Button(btn_frame, text="Cancel", command=login_win.destroy, bg='#9E9E9E', fg='white', width=10, relief=tk.FLAT).pack(side=tk.LEFT)

def show_teacher_selections():
    """Show semester -> batch -> period selection UI, then teacher control panel."""
    clear_main_area()
    header = tk.Label(main_area, text="Teacher — Select Semester, Batch & Period", font=('Segoe UI', 14, 'bold'), bg='#F5F5F5')
    header.pack(pady=(10,8))

    sel_frame = tk.Frame(main_area, bg='#F5F5F5')
    sel_frame.pack(pady=6)

    tk.Label(sel_frame, text="Semester:", font=('Segoe UI', 11), bg='#F5F5F5').grid(row=0, column=0, padx=10, pady=8, sticky='w')
    sem_combo = ttk.Combobox(sel_frame, values=SEMESTERS, state='readonly', width=18, font=('Segoe UI', 10))
    sem_combo.grid(row=0, column=1, padx=8, pady=8)
    sem_combo.set(SEMESTERS[0])

    tk.Label(sel_frame, text="Batch:", font=('Segoe UI', 11), bg='#F5F5F5').grid(row=1, column=0, padx=10, pady=8, sticky='w')
    batch_combo = ttk.Combobox(sel_frame, values=BATCHES, state='readonly', width=18, font=('Segoe UI', 10))
    batch_combo.grid(row=1, column=1, padx=8, pady=8)
    batch_combo.set(BATCHES[0])

    tk.Label(sel_frame, text="Period:", font=('Segoe UI', 11), bg='#F5F5F5').grid(row=2, column=0, padx=10, pady=8, sticky='w')
    period_combo = ttk.Combobox(sel_frame, values=PERIODS, state='readonly', width=18, font=('Segoe UI', 10))
    period_combo.grid(row=2, column=1, padx=8, pady=8)
    period_combo.set(PERIODS[0])

    def open_teacher_control():
        current_teacher_context['semester'] = sem_combo.get()
        current_teacher_context['batch'] = batch_combo.get()
        current_teacher_context['period'] = period_combo.get()
        show_teacher_control_panel()

    tk.Button(main_area, text="Proceed →", command=open_teacher_control, bg='#2979FF', fg='white', width=18, height=1, relief=tk.FLAT).pack(pady=(10,6))
    tk.Button(main_area, text="Back Home", command=show_home_screen, bg='#9E9E9E', fg='white', width=12, height=1, relief=tk.FLAT).pack()

def show_teacher_control_panel():
    """Teacher control with Start / Stop attendance and context display."""
    clear_main_area()
    header = tk.Label(main_area, text="Teacher Control Panel", font=('Segoe UI', 14, 'bold'), bg='#F5F5F5')
    header.pack(pady=(10,6))

    ctx_frame = tk.Frame(main_area, bg='#FFFFFF', relief=tk.RIDGE, bd=1, padx=12, pady=12)
    ctx_frame.pack(pady=8)
    tk.Label(ctx_frame, text=f"Semester: {current_teacher_context['semester']}", font=('Segoe UI', 11), bg='#FFFFFF').grid(row=0, column=0, sticky='w', padx=6, pady=4)
    tk.Label(ctx_frame, text=f"Batch: {current_teacher_context['batch']}", font=('Segoe UI', 11), bg='#FFFFFF').grid(row=1, column=0, sticky='w', padx=6, pady=4)
    tk.Label(ctx_frame, text=f"Period: {current_teacher_context['period']}", font=('Segoe UI', 11), bg='#FFFFFF').grid(row=2, column=0, sticky='w', padx=6, pady=4)

    btn_frame = tk.Frame(main_area, bg='#F5F5F5')
    btn_frame.pack(pady=12)

    start_btn_ui = tk.Button(btn_frame, text="Start Attendance", command=start_attendance_session_thread, bg='#00C853', fg='white', width=18, height=2, relief=tk.FLAT)
    start_btn_ui.grid(row=0, column=0, padx=8, pady=6)
    make_hover(start_btn_ui, '#00C853', '#009624')

    stop_btn_ui = tk.Button(btn_frame, text="Stop Attendance", command=stop_attendance_session, bg='#D50000', fg='white', width=18, height=2, relief=tk.FLAT)
    stop_btn_ui.grid(row=0, column=1, padx=8, pady=6)
    make_hover(stop_btn_ui, '#D50000', '#9B0000')

    back_btn = tk.Button(main_area, text="Back", command=show_teacher_selections, bg='#9E9E9E', fg='white', width=12, relief=tk.FLAT)
    back_btn.pack(pady=(6, 10))

# --- Main Home Screen ---

def show_home_screen():
    clear_main_area()
    title = tk.Label(main_area, text="Bluetooth Attendance System", font=('Segoe UI', 18, 'bold'), bg='#F5F5F5')
    title.pack(pady=(18,8))

    subtitle = tk.Label(main_area, text="App-like interface — Select an action", font=('Segoe UI', 10), bg='#F5F5F5')
    subtitle.pack(pady=(0,10))

    card_frame = tk.Frame(main_area, bg='#F5F5F5')
    card_frame.pack(pady=6)

    def make_card(text, command, bg_color):
        card = tk.Frame(card_frame, bg=bg_color, width=360, height=60, relief=tk.RAISED, bd=0)
        card.pack_propagate(False)
        card.pack(pady=8)
        btn = tk.Button(card, text=text, command=command, bg=bg_color, fg='white', font=('Segoe UI', 12, 'bold'), relief=tk.FLAT)
        btn.pack(fill=tk.BOTH, expand=True)
        make_hover(btn, bg_color, '#000000' if bg_color == '#9E9E9E' else '#333333')
        return card

    make_card("Register Student (Admin)", student_admin_auth_and_open_register, "#00C853")
    make_card("Teacher Section (Login)", teacher_login_flow, "#2979FF")
    make_card("Exit App", app.quit, "#9E9E9E")

# --- UI: Log area & overall window setup ---

def update_ui_state(enable_register_button):
    """Enable/disable UI elements depending on scanning state; primarily affects home screen buttons."""
    # This function is intentionally light because buttons are recreated in show_home_screen / control panels.
    # But we still want Stop to be disabled if not scanning - handled by logic and user feedback.
    pass

def setup_ui():
    global app, log_box, main_area
    app = tk.Tk()
    app.title("Bluetooth Attendance System — App UI")
    app.configure(bg='#F5F5F5')
    center_window(app, w=920, h=700)

    # --- Top App Bar ---
    top_bar = tk.Frame(app, bg='#2979FF', height=64)
    top_bar.pack(side=tk.TOP, fill=tk.X)
    tk.Label(top_bar, text="Attendance App", fg='white', bg='#2979FF', font=('Segoe UI', 14, 'bold')).pack(side=tk.LEFT, padx=16, pady=12)
    tk.Label(top_bar, text="(App-like Interface)", fg='white', bg='#2979FF', font=('Segoe UI', 9)).pack(side=tk.LEFT, padx=8, pady=18)

    # --- Main content area (left) and log area (right) ---
    content_frame = tk.Frame(app, bg='#F5F5F5')
    content_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

    main_area = tk.Frame(content_frame, bg='#F5F5F5', width=620)
    main_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0,12))

    log_frame = tk.LabelFrame(content_frame, text="System Log & Results", font=('Segoe UI', 10, 'bold'))
    log_frame.pack(side=tk.RIGHT, fill=tk.BOTH, ipadx=4, ipady=4)

    log_box = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, width=48, height=24, font=('Consolas', 10))
    log_box.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

    # Load data & show home
    load_registered_students()
    if not BLUETOOTH_AVAILABLE:
        log("\n*** WARNING: Bluetooth module (pybluez) not found. Running in SIMULATION MODE. ***")
        log("Please install pybluez (pip install pybluez) for real functionality.")
    log(f"Attendance Threshold is set to {ATTENDANCE_THRESHOLD*100:.0f}% of total scans.")

    show_home_screen()
    app.protocol("WM_DELETE_WINDOW", app.quit)
    app.mainloop()

if __name__ == "__main__":
    setup_ui()
