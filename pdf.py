from flask import send_file
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import io
from mail import send_email

def generate_pdf(req_id):
    requisition = Requisition.query.get_or_404(req_id)
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)

    pdf.drawString(100, 800, f"KICD Requisition Form")
    pdf.drawString(100, 780, f"Office Name: {requisition.office_name}")
    pdf.drawString(100, 760, f"Requested By: {requisition.requested_by}")
    pdf.drawString(100, 740, f"User Email: {requisition.user_email}")

    y_position = 720
    pdf.drawString(100, y_position, "Items Requested:")
    for item in requisition.items:
        y_position -= 20
        pdf.drawString(120, y_position, f"{item.item_name} - {item.quantity} {item.unit}")

    pdf.drawString(100, y_position - 40, f"Approval Status: {requisition.status}")

    pdf.save()
    buffer.seek(0)

    # Email notification to the user
    user_subject = "Your KICD Requisition Submission"
    user_body = f"""
    Hello {requisition.requested_by},

    Your requisition has been successfully submitted.

    - Office: {requisition.office_name}
    - Status: {requisition.status}

    We will notify you once it's approved.

    Regards,
    KICD Requisition System
    """
    send_email(requisition, buffer, user_subject, user_body, [requisition.user_email])

    # Email notification to approvers
    approvers = ["manager@example.com", "store@example.com"]
    approver_subject = "New Requisition Submitted"
    approver_body = f"""
    Hello,

    A new requisition has been submitted.

    - Office: {requisition.office_name}
    - Requested By: {requisition.requested_by}
    - User Email: {requisition.user_email}
    - Status: {requisition.status}

    Please review and approve.

    Regards,
    KICD Requisition System
    """
    send_email(requisition, buffer, approver_subject, approver_body, approvers)

    return send_file(buffer, as_attachment=True, download_name="requisition.pdf", mimetype="application/pdf")
