from app import create_app, db
from app.models import Staff, PayPeriod
from datetime import date

# Create the Flask app context
app = create_app()

with app.app_context():
    # Insert demo data into the Staff table
    staff_data = [
        Staff(
            EmpID=1,
            Salutation="Dr.",
            FirstName="John",
            LastName="Doe",
            FacilityFees_Percent=10.0,
        ),
        Staff(
            EmpID=2,
            Salutation="Dr.",
            FirstName="Jane",
            LastName="Smith",
            FacilityFees_Percent=12.5,
        ),
        Staff(
            EmpID=3,
            Salutation="Dr.",
            FirstName="Emily",
            LastName="Brown",
            FacilityFees_Percent=15.0,
        ),
    ]

    # Insert demo data into the PayPeriod table
    pay_period_data = [
        PayPeriod(
            PeriodSerial=1,
            Period_Start_Date=date(2025, 1, 1),  # Use datetime.date object
            Period_End_Date=date(2025, 1, 15),  # Use datetime.date object
        ),
        PayPeriod(
            PeriodSerial=2,
            Period_Start_Date=date(2025, 1, 16),  # Use datetime.date object
            Period_End_Date=date(2025, 1, 31),  # Use datetime.date object
        ),
    ]

    # Add data to the database
    db.session.add_all(staff_data)
    db.session.add_all(pay_period_data)
    db.session.commit()

    print("Demo data inserted successfully!")
