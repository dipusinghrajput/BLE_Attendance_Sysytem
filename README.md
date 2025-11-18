
# 📘 Bluetooth Attendance System

### A Desktop App for Seamless Bluetooth-Based Student Attendance

**Built with Python, Tkinter UI, and PyBluez (with simulation mode support)**

---

## 📌 Overview

This project is a modern desktop-based **Bluetooth attendance tracking system** designed for colleges, schools, and training centers.
It uses the student's **Bluetooth device MAC address** as a unique identifier and performs **continuous scanning** to determine presence during a class session.

A fully upgraded, app-like UI built using **Tkinter** makes it intuitive, reliable, and teacher-friendly.

The system supports:

* Student registration via BLE scan
* Teacher authentication
* Continuous attendance scanning
* Automatic presence evaluation (80% threshold)
* CSV report export
* Simulation mode if Bluetooth is unavailable

---

## 🎯 Features

### 📝 **Student Registration**

* Scans nearby Bluetooth devices
* Allows assigning each device MAC to a student
* Stores registration data in `registered_students.json`

### 👨‍🏫 **Teacher Login + Session Setup**

* Secure login using ID & password
* Select Semester → Batch → Period
* Start/Stop attendance session

### 🔁 **Continuous Attendance Scanning**

* Scans every few seconds
* Tracks how many times each student was detected
* Uses an **80% threshold rule** to mark Present/Absent
* Displays detailed logs in real time

### 📊 **Automatic CSV Export**

Generates a CSV report with:

* Student Name
* Beacon MAC
* Date
* Status (Present/Absent)
* Total detections
* Required detections

Example output file:

```
attendance_2025-11-18.csv
```

### 🔧 **Simulation Mode**

If PyBluez is unavailable, the system automatically enters simulation mode:

* Fake BLE devices are generated
* Attendance logic still works
* Great for testing without hardware

---

## 🛠 Tech Stack

| Component           | Technology                            |
| ------------------- | ------------------------------------- |
| **UI**              | Tkinter                               |
| **Backend Logic**   | Python                                |
| **Bluetooth**       | PyBluez (auto fallback to simulation) |
| **Data Storage**    | JSON + CSV                            |
| **UI Enhancements** | ttk, ScrolledText                     |

---

## 📂 Project Structure

```
project/
│ test.py                      # Main application
│ registered_students.json     # Auto-generated on first run
│ attendance_YYYY-MM-DD.csv    # Generated after each session
└── (optional) virtualenv/
```

---

## 🚀 How It Works

### 1️⃣ Register Students

Admin → scans for nearby Bluetooth devices → assigns name → stores MAC ID.

### 2️⃣ Teacher Logs In

Selects semester, batch, and period.

### 3️⃣ Start Attendance

System performs:

* Bluetooth scan (every X seconds)
* Tracks # times student device appears
* Waits for stop command

### 4️⃣ Stop Attendance

App evaluates:

```
Present if (detections ≥ threshold * total_scans)
```

### 5️⃣ Export & View Results

CSV is generated automatically.

---

## 📦 Installation

### 1. Install dependencies

```bash
pip install pybluez pandas
```

### 2. Run the app

```bash
python test.py
```

If Bluetooth is not available, simulation mode is automatically enabled.

---

## 🧪 Simulation Mode Preview

You'll see a message like:

```
*** WARNING: Bluetooth module (pybluez) not found. Running in SIMULATION MODE. ***
```

Fake devices will be created, so the full attendance workflow still works.

---

## 🛡 Security Features

* Protected admin registration (password based)
* Teacher login screen
* Device-level identity (unique MAC)
* Threshold-based presence validation
* Non-editable logs

---

## 🗂 Data Files

### `registered_students.json`

Stores:

```json
{
    "MAC_ADDRESS": {
        "name": "Student Name",
        "beacon_id": "MAC_ADDRESS"
    }
}
```

### `attendance_YYYY-MM-DD.csv`

Final attendance report.

---

## 🐞 Known Limitations

* Works best with Bluetooth Classic devices
* PyBluez support varies on Windows 10/11
* MAC address randomization on newer phones may impact stability

---

## 🤝 Contributions

Pull requests are welcome!
Feel free to add:

* Database integration
* BLE filtering improvements
* UI themes
* Export to PDF

---

## 📄 License

MIT License – free to use and modify.

---

## ⭐ Acknowledgements

* PyBluez for Bluetooth scanning
* Tkinter for UI
* Pandas for exporting data

