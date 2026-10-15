"""
============================================================================
 SMART RFID + ANPR VEHICLE GATE MANAGEMENT SYSTEM
 HARDWARE DEVICE & RFID SIMULATOR
============================================================================
This script simulates an ESP32-WROOM-32 microcontroller sending HTTP POST
scans, heartbeats, enrollment events, and ANPR camera detections to the Flask API.
"""

import sys
import time
import uuid
import json
import argparse
import requests

DEFAULT_SERVER_URL = "http://127.0.0.1:5000"
DEFAULT_DEVICE_ID = "GATE01"
DEFAULT_API_KEY = "dev_gate01_secret"

def print_header():
    print("=" * 65)
    print("  SMART VEHICLE GATE - HARDWARE & RFID SIMULATOR")
    print("=" * 65)

def send_scan(server_url, device_id, api_key, uid, direction="ENTRY", is_demo=True, alcohol_detected=False, alcohol_value=None):
    url = f"{server_url.rstrip('/')}/api/rfid/scan"
    event_id = f"sim-{uuid.uuid4().hex[:8]}"
    headers = {
        "Content-Type": "application/json",
        "X-Device-Id": device_id,
        "X-Api-Key": api_key
    }
    payload = {
        "uid": uid,
        "device_id": device_id,
        "direction": direction,
        "event_id": event_id,
        "is_demo": is_demo
    }
    if alcohol_detected:
        payload["alcohol_detected"] = True
        payload["alcohol_value"] = alcohol_value or 2450
    
    print(f"\n[HTTP POST] -> {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        start_t = time.time()
        resp = requests.post(url, json=payload, headers=headers, timeout=5)
        elapsed = int((time.time() - start_t) * 1000)
        
        print(f"[RESPONSE] HTTP {resp.status_code} ({elapsed}ms)")
        print(json.dumps(resp.json(), indent=2))
        return resp.json()
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Communication failed: {e}")
        return None

def send_heartbeat(server_url, device_id, api_key):
    url = f"{server_url.rstrip('/')}/api/device/heartbeat"
    headers = {
        "Content-Type": "application/json",
        "X-Device-Id": device_id,
        "X-Api-Key": api_key
    }
    payload = {
        "device_id": device_id,
        "api_key": api_key,
        "firmware_version": "v1.0.0-simulator"
    }
    
    print(f"\n[HEARTBEAT] -> {url}")
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=5)
        print(f"[RESPONSE] HTTP {resp.status_code}: {resp.text}")
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Heartbeat failed: {e}")

def send_enroll_scan(server_url, uid, device_id="SIMULATOR_READER"):
    url = f"{server_url.rstrip('/')}/api/rfid/enroll_scan"
    payload = {
        "uid": uid,
        "device_id": device_id
    }
    print(f"\n[ENROLL SCAN] -> {url}")
    try:
        resp = requests.post(url, json=payload, timeout=5)
        print(f"[RESPONSE] HTTP {resp.status_code}: {json.dumps(resp.json(), indent=2)}")
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Enrollment failed: {e}")

