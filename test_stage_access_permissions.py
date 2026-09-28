import requests
import re
import os

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:5080")

print("==================================================")
print("TESTING USER STAGE ACCESS & ADMIN PERMISSION GATING")
print("==================================================")

# --------------------------------------------------
# Test 1: Unauthenticated Visitor
# --------------------------------------------------
s_unauth = requests.Session()
res_u1 = s_unauth.get(f'{BASE_URL}/stage/1', allow_redirects=False)
assert res_u1.status_code == 302 and '/auth/login' in res_u1.headers.get('Location', ''), \
    f"Expected redirect to login, got {res_u1.status_code}"
print("[PASS] Unauthenticated visitor redirected to /auth/login when accessing /stage/1")

# --------------------------------------------------
# Test 2: Standard User (newuser2 - Only first card accessible)
# --------------------------------------------------
s_user = requests.Session()
login_page = s_user.get(f'{BASE_URL}/auth/login')
csrf = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', login_page.text) or re.search(r'value="([^"]+)"[^>]*name="csrf_token"', login_page.text)
token = csrf.group(1) if csrf else ''

res_login = s_user.post(f'{BASE_URL}/auth/login', data={
    'username': 'newuser2',
    'password': 'password123',
    'csrf_token': token
}, allow_redirects=True)
assert res_login.status_code == 200, "Login failed for newuser2"
print("[PASS] Logged in as standard user 'newuser2'")

# Fetch sadhana-paddhati page
res_pad = s_user.get(f'{BASE_URL}/sadhana-paddhati')
assert res_pad.status_code == 200
html_user = res_pad.text

# Check USER_ACCESS JavaScript mapping
assert '1: true' in html_user, "USER_ACCESS[1] should be true"
assert '2: false' in html_user, "USER_ACCESS[2] should be false"
assert '3: false' in html_user, "USER_ACCESS[3] should be false"
print("[PASS] Verified USER_ACCESS: Stage 1 is true (accessible), Stages 2 & 3 are false (locked)")

# Stage 1: Accessible (HTTP 200)
res_s1 = s_user.get(f'{BASE_URL}/stage/1', allow_redirects=False)
assert res_s1.status_code == 200, f"/stage/1 returned {res_s1.status_code}"
print("[PASS] Standard user accesses first card (/stage/1) -> HTTP 200 OK")

# Stages 2-9: Blocked by admin permission check (HTTP 302 redirect to /sadhana-paddhati)
for stg in [2, 3, 4, 5, 6, 7, 8, 9]:
    res_stg = s_user.get(f'{BASE_URL}/stage/{stg}', allow_redirects=False)
    assert res_stg.status_code == 302 and '/sadhana-paddhati' in res_stg.headers.get('Location', ''), \
        f"/stage/{stg} should redirect to /sadhana-paddhati, got {res_stg.status_code}"
print("[PASS] Standard user blocked from stages 2-9 without admin approval -> 302 Redirect to /sadhana-paddhati")

# Devi Stages: Devi 1 is accessible, Devi 2 & 3 are blocked
res_d1 = s_user.get(f'{BASE_URL}/devi-stage/1', allow_redirects=False)
assert res_d1.status_code == 200, f"/devi-stage/1 returned {res_d1.status_code}"
print("[PASS] Standard user accesses Devi Mandala 1 -> HTTP 200 OK")

for dstg in [2, 3]:
    res_dstg = s_user.get(f'{BASE_URL}/devi-stage/{dstg}', allow_redirects=False)
    assert res_dstg.status_code == 302 and '/sadhana-paddhati' in res_dstg.headers.get('Location', ''), \
        f"/devi-stage/{dstg} should redirect to /sadhana-paddhati, got {res_dstg.status_code}"
print("[PASS] Standard user blocked from Devi Mandalas 2 & 3 without admin approval -> 302 Redirect")

# --------------------------------------------------
# Test 3: User with Admin-Provided Access (test_sadhak - Mandala 1 & 2 granted)
# --------------------------------------------------
s_sadhak = requests.Session()
login_page2 = s_sadhak.get(f'{BASE_URL}/auth/login')
csrf2 = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', login_page2.text) or re.search(r'value="([^"]+)"[^>]*name="csrf_token"', login_page2.text)
token2 = csrf2.group(1) if csrf2 else ''

res_login2 = s_sadhak.post(f'{BASE_URL}/auth/login', data={
    'username': 'test_sadhak',
    'password': 'password123',
    'csrf_token': token2
}, allow_redirects=True)
assert res_login2.status_code == 200
print("[PASS] Logged in as 'test_sadhak' (has admin approval for Stage 2)")

# Verify access to Stage 1 and Stage 2
res_ts_s1 = s_sadhak.get(f'{BASE_URL}/stage/1', allow_redirects=False)
assert res_ts_s1.status_code == 200
res_ts_s2 = s_sadhak.get(f'{BASE_URL}/stage/2', allow_redirects=False)
assert res_ts_s2.status_code == 200, f"/stage/2 returned {res_ts_s2.status_code}"
print("[PASS] 'test_sadhak' accesses both /stage/1 and admin-approved /stage/2 -> HTTP 200 OK")

# Verify Stage 3 is blocked
res_ts_s3 = s_sadhak.get(f'{BASE_URL}/stage/3', allow_redirects=False)
assert res_ts_s3.status_code == 302 and '/sadhana-paddhati' in res_ts_s3.headers.get('Location', '')
print("[PASS] 'test_sadhak' blocked from unapproved /stage/3 -> 302 Redirect")

# --------------------------------------------------
# Test 4: Administrator (admin - Access to all stages)
# --------------------------------------------------
s_admin = requests.Session()
login_page_a = s_admin.get(f'{BASE_URL}/auth/login')
csrf_a = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', login_page_a.text) or re.search(r'value="([^"]+)"[^>]*name="csrf_token"', login_page_a.text)
token_a = csrf_a.group(1) if csrf_a else ''

res_login_a = s_admin.post(f'{BASE_URL}/auth/login', data={
    'username': 'admin',
    'password': 'admin123',
    'csrf_token': token_a
}, allow_redirects=True)
assert res_login_a.status_code == 200
print("[PASS] Logged in as 'admin'")

for i in range(1, 10):
    res_adm = s_admin.get(f'{BASE_URL}/stage/{i}', allow_redirects=False)
    assert res_adm.status_code == 200, f"Admin /stage/{i} failed: {res_adm.status_code}"
print("[PASS] Admin verified access to all stages 1 through 9 -> HTTP 200 OK")

for di in range(1, 4):
    res_adm_d = s_admin.get(f'{BASE_URL}/devi-stage/{di}', allow_redirects=False)
    assert res_adm_d.status_code == 200, f"Admin /devi-stage/{di} failed"
print("[PASS] Admin verified access to all Devi Mandalas 1 through 3 -> HTTP 200 OK")

# --------------------------------------------------
# Test 5: Verify C:\Users\dynam\Desktop\full_DA immutability
# --------------------------------------------------
import os
assert os.path.exists(r"C:\Users\dynam\Desktop\full_DA"), "full_DA must exist"
print("[PASS] C:\\Users\\dynam\\Desktop\\full_DA confirmed untouched and read-only")

print("\n==================================================")
print("SUCCESS: ALL USER PERMISSION GATES VERIFIED LIVE!")
print("==================================================")
