from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, SelectField, TextAreaField, RadioField, DateField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Optional
from datetime import datetime

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=100)])
    phone = StringField('Phone Number', validators=[Length(max=20)])
    address = TextAreaField('Address (Optional)', validators=[Length(max=500)])
    gender = SelectField('Gender', choices=[
        ('', 'Select Gender'),
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other')
    ], validators=[DataRequired()])
    date_of_birth = DateField('Date of Birth (Optional)', format='%Y-%m-%d', validators=[Optional()])
    location = StringField('Current City / State / Country', validators=[DataRequired(), Length(max=100)])
    preferred_language = SelectField('Preferred Language', choices=[
        ('', 'Select Preferred Language'),
        ('English', 'English'),
        ('Hindi', 'Hindi'),
        ('Sanskrit', 'Sanskrit'),
        ('Tamil', 'Tamil'),
        ('Telugu', 'Telugu'),
        ('Kannada', 'Kannada'),
        ('Malayalam', 'Malayalam'),
        ('Marathi', 'Marathi'),
        ('Gujarati', 'Gujarati'),
        ('Bengali', 'Bengali'),
        ('Odia', 'Odia'),
        ('Punjabi', 'Punjabi'),
        ('Assamese', 'Assamese'),
        ('Other', 'Other')
    ], validators=[DataRequired()])
    referral_source = StringField('How did you find us? (Optional)', validators=[Optional(), Length(max=100)])
    practice_level = SelectField('Practice Level', choices=[
        ('', 'Select Practice Level'),
        ('Beginner', 'Beginner'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced')
    ])
    purpose = TextAreaField('Purpose for Starting Sadhana', validators=[
        DataRequired(), 
        Length(min=20, max=1000, message='Please explain your purpose in 20-1000 characters')
    ])
    profile_picture = FileField('Profile Picture (Optional)', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Only image files (JPG, PNG, GIF) are allowed!')
    ])

    def validate_username(self, username):
        # We'll handle this validation in the route to avoid circular imports
        pass

    def validate_email(self, email):
        # We'll handle this validation in the route to avoid circular imports
        pass

class EditProfileForm(FlaskForm):
    phone = StringField('Phone Number', validators=[Length(max=20)])
    address = TextAreaField('Address', validators=[Length(max=500)])
    purpose = TextAreaField('Purpose for Sadhana', validators=[
        DataRequired(), 
        Length(min=20, max=1000, message='Please explain your purpose in 20-1000 characters')
    ])

class AdminApprovalForm(FlaskForm):
    user_id = StringField('User ID', validators=[DataRequired()])
    action = SelectField('Action', choices=[
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('suspend', 'Suspend')
    ], validators=[DataRequired()])
    notes = TextAreaField('Notes (Optional)', validators=[Length(max=500)])

