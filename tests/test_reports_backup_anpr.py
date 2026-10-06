import os
import io
from datetime import datetime, date, timedelta
from database.db_init import db
from models.vehicle import Vehicle, AuthStatus, VehicleType
from models.movement import VehicleMovement, MovementStatus, GateDirection
from models.rfid import RFIDCard
from models.camera import CameraConfig, ANPREvent
from services.report_service import ReportService, ReportType
from services.anpr_service import ANPRService

def test_11_report_types_generation(app):
    with app.app_context():
        # Seed test data
        v = Vehicle(registration_number="MH12AB1234", vehicle_type=VehicleType.GYPSY, auth_status=AuthStatus.AUTHORIZED)
        db.session.add(v)
        db.session.flush()

        m = VehicleMovement(vehicle_id=v.id, status=MovementStatus.INSIDE, direction=GateDirection.ENTRY)
        db.session.add(m)
        db.session.commit()

        # Test each of the 11 report types
        for r_type in ReportType.TITLES.keys():
            headers, rows = ReportService.get_report_data(r_type)
            assert isinstance(headers, list)
            assert isinstance(rows, list)
            assert len(headers) > 0

def test_report_exports_csv_excel_pdf(app):
    with app.app_context():
        v = Vehicle(registration_number="MH12AB1234", vehicle_type=VehicleType.GYPSY)
        db.session.add(v)
        db.session.commit()

        headers, rows = ReportService.get_report_data(ReportType.DAILY_MOVEMENT)

        # 1. CSV
        csv_data = ReportService.export_csv(ReportType.DAILY_MOVEMENT, headers, rows)
        assert isinstance(csv_data, str)
        assert "Daily Vehicle Movement Report" in csv_data

        # 2. Excel
        excel_bytes = ReportService.export_excel(ReportType.DAILY_MOVEMENT, headers, rows)
        assert isinstance(excel_bytes, bytes)
        assert len(excel_bytes) > 0

        # 3. PDF
        pdf_bytes = ReportService.export_pdf(ReportType.DAILY_MOVEMENT, headers, rows)
        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes.startswith(b'%PDF')

def test_anpr_ocr_verification(app):
    with app.app_context():
        v = Vehicle(registration_number="MH12AB1234", auth_status=AuthStatus.AUTHORIZED)
        db.session.add(v)
        db.session.commit()

        # 1. High confidence match
        res_match = ANPRService.process_plate_detection("MH-12 AB 1234", 95.0)
        assert res_match["success"] is True
        assert res_match["status"] == "MATCH"
        assert res_match["captured_plate"] == "MH12AB1234"

        # 2. Unregistered plate
        res_mismatch = ANPRService.process_plate_detection("KA99ZZ0000", 90.0)
        assert res_mismatch["status"] == "MISMATCH"

        # 3. Low confidence plate
        res_low = ANPRService.process_plate_detection("MH12AB1234", 45.0)
        assert res_low["status"] == "LOW_CONFIDENCE"
