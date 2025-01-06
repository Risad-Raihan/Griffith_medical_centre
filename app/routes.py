from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app.models import db, User, Invoice, Billing, PayPeriod, Staff
from datetime import date
from sqlalchemy.exc import IntegrityError
# Create a Blueprint for organizing routes (like a mini-app within Flask)
main = Blueprint('main', __name__)


# Home Route: This serves as the landing page for the app
@main.route('/')
def home():
    return render_template('index.html')  # Renders the index.html template

# Login Route: Handles both GET (to show the login form) and POST (to process login data)
@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':  # Handle form submission
        username = request.form.get('username')  # Get the entered username
        password = request.form.get('password')  # Get the entered password

        # Define fixed credentials
        fixed_username = "admin"
        fixed_password = "admin123"

        # Validate credentials
        if username == fixed_username and password == fixed_password:
            # Create a pseudo-user for session management
            from flask_login import UserMixin
            class FixedUser(UserMixin):
                def __init__(self, username):
                    self.id = 1  # Fixed ID for admin
                    self.username = username
                    self.role = "Admin"

            # Log in the pseudo-user
            admin_user = FixedUser(username)
            login_user(admin_user)
            return redirect(url_for('main.admin_dashboard'))
        else:
            flash('Invalid username or password')  # Show error message

    return render_template('login.html')  # Render the login form

# Admin Dashboard Route: Accessible only by Admin users
@main.route('/admin_dashboard')
@login_required  # Ensures only logged-in users can access this route
def admin_dashboard():
    if current_user.role != 'Admin':  # Restrict access to Admin role
        return redirect(url_for('main.home'))  # Redirect unauthorized users to home
    return render_template('admin_dashboard.html')  # Render the admin dashboard template

# Super Admin Dashboard Route: Accessible only by Super Admin users
@main.route('/super_admin_dashboard')
@login_required  # Ensures only logged-in users can access this route
def super_admin_dashboard():
    if current_user.role != 'Super Admin':  # Restrict access to Super Admin role
        return redirect(url_for('main.home'))  # Redirect unauthorized users to home
    return render_template('super_admin_dashboard.html')  # Render the super admin dashboard template

# Route to Create an Invoice: Admins can create invoices
@main.route('/create_invoice', methods=['GET', 'POST'])
def create_invoice():
    if request.method == 'POST':
        try:
            # Retrieve form data
            inv_number = request.form.get('inv_number')  # Invoice Number
            inv_date = request.form.get('inv_date')      # Invoice Date
            paid_date = request.form.get('paid_date')    # Paid Date
            doctor_id = request.form.get('doctor')       # Doctor's ID
            pay_period_id = request.form.get('pay_period')  # Pay Period ID
            
            # Convert dates (ensure valid date objects)
            from datetime import date
            inv_date = date.fromisoformat(inv_date) if inv_date else None
            paid_date = date.fromisoformat(paid_date) if paid_date else None

            # Create a new invoice object
            new_invoice = Invoice(
                InvNumber=inv_number,
                InvDate=inv_date,
                RefEmpID=doctor_id,
                GrossAmount=0.0,  # Initial gross amount (updated after adding billings)
                FacilityFees=None,  # Facility fees (calculated later)
                GST=None,           # GST (calculated later)
                OtherDeduction=None,  # Other deductions if any
                NetAmount=0.0,       # Initial net amount (updated after deductions)
                PaidOn=paid_date,
                RefPeriodSerial=pay_period_id,
                PayType=None         # Optional field
            )
            
            # Add and commit the new invoice to the database
            db.session.add(new_invoice)
            db.session.commit()

            # Redirect to the Add Billings page for this invoice
            flash('Invoice created successfully! Add billing details for this invoice.', 'success')
            return redirect(url_for('main.add_billings', invoice_id=new_invoice.InvID))
        
        except IntegrityError:  # Handle duplicate invoice numbers or constraint violations
            db.session.rollback()  # Roll back the transaction to avoid inconsistencies
            flash('Invoice number already exists. Please use a unique invoice number.', 'danger')

        except Exception as e:  # Handle any other unexpected errors
            db.session.rollback()
            flash(f'An unexpected error occurred: {str(e)}', 'danger')

    # For GET request: Fetch Pay Periods and Doctors to populate dropdowns
    pay_periods = PayPeriod.query.all()  # Fetch all pay periods
    doctors = Staff.query.all()  # Fetch all doctors/staff

    # Render the create invoice form with dynamic dropdown values
    return render_template('create_invoice.html', pay_periods=pay_periods, doctors=doctors)