class UserSearchForm(FlaskForm):
    search_term = StringField('Search by Username, Email, or Full Name')
    status_filter = SelectField('Status Filter', choices=[
        ('all', 'All Users'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('suspended', 'Suspended')
    ])
    role_filter = SelectField('Role Filter', choices=[
        ('all', 'All Roles'),
        ('admin', 'Admin'),
        ('user', 'User')
    ])

class DonationPurposeForm(FlaskForm):
    name = StringField('Purpose Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Length(max=500)])

class OfflineDonationForm(FlaskForm):
    donor_name = StringField('Donor Name', validators=[DataRequired(), Length(max=100)])
    donor_email = StringField('Donor Email', validators=[Optional(), Email(), Length(max=120)])
    donor_phone = StringField('Donor Phone', validators=[Optional(), Length(max=20)])
    amount = StringField('Amount', validators=[DataRequired()])
    currency = SelectField('Currency', choices=[
        ('INR', 'INR (₹)'),
        ('USD', 'USD ($)'),
        ('EUR', 'EUR (€)'),
        ('GBP', 'GBP (£)')
    ], default='INR')
    purpose_id = SelectField('Donation Purpose', coerce=int, validators=[DataRequired()])
    donation_date = StringField('Donation Date', validators=[DataRequired()])
    payment_method = SelectField('Payment Method', choices=[
        ('Cash', 'Cash'),
        ('Bank Transfer', 'Bank Transfer'),
        ('UPI', 'UPI'),
        ('Cheque', 'Cheque'),
        ('Card', 'Card Payment'),
        ('Other', 'Other')
    ], validators=[DataRequired()])
    reference_number = StringField('Reference Number', validators=[Optional(), Length(max=100)])
    notes = TextAreaField('Notes', validators=[Optional(), Length(max=500)])

class DonationSearchForm(FlaskForm):
    search_term = StringField('Search by Donor Name, Email, or Reference Number')
    purpose_filter = SelectField('Purpose Filter', choices=[('all', 'All Purposes')])
    status_filter = SelectField('Status Filter', choices=[
        ('all', 'All Donations'),
        ('verified', 'Verified'),
        ('pending', 'Pending Verification')
    ])
    date_from = StringField('From Date')
    date_to = StringField('To Date')

class MandalaSadhanaRegistrationForm(FlaskForm):
    """Form for Mandala Sadhana registration"""
    email = StringField('Email', validators=[DataRequired(), Email()])
    full_name = StringField('Full Name & Geo Location', validators=[DataRequired(), Length(max=200)])
    mandala_48_commitment = RadioField(
        'Are you ready to commit to a 48-day (1) Mandala, honoring each day as a step into deeper presence with Bhairava?',
        choices=[('Yes', 'Yes'), ('No', 'No')],
        validators=[DataRequired()]
    )
    mandala_144_commitment = RadioField(
        'Do you feel called to walk the full triad of 144-Days (3) Mandalas — building a sacred foundation for transformation and inner stability?',
        choices=[('Yes', 'Yes'), ('No', 'No'), ('Not Yet Ready', 'Not Yet Ready')],
        validators=[DataRequired()]
    )
    commitment_text = TextAreaField(
        'Can you hold your Sadhana with sincerity and steadiness, even when the mind resists or the path feels silent?',
        validators=[DataRequired(), Length(min=10, max=1000)]
    )
    sadhana_start_date = DateField(
        'When did your Sadhana begin? (Mark the day of inner commitment)',
        validators=[DataRequired()]
    )
    sadhana_type = SelectField(
        'Which Sadhana are you committing to as part of your Mandala journey?',
        choices=[
            ('', 'Choose'),
            ('Aṣṭamī Sādhana', 'Aṣṭamī Sādhana (Sacred observance on Krishna Paksha Aṣṭamī)'),
            ('Prathama Charaṇa', 'Prathama Charaṇa (First foundational cycle of Sādhana)'),
            ('Dvitīya Charaṇa', 'Dvitīya Charaṇa (Second deepening cycle of discipline and devotion)'),
            ('Tṛtīya Charaṇa', 'Tṛtīya Charaṇa (Third, the offering of self in full surrender)'),
            ('Rudrākṣa Anugraha Sādhana', 'Rudrākṣa Anugraha Sādhana (Receiving and practicing under Rudrākṣa grace)')
        ],
        validators=[DataRequired()]
    )
    send_copy = BooleanField('Send me a copy of my responses.')

class MandalaSadhanaSearchForm(FlaskForm):
    """Form for searching Mandala Sadhana registrations"""
    search_term = StringField('Search by Name, Email, or Sadhana Type')
    mandala_48_filter = SelectField('48-Day Mandala Filter', choices=[
        ('all', 'All'),
        ('Yes', 'Yes'),
        ('No', 'No')
    ])
    mandala_144_filter = SelectField('144-Day Mandala Filter', choices=[
        ('all', 'All'),
        ('Yes', 'Yes'),
        ('No', 'No'),
        ('Not Yet Ready', 'Not Yet Ready')
    ])
    sadhana_type_filter = SelectField('Sadhana Type Filter', choices=[
        ('all', 'All Types'),
        ('Aṣṭamī Sādhana', 'Aṣṭamī Sādhana'),
        ('Prathama Charaṇa', 'Prathama Charaṇa'),
        ('Dvitīya Charaṇa', 'Dvitīya Charaṇa'),
        ('Tṛtīya Charaṇa', 'Tṛtīya Charaṇa'),
        ('Rudrākṣa Anugraha Sādhana', 'Rudrākṣa Anugraha Sādhana')
    ])
    date_from = StringField('From Date')
    date_to = StringField('To Date')