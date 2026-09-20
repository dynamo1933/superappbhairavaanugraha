import os
import sys
import json
import csv
import re
import socket
import io
import base64
from datetime import datetime, timedelta

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
load_dotenv()

from flask import (
    Flask, render_template, jsonify, request, send_from_directory,
    abort, Response, redirect, url_for, flash, send_file
)
from flask_login import (
    LoginManager, current_user, login_required, login_user, logout_user
)
from flask_wtf.csrf import CSRFProtect, generate_csrf, CSRFError

# ==============================================================================
# BASE PATHS & DIRECTORY STRUCTURE
# ==============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

IS_VERCEL = bool(os.getenv('VERCEL') or os.getenv('AWS_LAMBDA_FUNCTION_NAME'))

LOCAL_BHAIRVA = r'C:\Users\dynam\Desktop\Bhairva'
LOCAL_INSTA = r'C:\Users\dynam\Desktop\instagram_scrap'

BHAIRVA_DIR = os.environ.get('BHAIRVA_DIR')
if not BHAIRVA_DIR:
    local_data_bhairva = os.path.join(BASE_DIR, 'data', 'bhairva')
    BHAIRVA_DIR = local_data_bhairva if os.path.exists(local_data_bhairva) else LOCAL_BHAIRVA

INSTA_DIR = os.environ.get('INSTA_DIR')
if not INSTA_DIR:
    local_data_insta = os.path.join(BASE_DIR, 'data', 'instagram_scrap')
    INSTA_DIR = local_data_insta if os.path.exists(local_data_insta) else LOCAL_INSTA

# Ensure runtime directories exist safely (use /tmp on Vercel read-only filesystem)
if IS_VERCEL:
    instance_dir = os.path.join('/tmp', 'instance')
    uploads_dir = os.path.join('/tmp', 'uploads')
else:
    instance_dir = os.path.join(BASE_DIR, 'instance')
    uploads_dir = os.path.join(BASE_DIR, 'uploads')

for d in (instance_dir, uploads_dir):
    try:
        os.makedirs(d, exist_ok=True)
    except Exception as e:
        print(f"[*] Note: Could not create directory {d}: {e}", file=sys.stderr)


# Add paths for optional helper imports
if os.path.exists(BHAIRVA_DIR) and BHAIRVA_DIR not in sys.path:
    sys.path.append(BHAIRVA_DIR)
if os.path.exists(INSTA_DIR) and INSTA_DIR not in sys.path:
    sys.path.append(INSTA_DIR)

try:
    import db_helper
except Exception as e:
    db_helper = None

# ==============================================================================
# FLASK APPLICATION CREATION & CONFIGURATION
# ==============================================================================
app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, 'templates'),
    static_folder=os.path.join(BASE_DIR, 'static')
)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.auto_reload = True
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'bhairava-anugraha-superapp-sacred-key-2026')
app.config['UPLOAD_FOLDER'] = uploads_dir
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Database URI configuration with Turso / PostgreSQL / local SQLite fallbacks
db_url = os.getenv('DATABASE_URL') or os.getenv('SQLALCHEMY_DATABASE_URI')
if db_url:
    db_url = db_url.strip().replace("\n", "").replace("\r", "")

if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

if db_url and db_url.startswith("libsql://"):
    db_url = db_url.replace("libsql://", "sqlite+libsql://", 1)

if db_url and "sqlite+libsql://" in db_url and "?" in db_url:
    parts = db_url.split("?", 1)
    if not parts[0].endswith("/"):
        db_url = f"{parts[0]}/?{parts[1]}"

# Fallback to local SQLite if using sqlite+libsql but driver is not available
if db_url and db_url.startswith("sqlite+libsql://"):
    try:
        import sqlalchemy_libsql
    except ImportError:
        print("[*] Note: 'sqlalchemy-libsql' driver is not installed. Using local SQLite database.", file=sys.stderr)
        db_url = None

if IS_VERCEL:
    local_db_path = os.path.join('/tmp', 'daiva_anughara.db')
    bundled_db = os.path.join(BASE_DIR, 'instance', 'daiva_anughara.db')
    if os.path.exists(bundled_db) and not os.path.exists(local_db_path):
        try:
            import shutil
            shutil.copy2(bundled_db, local_db_path)
            print("[*] Seeded database copied to /tmp/daiva_anughara.db", file=sys.stderr)
        except Exception as e:
            print(f"[*] Could not copy seeded database: {e}", file=sys.stderr)
else:
    local_db_path = os.path.join(instance_dir, 'daiva_anughara.db').replace('\\', '/')

app.config['SQLALCHEMY_DATABASE_URI'] = db_url or f"sqlite:///{local_db_path}"

# Engine options configuration
db_uri = app.config['SQLALCHEMY_DATABASE_URI']
if db_uri.startswith('postgresql'):
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 3600,
        'pool_size': 5,
        'max_overflow': 10,
        'connect_args': {
            'connect_timeout': 10,
            'options': '-c statement_timeout=30000'
        }
    }
elif db_uri.startswith('sqlite+libsql'):
    import urllib.parse as urlparse
    auth_token = None
    try:
        parsed_url = urlparse.urlparse(db_uri)
        query_params = urlparse.parse_qs(parsed_url.query)
        if 'authToken' in query_params:
            auth_token = query_params['authToken'][0]
            clean_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}?secure=true"
            app.config['SQLALCHEMY_DATABASE_URI'] = clean_url
    except Exception as e:
        print(f"Warning parsing Turso URI: {e}")
    if not auth_token:
        auth_token = os.getenv('TURSO_AUTH_TOKEN')
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'connect_args': {'auth_token': auth_token}
    }
