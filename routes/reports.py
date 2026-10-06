from datetime import datetime, date
from flask import Blueprint, render_template, request, Response, flash, redirect, url_for
from flask_login import login_required
from services.report_service import ReportService, ReportType

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/reports')
@login_required
def view_reports():
    report_type = request.args.get('type', ReportType.DAILY_MOVEMENT)
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    vehicle_number = request.args.get('vehicle_number', '').strip()
    status = request.args.get('status', '').strip()

    headers, rows = ReportService.get_report_data(
        report_type=report_type,
        start_date=start_date,
        end_date=end_date,
        vehicle_number=vehicle_number,
        status=status
    )

    report_title = ReportType.TITLES.get(report_type, 'Gate Management Report')

    return render_template(
        'reports.html',
        report_type=report_type,
        report_title=report_title,
        report_titles=ReportType.TITLES,
        headers=headers,
        rows=rows,
        start_date=start_date,
        end_date=end_date,
        vehicle_number=vehicle_number,
        status=status,
        now=datetime.utcnow()
    )

@reports_bp.route('/reports/export/<export_format>')
@login_required
def export_report(export_format):
    report_type = request.args.get('type', ReportType.DAILY_MOVEMENT)
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    vehicle_number = request.args.get('vehicle_number', '').strip()
    status = request.args.get('status', '').strip()

    headers, rows = ReportService.get_report_data(
        report_type=report_type,
        start_date=start_date,
        end_date=end_date,
        vehicle_number=vehicle_number,
        status=status
    )

    timestamp_str = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    filename_base = f"{report_type}_{timestamp_str}"

    if export_format == 'csv':
        csv_data = ReportService.export_csv(report_type, headers, rows)
        response = Response(csv_data, mimetype='text/csv')
        response.headers['Content-Disposition'] = f'attachment; filename={filename_base}.csv'
        return response

    elif export_format == 'excel':
        excel_data = ReportService.export_excel(report_type, headers, rows)
        response = Response(
            excel_data,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response.headers['Content-Disposition'] = f'attachment; filename={filename_base}.xlsx'
        return response

    elif export_format == 'pdf':
        pdf_data = ReportService.export_pdf(report_type, headers, rows)
        response = Response(pdf_data, mimetype='application/pdf')
        response.headers['Content-Disposition'] = f'attachment; filename={filename_base}.pdf'
        return response

    flash('Invalid export format requested.', 'danger')
    return redirect(url_for('reports.view_reports', type=report_type))
