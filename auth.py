from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_file, send_from_directory, abort
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse
from models import db, User, StageAccessRequest, MandalaSadhanaRegistration, OfflineDonation, ChatMessage
from forms import LoginForm, RegistrationForm, AdminApprovalForm, UserSearchForm, EditProfileForm
from datetime import datetime, timedelta
import os
from io import BytesIO
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.chart import BarChart, PieChart, Reference
from openpyxl.utils import get_column_letter
from werkzeug.utils import secure_filename


auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    form = LoginForm()
    if form.validate_on_submit():
        login_identifier = (form.username.data or '').strip()
        user = User.query.filter(
            db.or_(
                db.func.lower(User.username) == login_identifier.lower(),
                db.func.lower(User.email) == login_identifier.lower()
            )
        ).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'error')
            return redirect(url_for('auth.login'))
        
        if not user.can_login():
            if not user.is_approved and not user.is_admin():
                flash('Your account is currently under review by Guruji / Administrator. Once approved, you will be able to sign in and begin Mandala 1.', 'warning')
            elif not user.is_active:
                flash('Your account has been suspended. Please contact admin.', 'error')
            return redirect(url_for('auth.login'))
        
        login_user(user, remember=form.remember_me.data)
        user.last_active = datetime.utcnow()
        db.session.commit()
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('home')
        
        flash(f'Welcome back, {user.full_name}!', 'success')
        return redirect(next_page)
    
    return render_template('auth/login.html', title='Login', form=form, page_title='Login - Daiva Anughara')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        clean_username = (form.username.data or '').strip()
        clean_email = (form.email.data or '').strip().lower()

        # Check for existing username (case-insensitive)
        existing_user = User.query.filter(db.func.lower(User.username) == clean_username.lower()).first()
        if existing_user:
            flash('Username already taken. Please choose a different one.', 'error')
            return render_template('auth/register.html', title='Register', form=form)
        
        # Check for existing email (case-insensitive)
        existing_email = User.query.filter(db.func.lower(User.email) == clean_email).first()
        if existing_email:
            flash('Email already registered. Please use a different one.', 'error')
            return render_template('auth/register.html', title='Register', form=form)
        
        # Handle profile picture upload
        profile_picture_path = None
        if form.profile_picture.data:
            file = form.profile_picture.data
            if file and file.filename:
                # Create uploads directory if it doesn't exist
                if os.getenv('VERCEL'):
                    upload_dir = os.path.join('/tmp', 'static', 'uploads', 'profiles')
                else:
                    upload_dir = os.path.join(os.getcwd(), 'static', 'uploads', 'profiles')
                try:
                    os.makedirs(upload_dir, exist_ok=True)
                except Exception:
                    pass
                
                # Generate secure filename
                filename = secure_filename(file.filename)
                # Add timestamp to make filename unique
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                name, ext = os.path.splitext(filename)
                filename = f"{name}_{timestamp}{ext}"
                
                # Save file
                file_path = os.path.join(upload_dir, filename)
                file.save(file_path)
                profile_picture_path = f"uploads/profiles/{filename}"
        
        user = User(
            username=clean_username,
            email=clean_email,
            full_name=(form.full_name.data or '').strip(),
            phone=(form.phone.data or '').strip() or None,
            address=(form.address.data or '').strip() or None,
            practice_level=form.practice_level.data,
            purpose=form.purpose.data,
            profile_picture=profile_picture_path,
            date_of_birth=form.date_of_birth.data,
            gender=form.gender.data,
            location=(form.location.data or '').strip(),
            preferred_language=form.preferred_language.data,
            referral_source=(form.referral_source.data or '').strip() or None
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration submitted successfully! Your application has been queued for Guruji / Admin verification. Once approved, you will be able to sign in and begin Mandala 1.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', title='Register', form=form, page_title='Register - Daiva Anughara')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('home'))

@auth.route('/admin/users')
@login_required
def admin_users():
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('home'))
    
    search_form = UserSearchForm()
    approval_form = AdminApprovalForm()
    
    # Get search parameters
    search_term = request.args.get('search_term', '')
    status_filter = request.args.get('status_filter', 'all')
    role_filter = request.args.get('role_filter', 'all')
    
    # Build query
    query = User.query
    
    if search_term:
        query = query.filter(
            db.or_(
                User.username.contains(search_term),
                User.email.contains(search_term),
                User.full_name.contains(search_term)
            )
        )
    
    if status_filter != 'all':
        if status_filter == 'pending':
            query = query.filter_by(is_approved=False, is_active=True)
        elif status_filter == 'approved':
            query = query.filter_by(is_approved=True, is_active=True)
        elif status_filter == 'rejected':
            query = query.filter_by(is_approved=False, is_active=False)
        elif status_filter == 'suspended':
            query = query.filter_by(is_active=False)
    
    if role_filter != 'all':
        query = query.filter_by(role=role_filter)
    
    users = query.order_by(User.created_at.desc()).all()
    
    # Get all pending stage access requests
    pending_requests = StageAccessRequest.query.filter_by(status='pending').order_by(StageAccessRequest.requested_at.desc()).all()
    
    return render_template('admin/users.html', 
                         title='User Management',
                         page_title='User Management - Daiva Anughara',
                         users=users,
                         pending_requests=pending_requests,
                         search_form=search_form,
                         approval_form=approval_form)

@auth.route('/admin/approve_user', methods=['POST'])
@login_required
def approve_user():
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    form = AdminApprovalForm()
    if form.validate_on_submit():
        user_id = form.user_id.data
        action = form.action.data
        notes = form.notes.data
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        if action == 'approve':
            user.is_approved = True
            user.approved_at = datetime.utcnow()
            user.approved_by = current_user.id
            user.is_active = True
            user.mandala_1_access = True
            if not user.mandala_1_started_at:
                user.mandala_1_started_at = datetime.utcnow()
            message = f'User {user.username} has been approved successfully. Mandala 1 access unlocked.'
        elif action == 'reject':
            user.is_approved = False
            user.is_active = False
            message = f'User {user.username} has been rejected.'
        elif action == 'suspend':
            user.is_active = False
            message = f'User {user.username} has been suspended.'
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': message})
    
    return jsonify({'success': False, 'message': 'Invalid form data'}), 400

@auth.route('/admin/user/<int:user_id>')
@auth.route('/admin/users/<int:user_id>')
@login_required
def admin_user_detail(user_id):
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('home'))
    
    user = User.query.get_or_404(user_id)
    # Get pending stage access requests for this user
    pending_requests = StageAccessRequest.query.filter_by(
        user_id=user_id,
        status='pending'
    ).order_by(StageAccessRequest.requested_at.desc()).all()
    
    return render_template('admin/user_detail.html', 
                         title='User Detail', 
                         page_title='User Detail - Daiva Anughara', 
                         user=user,
                         pending_requests=pending_requests)

