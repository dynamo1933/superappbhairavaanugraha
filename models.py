from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy.orm import synonym

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.Text, nullable=True)
    role = db.Column(db.String(20), default='user')  # 'admin' or 'user'
    is_approved = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_active = db.Column(db.DateTime, nullable=True)  # Last activity timestamp
    approved_at = db.Column(db.DateTime, nullable=True)
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Additional fields for spiritual practice
    practice_level = db.Column(db.String(50), nullable=True)  # Beginner, Intermediate, Advanced
    purpose = db.Column(db.Text, nullable=False)  # Purpose for starting sadhana
    
    # Profile picture
    profile_picture = db.Column(db.String(255), nullable=True)  # Path to profile picture
    
    # New registration fields
    date_of_birth = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(20), nullable=False, default='Other')
    location = db.Column(db.String(100), nullable=True)
    preferred_language = db.Column(db.String(50), nullable=True)
    referral_source = db.Column(db.String(100), nullable=True)
    
    # Mandala access permissions
    mandala_1_access = db.Column(db.Boolean, default=True)  # All users get access to Mandala 1
    mandala_2_access = db.Column(db.Boolean, default=False)  # Admin must approve
    mandala_3_access = db.Column(db.Boolean, default=False)  # Admin must approve

    # Rudraksha access permissions
    rudraksha_8_mukhi_access = db.Column(db.Boolean, default=False)  # Admin must approve
    rudraksha_11_mukhi_access = db.Column(db.Boolean, default=False)  # Admin must approve
    rudraksha_14_mukhi_access = db.Column(db.Boolean, default=False)  # Admin must approve
    
    # Pratham Charana Diksha (Stage 7) - Introduction to Rudraksha Diksha
    pratham_charana_diksha_access = db.Column(db.Boolean, default=False)  # Admin must approve
    
    # Dutiya Charana (Stage 8) - Second Phase
    dutiya_charana_access = db.Column(db.Boolean, default=False)  # Admin must approve
    
    # Tritiya Charana (Stage 9) - Third Phase
    tritiya_charana_access = db.Column(db.Boolean, default=False)  # Admin must approve

    # Devi Mandala access permissions (for Devi Padathi - Kamakhya Sadhana)
    devi_mandala_1_access = db.Column(db.Boolean, default=True)  # All approved users get access
    devi_mandala_2_access = db.Column(db.Boolean, default=False)  # Admin must approve
    devi_mandala_3_access = db.Column(db.Boolean, default=False)  # Admin must approve

    # Stage completion dates
    mandala_1_completed_at = db.Column(db.DateTime, nullable=True)
    mandala_2_completed_at = db.Column(db.DateTime, nullable=True)
    mandala_3_completed_at = db.Column(db.DateTime, nullable=True)
    rudraksha_8_mukhi_completed_at = db.Column(db.DateTime, nullable=True)
    rudraksha_11_mukhi_completed_at = db.Column(db.DateTime, nullable=True)
    rudraksha_14_mukhi_completed_at = db.Column(db.DateTime, nullable=True)
    pratham_charana_diksha_completed_at = db.Column(db.DateTime, nullable=True)
    dutiya_charana_completed_at = db.Column(db.DateTime, nullable=True)
    tritiya_charana_completed_at = db.Column(db.DateTime, nullable=True)

    # Stage start dates (for duration calculation)
    mandala_1_started_at = db.Column(db.DateTime, nullable=True)
    mandala_2_started_at = db.Column(db.DateTime, nullable=True)
    mandala_3_started_at = db.Column(db.DateTime, nullable=True)
    rudraksha_8_mukhi_started_at = db.Column(db.DateTime, nullable=True)
    rudraksha_11_mukhi_started_at = db.Column(db.DateTime, nullable=True)
    rudraksha_14_mukhi_started_at = db.Column(db.DateTime, nullable=True)
    pratham_charana_diksha_started_at = db.Column(db.DateTime, nullable=True)
    dutiya_charana_started_at = db.Column(db.DateTime, nullable=True)
    tritiya_charana_started_at = db.Column(db.DateTime, nullable=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == 'admin'
    
    def can_login(self):
        return self.is_active and (self.is_admin() or self.is_approved)
    
    def has_mandala_access(self, stage_number):
        """Check if user has access to a specific stage (mandala or rudraksha)"""
        if stage_number == 1:
            return self.mandala_1_access
        elif stage_number == 2:
            return self.mandala_2_access
        elif stage_number == 3:
            return self.mandala_3_access
        elif stage_number == 4:  # Rudraksha 8 Mukhi
            return self.rudraksha_8_mukhi_access
        elif stage_number == 5:  # Rudraksha 11 Mukhi
            return self.rudraksha_11_mukhi_access
        elif stage_number == 6:  # Rudraksha 14 Mukhi
            return self.rudraksha_14_mukhi_access
        elif stage_number == 7:  # Pratham Charana Diksha
            return self.pratham_charana_diksha_access
        elif stage_number == 8:  # Dutiya Charana
            return self.dutiya_charana_access
        elif stage_number == 9:  # Tritiya Charana
            return self.tritiya_charana_access
        return False

    def get_current_stage(self):
        """Get the current stage the user is on (1-6)"""
        stages = [1, 2, 3, 4, 5, 6]
        for stage in stages:
            if not self.has_mandala_access(stage):
                return stage - 1 if stage > 1 else 1
        return 6  # All stages completed

    def get_next_required_stage(self):
        """Get the next stage that needs to be completed"""
        current = self.get_current_stage()
        if current < 6:
            return current + 1
        return None  # All stages completed

    def is_stage_completed(self, stage_number):
        """Check if a specific stage is completed"""
        completion_dates = {
            1: self.mandala_1_completed_at,
            2: self.mandala_2_completed_at,
            3: self.mandala_3_completed_at,
            4: self.rudraksha_8_mukhi_completed_at,
            5: self.rudraksha_11_mukhi_completed_at,
            6: self.rudraksha_14_mukhi_completed_at,
            7: self.pratham_charana_diksha_completed_at,
            8: self.dutiya_charana_completed_at,
            9: self.tritiya_charana_completed_at
        }
        return completion_dates.get(stage_number) is not None

    def get_stage_duration_days(self, stage_number):
        """Get duration spent on a specific stage in days"""
        start_dates = {
            1: self.mandala_1_started_at,
            2: self.mandala_2_started_at,
            3: self.mandala_3_started_at,
            4: self.rudraksha_8_mukhi_started_at,
            5: self.rudraksha_11_mukhi_started_at,
            6: self.rudraksha_14_mukhi_started_at,
            7: self.pratham_charana_diksha_started_at,
            8: self.dutiya_charana_started_at,
            9: self.tritiya_charana_started_at
        }
        completion_dates = {
            1: self.mandala_1_completed_at,
            2: self.mandala_2_completed_at,
            3: self.mandala_3_completed_at,
            4: self.rudraksha_8_mukhi_completed_at,
            5: self.rudraksha_11_mukhi_completed_at,
            6: self.rudraksha_14_mukhi_completed_at,
            7: self.pratham_charana_diksha_completed_at,
            8: self.dutiya_charana_completed_at,
            9: self.tritiya_charana_completed_at
        }

        start_date = start_dates.get(stage_number)
        completion_date = completion_dates.get(stage_number)

        if start_date and completion_date:
            return (completion_date - start_date).days
        elif start_date and not completion_date:
            # Stage started but not completed
            return (datetime.utcnow() - start_date).days
        return 0

    def complete_stage(self, stage_number):
        """Mark a stage as completed and set completion date"""
        from datetime import datetime

        completion_dates = {
            1: 'mandala_1_completed_at',
            2: 'mandala_2_completed_at',
            3: 'mandala_3_completed_at',
            4: 'rudraksha_8_mukhi_completed_at',
            5: 'rudraksha_11_mukhi_completed_at',
            6: 'rudraksha_14_mukhi_completed_at',
            7: 'pratham_charana_diksha_completed_at',
            8: 'dutiya_charana_completed_at',
            9: 'tritiya_charana_completed_at'
        }

        field_name = completion_dates.get(stage_number)
        if field_name:
            setattr(self, field_name, datetime.utcnow())

    def start_stage(self, stage_number):
        """Mark a stage as started and set start date"""
        from datetime import datetime

        start_dates = {
            1: 'mandala_1_started_at',
            2: 'mandala_2_started_at',
            3: 'mandala_3_started_at',
            4: 'rudraksha_8_mukhi_started_at',
            5: 'rudraksha_11_mukhi_started_at',
            6: 'rudraksha_14_mukhi_started_at',
            7: 'pratham_charana_diksha_started_at',
            8: 'dutiya_charana_started_at',
            9: 'tritiya_charana_started_at'
        }

        field_name = start_dates.get(stage_number)
        if field_name:
            setattr(self, field_name, datetime.utcnow())

    def get_stage_info(self, stage_number):
        """Get comprehensive info about a stage"""
        stage_names = {
            1: 'Mandala 1',
            2: 'Mandala 2',
            3: 'Mandala 3',
            4: 'Rudraksha 8 Mukhi',
            5: 'Rudraksha 11 Mukhi',
            6: 'Rudraksha 14 Mukhi',
            7: 'Pratham Charana Diksha',
            8: 'Dutiya Charana',
            9: 'Tritiya Charana'
        }

        # Get completion and start dates based on stage number
        completion_dates = {
            1: self.mandala_1_completed_at,
            2: self.mandala_2_completed_at,
            3: self.mandala_3_completed_at,
            4: self.rudraksha_8_mukhi_completed_at,
            5: self.rudraksha_11_mukhi_completed_at,
            6: self.rudraksha_14_mukhi_completed_at,
            7: self.pratham_charana_diksha_completed_at,
            8: self.dutiya_charana_completed_at,
            9: self.tritiya_charana_completed_at
        }

        start_dates = {
            1: self.mandala_1_started_at,
            2: self.mandala_2_started_at,
            3: self.mandala_3_started_at,
            4: self.rudraksha_8_mukhi_started_at,
            5: self.rudraksha_11_mukhi_started_at,
            6: self.rudraksha_14_mukhi_started_at,
            7: self.pratham_charana_diksha_started_at,
            8: self.dutiya_charana_started_at,
            9: self.tritiya_charana_started_at
        }

        return {
            'stage_number': stage_number,
            'stage_name': stage_names.get(stage_number, 'Unknown'),
            'has_access': self.has_mandala_access(stage_number),
            'is_completed': self.is_stage_completed(stage_number),
            'completion_date': completion_dates.get(stage_number),
            'start_date': start_dates.get(stage_number),
            'duration_days': self.get_stage_duration_days(stage_number)
        }
    
    def __repr__(self):
        return f'<User {self.username}>'

class DonationPurpose(db.Model):
    """Model for donation purposes/categories"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, default=1)
    
    # Relationships
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_purposes')
    
    def __repr__(self):
        return f'<DonationPurpose {self.name}>'

class OfflineDonation(db.Model):
    """Model for tracking offline donations"""
    id = db.Column(db.Integer, primary_key=True)
    donor_id = db.Column(db.String(50), nullable=True)  # Donor ID from Google Sheets (not unique)
    worksheet = db.Column(db.String(100), nullable=True)  # Worksheet name from Google Sheets
    donor_name = db.Column(db.String(100), nullable=False)
    donor_email = db.Column(db.String(120), nullable=True)
    donor_phone = db.Column(db.String(20), nullable=True)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='INR')
    purpose_id = db.Column(db.Integer, db.ForeignKey('donation_purpose.id'), nullable=False)
    donation_date = db.Column(db.Date, nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)  # Cash, Bank Transfer, UPI, etc.
    reference_number = db.Column(db.String(100), nullable=True)  # Transaction reference
    notes = db.Column(db.Text, nullable=True)
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    verified_at = db.Column(db.DateTime, nullable=True)
    verified_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Relationships
    purpose = db.relationship('DonationPurpose', backref='donations')
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_donations')
    verifier = db.relationship('User', foreign_keys=[verified_by], backref='verified_donations')
    
    def __repr__(self):
        return f'<OfflineDonation {self.donor_name} - {self.amount} {self.currency}>'

class MandalaSadhanaRegistration(db.Model):
    """Model for Mandala Sadhana registrations"""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    full_name = db.Column(db.String(200), nullable=False)  # Full Name & Geo Location
    mandala_48_commitment = db.Column(db.Boolean, nullable=False)  # 48-day Mandala commitment
    mandala_144_commitment = db.Column(db.String(50), nullable=False)  # 144-day Mandala commitment (Yes/No/Not Yet Ready)
    commitment_text = db.Column(db.Text, nullable=False)  # Sadhana commitment question
    sadhana_start_date = db.Column(db.Date, nullable=False)  # When did Sadhana begin
    sadhana_type = db.Column(db.String(100), nullable=False)  # Type of Sadhana
    send_copy = db.Column(db.Boolean, default=False)  # Send copy of responses
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<MandalaSadhanaRegistration {self.full_name} - {self.sadhana_type}>'
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'email': self.email,
            'full_name': self.full_name,
            'mandala_48_commitment': self.mandala_48_commitment,
            'mandala_144_commitment': self.mandala_144_commitment,
            'commitment_text': self.commitment_text,
            'sadhana_start_date': self.sadhana_start_date.strftime('%Y-%m-%d') if self.sadhana_start_date else None,
            'sadhana_type': self.sadhana_type,
            'send_copy': self.send_copy,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

class StageAccessRequest(db.Model):
    """Model for tracking stage access requests from users"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    stage_number = db.Column(db.Integer, nullable=False)  # Stage 1-6
    status = db.Column(db.String(20), default='pending')  # 'pending', 'approved', 'rejected'
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='stage_access_requests')
    reviewer = db.relationship('User', foreign_keys=[reviewed_by], backref='reviewed_requests')
    
    def get_stage_name(self):
        """Get human-readable stage name"""
        stage_names = {
            1: 'Mandala 1',
            2: 'Mandala 2',
            3: 'Mandala 3',
            4: 'Rudraksha 8 Mukhi',
            5: 'Rudraksha 11 Mukhi',
            6: 'Rudraksha 14 Mukhi',
            7: 'Pratham Charana Diksha',
            8: 'Dutiya Charana',
            9: 'Tritiya Charana',
            # Devi Mandala stages (Devi Padathi - Kamakhya Sadhana)
            101: 'Devi Mandala 1 (33 days)',
            102: 'Devi Mandala 2 (66 days)',
            103: 'Devi Mandala 3 (99 days)'
        }
        return stage_names.get(self.stage_number, f'Stage {self.stage_number}')
    
    def __repr__(self):
        return f'<StageAccessRequest {self.user.username} - Stage {self.stage_number} - {self.status}>'

class ChatMessage(db.Model):
    """Model for chat messages between users and admin"""
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # If recipient is null, it's a broadcast or general message, but for this app:
    # User -> Admin: recipient_id can be null (implies admin) or specific admin ID
    # Admin -> User: recipient_id is the user
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    is_from_admin = db.Column(db.Boolean, default=False)

    # Synonyms for queries and serialization compatibility
    created_at = synonym('timestamp')
    is_admin_message = synonym('is_from_admin')
    
    # Relationships
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    recipient = db.relationship('User', foreign_keys=[recipient_id], backref='received_messages')

    def to_dict(self):
        return {
            'id': self.id,
            'sender_id': self.sender_id,
            'recipient_id': self.recipient_id,
            'message': self.message,
            'timestamp': self.timestamp.isoformat(),
            'is_read': self.is_read,
            'is_from_admin': self.is_from_admin,
            'sender_name': self.sender.full_name if self.sender else 'Unknown'
        }
