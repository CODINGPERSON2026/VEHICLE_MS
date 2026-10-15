# Smart RFID + ANPR Vehicle Gate Management System

A production-grade Smart Vehicle Gate Entry & Exit Management System built with **Python Flask**, **MySQL / MySQL Workbench**, **ESP32-WROOM-32**, **RC522 RFID**, **Bootstrap 5**, and an extensible **OpenCV / ANPR** architecture.

---

## 🚀 Key Features

- **🔐 Multi-Tier Role-Based Access Control (RBAC):**
  - **ADMIN:** Full system access, vehicle master, device registration, API keys, database backup & restore, settings.
  - **GATE OPERATOR:** RFID gate control, manual IN/OUT overrides with mandatory audit reasons, live vehicle search.
  - **REPORT VIEWER:** Read-only access to movement registers, analytics, and data exports.
- **🏷️ Vehicle Master Management:**
  - Standardized normalization of vehicle registration plates (uppercase, alphanumeric).
  - Categorization across vehicle types (*Car, Jeep, Motorcycle, Bus, Truck, Ambulance, Other*).
  - Time-bounded authorization status (*AUTHORIZED, NOT AUTHORIZED, EXPIRED, BLOCKED*).
  - Soft-deactivation to preserve movement history and compliance audits.
- **📡 Hardware-Agnostic RFID Engine:**
  - One-to-many vehicle RFID tagging (multiple cards per vehicle; strict one-to-one active card mapping).
  - **Live Hardware Enrollment Mode:** Tap an unassigned card on the ESP32 reader to capture the UID in real-time in the browser.
- **⚡ High-Performance IN/OUT Movement Engine:**
  - Server-authoritative access decisions (`ENTRY_ALLOWED`, `ENTRY_DENIED`, `EXIT_RECORDED`, `DUPLICATE_ENTRY`, `EXIT_EXCEPTION`).
  - Strict prevention of double entries (anti-passback checking).
  - Configurable scan cooldown, per-device API key authentication, and idempotency token protection.
- **🖥️ Large-Screen Gate Control Center:**
  - Real-time decision indicator banner (*Green for Authorized, Red for Denied, Blue for Exit*).
  - Simulated physical barrier actuator with animated gate arm and auto-close countdown.
  - Controlled manual override modal with mandatory operator reasoning and audit trail.
- **📊 Reports & Exports:**
  - 11 distinct report types (*Daily Movement, Date Range, Vehicle History, Currently Inside, Unauthorized Attempts, Expired Authorization, Blocked Vehicles, Manual Overrides, Device Health, ANPR Verification, Monthly Summary*).
  - Export capabilities in **CSV**, **Excel (.xlsx)**, and **PDF (ReportLab)**.
- **📷 Extensible ANPR & Camera Architecture:**
  - RTSP stream configuration for gate entry/exit cameras.
  - OCR confidence scoring and license plate cross-verification with RFID records.
  - Interactive ANPR Test Mode.
- **💾 Backup & Disaster Recovery:**
  - Transactional online MySQL database snapshots (`.sql` dumps).
  - Compatible with MySQL Workbench with pre-restore safety snapshots.

---

## 🛠️ Hardware Requirements & Wiring Diagram

### Bill of Materials (BOM)
1. **ESP32-WROOM-32** Development Board (38-pin or 30-pin)
2. **RC522 (MFRC522)** 13.56MHz RFID Reader & Tag / Card
3. Jumper Wires & Breadboard
4. Micro-USB Cable

### SPI Wiring Connections

```
+------------------+----------------------+---------------------------+
|  RC522 Pin       |  ESP32 GPIO Pin      |  Notes                    |
+------------------+----------------------+---------------------------+
|  3.3V (VCC)      |  3V3                 |  DO NOT CONNECT TO 5V!    |
|  GND             |  GND                 |  Common Ground            |
|  RST             |  GPIO 22             |  Reset Pin                |
|  SDA (SS / CS)   |  GPIO 5              |  SPI Chip Select          |
|  SCK             |  GPIO 18             |  SPI Clock                |
|  MOSI            |  GPIO 23             |  SPI Master Out Slave In  |
|  MISO            |  GPIO 19             |  SPI Master In Slave Out  |
|  IRQ             |  Not Connected       |  Unused                   |
+------------------+----------------------+---------------------------+
```

*Optional Indicators:*
- Green LED (Granted): `GPIO 2`
- Red LED (Denied / Error): `GPIO 4`
- Buzzer (Audio Chime): `GPIO 15`

---

## 💻 Software Setup & Installation (Windows / Local PC)

### 1. Prerequisites
- Python 3.11+ installed.
- Arduino IDE (for ESP32 firmware upload).

### 2. Environment Setup
Clone or navigate to the repository directory in PowerShell:

