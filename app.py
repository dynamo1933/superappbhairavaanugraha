import os
import sys

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
import csv
import re
from datetime import datetime
from flask import Flask, render_template, jsonify, request, send_from_directory, abort, Response, redirect

# ==============================================================================
# PATH CONFIGURATION (Local Filesystem + Cloud/Vercel Fallbacks)
# ==============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_BHAIRVA = r'C:\Users\dynam\Desktop\Bhairva'
LOCAL_INSTA = r'C:\Users\dynam\Desktop\instagram_scrap'

BHAIRVA_DIR = os.environ.get('BHAIRVA_DIR', LOCAL_BHAIRVA)
if not os.path.exists(BHAIRVA_DIR):
    BHAIRVA_DIR = os.path.join(BASE_DIR, 'data', 'bhairva')

INSTA_DIR = os.environ.get('INSTA_DIR', LOCAL_INSTA)
if not os.path.exists(INSTA_DIR):
    INSTA_DIR = os.path.join(BASE_DIR, 'data', 'instagram_scrap')

# Create Flask application
app = Flask(__name__, template_folder=os.path.join(BASE_DIR, 'templates'), static_folder=os.path.join(BASE_DIR, 'static'))

# Add directories to sys.path in read-only mode for importing helper modules if present
if os.path.exists(BHAIRVA_DIR) and BHAIRVA_DIR not in sys.path:
    sys.path.append(BHAIRVA_DIR)
if os.path.exists(INSTA_DIR) and INSTA_DIR not in sys.path:
    sys.path.append(INSTA_DIR)

try:
    import db_helper
except Exception as e:
    print(f"[-] Warning importing db_helper: {e}")
    db_helper = None

# ==============================================================================
# INSTAGRAM_SCRAP LOGIC & CACHING
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
                "url": item.get('url', ''),
                "hashtags": tags
            })
    filtered.sort(key=lambda x: x['raw_timestamp'] or '', reverse=True)
    return filtered[:150]

CACHED_POSTS = load_filtered_posts()
print(f"[+] Loaded {len(CACHED_POSTS)} posts for Bhairav Loka Sahasralinga Codex")

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
# WEB ROUTES
# ==============================================================================
@app.route('/')
def index():
    """Main Landing Page - Recreated Bhairava Anugraha in Bhairva Dark-Gold Theme"""
    return render_template('index.html', active_page='home')

@app.route('/jnana-samvada')
def jnana_samvada_page():
    """Jnāna Samvāda Codex Page (Bhairava QnA Codex from C:\\Users\\dynam\\Desktop\\Bhairva)"""
    return render_template('qna.html', active_page='jnana_samvada')

@app.route('/qna')
def qna_redirect():
    """Redirect /qna to /jnana-samvada"""
    return redirect('/jnana-samvada', code=302)

@app.route('/bhairav-loka')
def bhairav_loka_page():
    """Task 3: Bhairav Loka Sahasralinga Codex Page (from C:\\Users\\dynam\\Desktop\\instagram_scrap)"""
    return render_template('bhairav_loka.html', total_posts=len(CACHED_POSTS), active_page='bhairav_loka')

@app.route('/sadhana-paddhati')
def sadhana_paddhati_page():
    """Sādhana Paddhati 3-Stage Path"""
    return render_template('sadhana_paddhati.html', active_page='sadhana')

@app.route('/ashtami')
def ashtami_page():
    """Ashtami Lunar Gateways & Timings"""
    return render_template('ashtami.html', active_page='ashtami')

# ==============================================================================
# API ROUTES (Supporting QnA and Bhairav Loka Codex)
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
    # Fallback to direct CSV parsing
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
    """Serves filtered Instagram posts to Bhairav Loka frontend"""
    return jsonify({"status": "success", "count": len(CACHED_POSTS), "posts": CACHED_POSTS})

@app.route('/api/posts/<post_id>')
def api_post_detail(post_id):
    """Serves single post details to Bhairav Loka frontend"""
    found = next((p for p in CACHED_POSTS if p['id'] == post_id), None)
    if not found:
        return jsonify({"status": "error", "message": "Post not found"}), 404
    return jsonify({"status": "success", "post": found})

