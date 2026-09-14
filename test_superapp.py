import urllib.request
import json
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:5050"

tests = [
    ("/", 200, "Journey into the Sacred Inner Realm"),
    ("/qna", 200, "Bhairava"),
    ("/bhairav-loka", 200, "Bhairava Loka"),
    ("/sadhana-paddhati", 200, "Sacred Sādhana Paddhati"),
    ("/ashtami", 200, "What Is Bhairava Waiting for on Ashtami?"),
    ("/jnana-samvada", 200, "Jnāna Samvāda"),
    ("/api/qna", 200, None),
    ("/api/posts", 200, None),
    ("/api/stats", 200, None),
    ("/index.css", 200, ":root"),
    ("/index.js", 200, "capitalizeFirstLetter"),
    ("/static/css/style.css", 200, ":root"),
    ("/static/js/app.js", 200, "DOMContentLoaded"),
    ("/static/css/superapp.css", 200, "--gold:"),
    ("/static/js/superapp.js", 200, "initAmbientCanvas"),
    ("/static/images/logo.jpeg", 200, None),
    ("/static/images/book_cover.jpg", 200, None),
]

all_passed = True
print("=== STARTING COMPREHENSIVE ENDPOINT VERIFICATION ===")

for path, expected_code, content_check in tests:
    url = BASE_URL + path
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'TestClient/1.0'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            code = resp.status
            body = resp.read()
            
            if code != expected_code:
                print(f"[FAIL] {path}: expected code {expected_code}, got {code}")
                all_passed = False
                continue
                
            if content_check:
                text = body.decode('utf-8', errors='ignore')
                if content_check not in text:
                    print(f"[FAIL] {path}: content check '{content_check}' not found")
                    all_passed = False
                    continue
            
            # Special check for JSON endpoints
            if path == "/api/qna":
                data = json.loads(body.decode('utf-8'))
                print(f"[PASS] {path} -> {code} OK (Loaded {len(data)} QnA records)")
            elif path == "/api/posts":
                data = json.loads(body.decode('utf-8'))
                posts = data.get('posts', [])
                print(f"[PASS] {path} -> {code} OK (Loaded {len(posts)} posts)")
                # Test media endpoint for first image
                if posts and posts[0].get('image_filename'):
                    img_path = f"/media/{posts[0]['image_filename']}"
                    try:
                        with urllib.request.urlopen(BASE_URL + img_path, timeout=5) as m_resp:
                            print(f"[PASS] {img_path} -> {m_resp.status} OK (Media served)")
                    except Exception as m_e:
                        print(f"[WARN] {img_path}: {m_e}")
            elif path == "/api/stats":
                data = json.loads(body.decode('utf-8'))
                print(f"[PASS] {path} -> {code} OK (Total posts: {data.get('stats', {}).get('total')})")
            else:
                print(f"[PASS] {path} -> {code} OK")

    except Exception as e:
        print(f"[FAIL] {path} -> Exception: {e}")
        all_passed = False

if all_passed:
    print("\n🎉 ALL 17 AUTOMATED TESTS PASSED SUCCESSFULLY!")
else:
    print("\n❌ SOME TESTS FAILED")
    sys.exit(1)