```powershell
# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Initialize & Start Application
```powershell
python app.py
```

The Flask server listens on `0.0.0.0:5000`.
- **Local PC Browser:** Open [http://127.0.0.1:5000](http://127.0.0.1:5000)
- On first launch, you will be automatically routed to the **First-Time Setup Wizard** to create your Master Administrator account.

---

## 🌐 Local Network & Windows Firewall Configuration

To allow the ESP32 microcontroller to send HTTP requests to your laptop/PC:

### Step 1: Find Host PC IPv4 Address
In PowerShell:
```powershell
ipconfig
```
Note down your Wi-Fi IPv4 address (e.g. `192.168.1.100`).

### Step 2: Allow Inbound Port 5000 through Windows Firewall
Run PowerShell as Administrator:
```powershell
netsh advfirewall firewall add rule name="Smart Vehicle Gate Server" dir=in action=allow protocol=TCP localport=5000
```

---

## 🔌 ESP32 Firmware Compilation & Upload

1. Open **Arduino IDE**.
2. Go to **Tools -> Board -> ESP32 Arduino -> ESP32 Dev Module**.
3. Install the required libraries via **Sketch -> Include Library -> Manage Libraries...**:
   - `MFRC522` (by GithubCommunity / Miguel Balboa)
4. Open the firmware file:
   `hardware/esp32/rfid_gate.ino`
5. Update your configuration:
   ```cpp
   const char* WIFI_SSID       = "YOUR_WIFI_NAME";
   const char* WIFI_PASSWORD   = "YOUR_WIFI_PASSWORD";
   const char* SERVER_URL      = "http://192.168.1.100:5000"; // Your PC IP
   const char* DEVICE_ID       = "GATE_ENTRY_01";
   const char* DEVICE_API_KEY  = "YOUR_API_KEY_FROM_DASHBOARD";
   const char* GATE_DIRECTION  = "ENTRY";
   ```
6. Connect the ESP32 via USB and click **Upload**.
7. Open the **Serial Monitor (115200 baud)** to view live connection logs.

---

## 🎮 Hardware & RFID Simulator

If physical ESP32 hardware is not currently connected, use the interactive Python hardware simulator:

```powershell
# Launch interactive simulator CLI
python hardware/simulator.py
```

Options include:
1. Scan Authorized Vehicle (ENTRY)
2. Scan Authorized Vehicle (EXIT)
3. Scan Unknown RFID Card
4. Scan Blocked Vehicle Card
5. Scan Expired Authorization Card
6. Send Device Heartbeat Ping
7. Send Live Card Enrollment Tag

---

## 🧪 Automated Pytest Test Suite

Run the full automated test suite:

```powershell
pytest -v
```

All 18 comprehensive tests cover:
- Admin account creation & login
- Vehicle registration & normalization
- Anti-passback duplicate entry prevention
- REST API scan decisions & idempotency
- Device authentication & heartbeat tracking
- 11 Report queries & CSV/Excel/PDF generation
- ANPR OCR verification logic

---

## 📁 Project Architecture

```
smart_vehicle_gate/
│
├── app.py                     # Flask application factory & context processors
├── config.py                  # Configurations (Dev, Prod, Testing)
├── requirements.txt           # Python dependencies
├── README.md                  # Comprehensive technical documentation
├── .env.example               # Environment variables template
│
├── database/
│ └── db_init.py              # MySQL DB initialization & settings seed
│
├── models/
│ ├── user.py                  # User authentication & RBAC roles
│ ├── vehicle.py               # Vehicle master & authorization validity
│ ├── rfid.py                  # RFID card tracking & status
│ ├── movement.py              # Entry/exit movements & duration calculations
│ ├── device.py                # Hardware device registry & event logging
│ ├── denied_attempt.py        # Security exception logs
│ ├── audit.py                 # System audit trail
│ ├── camera.py                # Camera configuration & ANPR OCR events
│ └── settings.py              # Persistent system settings
│
├── routes/
│ ├── auth.py                  # Login, logout, first-run wizard
│ ├── dashboard.py             # Dashboard KPIs & Chart.js telemetry
│ ├── vehicles.py              # Vehicle master CRUD & CSV export
│ ├── rfid_api.py              # Authenticated REST API for ESP32 & enrollment
│ ├── movements.py             # Gate Control, movement register, currently inside
│ ├── reports.py               # 11 Report types & multi-format exports
│ ├── devices.py               # Device management, API keys, ANPR test mode
│ └── settings.py              # Settings, users, audit logs, backup & restore
│
├── services/
│ ├── vehicle_service.py       # Vehicle logic & normalization
│ ├── rfid_service.py          # RFID lifecycle & enrollment buffer
│ ├── movement_service.py      # Authoritative gate movement decision engine
│ ├── report_service.py        # 11 Report datasets, CSV, openpyxl, reportlab
│ ├── audit_service.py         # System audit logger
│ └── anpr_service.py          # ANPR plate detection & verification
│
├── hardware/
│ ├── esp32/
│ │ └── rfid_gate.ino         # Production-ready Arduino C++ ESP32 firmware
│ ├── simulator.py             # Python hardware and RFID scanner simulator
│ └── device_protocol.md       # API specification & payload documentation
│
├── templates/                 # Modern Bootstrap 5 Jinja2 templates
│ ├── _scan_confirmation_modal.html # Direction-aware Scan Confirmation Modal
├── static/                    # CSS design system & JavaScript telemetry
├── tests/                     # Pytest automated test suite
├── backups/                   # MySQL Workbench compatible .sql snapshot storage
└── reports/                   # Exported report files
```

---

## 🔒 Security Best Practices
- Passwords hashed with `Werkzeug` secure hashing algorithms.
- Device communications authenticated using cryptographically secure per-device API keys.
- CSRF protection enabled on all operator web forms (REST hardware endpoints are authenticated via API keys).
- Idempotency tokens (`event_id`) prevent duplicate network packets from corrupting gate registers.