@app.route('/api/stats')
def api_stats():
    """Serves summary statistics to Bhairav Loka frontend"""
    return jsonify({"status": "success", "stats": get_summary_stats()})

# ==============================================================================
# SUB-APP STATIC ASSET PROXIES (Read-Only Serving)
# ==============================================================================
@app.route('/index.css')
def serve_bhairva_css():
    """Serves Bhairva index.css directly from Bhairva directory"""
    return send_from_directory(BHAIRVA_DIR, 'index.css', mimetype='text/css')

@app.route('/index.js')
def serve_bhairva_js():
    """Serves Bhairva index.js directly from Bhairva directory"""
    return send_from_directory(BHAIRVA_DIR, 'index.js', mimetype='application/javascript')

@app.route('/qna.csv')
def serve_bhairva_csv():
    """Serves Bhairva qna.csv directly from Bhairva directory"""
    return send_from_directory(BHAIRVA_DIR, 'qna.csv', mimetype='text/csv')

@app.route('/analytics.js')
def serve_bhairva_analytics():
    """Serves Bhairva analytics.js if present"""
    if os.path.exists(os.path.join(BHAIRVA_DIR, 'analytics.js')):
        return send_from_directory(BHAIRVA_DIR, 'analytics.js', mimetype='application/javascript')
    return Response("", mimetype='application/javascript')

@app.route('/images/<path:filename>')
def serve_bhairva_images(filename):
    """Serves images from Bhairva images directory with fallback"""
    img_dir = os.path.join(BHAIRVA_DIR, 'images')
    if os.path.exists(img_dir) and os.path.exists(os.path.join(img_dir, filename)):
        return send_from_directory(img_dir, filename)
    fallback_dir = os.path.join(BASE_DIR, 'static', 'images')
    if os.path.exists(os.path.join(fallback_dir, filename)):
        return send_from_directory(fallback_dir, filename)
    abort(404)

@app.route('/static/css/style.css')
def serve_loka_css():
    """Serves Bhairav Loka stylesheet"""
    return send_from_directory(os.path.join(INSTA_DIR, 'static', 'css'), 'style.css', mimetype='text/css')

@app.route('/static/js/app.js')
def serve_loka_js():
    """Serves Bhairav Loka app.js"""
    return send_from_directory(os.path.join(INSTA_DIR, 'static', 'js'), 'app.js', mimetype='application/javascript')

@app.route('/media/<path:filename>')
def serve_media(filename):
    """Serves images for Bhairav Loka darshans with fallback"""
    if os.path.exists(IMAGES_DIR) and os.path.exists(os.path.join(IMAGES_DIR, filename)):
        return send_from_directory(IMAGES_DIR, filename)
    fallback_dir = os.path.join(BASE_DIR, 'static', 'images')
    if os.path.exists(os.path.join(fallback_dir, filename)):
        return send_from_directory(fallback_dir, filename)
    abort(404)

# ==============================================================================
# MAIN ENTRYPOINT
# ==============================================================================
if __name__ == '__main__':
    PORT = 5050
    print(f"==================================================================")
    print(f"✦ SUPER APPLICATION BHAIRAVA ANUGRAHA STARTED")
    print(f"✦ Server listening at: http://localhost:{PORT}")
    print(f"✦ Landing Page:        http://localhost:{PORT}/")
    print(f"✦ QnA Codex:           http://localhost:{PORT}/qna")
    print(f"✦ Bhairav Loka Codex:  http://localhost:{PORT}/bhairav-loka")
    print(f"✦ Sādhana Paddhati:    http://localhost:{PORT}/sadhana-paddhati")
    print(f"✦ Ashtami Gateways:    http://localhost:{PORT}/ashtami")
    print(f"✦ Jnāna Samvāda:       http://localhost:{PORT}/jnana-samvada")
    print(f"==================================================================")
    app.run(host='0.0.0.0', port=PORT, debug=False)
