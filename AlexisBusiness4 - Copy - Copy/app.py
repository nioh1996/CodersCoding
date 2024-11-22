from flask import Flask, render_template, request, redirect, url_for
from config import Config
from extensions import db

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)

    # Import models after app and db initialization
    with app.app_context():
        from models import Client, Service, Appointment, Transaction
        db.create_all()  # Ensure tables are created

    return app

app = create_app()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/client/add', methods=['GET', 'POST'])
def add_client():
    from models import Client  # Import models within the route to avoid circular issues
    if request.method == 'POST':
        name = request.form['name']
        address = request.form['address']
        phone = request.form['phone']
        email = request.form['email']
        client = Client(name=name, address=address, phone=phone, email=email)
        db.session.add(client)
        db.session.commit()
        return redirect(url_for('view_clients'))
    return render_template('client_profile.html', clients=Client.query.all())

@app.route('/clients')
def view_clients():
    from models import Client  # Import models within the route to avoid circular issues
    clients = Client.query.all()
    return render_template('client_profile.html', clients=clients)

from datetime import datetime
from models import Client, Service, Appointment

@app.route('/booking', methods=['GET', 'POST'])
def booking():
    if request.method == 'POST':
        # Safely retrieve form data
        client_id = request.form.get('client_id')
        service_name = request.form.get('service_name')
        date_str = request.form.get('date')  # Date as string
        hours_worked = request.form.get('hours_worked')

        # Validate required fields
        if not (client_id and service_name and date_str and hours_worked):
            return "All fields are required.", 400

        # Convert date string to Python date object
        try:
            appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return "Invalid date format. Please use YYYY-MM-DD."

        # Check if service exists in the database
        service = Service.query.filter_by(service_name=service_name).first()
        if not service:
            return f"Service '{service_name}' does not exist. Please add it in the <a href='/setup'>Setup Page</a>."

        # Check for existing bookings
        if Appointment.query.filter_by(date=appointment_date).first():
            return "This date is already booked."

        # Calculate total amount and create new appointment
        total_amount = int(hours_worked) * service.hourly_rate

        # Create a new Appointment with the proper date object
        appointment = Appointment(client_id=client_id, service_id=service.id, date=appointment_date, hours_worked=hours_worked, total_amount=total_amount)
        db.session.add(appointment)
        db.session.commit()

        return redirect(url_for('booking_summary'))

    # GET request: Render booking form
    clients = Client.query.all()
    return render_template('booking.html', clients=clients)




@app.route('/booking/summary')
def booking_summary():
    from models import Appointment  # Import models within the route to avoid circular issues
    appointments = Appointment.query.all()
    return render_template('invoice.html', appointments=appointments)

@app.route('/setup', methods=['GET', 'POST'])
def setup_services():
    from models import Service  # Import models within the route to avoid circular issues
    if request.method == 'POST':
        service_name = request.form['service_name']
        hourly_rate = float(request.form['hourly_rate'])
        service = Service(service_name=service_name, hourly_rate=hourly_rate)
        db.session.add(service)
        db.session.commit()
        return redirect(url_for('setup_services'))
    return render_template('setup.html', services=Service.query.all())

if __name__ == '__main__':
    app.run(debug=True)

@app.before_first_request
def seed_services():
    from models import Service
    default_services = [
        {"service_name": "Plumbing", "hourly_rate": 50},
        {"service_name": "Electrical", "hourly_rate": 60},
        {"service_name": "Masonry", "hourly_rate": 55},
        {"service_name": "Carpentry Works", "hourly_rate": 45},
        {"service_name": "Others", "hourly_rate": 40},
    ]

    # Check if the service already exists to prevent duplicates
    for service_data in default_services:
        existing_service = Service.query.filter_by(service_name=service_data["service_name"]).first()
        if not existing_service:
            new_service = Service(**service_data)
            db.session.add(new_service)

    db.session.commit()