else:
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {}

# ==============================================================================
# MODELS, FORMS, EXTENSIONS & BLUEPRINTS
# ==============================================================================
from models import (
    db, User, DonationPurpose, OfflineDonation, MandalaSadhanaRegistration,
    StageAccessRequest, ChatMessage
)
from auth import auth
from forms import (
    DonationPurposeForm, OfflineDonationForm, DonationSearchForm,
    MandalaSadhanaRegistrationForm, MandalaSadhanaSearchForm
)
from google_sheets import get_sheets_manager

db.init_app(app)
csrf = CSRFProtect(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this sacred portal.'
login_manager.login_message_category = 'info'

app.register_blueprint(auth, url_prefix='/auth')

def initialize_database():
    """Ensure database schema is created and create default admin user if not present"""
    try:
        with app.app_context():
            db.create_all()
            admin = User.query.filter_by(role='admin').first()
            if not admin:
                admin = User(
                    username='admin',
                    email='admin@daivaanughara.com',
                    full_name='Administrator',
                    role='admin',
                    is_approved=True,
                    is_active=True,
                    purpose='Administrator account for sacred system management, stage approvals, and donations.',
                    mandala_1_access=True,
                    mandala_2_access=True,
                    mandala_3_access=True,
                    rudraksha_8_mukhi_access=True,
                    rudraksha_11_mukhi_access=True,
                    rudraksha_14_mukhi_access=True,
                    pratham_charana_diksha_access=True,
                    dutiya_charana_access=True,
                    tritiya_charana_access=True,
                    devi_mandala_1_access=True,
                    devi_mandala_2_access=True,
                    devi_mandala_3_access=True
                )
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
                print("[+] Admin user verified/initialized: admin / admin123")
    except Exception as e:
        print(f"[-] Database initialization notice: {e}", file=sys.stderr)

_db_initialized = False

@app.before_request
def ensure_db_initialized():
    global _db_initialized
    if not _db_initialized:
        _db_initialized = True
        initialize_database()

try:
    initialize_database()
except Exception as e:
    print(f"[-] Initial database setup notice: {e}", file=sys.stderr)

@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except Exception:
        return None

@app.before_request
def update_last_active():
    if current_user.is_authenticated:
        try:
            current_user.last_active = datetime.utcnow()
            db.session.commit()
        except Exception:
            db.session.rollback()

@app.context_processor
def inject_user():
    return dict(user=current_user, current_user=current_user)


@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=generate_csrf)

@app.context_processor
def inject_admin_notifications():
    if current_user.is_authenticated and current_user.is_admin():
        try:
            unread_chat = ChatMessage.query.filter_by(is_admin_message=False, is_read=False).count()
            pending_users = User.query.filter_by(is_approved=False, role='user').count()
            pending_requests = StageAccessRequest.query.filter_by(status='pending').count()
            return dict(
                unread_chat_count=unread_chat,
                pending_users_count=pending_users,
                pending_stage_requests=pending_requests
            )
        except Exception:
            pass
    return dict(unread_chat_count=0, pending_users_count=0, pending_stage_requests=0)

# ==============================================================================
# INSTAGRAM_SCRAP LOGIC & CACHING (BHAIRAV LOKA CODEX)
# ==============================================================================
POSTS_FILE = os.path.join(INSTA_DIR, 'posts_metadata.json')
IMAGES_DIR = os.path.join(INSTA_DIR, 'scraped_images')

def extract_title_and_clean_caption(caption):
    if not caption:
        return "Untitled Darshan", ""
    lines = [line.strip() for line in caption.splitlines() if line.strip()]
    if not lines:
        return "Untitled Darshan", ""
    first_line = re.sub(r'^[•\-\*~#]+\s*', '', lines[0]).strip()
    if (len(first_line) < 3 or first_line.startswith('#')) and len(lines) > 1:
        first_line = lines[1]
    title = first_line[:77] + "..." if len(first_line) > 80 else first_line
    return title, caption

def extract_hashtags(caption):
    return re.findall(r'#(\w+)', caption) if caption else []

def format_timestamp(iso_str):
    if not iso_str:
        return ""
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%B %d, %Y")
    except Exception:
        return iso_str[:10] if len(iso_str) >= 10 else iso_str

def load_filtered_posts():
    if not os.path.exists(POSTS_FILE):
        return []
    with open(POSTS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    filtered = []
    for item in data:
        caption = item.get('caption', '') or ''
        is_video = item.get('is_video', False)
        if len(caption) > 100 and not is_video:
            title, clean_cap = extract_title_and_clean_caption(caption)
            tags = extract_hashtags(caption)
            filtered.append({
                "id": item.get('id', ''),
                "shortcode": item.get('shortcode', ''),
                "title": title,
                "caption": clean_cap,
                "caption_length": len(clean_cap),
                "word_count": len(clean_cap.split()),
                "date": format_timestamp(item.get('timestamp', '')),
                "raw_timestamp": item.get('timestamp', ''),
                "likes": item.get('likes', 0),
                "comments": item.get('comments', 0),
                "image_filename": item.get('image_filename', ''),
                "hashtags": tags
            })
    filtered.sort(key=lambda x: x['raw_timestamp'] or '', reverse=True)
    results = filtered[:150]
    for idx, p in enumerate(results, start=1):
        p['index'] = idx
        p['post_id'] = p['id']
    return results

CACHED_POSTS = load_filtered_posts()

def get_summary_stats():
    total = len(CACHED_POSTS)
    if total == 0:
        return {"total": 0, "total_likes": 0, "total_words": 0, "top_tags": []}
    total_likes = sum(p['likes'] for p in CACHED_POSTS)
    total_comments = sum(p['comments'] for p in CACHED_POSTS)
    total_words = sum(p['word_count'] for p in CACHED_POSTS)
    avg_length = round(sum(p['caption_length'] for p in CACHED_POSTS) / total)
    tag_counts = {}
    for p in CACHED_POSTS:
        for t in p['hashtags']:
            tl = t.lower()
            tag_counts[tl] = tag_counts.get(tl, 0) + 1
    top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:12]
    return {
        "total": total,
        "total_likes": total_likes,
        "total_comments": total_comments,
        "total_words": total_words,
        "avg_length": avg_length,
        "top_tags": [{"tag": t[0], "count": t[1]} for t in top_tags]
    }

