# Smart Vehicle Gate - Hardware Communication Protocol & API Specification

This document details the REST API specification, JSON payloads, authentication schemes, idempotency semantics, and network configuration for microcontrollers (ESP32-WROOM-32), RFID readers (RC522), and edge ANPR cameras connecting to the Flask backend.

---

## 1. Authentication & Security Model

All hardware edge devices communicate with the Flask server using **per-device API keys**.
The server verifies credentials on every request and maintains device health metrics.

### Authentication Headers or Payload
Clients can authenticate using HTTP request headers or by embedding credentials directly in the JSON body:

```http
X-Device-Id: GATE_ENTRY_01
X-Api-Key: dev_dGVzdF9rZXlfZXhhbXBsZV8xMjM
Content-Type: application/json
```

> **Security Note:** In a local network development environment, communication occurs over plain HTTP. For production deployments beyond an isolated, trusted VLAN, always deploy behind an HTTPS reverse proxy (e.g., Nginx with TLS) to encrypt credentials in transit.

---

## 2. API Endpoints

### 2.1 Vehicle Gate RFID Scan
- **Endpoint:** `POST /api/rfid/scan`
- **Purpose:** Primary endpoint invoked when an RFID tag is detected at an entry or exit gate.

#### Request JSON
```json
{
  "uid": "A37F291C",
  "device_id": "GATE_ENTRY_01",
  "direction": "ENTRY",
  "event_id": "GATE_ENTRY_01-1727958000-A37F291C",
  "is_demo": false
}
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `uid` | String | Yes | Hexadecimal RFID tag UID (normalized, uppercase). |
| `device_id` | String | Yes | Unique registered identifier of the scanning device. |
| `direction` | String | No | `"ENTRY"` or `"EXIT"`. If omitted, server resolves using device configuration. |
| `event_id` | String | Yes | Unique UUID / timestamp for idempotency. |
| `is_demo` | Boolean | No | Mark as test/simulated scan. |

#### Successful Entry Response (`HTTP 200 OK`)
```json
{
  "success": true,
  "decision": "ENTRY_ALLOWED",
  "message": "Vehicle authorized. Entry permitted.",
  "vehicle_number": "MH12AB1234",
  "vehicle_type": "Car",
  "driver_name": "Rajesh Sharma",
  "movement_status": "INSIDE",
  "event_id": "GATE_ENTRY_01-1727958000-A37F291C",
  "timestamp": "2026-10-03T12:35:00.123456"
}
```

#### Successful Exit Response (`HTTP 200 OK`)
```json
{
  "success": true,
  "decision": "EXIT_RECORDED",
  "message": "Vehicle exit successful.",
  "vehicle_number": "MH12AB1234",
  "vehicle_type": "Car",
  "driver_name": "Rajesh Sharma",
  "movement_status": "OUTSIDE",
  "duration": "2h 15m 30s",
  "event_id": "GATE_EXIT_01-1727966000-A37F291C",
  "timestamp": "2026-10-03T14:50:30.123456"
}
```

#### Denied / Exception Responses
- **Unregistered RFID (`HTTP 404 Not Found`):**
  ```json
  {
    "success": false,
    "decision": "ENTRY_DENIED",
    "reason": "UNKNOWN_RFID",
    "message": "RFID tag is not registered in the system."
  }
  ```
- **Blocked / Expired Card (`HTTP 403 Forbidden`):**
  ```json
  {
    "success": false,
    "decision": "ENTRY_DENIED",
    "reason": "BLOCKED_CARD",
    "message": "RFID Card is BLOCKED."
  }
  ```
- **Duplicate Entry / Already Inside (`HTTP 409 Conflict`):**
  ```json
  {
    "success": false,
    "decision": "ENTRY_DENIED",
    "reason": "DUPLICATE_ENTRY",
    "message": "Vehicle is already marked INSIDE the premises.",
    "vehicle_number": "MH12AB1234"
  }
  ```
- **Exit Without Active Entry (`HTTP 409 Conflict`):**
  ```json
  {
    "success": false,
    "decision": "EXIT_EXCEPTION",
    "reason": "NO_ACTIVE_ENTRY",
    "message": "No active entry record found for this vehicle. Exit logged as exception.",
    "vehicle_number": "MH12AB1234"
  }
  ```

---

### 2.2 Device Heartbeat
- **Endpoint:** `POST /api/device/heartbeat`
- **Purpose:** Periodic ping from ESP32 to maintain `ONLINE` status and report client IP.

#### Request JSON
```json
{
  "device_id": "GATE_ENTRY_01",
  "api_key": "YOUR_DEVICE_API_KEY",
  "firmware_version": "v1.0.0"
}
```

#### Response (`HTTP 200 OK`)
```json
{
  "success": true,
  "message": "Heartbeat acknowledged",
  "device_id": "GATE_ENTRY_01",
  "status": "ONLINE",
  "server_time": "2026-10-03T12:35:00.000000"
}
```

---

### 2.3 New RFID Card Enrollment
- **Endpoint:** `POST /api/rfid/enroll_scan`
- **Purpose:** When the system is in card enrollment mode, newly scanned tags are sent here and cached for web assignment.

#### Request JSON
```json
{
  "uid": "98A1B2C3",
  "device_id": "GATE_ENTRY_01"
}
```

---

## 3. Idempotency & Repeat Protection

1. **Hardware Cooldown:** ESP32 enforces a `SCAN_COOLDOWN_MS` (default 3000ms) to ignore continuous reads of the same card sitting on the reader.
2. **Server Idempotency:** The server records `event_id` in `device_events`. If a duplicate network packet arrives with an identical `event_id`, the previous authorization outcome is returned immediately without creating duplicate database movement transactions.

---

## 4. Local Network & Firewall Setup

1. **Find Host PC IPv4 Address (Windows):**
   ```powershell
   ipconfig
   ```
   Look for `IPv4 Address` under your active Wi-Fi / Ethernet adapter (e.g. `192.168.1.100`).
2. **Windows Defender Firewall Rule:**
   Allow inbound traffic on port 5000:
   ```powershell
   netsh advfirewall firewall add rule name="Flask Gate Server" dir=in action=allow protocol=TCP localport=5000
   ```
3. **Verify ESP32 Connectivity:**
   Test with curl from another machine on the same Wi-Fi:
   ```bash
   curl http://192.168.1.100:5000/api/device/status
   ```