def send_alcohol_alert(server_url, device_id, api_key, alcohol_value=2450.0):
    url = f"{server_url.rstrip('/')}/api/device/alcohol_alert"
    headers = {
        "Content-Type": "application/json",
        "X-Device-Id": device_id,
        "X-Api-Key": api_key
    }
    payload = {
        "device_id": device_id,
        "alcohol_detected": True,
        "alcohol_value": alcohol_value
    }
    print(f"\n[TRIGGER LIVE ALCOHOL ALARM] -> {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=5)
        print(f"[RESPONSE] HTTP {resp.status_code}: {json.dumps(resp.json(), indent=2)}")
        return resp.json()
    except Exception as e:
        print(f"[ERROR] Live alarm trigger failed: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Vehicle Gate Hardware Simulator")
    parser.add_argument("--url", default=DEFAULT_SERVER_URL, help="Server Base URL (default: http://127.0.0.1:5000)")
    parser.add_argument("--device", default=DEFAULT_DEVICE_ID, help="Device ID (default: GATE_ENTRY_01)")
    parser.add_argument("--key", default=DEFAULT_API_KEY, help="Device API Key")
    parser.add_argument("--uid", help="Quick scan a specific RFID UID")
    parser.add_argument("--direction", default="ENTRY", choices=["ENTRY", "EXIT"], help="Gate direction")
    parser.add_argument("--heartbeat", action="store_true", help="Send a single heartbeat and exit")
    parser.add_argument("--alcohol", action="store_true", help="Simulate positive alcohol detection (MQ-3 sensor)")
    parser.add_argument("--alcohol-value", type=float, default=2450.0, help="Simulated alcohol sensor value")
    parser.add_argument("--alcohol-alert", action="store_true", help="Trigger real-time live alcohol sensor alert (tests auto-lockout)")
    args = parser.parse_args()

    if args.heartbeat:
        send_heartbeat(args.url, args.device, args.key)
        return

    if args.alcohol_alert:
        send_alcohol_alert(args.url, args.device, args.key, args.alcohol_value)
        return

    if args.uid:
        send_scan(args.url, args.device, args.key, args.uid, args.direction, alcohol_detected=args.alcohol, alcohol_value=args.alcohol_value)
        return

    print_header()
    print(f"Target Server : {args.url}")
    print(f"Device ID     : {args.device}")
    print("=" * 65)

    while True:
        print("\nSelect a Simulation Action:")
        print("  1) Send Authorized Scan (MH12AB1234 - UID: A37F291C) -> ENTRY")
        print("  2) Send Authorized Scan (MH12AB1234 - UID: A37F291C) -> EXIT")
        print("  3) Send Unknown RFID Scan (UID: UNKNOWN888)")
        print("  4) Send Blocked Vehicle Scan (HR26BK9999 - UID: CAFEBABE)")
        print("  5) Send Expired Auth Scan (UP32FF4321 - UID: DEADBEEF)")
        print("  6) Send Alcohol Detected Scan (MQ-3 Alert - Drunk Driver)")
        print("  7) 🚨 Trigger Live Alcohol Sensor Alarm (Auto-locks open modal!)")
        print("  8) Send Custom UID Scan")
        print("  9) Send Card Enrollment Scan (Capture new tag for assignment)")
        print("  10) Send Device Heartbeat")
        print("  11) Exit Simulator")
        
        choice = input("\nEnter choice (1-11): ").strip()

        if choice == "1":
            send_scan(args.url, args.device, args.key, "A37F291C", "ENTRY")
        elif choice == "2":
            send_scan(args.url, args.device, args.key, "A37F291C", "EXIT")
        elif choice == "3":
            send_scan(args.url, args.device, args.key, "UNKNOWN888", "ENTRY")
        elif choice == "4":
            send_scan(args.url, args.device, args.key, "CAFEBABE", "ENTRY")
        elif choice == "5":
            send_scan(args.url, args.device, args.key, "DEADBEEF", "ENTRY")
        elif choice == "6":
            print("\n[TEST] Simulating driver breath test with MQ-3 Alcohol Sensor...")
            send_scan(args.url, args.device, args.key, "A37F291C", "ENTRY", alcohol_detected=True, alcohol_value=2450.0)
        elif choice == "7":
            print("\n🚨 Simulating real-time MQ-3 Alcohol Sensor buzzer alarm...")
            send_alcohol_alert(args.url, args.device, args.key, 2550.0)
        elif choice == "8":
            custom_uid = input("Enter RFID UID (hex): ").strip()
            custom_dir = input("Enter Direction (ENTRY/EXIT) [ENTRY]: ").strip().upper() or "ENTRY"
            is_alc = input("Simulate Alcohol Detected? (y/N): ").strip().lower() == 'y'
            send_scan(args.url, args.device, args.key, custom_uid, custom_dir, alcohol_detected=is_alc, alcohol_value=2300.0 if is_alc else None)
        elif choice == "9":
            enroll_uid = input("Enter new tag UID to enroll (e.g. 98A1B2C3): ").strip() or "98A1B2C3"
            send_enroll_scan(args.url, enroll_uid, args.device)
        elif choice == "10":
            send_heartbeat(args.url, args.device, args.key)
        elif choice == "11":
            print("\nExiting simulator. Goodbye!")
            sys.exit(0)
        else:
            print("Invalid selection. Try again.")

if __name__ == "__main__":
    main()