# ==============================================================================
# ASHTAMI SACRED TIMINGS & API
# ==============================================================================
ASHTAMI_DATES = [
    {
        'date': '2026-10-03',
        'start_time': '08:00',
        'end_time': '2026-10-04 05:52',
        'description': 'Krishna Paksha Ashtami — Sacred Gateway of Kaal Bhairava'
    },
    {
        'date': '2026-11-02',
        'start_time': '06:15',
        'end_time': '2026-11-03 04:30',
        'description': 'Kaal Bhairav Jayanti Ashtami Mahotsav'
    }
]

# ==============================================================================
# CORE WEB ROUTES & PORTALS
# ==============================================================================
@app.route('/', endpoint='index')
@app.route('/home', endpoint='home')
def index():
    """Main Landing Sanctuary in Bhairva Dark-Gold Theme"""
    return render_template('index.html', active_page='home', page_title='Bhairava Anugraha · Super App')

@app.route('/jnana-samvada')
def jnana_samvada_page():
    """Jnāna Samvāda Codex Page (Bhairava QnA Codex)"""
    return render_template('qna.html', active_page='jnana_samvada', page_title='Jnāna Samvāda Codex')

@app.route('/qna')
def qna_redirect():
    return redirect('/jnana-samvada', code=302)

@app.route('/bhairav-loka')
def bhairav_loka_page():
    """Bhairav Loka Sahasralinga Codex Page"""
    return render_template('bhairav_loka.html', total_posts=len(CACHED_POSTS), active_page='bhairav_loka', page_title='Bhairav Loka Codex')

@app.route('/sadhana-paddhati', endpoint='sadhana_paddhati_page')
@app.route('/padati', endpoint='padati')
def sadhana_paddhati_page():
    """Sādhana Paddhati 3-Stage Path & Devi Anugraha Flow - Connected to Backend"""
    active_view = request.args.get('view', 'bhairava')
    stage_id = request.args.get('stage', None)
    return render_template(
        'sadhana_paddhati.html',
        active_page='sadhana',
        active_view=active_view,
        stage_id=stage_id,
        page_title='Sādhana Paddhati · Bhairava & Devi Flow'
    )

@app.route('/devi')
@app.route('/devi-padathi')
def devi_padathi_redirect():
    """Convenience redirect to Devi section on sadhana-paddhati page"""
    return redirect('/sadhana-paddhati?view=devi#devi-section')

@app.route('/vishesh-sadhana')
def vishesh_sadhana_redirect():
    """Convenience redirect to Vishesh Sadhana section"""
    return redirect('/sadhana-paddhati?view=devi#potent-timings')

@app.route('/documents')
def documents_page():
    """Serves sacred PDF documentation or documents download"""
    pdf_filename = 'Kāmākhyā–Bhairava.pdf'
    pdf_path = os.path.join(BASE_DIR, 'static', pdf_filename)
    if os.path.exists(pdf_path):
        return send_from_directory(os.path.join(BASE_DIR, 'static'), pdf_filename)
    return redirect('/static/Kāmākhyā–Bhairava.pdf')

@app.route('/ashtami')
def ashtami_page():
    """Ashtami Lunar Gateways & Timings"""
    return render_template('ashtami.html', active_page='ashtami', page_title='Ashtami Sacred Gateways')

@app.route('/guru-bhairava')
def guru_bhairava():
    return render_template('guru_bhairava.html', page_title='Guru Bhairava - Bhairava Anugraha')

@app.route('/prana-pratisthana')
def prana_pratisthana():
    return render_template('prana_pratisthana.html', page_title='Prāṇa Pratiṣṭhāna - Bhairava Anugraha')

@app.route('/about')
def about():
    return render_template('about.html', page_title='About - Bhairava Anugraha')

@app.route('/youtube')
def youtube():
    return render_template('youtube.html', page_title='YouTube - Bhairava Anugraha')