# Route to Fetch Doctor Details Dynamically (AJAX request)
@main.route('/get_doctor_details/<int:doctor_id>')
@login_required
def get_doctor_details(doctor_id):
    doctor = Staff.query.get(doctor_id)  # Fetch doctor details by ID
    if not doctor:
        return jsonify({'error': 'Doctor not found'}), 404  # Return error if doctor not found

    # Example GST calculation: 10% of Facility Fee
    gst = doctor.FacilityFees_Percent * 0.1

    # Return Facility Fee and GST as JSON
    return jsonify({
        'facility_fee': doctor.FacilityFees_Percent,
        'gst': gst
    })

@main.route('/add_billings/<int:invoice_id>', methods=['GET', 'POST'])
def add_billings(invoice_id):
    # Retrieve the invoice and related billing details
    invoice = Invoice.query.get_or_404(invoice_id)  # Fetch the invoice
    billings = Billing.query.filter_by(RefInvID=invoice_id).all()  # Fetch related billings

    if request.method == 'POST':
        # Retrieve billing details from form
        billing_date = request.form.get('billing_date')
        billing_type = request.form.get('billing_type')
        billing_ref = request.form.get('billing_ref')
        billing_amount = request.form.get('billing_amount')

        # Convert the billing_date to a proper date object
        from datetime import date
        billing_date = date.fromisoformat(billing_date) if billing_date else None

        # Add the new billing entry
        new_billing = Billing(
            BillingDate=billing_date,
            BillingType=billing_type,
            BillingRef=billing_ref,
            BillingAmount=float(billing_amount),
            RefInvID=invoice_id  # Link to the invoice
        )
        db.session.add(new_billing)

        # Update the invoice gross amount
        invoice.GrossAmount += float(billing_amount)
        db.session.commit()

        flash('Billing added successfully!', 'success')
        return redirect(url_for('main.add_billings', invoice_id=invoice_id))

    # Render the add billings page
    return render_template(
        'add_billings.html',
        invoice=invoice,
        billings=billings,
        invoice_id=invoice_id  # Pass the invoice ID explicitly
    )

@main.route('/full_receipt/<int:invoice_id>')
def full_receipt(invoice_id):
    # Fetch the invoice details
    invoice = Invoice.query.get(invoice_id)
    if not invoice:
        flash("Invoice not found")
        return redirect(url_for('main.home'))

    # Fetch the related staff (doctor) details
    doctor = Staff.query.get(invoice.RefEmpID)

    # Fetch the related pay period details
    pay_period = PayPeriod.query.get(invoice.RefPeriodSerial)

    # Fetch all the billing entries for this invoice
    billings = Billing.query.filter_by(RefInvID=invoice_id).all()

    # Calculate total billing amount
    total_billing = sum(billing.BillingAmount for billing in billings)

    # Fetch Facility Fees (percentage) and GST
    facility_fee_percent = doctor.FacilityFees_Percent if doctor else 0.0
    facility_fee_amount = (facility_fee_percent / 100) * total_billing
    gst_amount = invoice.GST if invoice.GST else 0.0

    # Calculate total deductions and net payment
    total_deductions = facility_fee_amount + gst_amount
    net_payment = total_billing - total_deductions

    return render_template(
        'full_receipt.html',
        invoice=invoice,
        doctor=doctor,
        pay_period=pay_period,
        billings=billings,
        total_billing=total_billing,
        facility_fee_amount=facility_fee_amount,
        gst_amount=gst_amount,
        total_deductions=total_deductions,
        net_payment=net_payment
    )
