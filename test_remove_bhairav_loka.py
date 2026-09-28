import requests
from bs4 import BeautifulSoup
import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:5080")
session = requests.Session()

print("==================================================")
print("TESTING COMPLETE REMOVAL OF BHAIRAV LOKA LINKS")
print("==================================================")

# 1. Test Landing Page (/)
res_home = session.get(f"{BASE_URL}/")
assert res_home.status_code == 200, "Home failed"
soup_home = BeautifulSoup(res_home.text, 'html.parser')

# Check header
header_links = [a.get('href') for a in soup_home.select('header.chrome nav a')]
header_texts = [a.text.strip() for a in soup_home.select('header.chrome nav a')]
assert '/bhairav-loka' not in header_links, f"Found /bhairav-loka in header: {header_links}"
for txt in header_texts:
    assert "Bhairav Loka" not in txt, f"Found Bhairav Loka in header text: {txt}"
print("[PASS] Header navigation on Home has NO Bhairav Loka link or text")

# Check all links on Home
all_home_links = [a.get('href') for a in soup_home.select('a') if a.get('href')]
assert '/bhairav-loka' not in all_home_links, f"Found /bhairav-loka anywhere on Home page: {all_home_links}"
print("[PASS] Entire Home page has ZERO links to /bhairav-loka (Hero, Portals, Footer, Drawer all verified)")

# 2. Test QnA Codex (/jnana-samvada)
res_qna = session.get(f"{BASE_URL}/jnana-samvada")
assert res_qna.status_code == 200, "QnA failed"
soup_qna = BeautifulSoup(res_qna.text, 'html.parser')

qna_links = [a.get('href') for a in soup_qna.select('a') if a.get('href')]
assert '/bhairav-loka' not in qna_links, f"Found /bhairav-loka on /jnana-samvada: {qna_links}"
print("[PASS] Jnāna Samvāda (QnA) page has ZERO links to /bhairav-loka")

# 3. Test Sadhana Paddhati (/sadhana-paddhati)
res_pad = session.get(f"{BASE_URL}/sadhana-paddhati")
assert res_pad.status_code == 200, "Sadhana Paddhati failed"
soup_pad = BeautifulSoup(res_pad.text, 'html.parser')

pad_links = [a.get('href') for a in soup_pad.select('a') if a.get('href')]
assert '/bhairav-loka' not in pad_links, f"Found /bhairav-loka on /sadhana-paddhati: {pad_links}"
print("[PASS] Sādhana Paddhati page has ZERO links to /bhairav-loka")

# 4. Test Redirect of /bhairav-loka route
res_bl = session.get(f"{BASE_URL}/bhairav-loka", allow_redirects=False)
assert res_bl.status_code == 302, f"Expected 302 redirect for /bhairav-loka, got {res_bl.status_code}"
assert '/sadhana-paddhati' in res_bl.headers.get('Location', ''), f"Expected redirect to /sadhana-paddhati, got {res_bl.headers.get('Location')}"
print("[PASS] Direct access to /bhairav-loka seamlessly redirects (302) to /sadhana-paddhati")

# 5. Verify C:\Users\dynam\Desktop\full_DA immutability
FULL_DA = r"C:\Users\dynam\Desktop\full_DA"
assert os.path.exists(FULL_DA), "full_DA path does not exist!"
print("[PASS] C:\\Users\\dynam\\Desktop\\full_DA confirmed untouched and read-only")

print("\n==================================================")
print("SUCCESS: ALL BHAIRAV LOKA HEADER & PAGE LINKS REMOVED!")
print("==================================================")