@auth.route('/admin/user/<int:user_id>/stage-access', methods=['POST'])
@login_required
def update_stage_access(user_id):
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('auth.admin_users'))

    user = User.query.get_or_404(user_id)

    # Get stage access updates from form (Bhairava stages 1-6)
    mandala_2_access = request.form.get('mandala_2_access') == 'on'
    mandala_3_access = request.form.get('mandala_3_access') == 'on'
    rudraksha_8_mukhi_access = request.form.get('rudraksha_8_mukhi_access') == 'on'
    rudraksha_11_mukhi_access = request.form.get('rudraksha_11_mukhi_access') == 'on'
    rudraksha_14_mukhi_access = request.form.get('rudraksha_14_mukhi_access') == 'on'
    pratham_charana_diksha_access = request.form.get('pratham_charana_diksha_access') == 'on'
    dutiya_charana_access = request.form.get('dutiya_charana_access') == 'on'
    tritiya_charana_access = request.form.get('tritiya_charana_access') == 'on'

    # Get Devi Mandala access updates (Kamakhya Sadhana)
    devi_mandala_2_access = request.form.get('devi_mandala_2_access') == 'on'
    devi_mandala_3_access = request.form.get('devi_mandala_3_access') == 'on'

    # Update Bhairava stage access
    user.mandala_2_access = mandala_2_access
    user.mandala_3_access = mandala_3_access
    user.rudraksha_8_mukhi_access = rudraksha_8_mukhi_access
    user.rudraksha_11_mukhi_access = rudraksha_11_mukhi_access
    user.rudraksha_14_mukhi_access = rudraksha_14_mukhi_access
    user.pratham_charana_diksha_access = pratham_charana_diksha_access
    user.dutiya_charana_access = dutiya_charana_access
    user.tritiya_charana_access = tritiya_charana_access

    # Update Devi Mandala access
    user.devi_mandala_2_access = devi_mandala_2_access
    user.devi_mandala_3_access = devi_mandala_3_access

    # Check if user should start the next available stage
    next_stage = user.get_next_required_stage()
    if next_stage and not getattr(user, f'mandala_{next_stage}_started_at' if next_stage <= 3 else f'rudraksha_{5 if next_stage == 4 else 11 if next_stage == 5 else 14}_mukhi_started_at', None):
        user.start_stage(next_stage)

    db.session.commit()

    flash(f'Stage access updated for {user.username}', 'success')
    return redirect(url_for('auth.admin_user_detail', user_id=user_id))

@auth.route('/admin/user/<int:user_id>/complete-stage', methods=['POST'])
@login_required
def complete_user_stage(user_id):
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('auth.admin_users'))

    user = User.query.get_or_404(user_id)
    stage_number = int(request.form.get('stage_number', 0))

    if stage_number < 1 or stage_number > 6:
        flash('Invalid stage number', 'error')
        return redirect(url_for('auth.admin_user_detail', user_id=user_id))

    # Check if user has access to this stage
    if not user.has_mandala_access(stage_number):
        flash('User does not have access to this stage', 'error')
        return redirect(url_for('auth.admin_user_detail', user_id=user_id))

    # Check if stage is already completed
    if user.is_stage_completed(stage_number):
        flash('Stage is already completed', 'warning')
        return redirect(url_for('auth.admin_user_detail', user_id=user_id))

    # Complete the stage
    user.complete_stage(stage_number)

    # Grant access to next stage if this is not the last stage
    if stage_number < 6:
        next_stage = stage_number + 1
        access_fields = {
            2: 'mandala_2_access',
            3: 'mandala_3_access',
            4: 'rudraksha_8_mukhi_access',
            5: 'rudraksha_11_mukhi_access',
            6: 'rudraksha_14_mukhi_access'
        }

        if next_stage in access_fields:
            setattr(user, access_fields[next_stage], True)
            user.start_stage(next_stage)

    db.session.commit()

    flash(f'Stage {stage_number} completed for {user.username}', 'success')
    return redirect(url_for('auth.admin_user_detail', user_id=user_id))

@auth.route('/admin/user/<int:user_id>/reset-stage', methods=['POST'])
@login_required
def reset_user_stage(user_id):
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('auth.admin_users'))

    user = User.query.get_or_404(user_id)
    stage_number = int(request.form.get('stage_number', 0))

    if stage_number < 1 or stage_number > 6:
        flash('Invalid stage number', 'error')
        return redirect(url_for('auth.admin_user_detail', user_id=user_id))

    # Reset stage completion and dates
    completion_fields = {
        1: 'mandala_1_completed_at',
        2: 'mandala_2_completed_at',
        3: 'mandala_3_completed_at',
        4: 'rudraksha_8_mukhi_completed_at',
        5: 'rudraksha_11_mukhi_completed_at',
        6: 'rudraksha_14_mukhi_completed_at'
    }

    start_fields = {
        1: 'mandala_1_started_at',
        2: 'mandala_2_started_at',
        3: 'mandala_3_started_at',
        4: 'rudraksha_8_mukhi_started_at',
        5: 'rudraksha_11_mukhi_started_at',
        6: 'rudraksha_14_mukhi_started_at'
    }

    if stage_number in completion_fields:
        setattr(user, completion_fields[stage_number], None)
        setattr(user, start_fields[stage_number], None)

    # If resetting a stage, also reset all subsequent stages
    for i in range(stage_number + 1, 7):
        if i in completion_fields:
            setattr(user, completion_fields[i], None)
            setattr(user, start_fields[i], None)

        # Remove access to subsequent stages
        if i == 2:
            user.mandala_2_access = False
        elif i == 3:
            user.mandala_3_access = False
        elif i == 4:
            user.rudraksha_8_mukhi_access = False
        elif i == 5:
            user.rudraksha_11_mukhi_access = False
        elif i == 6:
            user.rudraksha_14_mukhi_access = False

    db.session.commit()

    flash(f'Stage {stage_number} and subsequent stages reset for {user.username}', 'success')
    return redirect(url_for('auth.admin_user_detail', user_id=user_id))

@auth.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = EditProfileForm()
    
    if form.validate_on_submit():
        current_user.address = form.address.data
        current_user.purpose = form.purpose.data
        current_user.phone = form.phone.data
        
        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('auth.profile'))
        except Exception as e:
            db.session.rollback()
            flash('Error updating profile. Please try again.', 'error')
    
    # Pre-fill form
    if request.method == 'GET':
        form.address.data = current_user.address
        form.purpose.data = current_user.purpose
        form.phone.data = current_user.phone

    return render_template('auth/profile.html', 
                         title='Profile', 
                         page_title='Profile - Daiva Anughara',
                         form=form)

@auth.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    # This would be implemented for users to edit their own profile
    pass

@auth.route('/profile-picture/<int:user_id>')
@auth.route('/profile_picture/<int:user_id>')
def profile_picture(user_id):
    """Serve user profile picture or fallback avatar"""
    user = User.query.get_or_404(user_id)
    if user.profile_picture:
        if os.getenv('VERCEL'):
            full_path = os.path.join('/tmp', 'static', user.profile_picture.replace('/', os.sep))
            if os.path.exists(full_path):
                return send_from_directory(os.path.dirname(full_path), os.path.basename(full_path))
        full_path = os.path.join(os.getcwd(), 'static', user.profile_picture.replace('/', os.sep))
        if os.path.exists(full_path):
            return send_from_directory(os.path.dirname(full_path), os.path.basename(full_path))
    # Fallback default image if exists
    default_img = os.path.join(os.getcwd(), 'static', 'images', 'logo.jpeg')
    if os.path.exists(default_img):
        return send_from_directory(os.path.dirname(default_img), os.path.basename(default_img))
    abort(404)


