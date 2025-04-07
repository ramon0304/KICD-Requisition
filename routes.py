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

from functools import wraps
from sqlalchemy import func, desc

from flask_chartjs import ChartJS, BaseChart
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
import io
import matplotlib.pyplot as plt
import seaborn as sns
from dateutil.relativedelta import relativedelta

# Initialize ChartJS
chartjs = ChartJS(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

app = create_app()

@app.before_request
def session_handler():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=1)


# home route
@app.route("/", methods=("GET", "POST"), strict_slashes=False)
def index():
    return render_template("index.html", title="Home")


# login route
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


# user registration
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


# user logout
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


# Admin statistics with charts
@app.route("/admin/statistics")
@login_required
@admin_required
def admin_statistics():
    # Date range for statistics (last 30 days)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)
    
    # Requisitions by status
    status_data = db.session.query(
        Requisition.status,
        func.count(Requisition.id).label('count')
    ).group_by(Requisition.status).all()
    
    # Requisitions by day
    daily_data = db.session.query(
        func.date(Requisition.date_created).label('date'),
        func.count(Requisition.id).label('count')
    ).filter(Requisition.date_created >= start_date)\
     .group_by(func.date(Requisition.date_created))\
     .order_by(func.date(Requisition.date_created)).all()
    
    # Top requested items
    top_items = db.session.query(
        RequisitionItems.item_name,
        func.sum(RequisitionItems.quantity).label('total')
    ).group_by(RequisitionItems.item_name)\
     .order_by(func.sum(RequisitionItems.quantity).desc())\
     .limit(10).all()
    
    return render_template("admin/statistics.html",
        status_data=status_data,
        daily_data=daily_data,
        top_items=top_items,
        start_date=start_date.date(),
        end_date=end_date.date()
    )


# Generate PDF report
@app.route("/admin/report/pdf")
@login_required
@admin_required
def generate_pdf_report():
    # Create a file-like buffer to receive PDF data
    buffer = io.BytesIO()
    
    # Create the PDF object
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    Story = []
    
    # Add title
    Story.append(Paragraph("KICD Requisition System Report", styles['Title']))
    Story.append(Spacer(1, 12))
    
    # Generate and add charts
    charts = generate_chart_images()
    for chart in charts:
        Story.append(Paragraph(chart['title'], styles['Heading2']))
        Story.append(Spacer(1, 12))
        Story.append(Image(chart['image'], width=400, height=300))
        Story.append(Spacer(1, 24))
    
    # Add summary statistics
    total_users = User.query.count()
    total_requisitions = Requisition.query.count()
    
    Story.append(Paragraph("Summary Statistics", styles['Heading2']))
    Story.append(Spacer(1, 12))
    Story.append(Paragraph(f"Total Users: {total_users}", styles['Normal']))
    Story.append(Paragraph(f"Total Requisitions: {total_requisitions}", styles['Normal']))
    
    # Build the PDF
    doc.build(Story)
    
    # File response
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"kicd_report_{datetime.now().date()}.pdf",
        mimetype='application/pdf'
    )

def generate_chart_images():
    charts = []
    
    # Chart 1: Requisitions by Status (Pie)
    status_data = db.session.query(
        Requisition.status,
        func.count(Requisition.id).label('count')
    ).group_by(Requisition.status).all()
    
    labels = [item[0] for item in status_data]
    sizes = [item[1] for item in status_data]
    
    plt.figure(figsize=(6, 6))
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
    plt.axis('equal')
    plt.title('Requisitions by Status')
    
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png')
    plt.close()
    img_buffer.seek(0)
    
    charts.append({
        'title': 'Requisitions by Status',
        'image': img_buffer
    })
    
    # Chart 2: Daily Requisitions (Line)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)
    
    daily_data = db.session.query(
        func.date(Requisition.date_created).label('date'),
        func.count(Requisition.id).label('count')
    ).filter(Requisition.date_created >= start_date)\
     .group_by(func.date(Requisition.date_created))\
     .order_by(func.date(Requisition.date_created)).all()
    
    dates = [item[0] for item in daily_data]
    counts = [item[1] for item in daily_data]
    
    plt.figure(figsize=(8, 4))
    sns.lineplot(x=dates, y=counts)
    plt.title('Daily Requisitions (Last 30 Days)')
    plt.xlabel('Date')
    plt.ylabel('Number of Requisitions')
    plt.xticks(rotation=45)
    
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', bbox_inches='tight')
    plt.close()
    img_buffer.seek(0)
    
    charts.append({
        'title': 'Daily Requisitions Trend',
        'image': img_buffer
    })
    
    return charts


# Add this to your existing admin routes
@app.route("/admin/requisitions/export")
@login_required
@admin_required
def export_requisitions():
    status = request.args.get('status', 'all')
    
    query = Requisition.query
    
    if status == 'pending':
        query = query.filter_by(status="Pending")
    elif status == 'approved':
        query = query.filter_by(status="Approved")
    elif status == 'rejected':
        query = query.filter_by(status="Rejected")
    
    requisitions = query.order_by(Requisition.date_created.desc()).all()
    
    # Generate CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'ID', 'Office', 'Requested By', 'Email', 
        'Status', 'Date Created', 'Items Count'
    ])
    
    # Write data
    for req in requisitions:
        writer.writerow([
            req.id, req.office_name, req.requested_by, req.user_email,
            req.status, req.date_created.strftime('%Y-%m-%d'), len(req.items)
        ])
    
    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={
            "Content-Disposition": f"attachment;filename=requisitions_{status}_{datetime.now().date()}.csv"
        }
    )

if __name__ == "__main__":
    app.run(debug=True)