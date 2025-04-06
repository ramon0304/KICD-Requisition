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

from datetime import timedelta, datetime
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
from models import User, Requisition, RequisitionItems, Approval  
from forms import login_form, register_form, OfficeDetailsForm, ItemsForm, ApprovalForm
from pdf import generate_pdf

from functools import wraps
from sqlalchemy import func, desc

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
    # Ensure we're getting JSON data
    if not request.is_json:
        return jsonify({
            "status": "error",
            "message": "Request must be JSON"
        }), 400

    try:
        data = request.get_json()
        current_user_obj = User.query.get(int(current_user.get_id()))
        
        # Validate required fields
        required_fields = ['office_name', 'requested_by', 'user_email', 'items']
        if not all(field in data for field in required_fields):
            return jsonify({
                "status": "error",
                "message": "Missing required fields"
            }), 400

        # Validate email
        if not validate_email(data['user_email']):
            return jsonify({
                "status": "error",
                "message": "Invalid email address"
            }), 400

        # Validate items
        if not data['items'] or len(data['items']) == 0:
            return jsonify({
                "status": "error",
                "message": "No items provided"
            }), 400

        # Create new requisition
        new_requisition = Requisition(
            office_name=data['office_name'],
            requested_by=data['requested_by'],
            user_email=data['user_email'],
            status="Pending"
        )
        db.session.add(new_requisition)
        db.session.flush()

        # Add items
        for item in data['items']:
            new_item = RequisitionItems(
                requisition_id=new_requisition.id,
                item_name=item.get('item_name'),
                unit=item.get('unit', 'pieces'),
                quantity=item.get('quantity', 1),
                remarks=item.get('remarks', '')
            )
            db.session.add(new_item)

        # Initial approval record
        initial_approval = Approval(
            requisition_id=new_requisition.id,
            approver_name=current_user_obj.username,
            role="Requester",
            status="Submitted",
            date_signed=datetime.utcnow()
        )
        db.session.add(initial_approval)

        db.session.commit()

        return jsonify({
            "status": "success",
            "message": "Requisition submitted successfully!",
            "requisition_id": new_requisition.id,
            "redirect_url": url_for('view_requisitions')
        }), 200

    except IntegrityError as e:
        db.session.rollback()
        app.logger.error(f"Integrity error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Database integrity error"
        }), 500
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Requisition submission error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "An internal server error occurred"
        }), 500

#Handling requisition views
@app.route("/requisitions")
@login_required
def view_requisitions():
    # Get requisitions for the current user
    user_requisitions = Requisition.query.filter_by(user_email=current_user.email)\
                                       .order_by(Requisition.date_created.desc())\
                                       .all()
    return render_template("requisitions.html", 
                         requisitions=user_requisitions,
                         title="My Requisitions")

@app.route("/requisition/<int:req_id>")
@login_required
def requisition_detail(req_id):
    # Get the specific requisition
    requisition = Requisition.query.get_or_404(req_id)
    
    return render_template("requisition_detail.html", 
                         requisition=requisition,
                         title=f"Requisition #{requisition.id}")

# Helper function to validate email
def validate_email(email):
    import re
    regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
    return re.match(regex, email) is not None

# Admin decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("You don't have permission to access this page", "danger")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# Admin dashboard
@app.route("/admin")
@login_required
@admin_required
def admin_dashboard():
    # Get statistics
    total_users = User.query.count()
    total_requisitions = Requisition.query.count()
    pending_requisitions = Requisition.query.filter_by(status="Pending").count()
    
    # Get recent requisitions
    recent_requisitions = Requisition.query.order_by(Requisition.date_created.desc()).limit(5).all()
    
    # Get frequently requested items
    frequent_items = db.session.query(
        RequisitionItems.item_name,
        func.sum(RequisitionItems.quantity).label('total_quantity')
    ).group_by(RequisitionItems.item_name).order_by(desc('total_quantity')).limit(5).all()
    
    return render_template("admin/dashboard.html",
        total_users=total_users,
        total_requisitions=total_requisitions,
        pending_requisitions=pending_requisitions,
        recent_requisitions=recent_requisitions,
        frequent_items=frequent_items
    )


# Admin users management
@app.route("/admin/users")
@login_required
@admin_required
def admin_users():
    users = User.query.order_by(User.username).all()
    return render_template("admin/users.html", users=users)


# Admin requisitions management
@app.route("/admin/requisitions")
@login_required
@admin_required
def admin_requisitions():
    status = request.args.get('status', 'all')
    
    query = Requisition.query
    
    if status == 'pending':
        query = query.filter_by(status="Pending")
    elif status == 'approved':
        query = query.filter_by(status="Approved")
    elif status == 'rejected':
        query = query.filter_by(status="Rejected")
    
    requisitions = query.order_by(Requisition.date_created.desc()).all()
    
    return render_template("admin/requisitions.html", 
                         requisitions=requisitions,
                         status=status)


# Approve/Reject requisition
@app.route("/admin/requisition/<int:req_id>/<action>", methods=["POST"])
@login_required
@admin_required
def admin_requisition_action(req_id, action):
    requisition = Requisition.query.get_or_404(req_id)
    
    if action == "approve":
        requisition.status = "Approved"
        flash("Requisition approved successfully", "success")
    elif action == "reject":
        requisition.status = "Rejected"
        flash("Requisition rejected", "info")
    else:
        flash("Invalid action", "danger")
        return redirect(url_for('admin_requisitions'))
    
    # Add approval record
    approval = Approval(
        requisition_id=requisition.id,
        approver_name=current_user.username,
        role="Admin",
        status=requisition.status,
        date_signed=datetime.utcnow()
    )
    db.session.add(approval)
    db.session.commit()
    
    return redirect(url_for('admin_requisitions'))




if __name__ == "__main__":
    app.run(debug=True)