@auth.route('/admin/user/<int:user_id>/update-profile-picture', methods=['POST'])
@login_required
def update_profile_picture(user_id):
    """Admin endpoint to update a user's profile picture"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('home'))
    
    user = User.query.get_or_404(user_id)
    
    if 'profile_picture' not in request.files:
        flash('No file selected.', 'error')
        return redirect(url_for('auth.admin_user_detail', user_id=user_id))
    
    file = request.files['profile_picture']
    
    if file.filename == '':
        flash('No file selected.', 'error')
        return redirect(url_for('auth.admin_user_detail', user_id=user_id))
    
    if file:
        # Validate file extension
        allowed_extensions = {'jpg', 'jpeg', 'png', 'gif'}
        filename = secure_filename(file.filename)
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        
        if ext not in allowed_extensions:
            flash('Invalid file type. Only JPG, PNG, and GIF are allowed.', 'error')
            return redirect(url_for('auth.admin_user_detail', user_id=user_id))
        
        # Create uploads directory if it doesn't exist
        if os.getenv('VERCEL'):
            upload_dir = os.path.join('/tmp', 'static', 'uploads', 'profiles')
        else:
            upload_dir = os.path.join(os.getcwd(), 'static', 'uploads', 'profiles')
            
        try:
            os.makedirs(upload_dir, exist_ok=True)
        except Exception as e:
            flash(f"Upload failed: Read-only serverless filesystem. {e}", 'error')
            return redirect(url_for('auth.admin_user_detail', user_id=user_id))
        
        # Generate secure filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        name, _ = os.path.splitext(filename)
        new_filename = f"{name}_{user.id}_{timestamp}.{ext}"
        
        # Save file
        file_path = os.path.join(upload_dir, new_filename)
        file.save(file_path)
        
        # Delete old profile picture if exists
        if user.profile_picture:
            old_path = os.path.join(os.getcwd(), 'static', user.profile_picture)
            if os.path.exists(old_path):
                try:
                    os.remove(old_path)
                except Exception as e:
                    print(f"Warning: Could not delete old profile picture: {e}")
        
        # Update user's profile picture path
        user.profile_picture = f"uploads/profiles/{new_filename}"
        db.session.commit()
        
        flash(f'Profile picture updated successfully for {user.username}!', 'success')
    
    return redirect(url_for('auth.admin_user_detail', user_id=user_id))

def generate_user_report(report_type='full'):
    users = User.query.order_by(User.created_at.desc()).all()
    stage_requests = StageAccessRequest.query.all()
    vows = MandalaSadhanaRegistration.query.all()
    chat_msgs = ChatMessage.query.all()
    donations = OfflineDonation.query.all()

    now = datetime.utcnow()

    # Precompute fast lookups
    vows_by_email = {}
    for v in vows:
        email_key = (v.email or '').strip().lower()
        if email_key:
            vows_by_email.setdefault(email_key, []).append(v)

    chat_counts_by_user = {}
    for m in chat_msgs:
        if not m.is_admin_message and m.sender_id:
            chat_counts_by_user[m.sender_id] = chat_counts_by_user.get(m.sender_id, 0) + 1

    donations_by_email = {}
    for d in donations:
        d_email = (d.donor_email or '').strip().lower()
        if d_email:
            donations_by_email[d_email] = donations_by_email.get(d_email, 0.0) + (d.amount or 0.0)

    admin_names = {u.id: (u.full_name or u.username) for u in users if u.is_admin()}

    # Core Metrics Calculations
    total_users = len(users)
    admin_users = len([u for u in users if u.is_admin()])
    seeker_users = total_users - admin_users
    approved_users = len([u for u in users if u.is_approved and u.is_active and not u.is_admin()])
    pending_users = len([u for u in users if not u.is_approved and u.is_active and not u.is_admin()])
    suspended_users = len([u for u in users if not u.is_active and not u.is_admin()])
    approval_denom = approved_users + pending_users + suspended_users
    approval_rate = (approved_users / approval_denom * 100.0) if approval_denom > 0 else 0.0

    # Engagement & Retention
    active_24h = len([u for u in users if u.last_active and (now - u.last_active).total_seconds() <= 86400])
    active_7d = len([u for u in users if u.last_active and (now - u.last_active).days <= 7])
    active_30d = len([u for u in users if u.last_active and (now - u.last_active).days <= 30])
    dormant_30d = len([u for u in users if u.is_approved and u.last_active and (now - u.last_active).days > 30])
    never_active = len([u for u in users if u.is_approved and not u.last_active])
    stickiness = (active_24h / active_30d * 100.0) if active_30d > 0 else 0.0

    new_7d = len([u for u in users if u.created_at and (now - u.created_at).days <= 7])
    new_30d = len([u for u in users if u.created_at and (now - u.created_at).days <= 30])
    new_90d = len([u for u in users if u.created_at and (now - u.created_at).days <= 90])

    vetting_latencies = [(u.approved_at - u.created_at).total_seconds() / 86400.0 for u in users if u.approved_at and u.created_at and u.is_approved]
    avg_vetting_days = (sum(vetting_latencies) / len(vetting_latencies)) if vetting_latencies else 0.0

    # Stage Progression Matrix
    stage_defs = [
        (1, 'Mandala 1 (40 Days)', 'Mandala Sadhana', lambda u: u.mandala_1_access, lambda u: u.mandala_1_completed_at, lambda u: u.mandala_1_started_at),
        (2, 'Mandala 2 (40 Days)', 'Mandala Sadhana', lambda u: u.mandala_2_access, lambda u: u.mandala_2_completed_at, lambda u: u.mandala_2_started_at),
        (3, 'Mandala 3 (40 Days)', 'Mandala Sadhana', lambda u: u.mandala_3_access, lambda u: u.mandala_3_completed_at, lambda u: u.mandala_3_started_at),
        (4, 'Rudraksha 8 Mukhi', 'Sacred Mukhi', lambda u: u.rudraksha_8_mukhi_access, lambda u: u.rudraksha_8_mukhi_completed_at, lambda u: u.rudraksha_8_mukhi_started_at),
        (5, 'Rudraksha 11 Mukhi', 'Sacred Mukhi', lambda u: u.rudraksha_11_mukhi_access, lambda u: u.rudraksha_11_mukhi_completed_at, lambda u: u.rudraksha_11_mukhi_started_at),
        (6, 'Rudraksha 14 Mukhi', 'Sacred Mukhi', lambda u: u.rudraksha_14_mukhi_access, lambda u: u.rudraksha_14_mukhi_completed_at, lambda u: u.rudraksha_14_mukhi_started_at),
        (7, 'Pratham Charana Diksha', 'Diksha Phase', lambda u: u.pratham_charana_diksha_access, lambda u: u.pratham_charana_diksha_completed_at, lambda u: u.pratham_charana_diksha_started_at),
        (8, 'Dutiya Charana', 'Diksha Phase', lambda u: u.dutiya_charana_access, lambda u: u.dutiya_charana_completed_at, lambda u: u.dutiya_charana_started_at),
        (9, 'Tritiya Charana', 'Diksha Phase', lambda u: u.tritiya_charana_access, lambda u: u.tritiya_charana_completed_at, lambda u: u.tritiya_charana_started_at),
        (101, 'Devi Mandala 1 (33d)', 'Devi Sadhana', lambda u: u.devi_mandala_1_access, lambda u: None, lambda u: None),
        (102, 'Devi Mandala 2 (66d)', 'Devi Sadhana', lambda u: u.devi_mandala_2_access, lambda u: None, lambda u: None),
        (103, 'Devi Mandala 3 (99d)', 'Devi Sadhana', lambda u: u.devi_mandala_3_access, lambda u: None, lambda u: None),
    ]

    stage_metrics = []
    prev_authorized = None
    for s_num, s_name, s_cat, acc_fn, comp_fn, start_fn in stage_defs:
        auth_count = len([u for u in users if acc_fn(u)])
        comp_count = len([u for u in users if comp_fn(u) is not None])
        conv_rate = (auth_count / prev_authorized * 100.0) if (prev_authorized and prev_authorized > 0) else (100.0 if auth_count > 0 else 0.0)
        prev_authorized = auth_count

        durations = []
        for u in users:
            c_date = comp_fn(u)
            s_date = start_fn(u)
            if c_date and s_date:
                durations.append((c_date - s_date).days)
        avg_dur = (sum(durations) / len(durations)) if durations else 0

        stage_metrics.append({
            'num': s_num,
            'name': s_name,
            'category': s_cat,
            'authorized': auth_count,
            'completed': comp_count,
            'conversion_rate': conv_rate,
            'avg_duration': avg_dur
        })

    # Styling Tokens
    gold_fill = PatternFill(start_color="2B1F3D", end_color="2B1F3D", fill_type="solid")
    gold_header_font = Font(name="Arial", size=10, bold=True, color="F5DFA2")
    title_font = Font(name="Arial", size=13, bold=True, color="FFFFFF")
    sub_font = Font(name="Arial", size=9, italic=True, color="C7BEAB")
    banner_fill = PatternFill(start_color="181222", end_color="181222", fill_type="solid")
    section_fill = PatternFill(start_color="3B2D54", end_color="3B2D54", fill_type="solid")
    section_font = Font(name="Arial", size=11, bold=True, color="F5DFA2")
    zebra_fill = PatternFill(start_color="FBF9F4", end_color="FBF9F4", fill_type="solid")
    white_fill = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
    border_thin = Border(
        left=Side(style='thin', color='D4AF37'),
        right=Side(style='thin', color='D4AF37'),
        top=Side(style='thin', color='D4AF37'),
        bottom=Side(style='thin', color='D4AF37')
    )
    cell_border = Border(
        left=Side(style='thin', color='E5E0D8'),
        right=Side(style='thin', color='E5E0D8'),
        top=Side(style='thin', color='E5E0D8'),
        bottom=Side(style='thin', color='E5E0D8')
    )

    wb = Workbook()

    # =========================================================================
    # SHEET 1: EXECUTIVE KPI SCORECARD
    # =========================================================================
    ws1 = wb.active
    ws1.title = "Executive Scorecard"
    ws1.views.sheetView[0].showGridLines = True

    # Header Banner
    ws1.merge_cells("A1:K1")
    ws1.merge_cells("A2:K2")
    ws1["A1"] = "BHAIRAVA ANUGRAHA · SANCTUARY EXECUTIVE INTELLIGENCE REPORT"
    ws1["A1"].font = title_font
    ws1["A1"].fill = banner_fill
    ws1["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws1.row_dimensions[1].height = 28

    ws1["A2"] = f"Generated: {now.strftime('%Y-%m-%d %H:%M:%S')} UTC · Total Devotees: {total_users} · Active Initiated Sadhaks: {approved_users} · Pending Vetting: {pending_users}"
    ws1["A2"].font = sub_font
    ws1["A2"].fill = banner_fill
    ws1["A2"].alignment = Alignment(horizontal="center", vertical="center")
    ws1.row_dimensions[2].height = 20

    # Section 1: Executive Sanctuary Scorecard
    ws1["A4"] = "1. EXECUTIVE SANCTUARY SCORECARD"
    ws1["A4"].font = section_font
    ws1["A4"].fill = section_fill
    ws1.merge_cells("A4:K4")

    scorecard_rows = [
        ("Seeker Growth & Scale", [
            ("Total Registered Devotees", total_users),
            ("Active Initiated Sadhaks", approved_users),
            ("Pending Vetting Backlog", pending_users),
            ("Suspended / Inactive", suspended_users),
            ("Vetting Approval Rate", f"{approval_rate:.1f}%"),
            ("New Registrations (7 Days)", new_7d),
            ("New Registrations (30 Days)", new_30d),
        ]),
        ("Engagement & Retention", [
            ("Daily Active Users (DAU 24h)", active_24h),
            ("Weekly Active Users (WAU 7d)", active_7d),
            ("Monthly Active Users (MAU 30d)", active_30d),
            ("Platform Stickiness (DAU/MAU)", f"{stickiness:.1f}%"),
            ("Dormant Seekers (>30d Inactive)", dormant_30d),
            ("Never Logged In (Approved)", never_active),
            ("Avg Vetting Latency", f"{avg_vetting_days:.1f} days"),
        ]),
        ("Stage Funnel & Milestones", [
            ("Mandala 1 Authorized", stage_metrics[0]['authorized']),
            ("Mandala 2 Advanced", stage_metrics[1]['authorized']),
            ("Mandala 3 Completed", stage_metrics[2]['authorized']),
            ("Rudraksha Mukhi Diksha", sum(m['authorized'] for m in stage_metrics[3:6])),
            ("Charana Diksha Initiations", sum(m['authorized'] for m in stage_metrics[6:9])),
            ("Devi Mandala Initiations", sum(m['authorized'] for m in stage_metrics[9:])),
            ("Pending Stage Advance Requests", len([r for r in stage_requests if r.status == 'pending'])),
        ]),
        ("Discipline, Vows & Community", [
            ("48-Day Mandala Vows", len([v for v in vows if v.mandala_48_commitment])),
            ("144-Day Mandala Vows", len([v for v in vows if v.mandala_144_commitment == 'Yes'])),
            ("Mentorship Messages Sent", len([m for m in chat_msgs if not m.is_admin_message])),
            ("Devotees Mentored via Chat", len(chat_counts_by_user)),
            ("Total Sacred Bhiksha Recorded", f"INR {sum(d.amount or 0 for d in donations):,.2f}"),
            ("Bhiksha Contributions Count", len(donations)),
            ("Platform Role Count (Admins)", admin_users),
        ]),
    ]

    curr_row = 6
    for cat_title, items in scorecard_rows:
        ws1.cell(row=curr_row, column=1, value=cat_title).font = Font(name="Arial", size=10, bold=True, color="2B1F3D")
        ws1.cell(row=curr_row, column=1).fill = PatternFill(start_color="F5EFCF", end_color="F5EFCF", fill_type="solid")
        ws1.cell(row=curr_row, column=2, value="Value").font = Font(name="Arial", size=10, bold=True, color="2B1F3D")
        ws1.cell(row=curr_row, column=2).fill = PatternFill(start_color="F5EFCF", end_color="F5EFCF", fill_type="solid")
        curr_row += 1
        for k, val in items:
            c1 = ws1.cell(row=curr_row, column=1, value=k)
            c2 = ws1.cell(row=curr_row, column=2, value=val)
            c1.border = cell_border
            c2.border = cell_border
            c1.font = Font(name="Arial", size=9)
            c2.font = Font(name="Arial", size=9, bold=True)
            c2.alignment = Alignment(horizontal="right")
            curr_row += 1
        curr_row += 1

    # Stage Progression Table
    ws1.cell(row=curr_row, column=1, value="2. SPIRITUAL STAGE PROGRESSION & FUNNEL ANALYSIS").font = section_font
    ws1.cell(row=curr_row, column=1).fill = section_fill
    ws1.merge_cells(start_row=curr_row, start_column=1, end_row=curr_row, end_column=7)
    curr_row += 1

    stage_headers = ["Stage ID", "Stage Discipline Name", "Category", "Authorized Seekers", "Completed Seekers", "Stage Conversion %", "Avg Duration (Days)"]
    for col_idx, h in enumerate(stage_headers, 1):
        cell = ws1.cell(row=curr_row, column=col_idx, value=h)
        cell.font = gold_header_font
        cell.fill = gold_fill
        cell.alignment = Alignment(horizontal="center")
        cell.border = border_thin
    curr_row += 1

    stage_table_start = curr_row
    for sm in stage_metrics:
        ws1.cell(row=curr_row, column=1, value=sm['num']).alignment = Alignment(horizontal="center")
        ws1.cell(row=curr_row, column=2, value=sm['name'])
        ws1.cell(row=curr_row, column=3, value=sm['category'])
        ws1.cell(row=curr_row, column=4, value=sm['authorized']).alignment = Alignment(horizontal="right")
        ws1.cell(row=curr_row, column=5, value=sm['completed']).alignment = Alignment(horizontal="right")
        ws1.cell(row=curr_row, column=6, value=f"{sm['conversion_rate']:.1f}%").alignment = Alignment(horizontal="right")
        ws1.cell(row=curr_row, column=7, value=sm['avg_duration']).alignment = Alignment(horizontal="right")
        for col_idx in range(1, 8):
            ws1.cell(row=curr_row, column=col_idx).border = cell_border
            ws1.cell(row=curr_row, column=col_idx).font = Font(name="Arial", size=9)
        curr_row += 1
    stage_table_end = curr_row - 1

    # Chart Data Setup
    chart_data_start = curr_row + 2
    ws1.cell(row=chart_data_start, column=4, value="Status").font = gold_header_font
    ws1.cell(row=chart_data_start, column=4).fill = gold_fill
    ws1.cell(row=chart_data_start, column=5, value="Count").font = gold_header_font
    ws1.cell(row=chart_data_start, column=5).fill = gold_fill

    status_rows = [
        ("Approved Sādhaks", approved_users),
        ("Pending Vetting", pending_users),
        ("Suspended / Inactive", suspended_users),
        ("Administrators", admin_users)
    ]
    for idx, (st_name, st_val) in enumerate(status_rows, 1):
        ws1.cell(row=chart_data_start + idx, column=4, value=st_name)
        ws1.cell(row=chart_data_start + idx, column=5, value=st_val)

    # Native Charts on Sheet 1
    try:
        bc = BarChart()
        bc.title = "Stage Progression Distribution"
        bc.style = 10
        bc.height = 12
        bc.width = 18
        bc_data = Reference(ws1, min_col=4, min_row=stage_table_start-1, max_row=stage_table_end)
        bc_cats = Reference(ws1, min_col=2, min_row=stage_table_start, max_row=stage_table_end)
        bc.add_data(bc_data, titles_from_data=True)
        bc.set_categories(bc_cats)
        ws1.add_chart(bc, "D6")

        pie = PieChart()
        pie.title = "Seeker Status Breakdown"
        pie.height = 10
        pie.width = 14
        pie_data = Reference(ws1, min_col=5, min_row=chart_data_start, max_row=chart_data_start + len(status_rows))
        pie_cats = Reference(ws1, min_col=4, min_row=chart_data_start + 1, max_row=chart_data_start + len(status_rows))
        pie.add_data(pie_data, titles_from_data=True)
        pie.set_categories(pie_cats)
        ws1.add_chart(pie, "D24")
    except Exception as e:
        print(f"Warning: Chart rendering skipped: {e}")

    ws1.column_dimensions["A"].width = 34
    ws1.column_dimensions["B"].width = 28
    for col in range(3, 8):
        ws1.column_dimensions[get_column_letter(col)].width = 20

    # =========================================================================
    # SHEET 2: MASTER SEEKER DOSSIER (35 granular attributes)
    # =========================================================================
    ws2 = wb.create_sheet(title="Seeker Master Dossier")
    ws2.views.sheetView[0].showGridLines = True

    dossier_headers = [
        "User ID", "Username", "Full Name", "Email", "Phone",
        "Location", "Language", "Gender", "Date of Birth", "Age",
        "Referral Source", "Role", "Account Status", "Registration Date (UTC)",
        "Approval Date", "Approved By", "Vetting Latency (Days)",
        "Last Active (UTC)", "Days Inactive", "Activity State",
        "Current Highest Stage", "Mandala 1 Authorized", "Mandala 2 Authorized", "Mandala 3 Authorized",
        "Rudraksha 8M", "Rudraksha 11M", "Rudraksha 14M",
        "Diksha Pratham", "Diksha Dutiya", "Diksha Tritiya", "Devi Mandala Access",
        "Mandala 1 Days", "Mandala 2 Days", "Mandala 3 Days",
        "Practice Level", "Mandala Vow Registered", "Mentorship Chats Sent",
        "Sacred Bhiksha Donated (INR)", "Sadhana Purpose / Spiritual Vow"
    ]

    ws2.append(dossier_headers)
    ws2.row_dimensions[1].height = 26

    for col_idx in range(1, len(dossier_headers) + 1):
        cell = ws2.cell(row=1, column=col_idx)
        cell.font = gold_header_font
        cell.fill = gold_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = border_thin

    fill_approved = PatternFill(start_color="D1FAE5", end_color="D1FAE5", fill_type="solid")
    font_approved = Font(color="065F46", bold=True, size=9)
    fill_pending = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")
    font_pending = Font(color="92400E", bold=True, size=9)
    fill_suspended = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
    font_suspended = Font(color="991B1B", bold=True, size=9)
    fill_admin = PatternFill(start_color="DBEAFE", end_color="DBEAFE", fill_type="solid")
    font_admin = Font(color="1E40AF", bold=True, size=9)

    for row_idx, u in enumerate(users, 2):
        status = "Admin" if u.is_admin() else ("Approved" if u.is_approved else ("Suspended" if not u.is_active else "Pending"))

        age_val = ""
        if u.date_of_birth:
            age_val = (now.date() - u.date_of_birth).days // 365

        v_lat = round((u.approved_at - u.created_at).total_seconds() / 86400.0, 1) if (u.approved_at and u.created_at) else ""

        days_inactive = (now - u.last_active).days if u.last_active else None
        if not u.last_active:
            act_state = "Never Logged In"
        elif days_inactive <= 7:
            act_state = "Active (<=7d)"
        elif days_inactive <= 30:
            act_state = "Recent (8-30d)"
        else:
            act_state = "Dormant (>30d)"

        highest_st = u.get_current_stage()
        highest_st_name = {
            1: 'Stage 1 (Mandala 1)',
            2: 'Stage 2 (Mandala 2)',
            3: 'Stage 3 (Mandala 3)',
            4: 'Stage 4 (Rudraksha 8M)',
            5: 'Stage 5 (Rudraksha 11M)',
            6: 'Stage 6 (Rudraksha 14M)'
        }.get(highest_st, f"Stage {highest_st}")

        u_email_key = (u.email or '').strip().lower()
        vow_list = vows_by_email.get(u_email_key, [])
        vow_status = "No"
        if vow_list:
            vow_types = [v.sadhana_type for v in vow_list if v.sadhana_type]
            vow_status = f"Yes ({', '.join(vow_types[:2])})" if vow_types else "Yes"

        chats_sent = chat_counts_by_user.get(u.id, 0)
        bhiksha_amt = donations_by_email.get(u_email_key, 0.0)

        m1_days = u.get_stage_duration_days(1)
        m2_days = u.get_stage_duration_days(2)
        m3_days = u.get_stage_duration_days(3)

        row_data = [
            u.id,
            u.username,
            u.full_name or u.username,
            u.email,
            u.phone or "",
            u.location or "",
            u.preferred_language or "",
            u.gender or "",
            u.date_of_birth.strftime("%Y-%m-%d") if u.date_of_birth else "",
            age_val,
            u.referral_source or "",
            u.role,
            status,
            u.created_at.strftime("%Y-%m-%d %H:%M") if u.created_at else "",
            u.approved_at.strftime("%Y-%m-%d %H:%M") if u.approved_at else "",
            admin_names.get(u.approved_by, str(u.approved_by or "")),
            v_lat,
            u.last_active.strftime("%Y-%m-%d %H:%M") if u.last_active else "Never",
            days_inactive if days_inactive is not None else "—",
            act_state,
            highest_st_name,
            "Yes" if u.mandala_1_access else "No",
            "Yes" if u.mandala_2_access else "No",
            "Yes" if u.mandala_3_access else "No",
            f"8M:{'Y' if u.rudraksha_8_mukhi_access else 'N'} 11M:{'Y' if u.rudraksha_11_mukhi_access else 'N'} 14M:{'Y' if u.rudraksha_14_mukhi_access else 'N'}",
            f"1:{'Y' if u.pratham_charana_diksha_access else 'N'} 2:{'Y' if u.dutiya_charana_access else 'N'} 3:{'Y' if u.tritiya_charana_access else 'N'}",
            f"1:{'Y' if u.devi_mandala_1_access else 'N'} 2:{'Y' if u.devi_mandala_2_access else 'N'} 3:{'Y' if u.devi_mandala_3_access else 'N'}",
            m1_days,
            m2_days,
            m3_days,
            u.practice_level or "Beginner",
            vow_status,
            chats_sent,
            bhiksha_amt,
            u.purpose or ""
        ]
        ws2.append(row_data)

        row_fill = zebra_fill if (row_idx % 2 == 0) else white_fill
        for col_idx in range(1, len(dossier_headers) + 1):
            c = ws2.cell(row=row_idx, column=col_idx)
            c.fill = row_fill
            c.border = cell_border
            c.font = Font(name="Arial", size=9)

        status_cell = ws2.cell(row=row_idx, column=13)
        if status == "Approved":
            status_cell.fill = fill_approved
            status_cell.font = font_approved
        elif status == "Pending":
            status_cell.fill = fill_pending
            status_cell.font = font_pending
        elif status == "Suspended":
            status_cell.fill = fill_suspended
            status_cell.font = font_suspended
        elif status == "Admin":
            status_cell.fill = fill_admin
            status_cell.font = font_admin

        ws2.cell(row=row_idx, column=38).number_format = '"₹"#,##0.00'

    ws2.auto_filter.ref = f"A1:{get_column_letter(len(dossier_headers))}{len(users) + 1}"
    for col in ws2.columns:
        col_letter = get_column_letter(col[0].column)
        col_len = max(len(str(cell.value or '')) for cell in col[:40])
        ws2.column_dimensions[col_letter].width = min(max(col_len + 3, 11), 38)
    ws2.column_dimensions["A"].width = 9
    ws2.column_dimensions["D"].width = 24
    ws2.column_dimensions["AM"].width = 38  # Purpose column

    # =========================================================================
    # SHEET 3: STAGE PROGRESSION ANALYTICS
    # =========================================================================
    ws3 = wb.create_sheet(title="Stage Progression Roster")
    ws3.views.sheetView[0].showGridLines = True

    ws3.merge_cells("A1:G1")
    ws3["A1"] = "SANCTUARY SPIRITUAL STAGES & ACTIVE SĀDHAK ROSTER"
    ws3["A1"].font = title_font
    ws3["A1"].fill = banner_fill
    ws3["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws3.row_dimensions[1].height = 26

    curr_s3_row = 3
    for s_num, s_name, s_cat, acc_fn, comp_fn, start_fn in stage_defs:
        stage_seekers = [u for u in users if acc_fn(u)]
        ws3.cell(row=curr_s3_row, column=1, value=f"{s_name} ({s_cat}) — {len(stage_seekers)} Authorized Devotees").font = section_font
        ws3.cell(row=curr_s3_row, column=1).fill = section_fill
        ws3.merge_cells(start_row=curr_s3_row, start_column=1, end_row=curr_s3_row, end_column=6)
        curr_s3_row += 1

        headers_sub = ["User ID", "Seeker Name", "Username", "Email", "Completed?", "Days on Stage"]
        for c_i, h in enumerate(headers_sub, 1):
            cell = ws3.cell(row=curr_s3_row, column=c_i, value=h)
            cell.font = gold_header_font
            cell.fill = gold_fill
            cell.alignment = Alignment(horizontal="center")
            cell.border = border_thin
        curr_s3_row += 1

        if stage_seekers:
            for u in stage_seekers:
                is_comp = comp_fn(u) is not None if comp_fn(u) is not None else False
                dur = u.get_stage_duration_days(s_num if s_num < 10 else 1)
                ws3.cell(row=curr_s3_row, column=1, value=u.id).alignment = Alignment(horizontal="center")
                ws3.cell(row=curr_s3_row, column=2, value=u.full_name or u.username)
                ws3.cell(row=curr_s3_row, column=3, value=f"@{u.username}")
                ws3.cell(row=curr_s3_row, column=4, value=u.email)
                ws3.cell(row=curr_s3_row, column=5, value="Completed" if is_comp else "In Progress").alignment = Alignment(horizontal="center")
                ws3.cell(row=curr_s3_row, column=6, value=f"{dur} days").alignment = Alignment(horizontal="right")
                for col_idx in range(1, 7):
                    ws3.cell(row=curr_s3_row, column=col_idx).border = cell_border
                    ws3.cell(row=curr_s3_row, column=col_idx).font = Font(name="Arial", size=9)
                curr_s3_row += 1
        else:
            ws3.cell(row=curr_s3_row, column=1, value="No seekers currently authorized for this sacred milestone.").font = Font(name="Arial", size=9, italic=True)
            ws3.merge_cells(start_row=curr_s3_row, start_column=1, end_row=curr_s3_row, end_column=6)
            curr_s3_row += 1
        curr_s3_row += 1

    for col in range(1, 7):
        ws3.column_dimensions[get_column_letter(col)].width = 22

    # =========================================================================
    # SHEET 4: ACTION ITEMS & VETTING QUEUE
    # =========================================================================
    ws4 = wb.create_sheet(title="Action Items & Vetting Queue")
    ws4.views.sheetView[0].showGridLines = True

    ws4.merge_cells("A1:H1")
    ws4["A1"] = "SANCTUARY GOVERNANCE: PENDING VETTING & AUTHORIZATION BACKLOG"
    ws4["A1"].font = title_font
    ws4["A1"].fill = banner_fill
    ws4["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws4.row_dimensions[1].height = 26

    curr_s4_row = 3
    # Section A: Pending Devotee Vetting
    pending_devotees = [u for u in users if not u.is_approved and u.is_active and not u.is_admin()]
    pending_devotees.sort(key=lambda u: u.created_at or now)

    ws4.cell(row=curr_s4_row, column=1, value=f"A. PENDING SEEKER INITIATION APPROVALS ({len(pending_devotees)} Awaiting Vetting)").font = section_font
    ws4.cell(row=curr_s4_row, column=1).fill = section_fill
    ws4.merge_cells(start_row=curr_s4_row, start_column=1, end_row=curr_s4_row, end_column=8)
    curr_s4_row += 1

    queue_headers = ["User ID", "Seeker Name", "Username", "Email", "Phone", "Registration Date", "Days Waiting", "Sadhana Vow Statement"]
    for c_i, h in enumerate(queue_headers, 1):
        cell = ws4.cell(row=curr_s4_row, column=c_i, value=h)
        cell.font = gold_header_font
        cell.fill = gold_fill
        cell.alignment = Alignment(horizontal="center")
        cell.border = border_thin
    curr_s4_row += 1

    if pending_devotees:
        for u in pending_devotees:
            wait_days = (now - u.created_at).days if u.created_at else 0
            ws4.cell(row=curr_s4_row, column=1, value=u.id).alignment = Alignment(horizontal="center")
            ws4.cell(row=curr_s4_row, column=2, value=u.full_name or u.username)
            ws4.cell(row=curr_s4_row, column=3, value=f"@{u.username}")
            ws4.cell(row=curr_s4_row, column=4, value=u.email)
            ws4.cell(row=curr_s4_row, column=5, value=u.phone or "—")
            ws4.cell(row=curr_s4_row, column=6, value=u.created_at.strftime("%Y-%m-%d %H:%M") if u.created_at else "—")
            c_wait = ws4.cell(row=curr_s4_row, column=7, value=f"{wait_days} days")
            c_wait.alignment = Alignment(horizontal="right")
            if wait_days >= 3:
                c_wait.font = Font(name="Arial", size=9, bold=True, color="991B1B")
            ws4.cell(row=curr_s4_row, column=8, value=u.purpose or "—")
            for col_idx in range(1, 9):
                ws4.cell(row=curr_s4_row, column=col_idx).border = cell_border
                if col_idx != 7 or wait_days < 3:
                    ws4.cell(row=curr_s4_row, column=col_idx).font = Font(name="Arial", size=9)
            curr_s4_row += 1
    else:
        ws4.cell(row=curr_s4_row, column=1, value="All registration vetting requests are completely cleared.").font = Font(name="Arial", size=9, italic=True)
        ws4.merge_cells(start_row=curr_s4_row, start_column=1, end_row=curr_s4_row, end_column=8)
        curr_s4_row += 1

    curr_s4_row += 2

    # Section B: Pending Stage Advance Requests
    pending_st_reqs = [r for r in stage_requests if r.status == 'pending']
    pending_st_reqs.sort(key=lambda r: r.requested_at or now)

    ws4.cell(row=curr_s4_row, column=1, value=f"B. PENDING STAGE PROGRESSION REQUESTS ({len(pending_st_reqs)} Awaiting Authorization)").font = section_font
    ws4.cell(row=curr_s4_row, column=1).fill = section_fill
    ws4.merge_cells(start_row=curr_s4_row, start_column=1, end_row=curr_s4_row, end_column=8)
    curr_s4_row += 1

    req_headers = ["Request ID", "User ID", "Seeker Name", "Username", "Email", "Requested Stage", "Requested Timestamp", "Days Pending"]
    for c_i, h in enumerate(req_headers, 1):
        cell = ws4.cell(row=curr_s4_row, column=c_i, value=h)
        cell.font = gold_header_font
        cell.fill = gold_fill
        cell.alignment = Alignment(horizontal="center")
        cell.border = border_thin
    curr_s4_row += 1

    if pending_st_reqs:
        for r in pending_st_reqs:
            wait_days = (now - r.requested_at).days if r.requested_at else 0
            ws4.cell(row=curr_s4_row, column=1, value=r.id).alignment = Alignment(horizontal="center")
            ws4.cell(row=curr_s4_row, column=2, value=r.user_id).alignment = Alignment(horizontal="center")
            ws4.cell(row=curr_s4_row, column=3, value=r.user.full_name or r.user.username if r.user else "Unknown")
            ws4.cell(row=curr_s4_row, column=4, value=f"@{r.user.username}" if r.user else "—")
            ws4.cell(row=curr_s4_row, column=5, value=r.user.email if r.user else "—")
            ws4.cell(row=curr_s4_row, column=6, value=r.get_stage_name())
            ws4.cell(row=curr_s4_row, column=7, value=r.requested_at.strftime("%Y-%m-%d %H:%M") if r.requested_at else "—")
            c_wait = ws4.cell(row=curr_s4_row, column=8, value=f"{wait_days} days")
            c_wait.alignment = Alignment(horizontal="right")
            if wait_days >= 2:
                c_wait.font = Font(name="Arial", size=9, bold=True, color="991B1B")
            for col_idx in range(1, 9):
                ws4.cell(row=curr_s4_row, column=col_idx).border = cell_border
                if col_idx != 8 or wait_days < 2:
                    ws4.cell(row=curr_s4_row, column=col_idx).font = Font(name="Arial", size=9)
            curr_s4_row += 1
    else:
        ws4.cell(row=curr_s4_row, column=1, value="All stage progression requests are completely authorized.").font = Font(name="Arial", size=9, italic=True)
        ws4.merge_cells(start_row=curr_s4_row, start_column=1, end_row=curr_s4_row, end_column=8)
        curr_s4_row += 1

    for col in range(1, 9):
        ws4.column_dimensions[get_column_letter(col)].width = 22
    ws4.column_dimensions["H"].width = 36

    # Save to BytesIO object
    excel_file = BytesIO()
    wb.save(excel_file)
    excel_file.seek(0)
    return excel_file

@auth.route('/admin/users/report')
@login_required
def user_report():
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('home'))

    report_type = request.args.get('type', 'full')
    excel_file = generate_user_report(report_type=report_type)
    date_tag = datetime.utcnow().strftime("%Y%m%d")

    return send_file(
        excel_file,
        as_attachment=True,
        download_name=f'Bhairava_Sanctuary_Intelligence_Report_{date_tag}.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@auth.route('/admin/users/kpi_data')
@login_required
def user_kpi_data():
    if not current_user.is_admin():
        return jsonify({'error': 'Access denied'}), 403

    users = User.query.all()

    total_users = len(users)
    approved_users = len([u for u in users if u.is_approved and u.is_active])
    pending_users = len([u for u in users if not u.is_approved and u.is_active])
    suspended_users = len([u for u in users if not u.is_active and not u.is_admin()])

    mandala_2_users = len([u for u in users if u.mandala_2_access])
    mandala_3_users = len([u for u in users if u.mandala_3_access])

    # Calculate average days to approval
    approved_users_with_approval_date = [u for u in users if u.is_approved and u.approved_at and u.created_at]
    if approved_users_with_approval_date:
        total_days_to_approval = sum([(u.approved_at - u.created_at).days for u in approved_users_with_approval_date])
        average_days_to_approval = total_days_to_approval / len(approved_users_with_approval_date)
    else:
        average_days_to_approval = 0

    data = {
        'kpis': {
            'total_users': total_users,
            'approved_users': approved_users,
            'pending_users': pending_users,
            'suspended_users': suspended_users,
            'average_days_to_approval': round(average_days_to_approval, 2)
        },
        'charts': {
            'user_status_distribution': {
                'labels': ['Approved', 'Pending', 'Suspended'],
                'data': [approved_users, pending_users, suspended_users]
            },
            'mandala_access_distribution': {
                'labels': ['Mandala 2 Access', 'Mandala 3 Access'],
                'data': [mandala_2_users, mandala_3_users]
            }
        }
    }
    return jsonify(data)

@auth.route('/request_stage_access', methods=['POST'])
@auth.route('/request-stage-access', methods=['POST'])
@login_required
def request_stage_access():
    """Allow users to request access for a locked stage"""
    try:
        data = request.get_json(silent=True) or {}
        stage_number = request.form.get('stage_number', type=int) or data.get('stage_number')
        if stage_number is not None:
            stage_number = int(stage_number)
        
        if not stage_number or stage_number < 1 or stage_number > 9:
            return jsonify({'success': False, 'message': 'Invalid stage number'}), 400
        
        # Check if user already has access to this stage
        if current_user.has_mandala_access(stage_number):
            return jsonify({'success': False, 'message': 'You already have access to this stage'}), 400
        
        # Check if there's already a pending request for this stage
        existing_request = StageAccessRequest.query.filter_by(
            user_id=current_user.id,
            stage_number=stage_number,
            status='pending'
        ).first()
        
        if existing_request:
            return jsonify({'success': False, 'message': 'You already have a pending request for this stage'}), 400
        
        # Create new request
        new_request = StageAccessRequest(
            user_id=current_user.id,
            stage_number=stage_number,
            status='pending'
        )
        
        db.session.add(new_request)
        db.session.commit()
        
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
        stage_name = stage_names.get(stage_number, f'Stage {stage_number}')
        
        return jsonify({
            'success': True,
            'message': f'Access request for {stage_name} has been sent to administrators'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500

@auth.route('/request_devi_stage_access', methods=['POST'])
@auth.route('/request-devi-stage-access', methods=['POST'])
@login_required
def request_devi_stage_access():
    """Allow users to request access for a locked Devi Mandala stage"""
    try:
        data = request.get_json(silent=True) or {}
        mandala_number = request.form.get('mandala_number', type=int) or data.get('mandala_number')
        if mandala_number is not None:
            mandala_number = int(mandala_number)
        
        if not mandala_number or mandala_number < 1 or mandala_number > 3:
            return jsonify({'success': False, 'message': 'Invalid mandala number'}), 400
        
        # Check if user is approved
        if not current_user.is_approved and not current_user.is_admin():
            return jsonify({'success': False, 'message': 'Your account needs to be approved first'}), 400
        
        # Check if there's already a pending request for this Devi mandala
        # Using stage_number 101, 102, 103 for Devi mandalas to distinguish from Bhairava stages
        devi_stage_number = 100 + mandala_number
        
        existing_request = StageAccessRequest.query.filter_by(
            user_id=current_user.id,
            stage_number=devi_stage_number,
            status='pending'
        ).first()
        
        if existing_request:
            return jsonify({'success': False, 'message': 'You already have a pending request for this Devi Mandala'}), 400
        
        # Create new request
        new_request = StageAccessRequest(
            user_id=current_user.id,
            stage_number=devi_stage_number,
            status='pending'
        )
        
        db.session.add(new_request)
        db.session.commit()
        
        mandala_days = {1: 33, 2: 66, 3: 99}
        
        return jsonify({
            'success': True,
            'message': f'Access request for Devi Mandala {mandala_number} ({mandala_days.get(mandala_number, 33)} days) has been sent to administrators'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500


@auth.route('/admin/approve_stage_request/<int:request_id>', methods=['POST'])
@login_required
def approve_stage_request(request_id):
    """Admin endpoint to approve a stage access request"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        access_request = StageAccessRequest.query.get_or_404(request_id)
        
        if access_request.status != 'pending':
            return jsonify({'success': False, 'message': 'Request has already been processed'}), 400
        
        action = request.form.get('action', 'approve')  # 'approve' or 'reject'
        
        if action == 'approve':
            # Grant access to the stage
            user = access_request.user
            
            # Grant access based on stage number
            if access_request.stage_number == 2:
                user.mandala_2_access = True
            elif access_request.stage_number == 3:
                user.mandala_3_access = True
            elif access_request.stage_number == 4:
                user.rudraksha_8_mukhi_access = True
            elif access_request.stage_number == 5:
                user.rudraksha_11_mukhi_access = True
            elif access_request.stage_number == 6:
                user.rudraksha_14_mukhi_access = True
            elif access_request.stage_number == 7:
                user.pratham_charana_diksha_access = True
            elif access_request.stage_number == 8:
                user.dutiya_charana_access = True
            elif access_request.stage_number == 9:
                user.tritiya_charana_access = True
            # Devi Mandala stages (Devi Padathi - Kamakhya Sadhana)
            elif access_request.stage_number == 101:
                user.devi_mandala_1_access = True
            elif access_request.stage_number == 102:
                user.devi_mandala_2_access = True
            elif access_request.stage_number == 103:
                user.devi_mandala_3_access = True
            
            # Start the stage if it's the next one
            next_stage = user.get_next_required_stage()
            if next_stage == access_request.stage_number:
                user.start_stage(access_request.stage_number)
            
            access_request.status = 'approved'
            access_request.reviewed_at = datetime.utcnow()
            access_request.reviewed_by = current_user.id
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Access to {access_request.get_stage_name()} has been granted to {user.username}'
            })
        else:  # reject
            access_request.status = 'rejected'
            access_request.reviewed_at = datetime.utcnow()
            access_request.reviewed_by = current_user.id
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Access request for {access_request.get_stage_name()} has been rejected'
            })
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'An error occurred. Please try again.'}), 500

@auth.route('/admin/user/<int:user_id>/change-password', methods=['POST'])
@login_required
def admin_change_password(user_id):
    """Admin endpoint to change a user's password"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': 'Access denied. Admin privileges required.'}), 403
    
    try:
        user = User.query.get_or_404(user_id)
        
        # Prevent changing admin passwords (security measure)
        if user.is_admin() and user.id != current_user.id:
            return jsonify({'success': False, 'message': 'Cannot change password of another admin'}), 403
        
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        # Validation
        if not new_password:
            return jsonify({'success': False, 'message': 'Password is required'}), 400
        
        if len(new_password) < 6:
            return jsonify({'success': False, 'message': 'Password must be at least 6 characters long'}), 400
        
        if new_password != confirm_password:
            return jsonify({'success': False, 'message': 'Passwords do not match'}), 400
        
        # Update password
        user.set_password(new_password)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Password successfully changed for {user.username}'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'An error occurred. Please try again.'}), 500