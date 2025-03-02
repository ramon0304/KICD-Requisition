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
from forms import *


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
def generate_pdf(req_id):
    requisition = Requisition.query.get_or_404(req_id)
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)

    pdf.drawString(100, 800, f"KICD Requisition Form")
    pdf.drawString(100, 780, f"Office Name: {requisition.office_name}")
    pdf.drawString(100, 760, f"Requested By: {requisition.requested_by}")

    y_position = 740
    pdf.drawString(100, y_position, "Items Requested:")
    for item in requisition.items:
        y_position -= 20
        pdf.drawString(120, y_position, f"{item.item_name} - {item.quantity} {item.unit}")

    pdf.drawString(100, y_position - 40, f"Approval: {requisition.approvals[0].approver_name} ({requisition.approvals[0].role}) - {requisition.approvals[0].status}")

    pdf.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="requisition.pdf", mimetype="application/pdf")

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



if __name__ == "__main__":
    app.run(debug=True)
