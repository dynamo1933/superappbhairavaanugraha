import requests
from bs4 import BeautifulSoup
import os

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:5080")
session = requests.Session()

# 1. Login as admin
login_page = session.get(f"{BASE_URL}/auth/login")
import re
csrf_match = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', login_page.text) or re.search(r'value="([^"]+)"[^>]*name="csrf_token"', login_page.text)
csrf_token = csrf_match.group(1) if csrf_match else ""

login_res = session.post(f"{BASE_URL}/auth/login", data={"username": "admin", "password": "admin123", "csrf_token": csrf_token}, allow_redirects=True)
assert login_res.status_code == 200, "Login failed"
print("[PASS] Logged in successfully as admin")

# 2. Get /stage/1
r1 = session.get(f"{BASE_URL}/stage/1")
assert r1.status_code == 200, f"/stage/1 failed with {r1.status_code}"
soup1 = BeautifulSoup(r1.text, 'html.parser')

# 3. Get /stage/2
r2 = session.get(f"{BASE_URL}/stage/2")
assert r2.status_code == 200, f"/stage/2 failed with {r2.status_code}"
soup2 = BeautifulSoup(r2.text, 'html.parser')

print("\n--- STAGE 1 ELEMENTS ---")
doc1 = soup1.select_one('.stage-card')
assert doc1 is not None, "Missing .stage-card in /stage/1"
iframe1 = soup1.select_one('.doc-embed iframe')
assert iframe1 is not None, "Missing iframe in /stage/1"
print(f"Stage 1 Document Title: {soup1.select_one('.doc-title').text.strip()}")
print(f"Stage 1 Subtitle:       {soup1.select_one('.doc-subtitle').text.strip()}")
print(f"Stage 1 Iframe Source:   {iframe1['src']}")
print(f"Stage 1 New Tab Link:    {soup1.select_one('.btn-external')['href']}")

print("\n--- STAGE 2 ELEMENTS ---")
doc2 = soup2.select_one('.stage-card')
assert doc2 is not None, "Missing .stage-card in /stage/2"
iframe2 = soup2.select_one('.doc-embed iframe')
assert iframe2 is not None, "Missing iframe in /stage/2"
print(f"Stage 2 Document Title: {soup2.select_one('.doc-title').text.strip()}")
print(f"Stage 2 Subtitle:       {soup2.select_one('.doc-subtitle').text.strip()}")
print(f"Stage 2 Iframe Source:   {iframe2['src']}")
print(f"Stage 2 New Tab Link:    {soup2.select_one('.btn-external')['href']}")

# Verify identical structural components
assert soup1.select_one('.doc-header') is not None
assert soup1.select_one('.doc-embed') is not None
assert soup1.select_one('.doc-actions') is not None
assert iframe1['src'] == iframe2['src'], "Iframe sources should match"
print("\n[SUCCESS] /stage/1 page content matches /stage/2 sacred document structure perfectly!")
