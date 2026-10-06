import io
import csv
from datetime import datetime, date, timedelta
from database.db_init import db
from models.vehicle import Vehicle, AuthStatus, normalize_plate
from models.movement import VehicleMovement, MovementStatus, GateDirection
from models.denied_attempt import DeniedAttempt
from models.device import Device, DeviceStatus
from models.rfid import RFIDCard
from models.camera import ANPREvent, CameraConfig
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

class ReportType:
    DAILY_MOVEMENT = 'daily_movement'
    DATE_RANGE_MOVEMENT = 'date_range_movement'
    VEHICLE_HISTORY = 'vehicle_history'
    CURRENTLY_INSIDE = 'currently_inside'
    UNAUTHORIZED_ATTEMPTS = 'unauthorized_attempts'
    EXPIRED_AUTH = 'expired_auth'
    BLOCKED_VEHICLES = 'blocked_vehicles'
    MANUAL_OVERRIDES = 'manual_overrides'
    DEVICE_HEALTH = 'device_health'
    ANPR_VERIFICATION = 'anpr_verification'
    MONTHLY_SUMMARY = 'monthly_summary'

    TITLES = {
        DAILY_MOVEMENT: 'Daily Vehicle Movement Report',
        DATE_RANGE_MOVEMENT: 'Date Range Movement Report',
        VEHICLE_HISTORY: 'Vehicle-wise Movement History',
        CURRENTLY_INSIDE: 'Vehicles Currently Inside Premises',
        UNAUTHORIZED_ATTEMPTS: 'Unauthorized & Denied RFID Attempts',
        EXPIRED_AUTH: 'Expired Vehicle Authorizations',
        BLOCKED_VEHICLES: 'Blocked Vehicles & Cards Report',
        MANUAL_OVERRIDES: 'Manual Gate Overrides Log',
        DEVICE_HEALTH: 'Device Status & Health Report',
        ANPR_VERIFICATION: 'ANPR License Plate Verification Report',
        MONTHLY_SUMMARY: 'Monthly Movement Summary'
    }