# ==============================================================================
# STAGE PROGRESSION & ACCESS CONTROL
# ==============================================================================
@app.route('/stage/<int:stage_num>')
@login_required
def stage_page(stage_num):
    """Individual stage portal with authentication & mandala permission enforcement"""
    if stage_num < 1 or stage_num > 9:
        flash('Invalid stage identifier.', 'error')
        return redirect(url_for('sadhana_paddhati_page'))

    # Check access permission
    if not (current_user.is_admin() or current_user.has_mandala_access(stage_num)):
        flash('You do not have access to this sacred stage yet. Please complete previous mandalas or submit an access request.', 'warning')
        return redirect(url_for('sadhana_paddhati_page'))

    stage_info = current_user.get_stage_info(stage_num)

    stage_data = {
        1: {
            'name': 'Mandala 1',
            'phase': 'Pratham Charana',
            'description': 'The first sacred mandala of your spiritual journey.',
            'icon': 'ॐ',
            'type': 'mandala'
        },
        2: {
            'name': 'Mandala 2',
            'phase': 'Pratham Charana',
            'description': 'The second sacred mandala, deepening your practice.',
            'icon': '✦',
            'type': 'mandala'
        },
        3: {
            'name': 'Mandala 3',
            'phase': 'Pratham Charana',
            'description': 'The third sacred mandala, completing the foundational purification.',
            'icon': '🔱',
            'type': 'mandala'
        },
        4: {
            'name': '8 Mukhi Rudraksha',
            'phase': 'Rudraksha Diksha',
            'description': 'Sacred 8 Mukhi Rudraksha initiation after completing Pratham Charana.',
            'icon': '📿',
            'type': 'rudraksha',
            'image': 'images/8 Mukhi _ Achtgesicht Rudraksha Nepal 20-22 mm.jpeg'
        },
        5: {
            'name': '11 Mukhi Rudraksha',
            'phase': 'Rudraksha Diksha',
            'description': 'Sacred 11 Mukhi Rudraksha initiation.',
            'icon': '📿',
            'type': 'rudraksha',
            'image': 'images/rudraksha/rudrakha_11_mukhi.jpeg'
        },
        6: {
            'name': '14 Mukhi Rudraksha',
            'phase': 'Rudraksha Diksha',
            'description': 'Sacred 14 Mukhi Rudraksha initiation, the highest diksha.',
            'icon': '💎',
            'type': 'rudraksha',
            'image': 'images/rudraksha/rudarakha_14_muki.jpeg'
        },
        7: {
            'name': 'Pratham Charana Diksha',
            'phase': 'Pratham Charana',
            'description': 'Sacred initiation into Pratham Charana - the first step of Rudraksha Diksha journey.',
            'icon': '🙏',
            'type': 'diksha',
            'image': 'images/rudraksha/5 mukhi.png'
        },
        8: {
            'name': 'Dutiya Charana',
            'phase': 'Dutiya Charana',
            'description': 'The second phase of your spiritual journey - deepening the internal sadhana practice.',
            'icon': '🌙',
            'type': 'charana',
            'image': 'images/bhairava_black.jpg'
        },
        9: {
            'name': 'Tritiya Charana',
            'phase': 'Tritiya Charana',
            'description': 'The third phase of spiritual evolution - advanced sadhana practices.',
            'icon': '⭐',
            'type': 'charana',
            'image': 'images/bhairava_eight_hands.jpeg'
        }
    }

    current_stage_data = stage_data.get(stage_num, {})

    if stage_num == 7:
        return render_template(
            'stage_7.html',
            page_title='Pratham Charana Diksha - Bhairava Anugraha',
            stage_num=stage_num,
            stage_info=stage_info,
            stage_data=current_stage_data
        )

    return render_template(
        'stage.html',
        page_title=f"{current_stage_data.get('name', 'Stage')} - Bhairava Anugraha",
        stage_num=stage_num,
        stage_info=stage_info,
        stage_data=current_stage_data
    )

@app.route('/devi-stage/<int:stage_num>')
@login_required
def devi_stage_page(stage_num):
    """Individual Devi Mandala stage page"""
    if stage_num < 1 or stage_num > 3:
        flash('Invalid Devi Mandala identifier.', 'error')
        return redirect(url_for('sadhana_paddhati_page'))

    stage_data = {
        1: {'name': 'Mandala 1', 'days': 33, 'description': 'Begin your sacred journey with Maa Kamakhya - 33 days of devotion', 'icon': '🌸'},
        2: {'name': 'Mandala 2', 'days': 66, 'description': 'Deepen your connection with the Divine Feminine - 66 days of practice', 'icon': '🌺'},
        3: {'name': 'Mandala 3', 'days': 99, 'description': 'Complete transformation through 99 days of sacred sadhana', 'icon': '💮'}
    }
    current_stage_data = stage_data.get(stage_num, {})
    return render_template(
        'devi_stage.html',
        page_title=f"Devi {current_stage_data.get('name', 'Mandala')} - Bhairava Anugraha",
        stage_num=stage_num,
        stage_data=current_stage_data
    )

@app.route('/chaya_siddhi')
@login_required
def chaya_siddhi():
    if not (current_user.is_admin() or current_user.mandala_3_access):
        flash('You must complete Mandala 3 foundational sādhanā to enter Chāyā Siddhi.', 'error')
        return redirect(url_for('sadhana_paddhati_page'))
    return render_template('chaya_siddhi.html', page_title='Chāyā Pūjā - Bhairava Anugraha')

