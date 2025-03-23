from flask import (
    Flask,
    render_template,
    redirect,
    flash,
    url_for,
    session
)

from datetime import timedelta
from sqlalchemy.exc import (
    IntegrityError,
    DataError,
    DatabaseError,
    InterfaceError,
    InvalidRequestError,
)
from werkzeug.routing import BuildError


from flask_bcrypt import Bcrypt,generate_password_hash, check_password_hash

from flask_login import (
    UserMixin,
    login_user,
    LoginManager,
    current_user,
    logout_user,
    login_required,
)

from app import create_app,db,login_manager,bcrypt
from models import User
from forms import login_form,register_form,OfficeDetailsForm,ItemsForm,ApprovalForm
from pdf import generate_pdf

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

app = create_app()

@app.before_request
def session_handler():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=1)

@app.route("/", methods=("GET", "POST"), strict_slashes=False)
def index():
    return render_template("index.html",title="Home")


@app.route("/login/", methods=("GET", "POST"), strict_slashes=False)
def login():
    form = login_form()

    if form.validate_on_submit():
        try:
            user = User.query.filter_by(email=form.email.data).first()
            if check_password_hash(user.pwd, form.pwd.data):
                login_user(user)
                return redirect(url_for('index'))
            else:
                flash("Invalid Username or password!", "danger")
        except Exception as e:
            flash(e, "danger")

    return render_template("auth.html",
        form=form,
        text="Login",
        title="Login",
        btn_action="Login"
        )



# Register route
@app.route("/register/", methods=("GET", "POST"), strict_slashes=False)
def register():
    form = register_form()
    if form.validate_on_submit():
        try:
            email = form.email.data
            pwd = form.pwd.data
            username = form.username.data
            
            newuser = User(
                username=username,
                email=email,
                pwd=bcrypt.generate_password_hash(pwd),
            )
    
            db.session.add(newuser)
            db.session.commit()
            flash(f"Account Succesfully created", "success")
            return redirect(url_for("login"))

        except InvalidRequestError:
            db.session.rollback()
            flash(f"Something went wrong!", "danger")
        except IntegrityError:
            db.session.rollback()
            flash(f"User already exists!.", "warning")
        except DataError:
            db.session.rollback()
            flash(f"Invalid Entry", "warning")
        except InterfaceError:
            db.session.rollback()
            flash(f"Error connecting to the database", "danger")
        except DatabaseError:
            db.session.rollback()
            flash(f"Error connecting to the database", "danger")
        except BuildError:
            db.session.rollback()
            flash(f"An error occured !", "danger")
    return render_template("auth.html",
        form=form,
        text="Create account",
        title="Register",
        btn_action="Register account"
        )

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Routes for Step-wise Form Handling
@app.route('/step1', methods=['GET', 'POST'])
def step1():
    form = OfficeDetailsForm()
    if form.validate_on_submit():
        session['office_details'] = {
            'office_name': form.office_name.data,
            'requested_by': form.requested_by.data
        }
        return redirect(url_for('step2'))
    return render_template('step1.html', form=form)

@app.route('/step2', methods=['GET', 'POST'])
def step2():
    form = ItemsForm()
    if form.validate_on_submit():
        session['items'] = [{'item_name': item.item_name.data, 'unit': item.unit.data, 'quantity': item.quantity.data, 'remarks': item.remarks.data} for item in form.items]
        return redirect(url_for('step3'))
    return render_template('step2.html', form=form)

@app.route('/step3', methods=['GET', 'POST'])
def step3():
    form = ApprovalForm()
    if form.validate_on_submit():
        session['approval'] = {
            'approver_name': form.approver_name.data,
            'role': form.role.data,
            'status': form.status.data
        }

        # Save data to database
        requisition = Requisition(
            office_name=session['office_details']['office_name'],
            requested_by=session['office_details']['requested_by']
        )
        db.session.add(requisition)
        db.session.commit()

        for item in session['items']:
            db.session.add(RequisitionItems(
                requisition_id=requisition.id,
                item_name=item['item_name'],
                unit=item['unit'],
                quantity=item['quantity'],
                remarks=item['remarks']
            ))

        db.session.add(Approval(
            requisition_id=requisition.id,
            approver_name=session['approval']['approver_name'],
            role=session['approval']['role'],
            status=session['approval']['status']
        ))

        db.session.commit()

        return redirect(url_for('generate_pdf', req_id=requisition.id))
    return render_template('step3.html', form=form)