class ReportService:
    @staticmethod
    def get_report_data(report_type: str, start_date=None, end_date=None, vehicle_number=None, status=None, is_demo=None):
        """
        Generate datasets (headers and rows) for each of the 11 report types.
        """
        # Parse dates
        if isinstance(start_date, str) and start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            except ValueError:
                start_date = None
        if isinstance(end_date, str) and end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                end_date = None

        today = date.today()

        # 1. DAILY MOVEMENT
        if report_type == ReportType.DAILY_MOVEMENT:
            target_date = start_date or today
            start_dt = datetime.combine(target_date, datetime.min.time())
            end_dt = datetime.combine(target_date, datetime.max.time())
            
            query = VehicleMovement.query.filter(VehicleMovement.entry_time.between(start_dt, end_dt))
            if is_demo is not None:
                query = query.filter_by(is_demo=is_demo)
            movements = query.order_by(VehicleMovement.entry_time.desc()).all()

            headers = ['Sr No', 'Date', 'Vehicle No', 'Type', 'Driver', 'RFID UID', 'Entry Time', 'Exit Time', 'Duration', 'Gate/Device', 'Status']
            rows = []
            for idx, m in enumerate(movements, 1):
                rows.append([
                    idx,
                    m.entry_time.strftime('%Y-%m-%d'),
                    m.vehicle.registration_number if m.vehicle else 'N/A',
                    m.vehicle.vehicle_type if m.vehicle else 'N/A',
                    m.vehicle.driver_name if m.vehicle and m.vehicle.driver_name else 'N/A',
                    m.rfid_card.uid if m.rfid_card else 'N/A',
                    m.entry_time.strftime('%H:%M:%S'),
                    m.exit_time.strftime('%H:%M:%S') if m.exit_time else '-',
                    m.formatted_duration,
                    m.entry_device.device_name if m.entry_device else 'System',
                    m.status
                ])
            return headers, rows

        # 2. DATE RANGE MOVEMENT
        elif report_type == ReportType.DATE_RANGE_MOVEMENT:
            start_dt = datetime.combine(start_date or (today - timedelta(days=7)), datetime.min.time())
            end_dt = datetime.combine(end_date or today, datetime.max.time())
            
            query = VehicleMovement.query.filter(VehicleMovement.entry_time.between(start_dt, end_dt))
            if is_demo is not None:
                query = query.filter_by(is_demo=is_demo)
            if status:
                query = query.filter_by(status=status)
            movements = query.order_by(VehicleMovement.entry_time.desc()).all()

            headers = ['Sr No', 'Date', 'Vehicle No', 'Type', 'Driver', 'RFID UID', 'Entry Time', 'Exit Time', 'Duration', 'Direction', 'Status']
            rows = []
            for idx, m in enumerate(movements, 1):
                rows.append([
                    idx,
                    m.entry_time.strftime('%Y-%m-%d'),
                    m.vehicle.registration_number if m.vehicle else 'N/A',
                    m.vehicle.vehicle_type if m.vehicle else 'N/A',
                    m.vehicle.driver_name if m.vehicle and m.vehicle.driver_name else 'N/A',
                    m.rfid_card.uid if m.rfid_card else 'N/A',
                    m.entry_time.strftime('%H:%M:%S'),
                    m.exit_time.strftime('%H:%M:%S') if m.exit_time else '-',
                    m.formatted_duration,
                    m.direction,
                    m.status
                ])
            return headers, rows

        # 3. VEHICLE-WISE HISTORY
        elif report_type == ReportType.VEHICLE_HISTORY:
            norm_p = normalize_plate(vehicle_number) if vehicle_number else None
            query = VehicleMovement.query.join(Vehicle)
            if norm_p:
                query = query.filter(Vehicle.registration_number.ilike(f"%{norm_p}%"))
            if is_demo is not None:
                query = query.filter(VehicleMovement.is_demo == is_demo)
            movements = query.order_by(VehicleMovement.entry_time.desc()).limit(200).all()

            headers = ['Sr No', 'Vehicle No', 'Type', 'Driver', 'Entry Time', 'Exit Time', 'Duration', 'Entry Device', 'Exit Device', 'Status']
            rows = []
            for idx, m in enumerate(movements, 1):
                rows.append([
                    idx,
                    m.vehicle.registration_number if m.vehicle else 'N/A',
                    m.vehicle.vehicle_type if m.vehicle else 'N/A',
                    m.vehicle.driver_name if m.vehicle and m.vehicle.driver_name else 'N/A',
                    m.entry_time.strftime('%Y-%m-%d %H:%M:%S'),
                    m.exit_time.strftime('%Y-%m-%d %H:%M:%S') if m.exit_time else 'Still Inside',
                    m.formatted_duration,
                    m.entry_device.device_name if m.entry_device else 'System',
                    m.exit_device.device_name if m.exit_device else '-',
                    m.status
                ])
            return headers, rows

        # 4. CURRENTLY INSIDE
        elif report_type == ReportType.CURRENTLY_INSIDE:
            query = VehicleMovement.query.filter_by(status=MovementStatus.INSIDE)
            if is_demo is not None:
                query = query.filter_by(is_demo=is_demo)
            movements = query.order_by(VehicleMovement.entry_time.asc()).all()

            headers = ['Sr No', 'Vehicle No', 'Type', 'Driver', 'Mobile', 'RFID UID', 'Entry Date & Time', 'Time Spent', 'Entry Gate']
            rows = []
            for idx, m in enumerate(movements, 1):
                rows.append([
                    idx,
                    m.vehicle.registration_number if m.vehicle else 'N/A',
                    m.vehicle.vehicle_type if m.vehicle else 'N/A',
                    m.vehicle.driver_name if m.vehicle and m.vehicle.driver_name else 'N/A',
                    m.vehicle.mobile_number if m.vehicle and m.vehicle.mobile_number else 'N/A',
                    m.rfid_card.uid if m.rfid_card else 'N/A',
                    m.entry_time.strftime('%Y-%m-%d %H:%M:%S'),
                    m.formatted_duration,
                    m.entry_device.device_name if m.entry_device else 'Main Gate'
                ])
            return headers, rows

        # 5. UNAUTHORIZED RFID ATTEMPTS
        elif report_type == ReportType.UNAUTHORIZED_ATTEMPTS:
            query = DeniedAttempt.query
            if is_demo is not None:
                query = query.filter_by(is_demo=is_demo)
            if start_date:
                query = query.filter(DeniedAttempt.timestamp >= datetime.combine(start_date, datetime.min.time()))
            if end_date:
                query = query.filter(DeniedAttempt.timestamp <= datetime.combine(end_date, datetime.max.time()))
            attempts = query.order_by(DeniedAttempt.timestamp.desc()).all()

            headers = ['Sr No', 'Timestamp', 'RFID UID', 'Vehicle No', 'Gate/Device', 'Direction', 'Reason', 'Remarks']
            rows = []
            for idx, a in enumerate(attempts, 1):
                rows.append([
                    idx,
                    a.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    a.rfid_uid or 'Unknown',
                    a.vehicle_number or 'N/A',
                    a.device.device_name if a.device else 'System',
                    a.direction,
                    a.reason,
                    a.remarks or ''
                ])
            return headers, rows

        # 6. EXPIRED AUTHORIZATION
        elif report_type == ReportType.EXPIRED_AUTH:
            query = Vehicle.query.filter_by(auth_status=AuthStatus.EXPIRED)
            if is_demo is not None:
                query = query.filter_by(is_demo=is_demo)
            vehicles = query.all()

            headers = ['Sr No', 'BA Number', 'Type', 'Custodian', 'Army No', 'Mobile', 'Auth Status', 'Date of Issue']
            rows = []
            for idx, v in enumerate(vehicles, 1):
                rows.append([
                    idx,
                    v.registration_number,
                    v.vehicle_type,
                    v.custodian_name or 'N/A',
                    v.armynumber or 'N/A',
                    v.mobile_number or 'N/A',
                    v.auth_status,
                    v.issue_date.strftime('%Y-%m-%d') if v.issue_date else 'N/A'
                ])
            return headers, rows

        # 7. BLOCKED VEHICLES
        elif report_type == ReportType.BLOCKED_VEHICLES:
            query = Vehicle.query.filter_by(auth_status=AuthStatus.BLOCKED)
            if is_demo is not None:
                query = query.filter_by(is_demo=is_demo)
            vehicles = query.all()

            headers = ['Sr No', 'BA Number', 'Type', 'Custodian', 'Army No', 'Mobile', 'Status', 'Blocked Date']
            rows = []
            for idx, v in enumerate(vehicles, 1):
                rows.append([
                    idx,
                    v.registration_number,
                    v.vehicle_type,
                    v.custodian_name or 'N/A',
                    v.armynumber or 'N/A',
                    v.mobile_number or 'N/A',
                    v.auth_status,
                    v.updated_at.strftime('%Y-%m-%d %H:%M:%S')
                ])
            return headers, rows

        # 8. MANUAL OVERRIDES
        elif report_type == ReportType.MANUAL_OVERRIDES:
            query = VehicleMovement.query.filter_by(is_manual=True)
            if is_demo is not None:
                query = query.filter_by(is_demo=is_demo)
            movements = query.order_by(VehicleMovement.entry_time.desc()).all()

            headers = ['Sr No', 'Date & Time', 'Vehicle No', 'Direction', 'Operator', 'Mandatory Reason', 'Status', 'Remarks']
            rows = []
            for idx, m in enumerate(movements, 1):
                rows.append([
                    idx,
                    m.entry_time.strftime('%Y-%m-%d %H:%M:%S'),
                    m.vehicle.registration_number if m.vehicle else 'N/A',
                    m.direction,
                    m.entry_operator.username if m.entry_operator else (m.exit_operator.username if m.exit_operator else 'Operator'),
                    m.manual_reason or 'No reason provided',
                    m.status,
                    m.remarks or ''
                ])
            return headers, rows

        # 9. DEVICE HEALTH
        elif report_type == ReportType.DEVICE_HEALTH:
            devices = Device.query.order_by(Device.created_at.desc()).all()
            headers = ['Sr No', 'Device ID', 'Device Name', 'Type', 'Gate', 'IP Address', 'Health Status', 'Last Seen', 'Last Event']
            rows = []
            for idx, d in enumerate(devices, 1):
                rows.append([
                    idx,
                    d.device_id,
                    d.device_name,
                    d.device_type,
                    d.gate,
                    d.ip_address or 'Not recorded',
                    'ONLINE' if d.is_online() else d.status,
                    d.last_seen.strftime('%Y-%m-%d %H:%M:%S') if d.last_seen else 'Never',
                    d.last_event or 'None'
                ])
            return headers, rows

        # 10. ANPR VERIFICATION
        elif report_type == ReportType.ANPR_VERIFICATION:
            query = ANPREvent.query
            if is_demo is not None:
                query = query.filter_by(is_demo=is_demo)
            events = query.order_by(ANPREvent.timestamp.desc()).all()

            headers = ['Sr No', 'Timestamp', 'Captured Plate', 'Confidence', 'Matched Vehicle', 'RFID Ref', 'Verification Status']
            rows = []
            for idx, e in enumerate(events, 1):
                rows.append([
                    idx,
                    e.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    e.captured_plate,
                    f"{e.confidence:.1f}%",
                    e.matched_vehicle.registration_number if e.matched_vehicle else 'No Match',
                    e.rfid_event_id or '-',
                    e.verification_status
                ])
            return headers, rows

        # 11. MONTHLY MOVEMENT SUMMARY
        elif report_type == ReportType.MONTHLY_SUMMARY:
            # Summary grouped by day for the current month
            start_month = today.replace(day=1)
            start_dt = datetime.combine(start_month, datetime.min.time())
            
            query = VehicleMovement.query.filter(VehicleMovement.entry_time >= start_dt)
            if is_demo is not None:
                query = query.filter_by(is_demo=is_demo)
            movements = query.all()

            daily_in = {}
            daily_out = {}
            for m in movements:
                d_str = m.entry_time.strftime('%Y-%m-%d')
                daily_in[d_str] = daily_in.get(d_str, 0) + 1
                if m.exit_time:
                    out_d_str = m.exit_time.strftime('%Y-%m-%d')
                    daily_out[out_d_str] = daily_out.get(out_d_str, 0) + 1

            all_days = sorted(set(list(daily_in.keys()) + list(daily_out.keys())), reverse=True)
            headers = ['Sr No', 'Date', 'Total Entries (IN)', 'Total Exits (OUT)', 'Net Active (INSIDE)']
            rows = []
            for idx, d_str in enumerate(all_days, 1):
                entries = daily_in.get(d_str, 0)
                exits = daily_out.get(d_str, 0)
                rows.append([idx, d_str, entries, exits, max(0, entries - exits)])
            return headers, rows

        # Fallback default
        return ['Sr No', 'Detail'], []

    @staticmethod
    def export_csv(report_type: str, headers, rows):
        """Generate CSV string."""
        output = io.StringIO()
        writer = csv.writer(output)
        title = ReportType.TITLES.get(report_type, 'Vehicle Gate Report')
        writer.writerow([title])
        writer.writerow([f"Generated at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"])
        writer.writerow([])
        writer.writerow(headers)
        for r in rows:
            writer.writerow(r)
        return output.getvalue()

    @staticmethod
    def export_excel(report_type: str, headers, rows):
        """Generate formatted Excel spreadsheet bytes."""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Report"
        
        # Styles
        title_font = Font(name='Segoe UI', size=16, bold=True, color='1E293B')
        meta_font = Font(name='Segoe UI', size=10, italic=True, color='64748B')
        header_font = Font(name='Segoe UI', size=11, bold=True, color='FFFFFF')
        header_fill = PatternFill(start_color='1E3A8A', end_color='1E3A8A', fill_type='solid') # Navy
        cell_font = Font(name='Segoe UI', size=10)
        thin_border = Border(
            left=Side(style='thin', color='E2E8F0'),
            right=Side(style='thin', color='E2E8F0'),
            top=Side(style='thin', color='E2E8F0'),
            bottom=Side(style='thin', color='E2E8F0')
        )
        
        # Title & Meta
        title = ReportType.TITLES.get(report_type, 'Vehicle Gate Report')
        ws.merge_cells('A1:G1')
        ws['A1'] = title
        ws['A1'].font = title_font
        
        ws.merge_cells('A2:G2')
        ws['A2'] = f"Generated at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')} | Smart RFID Gate Management System"
        ws['A2'].font = meta_font
        
        # Headers (Row 4)
        for col_idx, h in enumerate(headers, 1):
            cell = ws.cell(row=4, column=col_idx, value=h)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.border = thin_border
            
        # Data rows
        for row_idx, r_data in enumerate(rows, 5):
            for col_idx, val in enumerate(r_data, 1):
                cell = ws.cell(row=row_idx, column=col_idx, value=str(val) if val is not None else "")
                cell.font = cell_font
                cell.border = thin_border
                if col_idx == 1:
                    cell.alignment = Alignment(horizontal='center')
                    
        # Auto column width
        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = openpyxl.utils.get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 4, 12)
            
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return output.getvalue()

    @staticmethod
    def export_pdf(report_type: str, headers, rows):
        """Generate PDF document bytes using ReportLab."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(letter),
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=30
        )
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=18,
            leading=22,
            textColor=colors.HexColor('#0F172A')
        )
        meta_style = ParagraphStyle(
            'ReportMeta',
            parent=styles['Normal'],
            fontName='Helvetica-Oblique',
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#64748B')
        )
        
        elements = []
        title = ReportType.TITLES.get(report_type, 'Vehicle Gate Report')
        elements.append(Paragraph(title, title_style))
        elements.append(Paragraph(f"Generated at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')} | Smart RFID + ANPR Gate System", meta_style))
        elements.append(Spacer(1, 15))
        
        # Table data
        table_data = [headers]
        for row in rows:
            # Wrap strings nicely
            table_data.append([str(item) if item is not None else "" for item in row])
            
        # Style the table
        pdf_table = Table(table_data, repeatRows=1)
        pdf_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E3A8A')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('TOPPADDING', (0, 0), (-1, 0), 6),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
            ('TOPPADDING', (0, 1), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        ]))
        elements.append(pdf_table)
        
        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
