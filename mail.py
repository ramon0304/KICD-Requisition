def send_email(requisition, pdf_buffer, subject, body, recipients):
    recipients = ["manager@example.com", "store@example.com"]  # Update with actual recipients

    msg = Message(
        subject=f"New Requisition from {requisition.office_name}",
        recipients=recipients,
        body=f"""
        Hello,

        A new requisition has been submitted from {requisition.office_name}.

        - Requested By: {requisition.requested_by}
        - Approved By: {requisition.approvals[0].approver_name} ({requisition.approvals[0].role})
        - Status: {requisition.approvals[0].status}

        Please find the attached requisition form.

        Regards,
        KICD Requisition System
        """,
    )

    pdf_buffer.seek(0)
    msg.attach("Requisition_Form.pdf", "application/pdf", pdf_buffer.read())

    try:
        mail.send(msg)
        print("Email sent successfully.")
    except Exception as e:
        print(f"Error sending email: {e}")