# PDF Generation Route
@app.route('/pdf/<int:req_id>')
def create_pdf(req_id):
    generate_pdf(req_id)
    return redirect(url_for('index'))

@app.route('/update_status/<int:req_id>/<status>', methods=['POST'])
def update_status(req_id, status):
    requisition = Requisition.query.get_or_404(req_id)
    requisition.status = status
    db.session.commit()

    # Notify user about status update
    subject = "Requisition Status Update"
    body = f"""
    Hello {requisition.requested_by},

    Your requisition status has been updated.

    - Office: {requisition.office_name}
    - Status: {status}

    Thank you for using the KICD Requisition System.

    Regards,
    KICD Requisition System
    """
    send_email(requisition, io.BytesIO(), subject, body, [requisition.user_email])

    return jsonify({'message': 'Status updated and email sent.'}), 200

def send_email(requisition, pdf_buffer, subject, body, recipients):
    msg = Message(subject, recipients=recipients)
    msg.body = body
    pdf_buffer.seek(0)
    msg.attach("requisition.pdf", "application/pdf", pdf_buffer.read())
    try:
        mail.send(msg)
        print("Email sent successfully.")
    except Exception as e:
        print(f"Error sending email: {e}")

# Route to handle the final submission of the requisition form
@app.route('/submit-requisition', methods=['POST'])
def submit_requisition():
    # Ensure required session data exists
    if not all(k in session for k in ('office_details', 'items', 'approval')):
        flash("Session expired. Please restart your requisition form.", "danger")
        return redirect(url_for('step1'))
    
    # Create the Requisition record using session data
    requisition = Requisition(
        office_name=session['office_details']['office_name'],
        requested_by=session['office_details']['requested_by']
        # If you store user_email in your model, add it here.
    )
    db.session.add(requisition)
    db.session.commit()

    # Save each item into RequisitionItems
    for item in session['items']:
        db.session.add(RequisitionItems(
            requisition_id=requisition.id,
            item_name=item['item_name'],
            unit=item['unit'],
            quantity=item['quantity'],
            remarks=item['remarks']
        ))
    
    # Save the approval details into Approval
    db.session.add(Approval(
        requisition_id=requisition.id,
        approver_name=session['approval']['approver_name'],
        role=session['approval']['role'],
        status=session['approval']['status']
    ))
    db.session.commit()

    # Generate the PDF for this requisition.
    # Our generate_pdf function is expected to create a PDF file (e.g., "pdfs/requisition_<id>.pdf")
    generate_pdf(requisition.id)
    
    # Load the generated PDF into a BytesIO buffer for email attachment.
    pdf_path = f"pdfs/requisition_{requisition.id}.pdf"
    if not os.path.exists(pdf_path):
        flash("Failed to generate PDF.", "danger")
        return redirect(url_for('step3'))
    
    pdf_buffer = io.BytesIO()
    with open(pdf_path, "rb") as f:
        pdf_buffer.write(f.read())
    pdf_buffer.seek(0)
    
    # Prepare email content
    subject = "KICD Requisition Submitted"
    body = f"""Hello {requisition.requested_by},

Your requisition has been submitted successfully.
Please find the attached PDF for your records.

Thank you for using the KICD Requisition System.
"""
    # For example, you might send the email to the requester and/or approvers.
    # Here, we'll send it to the requester's email if you store it in your model or session.
    recipient_list = [session.get('office_details').get('requested_by')]  # Replace with actual email retrieval
    # If your model includes user_email, you can do: [requisition.user_email]
    
    # Send the email
    send_email(requisition, pdf_buffer, subject, body, recipient_list)
    
    # Optionally, remove the temporary PDF file if not needed
    try:
        os.remove(pdf_path)
    except Exception as e:
        print(f"Could not remove PDF file: {e}")
    
    # Clear the session data related to the form
    session.pop('office_details', None)
    session.pop('items', None)
    session.pop('approval', None)
    
    # Redirect to a thank-you page
    return redirect(url_for('thank_you'))

# Thank-you page route (if not already defined)
@app.route('/thank-you')
def thank_you():
    return render_template("thank_you.html", title="Thank You")


if __name__ == "__main__":
    app.run(debug=True)
