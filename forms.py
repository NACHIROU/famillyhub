from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField, DateField, DateTimeField, BooleanField, DecimalField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Optional, NumberRange


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


class RegisterForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone', validators=[Optional()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')


class CreateFamilyForm(FlaskForm):
    family_name = StringField('Family Name', validators=[DataRequired()])
    submit = SubmitField('Create Family')


class AddMemberForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone', validators=[Optional()])
    family_role = StringField('Family Role', validators=[Optional()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Add Member')


class MeetingForm(FlaskForm):
    title = StringField('Meeting Title', validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()])
    time = StringField('Time', validators=[DataRequired()])
    location = StringField('Location', validators=[Optional()])
    agenda = TextAreaField('Agenda', validators=[Optional()])
    themes_discussed = TextAreaField('Themes Discussed', validators=[Optional()])
    minutes = TextAreaField('Meeting Minutes', validators=[Optional()])
    submit = SubmitField('Save Meeting')


class DecisionForm(FlaskForm):
    title = StringField('Decision Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Optional()])
    meeting_id = SelectField('Link to Meeting', coerce=int, validators=[Optional()])
    status = SelectField('Status', choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], validators=[DataRequired()])
    submit = SubmitField('Save Decision')


class VoteForm(FlaskForm):
    title = StringField('Vote Title', validators=[DataRequired()])
    decision_id = SelectField('Related Decision', coerce=int, validators=[Optional()])
    vote_type = SelectField('Vote Type', choices=[('yes_no', 'Yes/No'), ('multiple_choice', 'Multiple Choice'), ('secret', 'Secret Voting')], validators=[DataRequired()])
    options = StringField('Options (comma separated)', validators=[Optional()])
    deadline = DateTimeField('Deadline', validators=[Optional()])
    submit = SubmitField('Create Vote')


class ContributionForm(FlaskForm):
    title = StringField('Contribution Title', validators=[DataRequired()])
    amount = DecimalField('Amount', validators=[DataRequired(), NumberRange(min=0)])
    frequency = SelectField('Frequency', choices=[('one_time', 'One Time'), ('monthly', 'Monthly'), ('yearly', 'Yearly')], validators=[DataRequired()])
    due_date = DateField('Due Date', validators=[DataRequired()])
    submit = SubmitField('Create Contribution')


class PaymentForm(FlaskForm):
    user_id = SelectField('Member', coerce=int, validators=[DataRequired()])
    amount = DecimalField('Amount', validators=[DataRequired(), NumberRange(min=0)])
    payment_date = DateField('Payment Date', validators=[DataRequired()])
    status = SelectField('Status', choices=[('paid', 'Paid'), ('pending', 'Pending'), ('overdue', 'Overdue')], validators=[DataRequired()])


class DocumentForm(FlaskForm):
    title = StringField('Document Title', validators=[DataRequired()])
    file = None


class ProfileForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone', validators=[Optional()])
    family_role = StringField('Family Role', validators=[Optional()])
    submit = SubmitField('Update Profile')