# ==============================================================================
# MANDALA SADHANA VOWS & REGISTRATION
# ==============================================================================
@app.route('/mandala-sadhana', methods=['GET', 'POST'])
@login_required
def mandala_sadhana_registration():
    """Mandala Sadhana registration form for 48/144-day sacred commitments"""
    if not current_user.is_admin() and not current_user.is_approved:
        flash('Your account is awaiting approval before submitting Mandala Sādhana vows.', 'warning')
        return redirect(url_for('auth.profile'))

    form = MandalaSadhanaRegistrationForm()
    if form.validate_on_submit():
        try:
            mandala_48 = (form.mandala_48_commitment.data == 'Yes') if form.mandala_48_commitment.data else False
            send_copy = (form.send_copy.data == 'True') if form.send_copy.data else False
            registration = MandalaSadhanaRegistration(
                email=form.email.data,
                full_name=form.full_name.data,
                mandala_48_commitment=mandala_48,
                mandala_144_commitment=form.mandala_144_commitment.data or 'No',
                commitment_text=form.commitment_text.data,
                sadhana_start_date=form.sadhana_start_date.data,
                sadhana_type=form.sadhana_type.data,
                send_copy=send_copy
            )
            db.session.add(registration)
            db.session.commit()
            flash('Sacred Mandala Sādhana registration submitted successfully! ॐ नमः शिवाय ॥', 'success')
            return redirect(url_for('sadhana_paddhati_page'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error recording registration: {str(e)}', 'error')

    return render_template(
        'mandala_sadhana_form.html',
        form=form,
        active_page='mandala_vow',
        page_title='Mandala Sādhana Registration - Bhairava Anugraha'
    )

@app.route('/api/mandala-sadhana', methods=['POST'])
@login_required
def api_mandala_sadhana_registration():
    """AJAX endpoint for Mandala Sadhana registrations"""
    if not current_user.is_admin() and not current_user.is_approved:
        return jsonify({'success': False, 'error': 'Account pending approval.'}), 403

    try:
        data = request.get_json()
        required = ['email', 'full_name', 'mandala_48_commitment', 'mandala_144_commitment', 'commitment_text', 'sadhana_start_date', 'sadhana_type']
        for req in required:
            if req not in data or not data[req]:
                return jsonify({'success': False, 'error': f'Missing required field: {req}'}), 400

        mandala_48 = data['mandala_48_commitment'] == 'Yes'
        start_date = datetime.strptime(data['sadhana_start_date'], '%Y-%m-%d').date()

        reg = MandalaSadhanaRegistration(
            email=data['email'],
            full_name=data['full_name'],
            mandala_48_commitment=mandala_48,
            mandala_144_commitment=data['mandala_144_commitment'],
            commitment_text=data['commitment_text'],
            sadhana_start_date=start_date,
            sadhana_type=data['sadhana_type'],
            send_copy=data.get('send_copy', False)
        )
        db.session.add(reg)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Registration recorded successfully.', 'registration_id': reg.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# ==============================================================================
# BHIKSHA & DONATIONS MANAGEMENT
# ==============================================================================
@app.route('/bhiksha')
def bhiksha():
    """Public donations & sacred offerings transparency portal"""
    try:
        all_donations = OfflineDonation.query.order_by(OfflineDonation.donation_date.desc()).all()
        purposes = DonationPurpose.query.filter_by(is_active=True).all()
        total_amount = sum(d.amount for d in all_donations)
        verified_donations = [d for d in all_donations if d.is_verified]
        unverified_donations = [d for d in all_donations if not d.is_verified]

        return render_template(
            'donations.html',
            active_page='bhiksha',
            page_title='Sacred Bhiksha Offerings - Bhairava Anugraha',
            donations=all_donations,
            verified_donations=verified_donations,
            unverified_donations=unverified_donations,
            purposes=purposes,
            total_donations=len(all_donations),
            total_amount=total_amount,
            recent_donations=all_donations[:10]
        )
    except Exception as e:
        return render_template('donations.html', active_page='bhiksha', page_title='Bhiksha', error=str(e), donations=[], verified_donations=[], unverified_donations=[], purposes=[], total_donations=0, total_amount=0, recent_donations=[])

@app.route('/admin/donations')
@login_required
def admin_donations():
    """Admin donations management ledger"""
    if not current_user.is_admin():
        flash('Access denied. Administrator privileges required.', 'error')
        return redirect(url_for('home'))

    all_donations = OfflineDonation.query.order_by(OfflineDonation.donation_date.desc()).all()
    purposes = DonationPurpose.query.all()
    total_amount = sum(d.amount for d in all_donations)
    return render_template(
        'admin/donations.html',
        page_title='Donations Ledger - Admin Desk',
        donations=all_donations,
        all_purposes=purposes,
        total_donations=len(all_donations),
        total_amount=total_amount,
        recent_donations=all_donations[:20],
        data_source='Local Database'
    )

@app.route('/admin/donations/add', methods=['GET', 'POST'])
@login_required
def add_donation():
    """Add new offline donation record"""
    if not current_user.is_admin():
        flash('Access denied.', 'error')
        return redirect(url_for('home'))

    form = OfflineDonationForm()
    purposes = DonationPurpose.query.filter_by(is_active=True).all()
    form.purpose_id.choices = [(p.id, p.name) for p in purposes]

    if form.validate_on_submit():
        try:
            donation_date = datetime.strptime(form.donation_date.data, '%Y-%m-%d').date()
            donation = OfflineDonation(
                donor_name=form.donor_name.data,
                donor_email=form.donor_email.data,
                donor_phone=form.donor_phone.data,
                amount=float(form.amount.data),
                currency=form.currency.data,
                purpose_id=form.purpose_id.data,
                donation_date=donation_date,
                payment_method=form.payment_method.data,
                reference_number=form.reference_number.data,
                notes=form.notes.data,
                created_by=current_user.id
            )
            db.session.add(donation)
            db.session.commit()
            flash('Donation added successfully!', 'success')
            return redirect(url_for('admin_donations'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error recording donation: {str(e)}', 'error')

    return render_template('admin/add_donation.html', form=form, page_title='Add Donation - Admin Desk')

@app.route('/admin/donations/verify/<int:donation_id>')
@login_required
def verify_donation(donation_id):
    """Verify an offline donation"""
    if not current_user.is_admin():
        flash('Access denied.', 'error')
        return redirect(url_for('home'))

    donation = OfflineDonation.query.get_or_404(donation_id)
    donation.is_verified = True
    db.session.commit()
    flash(f'Donation #{donation.id} marked as verified!', 'success')
    return redirect(url_for('admin_donations'))

@app.route('/admin/donation-purposes', methods=['GET', 'POST'])
@login_required
def donation_purposes():
    """Manage donation purpose categories"""
    if not current_user.is_admin():
        flash('Access denied.', 'error')
        return redirect(url_for('home'))

    form = DonationPurposeForm()
    if form.validate_on_submit():
        try:
            purpose = DonationPurpose(
                name=form.name.data,
                description=form.description.data,
                created_by=current_user.id
            )
            db.session.add(purpose)
            db.session.commit()
            flash('Donation purpose created successfully!', 'success')
            return redirect(url_for('donation_purposes'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating purpose: {str(e)}', 'error')

    purposes = DonationPurpose.query.all()
    return render_template('admin/donation_purposes.html', form=form, purposes=purposes, page_title='Donation Purposes - Admin Desk')

@app.route('/admin/donation-purposes/toggle/<int:purpose_id>')
@login_required
def toggle_donation_purpose(purpose_id):
    if not current_user.is_admin():
        flash('Access denied.', 'error')
        return redirect(url_for('home'))

    purpose = DonationPurpose.query.get_or_404(purpose_id)
    purpose.is_active = not purpose.is_active
    db.session.commit()
    flash(f'Purpose status toggled to {"Active" if purpose.is_active else "Inactive"}.', 'success')
    return redirect(url_for('donation_purposes'))

@app.route('/admin/sync-donations')
@app.route('/admin/sync-now')
@login_required
def sync_donations():
    if not current_user.is_admin():
        flash('Access denied.', 'error')
        return redirect(url_for('home'))

    try:
        sheets_mgr = get_sheets_manager()
        if not sheets_mgr or not sheets_mgr.is_connected():
            flash('Google Sheets not connected. Verify credentials in .env.', 'warning')
            return redirect(url_for('admin_donations'))
        success, message = sheets_mgr.sync_donations_from_sheets()
        flash(message if success else f'Sync failed: {message}', 'success' if success else 'error')
    except Exception as e:
        flash(f'Sync error: {str(e)}', 'error')

    return redirect(url_for('admin_donations'))

@app.route('/admin/api/sync-donations', methods=['POST'])
@login_required
def api_sync_donations():
    if not current_user.is_admin():
        return jsonify({'error': 'Access denied'}), 403
    try:
        sheets_mgr = get_sheets_manager()
        if not sheets_mgr or not sheets_mgr.is_connected():
            return jsonify({'success': False, 'error': 'Google Sheets not connected.'}), 400
        success, message = sheets_mgr.sync_donations_from_sheets()
        return jsonify({'success': success, 'message': message})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/sync-status')
@login_required
def admin_sync_status():
    if not current_user.is_admin():
        return jsonify({'connected': False, 'message': 'Access denied'}), 403
    try:
        sheets_mgr = get_sheets_manager()
        is_connected = bool(sheets_mgr and sheets_mgr.is_connected())
        return jsonify({
            'connected': is_connected,
            'message': 'Connected to Google Sheets' if is_connected else 'Google Sheets not connected'
        })
    except Exception as e:
        return jsonify({'connected': False, 'message': str(e)})

@app.route('/admin/api/donations-from-sheets')
@login_required
def api_donations_from_sheets():
    if not current_user.is_admin():
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    try:
        sheets_mgr = get_sheets_manager()
        if not sheets_mgr or not sheets_mgr.is_connected():
            return jsonify({'success': False, 'error': 'Google Sheets not connected.', 'donations': [], 'count': 0}), 200
        donations = sheets_mgr.get_all_donations()
        return jsonify({
            'success': True,
            'count': len(donations),
            'donations': donations
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e), 'donations': [], 'count': 0}), 200


@app.route('/admin/api/search-users')
@login_required
def api_search_users():
    if not current_user.is_admin():
        return jsonify({'error': 'Access denied'}), 403
    q = request.args.get('q', '').strip()
    if not q or len(q) < 2:
        return jsonify({'users': []})
    users = User.query.filter(
        db.or_(User.full_name.ilike(f'%{q}%'), User.username.ilike(f'%{q}%'), User.email.ilike(f'%{q}%'))
    ).limit(20).all()
    return jsonify({'users': [{'id': u.id, 'full_name': u.full_name, 'username': u.username, 'email': u.email} for u in users]})

# ==============================================================================
# ADMIN MANDALA SADHANA REGISTRATIONS DESK
# ==============================================================================
@app.route('/admin/mandala-sadhana')
@login_required
def admin_mandala_sadhana():
    if not current_user.is_admin():
        flash('Access denied.', 'error')
        return redirect(url_for('home'))

    registrations = MandalaSadhanaRegistration.query.order_by(MandalaSadhanaRegistration.created_at.desc()).all()
    form = MandalaSadhanaSearchForm()
    return render_template(
        'admin/mandala_sadhana.html',
        registrations=registrations,
        form=form,
        search_form=form,
        page_title='Mandala Sādhana Registrations - Admin Desk'
    )

@app.route('/admin/mandala-sadhana/<int:registration_id>')
@login_required
def admin_mandala_sadhana_detail(registration_id):
    if not current_user.is_admin():
        flash('Access denied.', 'error')
        return redirect(url_for('home'))

    reg = MandalaSadhanaRegistration.query.get_or_404(registration_id)
    return render_template('admin/mandala_sadhana_detail.html', registration=reg, page_title='Vow Inspection - Admin Desk')

@app.route('/admin/mandala-sadhana/export')
@login_required
def admin_mandala_sadhana_export():
    if not current_user.is_admin():
        flash('Access denied.', 'error')
        return redirect(url_for('home'))

    registrations = MandalaSadhanaRegistration.query.all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Full Name', 'Email', 'Sadhana Type', '48 Day Commitment', '144 Day Commitment', 'Start Date', 'Commitment Text', 'Created At'])
    for r in registrations:
        writer.writerow([r.id, r.full_name, r.email, r.sadhana_type, 'Yes' if r.mandala_48_commitment else 'No', r.mandala_144_commitment, r.sadhana_start_date, r.commitment_text, r.created_at])

    output.seek(0)
    return Response(output.getvalue(), mimetype='text/csv', headers={"Content-Disposition": "attachment;filename=mandala_sadhana_registrations.csv"})

# ==============================================================================
# SPIRITUAL GUIDANCE CHAT SYSTEM
# ==============================================================================
@app.route('/api/chat/send', methods=['POST'])
@login_required
def send_chat_message():
    try:
        data = request.get_json()
        content = data.get('message', '').strip()
        recipient_id = data.get('recipient_id')
        if not content:
            return jsonify({'success': False, 'error': 'Message content cannot be empty.'}), 400

        is_admin = current_user.is_admin()
        if is_admin and not recipient_id:
            return jsonify({'success': False, 'error': 'Recipient ID required for admin responses.'}), 400

        msg = ChatMessage(
            sender_id=current_user.id,
            recipient_id=recipient_id if is_admin else None,
            message=content,
            is_admin_message=is_admin
        )
        db.session.add(msg)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': {
                'id': msg.id,
                'content': msg.message,
                'created_at': msg.created_at.strftime('%Y-%m-%d %H:%M'),
                'is_admin': msg.is_admin_message
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/chat/history', methods=['GET'])
@login_required
def get_chat_history():
    try:
        messages = ChatMessage.query.filter(
            db.or_(
                ChatMessage.sender_id == current_user.id,
                ChatMessage.recipient_id == current_user.id
            )
        ).order_by(ChatMessage.created_at.asc()).all()

        return jsonify({
            'success': True,
            'messages': [{
                'id': m.id,
                'message': m.message,
                'is_admin': m.is_admin_message,
                'created_at': m.created_at.strftime('%Y-%m-%d %H:%M'),
                'is_read': m.is_read
            } for m in messages]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/chat/mark-read', methods=['POST'])
@login_required
def mark_messages_read():
    try:
        ChatMessage.query.filter_by(recipient_id=current_user.id, is_read=False).update({'is_read': True})
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/chat')
@login_required
def admin_chat():
    if not current_user.is_admin():
        flash('Access denied.', 'error')
        return redirect(url_for('home'))
    return render_template('admin/chat.html', page_title='Spiritual Guidance Chat - Admin Desk')

@app.route('/api/admin/chat/users')
@login_required
def get_chat_users():
    if not current_user.is_admin():
        return jsonify({'error': 'Access denied'}), 403
    users_with_messages = User.query.join(
        ChatMessage, db.or_(ChatMessage.sender_id == User.id, ChatMessage.recipient_id == User.id)
    ).filter(User.role != 'admin').distinct().all()

    user_list = []
    for u in users_with_messages:
        unread = ChatMessage.query.filter_by(sender_id=u.id, is_read=False).count()
        last_msg = ChatMessage.query.filter(
            db.or_(ChatMessage.sender_id == u.id, ChatMessage.recipient_id == u.id)
        ).order_by(ChatMessage.created_at.desc()).first()
        user_list.append({
            'id': u.id,
            'name': u.full_name or u.username,
            'email': u.email,
            'unread': unread,
            'last_message': last_msg.message[:40] if last_msg else '',
            'last_active': u.last_active.strftime('%Y-%m-%d %H:%M') if u.last_active else ''
        })
    return jsonify({'success': True, 'users': user_list})

@app.route('/api/admin/chat/<int:user_id>')
@login_required
def get_admin_user_chat(user_id):
    if not current_user.is_admin():
        return jsonify({'error': 'Access denied'}), 403
    target_user = User.query.get_or_404(user_id)
    messages = ChatMessage.query.filter(
        db.or_(
            db.and_(ChatMessage.sender_id == user_id, ChatMessage.is_admin_message == False),
            db.and_(ChatMessage.recipient_id == user_id, ChatMessage.is_admin_message == True)
        )
    ).order_by(ChatMessage.created_at.asc()).all()

    ChatMessage.query.filter_by(sender_id=user_id, is_read=False).update({'is_read': True})
    db.session.commit()

    return jsonify({
        'success': True,
        'user': {'id': target_user.id, 'name': target_user.full_name, 'email': target_user.email},
        'messages': [{
            'id': m.id,
            'message': m.message,
            'is_admin': m.is_admin_message,
            'created_at': m.created_at.strftime('%Y-%m-%d %H:%M')
        } for m in messages]
    })

# ==============================================================================
# CODEX APIS & HEALTH DIAGNOSTICS
# ==============================================================================
@app.route('/api/qna')
def api_qna():
    """Serves QnA entries to Bhairva frontend"""
    active_db = request.headers.get('x-active-db') or request.headers.get('X-Active-DB')
    if db_helper:
        try:
            entries = db_helper.get_all_qna(active_db=active_db)
            return jsonify(entries)
        except Exception as e:
            print(f"[-] db_helper error: {e}, falling back to CSV")
    csv_path = os.path.join(BHAIRVA_DIR, 'qna.csv')
    if os.path.exists(csv_path):
        entries = []
        with open(csv_path, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)
            for row in reader:
                entries.append(row)
        return jsonify(entries)
    return jsonify([])

@app.route('/api/posts')
def api_posts():
    return jsonify({"status": "success", "count": len(CACHED_POSTS), "posts": CACHED_POSTS})

@app.route('/api/posts/<post_id>')
def api_post_detail(post_id):
    found = next((p for p in CACHED_POSTS if p['id'] == post_id), None)
    if not found:
        return jsonify({"status": "error", "message": "Post not found"}), 404
    return jsonify({"status": "success", "post": found})

@app.route('/api/stats')
def api_stats():
    return jsonify({"status": "success", "stats": get_summary_stats()})

@app.route('/api/next-ashtami')
def next_ashtami():
    today = datetime.now().date()
    for ashtami in ASHTAMI_DATES:
        try:
            ashtami_date = datetime.strptime(ashtami['date'], '%Y-%m-%d').date()
            if ashtami_date >= today:
                return jsonify(ashtami)
        except Exception:
            pass
    return jsonify(ASHTAMI_DATES[0] if ASHTAMI_DATES else None)

@app.route('/api/countdown')
def countdown():
    date_str = request.args.get('next_ashtami') or (ASHTAMI_DATES[0]['date'] if ASHTAMI_DATES else '')
    return jsonify({'date': date_str, 'status': 'active'})

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'service': 'Bhairava Anugraha Super App', 'timestamp': datetime.utcnow().isoformat()}), 200

# ==============================================================================
# STATIC PROXIES FOR COMPATIBILITY
# ==============================================================================
@app.route('/index.css')
def serve_bhairva_css():
    return send_from_directory(BHAIRVA_DIR, 'index.css', mimetype='text/css')

@app.route('/index.js')
def serve_bhairva_js():
    return send_from_directory(BHAIRVA_DIR, 'index.js', mimetype='application/javascript')

@app.route('/qna.csv')
def serve_bhairva_csv():
    return send_from_directory(BHAIRVA_DIR, 'qna.csv', mimetype='text/csv')

@app.route('/analytics.js')
def serve_bhairva_analytics():
    if os.path.exists(os.path.join(BHAIRVA_DIR, 'analytics.js')):
        return send_from_directory(BHAIRVA_DIR, 'analytics.js', mimetype='application/javascript')
    return Response("", mimetype='application/javascript')

@app.route('/images/<path:filename>')
def serve_bhairva_images(filename):
    img_dir = os.path.join(BHAIRVA_DIR, 'images')
    if os.path.exists(img_dir) and os.path.exists(os.path.join(img_dir, filename)):
        return send_from_directory(img_dir, filename)
    fallback_dir = os.path.join(BASE_DIR, 'static', 'images')
    if os.path.exists(os.path.join(fallback_dir, filename)):
        return send_from_directory(fallback_dir, filename)
    abort(404)

@app.route('/static/css/style.css')
def serve_loka_css():
    return send_from_directory(os.path.join(INSTA_DIR, 'static', 'css'), 'style.css', mimetype='text/css')

@app.route('/static/js/app.js')
def serve_loka_js():
    return send_from_directory(os.path.join(INSTA_DIR, 'static', 'js'), 'app.js', mimetype='application/javascript')

@app.route('/media/<path:filename>')
def serve_media(filename):
    if os.path.exists(IMAGES_DIR) and os.path.exists(os.path.join(IMAGES_DIR, filename)):
        return send_from_directory(IMAGES_DIR, filename)
    fallback_dir = os.path.join(BASE_DIR, 'static', 'images')
    if os.path.exists(os.path.join(fallback_dir, filename)):
        return send_from_directory(fallback_dir, filename)
    abort(404)

# ==============================================================================
# ERROR HANDLERS
# ==============================================================================
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html', page_title='Page Not Found - Bhairava Anugraha'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    import traceback
    traceback.print_exc(file=sys.stderr)
    return render_template('500.html', page_title='Internal Sanctuary Error'), 500

# ==============================================================================
# SERVERLESS WSGI ENTRYPOINTS FOR VERCEL
# ==============================================================================
application = app
handler = app

if __name__ == '__main__':
    PORT = int(os.getenv('PORT', 5000))
    print(f"==================================================================")
    print(f"✦ SUPER APPLICATION BHAIRAVA ANUGRAHA WITH FULL ADMIN SUITE")
    print(f"✦ Server listening at: http://localhost:{PORT}")
    print(f"✦ Landing Page:        http://localhost:{PORT}/")
    print(f"✦ Sādhana Paddhati:    http://localhost:{PORT}/sadhana-paddhati")
    print(f"✦ Admin Users Portal:  http://localhost:{PORT}/auth/admin/users")
    print(f"✦ Admin Donations:     http://localhost:{PORT}/admin/donations")
    print(f"✦ Admin Mandala Vows:  http://localhost:{PORT}/admin/mandala-sadhana")
    print(f"✦ Admin Mentorship:    http://localhost:{PORT}/admin/chat")
    print(f"✦ QnA Codex:           http://localhost:{PORT}/jnana-samvada")
    print(f"✦ Bhairav Loka Codex:  http://localhost:{PORT}/bhairav-loka")
    print(f"==================================================================")
    app.run(host='0.0.0.0', port=PORT, debug=False)
