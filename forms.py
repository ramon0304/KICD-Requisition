from wtforms import (
    StringField,
    PasswordField,
    BooleanField,
    IntegerField,
    DateField,
    TextAreaField,
    SelectField,
    SubmitField,
    FieldList,
    FormField,
    EmailField,
)

from flask_wtf import FlaskForm
from wtforms.validators import InputRequired, Length, EqualTo, Email, Regexp ,Optional, DataRequired
import email_validator
from flask_login import current_user
from wtforms import ValidationError,validators
from models import User


class login_form(FlaskForm):
    email = StringField(validators=[InputRequired(), Email(), Length(1, 64)])
    pwd = PasswordField(validators=[InputRequired(), Length(min=8, max=72)])
    # Placeholder labels to enable form rendering
    username = StringField(
        validators=[Optional()]
    )


class register_form(FlaskForm):
    username = StringField(
        validators=[
            InputRequired(),
            Length(3, 20, message="Please provide a valid name"),
            Regexp(
                "^[A-Za-z][A-Za-z0-9_.]*$",
                0,
                "Usernames must have only letters, " "numbers, dots or underscores",
            ),
        ]
    )
    email = StringField(validators=[InputRequired(), Email(), Length(1, 64)])
    pwd = PasswordField(validators=[InputRequired(), Length(8, 72)])
    cpwd = PasswordField(
        validators=[
            InputRequired(),
            Length(8, 72),
            EqualTo("pwd", message="Passwords must match !"),
        ]
    )


    def validate_email(self, email):
        if User.query.filter_by(email=email.data).first():
            raise ValidationError("Email already registered!")

    def validate_uname(self, uname):
        if User.query.filter_by(username=username.data).first():
            raise ValidationError("Username already taken!")

class OfficeDetailsForm(FlaskForm):
    office_name = StringField("Office Name", validators=[DataRequired()])
    requested_by = StringField("Requested By", validators=[DataRequired()])
    user_email = EmailField("Your Email", validators=[DataRequired(), Email()])
    next = SubmitField("Next")

class ItemForm(FlaskForm):
    item_name = StringField("Item Name", validators=[DataRequired()])
    unit = SelectField("Unit of Issue", choices=[('500ml', '500ml'), ('20L', '20L'), ('300ml', '300ml')], validators=[DataRequired()])
    quantity = IntegerField("Quantity", validators=[DataRequired()])
    remarks = StringField("Remarks")
    
class ItemsForm(FlaskForm):
    items = FieldList(FormField(ItemForm), min_entries=1)
    next = SubmitField("Next")

class ApprovalForm(FlaskForm):
    approver_name = StringField("Approver Name", validators=[DataRequired()])
    role = SelectField("Role", choices=[('Head of Division', 'Head of Division'), ('DDA', 'DDA'), ('DDFA', 'DDFA')], validators=[DataRequired()])
    status = SelectField("Status", choices=[('Approved', 'Approved'), ('Not Approved', 'Not Approved')], validators=[DataRequired()])
    next = SubmitField("Submit")