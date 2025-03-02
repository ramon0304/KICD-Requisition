from flask import Flask
from flask_mail import Mail, Message
app = Flask(__name__)

def mail_configs():
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Use your mail server
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'your-email@gmail.com'  # Replace with your email
    app.config['MAIL_PASSWORD'] = 'your-email-password'  # Replace with your email password
    app.config['MAIL_DEFAULT_SENDER'] = 'your-email@gmail.com'  # Replace with your sender email

    mail = Mail(app)