from flask import (
    Flask,
    render_template,
    redirect,
    flash,
    url_for,
    session,
    request,
    jsonify
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

from flask_bcrypt import Bcrypt, generate_password_hash, check_password_hash

from flask_login import (
    UserMixin,
    login_user,
    LoginManager,
    current_user,
    logout_user,
    login_required,
)

from app import create_app, db, login_manager, bcrypt
from models import User
from forms import login_form, register_form, OfficeDetailsForm, ItemsForm, ApprovalForm
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
    return render_template("index.html", title="Home")

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


# Route to handle form submission
@app.route("/submit-requisition", methods=["POST"])
@login_required
def submit_requisition():
    try:
        # Check if request is JSON
        if request.is_json:
            data = request.get_json()
            office_name = data.get("office_name")
            requested_by = data.get("requested_by")
            user_email = data.get("user_email")
            items = data.get("items", [])
        else:
            # Fall back to form data
            office_name = request.form.get("office_name")
            requested_by = request.form.get("requested_by")
            user_email = request.form.get("user_email")
            items = request.form.getlist("items[]")

        # Validate required fields
        if not all([office_name, requested_by, user_email]):
            return jsonify({
                "status": "error",
                "message": "Missing required fields"
            }), 400

        # Validate email
        if not validate_email(user_email):
            return jsonify({
                "status": "error",
                "message": "Invalid email address"
            }), 400

        # Validate items
        if not items:
            return jsonify({
                "status": "error",
                "message": "No items provided"
            }), 400

        # Process the data (replace with your actual logic)
        print(f"Processing requisition from {office_name}")
        
        # Return success response
        return jsonify({
            "status": "success",
            "message": "Requisition submitted successfully!",
            "data": {
                "office": office_name,
                "requester": requested_by,
                "email": user_email,
                "items_count": len(items)
            }
        }), 200

    except Exception as e:
        app.logger.error(f"Requisition submission error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "An internal server error occurred"
        }), 500
    
    
# Helper function to validate email
def validate_email(email):
    import re
    regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
    return re.match(regex, email) is not None

if __name__ == "__main__":
    app.run(debug=True)