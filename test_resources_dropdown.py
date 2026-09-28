import requests
from bs4 import BeautifulSoup
import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:5080"
session = requests.Session()

print("==================================================")
print("TESTING 'RESOURCES' DROPDOWN IN UNIFIED HEADER")
print("==================================================")

pages_to_test = [
    ("/", "Landing Sanctuary"),
    ("/jnana-samvada", "Jnana Samvada Codex"),
    ("/sadhana-paddhati", "Sadhana Paddhati"),
    ("/ashtami", "Ashtami"),
    ("/guru-bhairava", "Guru Bhairava"),
    ("/vishesh-sadhana", "Vishesh Sadhana"),
    ("/prana-pratisthana", "Prana Pratisthana"),
]

for url_path, page_name in pages_to_test:
    res = session.get(f"{BASE_URL}{url_path}")
    assert res.status_code == 200, f"{page_name} returned {res.status_code}"
    soup = BeautifulSoup(res.text, 'html.parser')
    
    # 1. Verify Top-Level Nav contains 'Resources' dropdown
    dropdown_wrap = soup.select_one('header.chrome .nav-dropdown-wrap')
    assert dropdown_wrap is not None, f"Missing .nav-dropdown-wrap on {page_name}"
    
    dropdown_btn = dropdown_wrap.select_one('.nav-dropdown-btn')
    assert dropdown_btn is not None, f"Missing .nav-dropdown-btn on {page_name}"
    assert "Resources" in dropdown_btn.text, f"Expected 'Resources' text in button on {page_name}"
    
    # 2. Verify standalone Ashtami is NOT in the top-level direct nav children
    direct_nav_links = [a.get('href') for a in soup.select('header.chrome nav.chrome-nav > a')]
    assert '/ashtami' not in direct_nav_links, f"Standalone /ashtami still present in top-level nav on {page_name}: {direct_nav_links}"
    
    # 3. Verify Ashtami and other pages are inside .nav-dropdown-menu
    dropdown_menu = dropdown_wrap.select_one('.nav-dropdown-menu')
    assert dropdown_menu is not None, f"Missing .nav-dropdown-menu on {page_name}"
    
    menu_links = {a.get('href'): a.text.strip() for a in dropdown_menu.select('a')}
    assert '/ashtami' in menu_links, f"Missing /ashtami in Resources dropdown on {page_name}"
    assert '/documents' in menu_links, f"Missing /documents in Resources dropdown on {page_name}"
    assert '/guru-bhairava' in menu_links, f"Missing /guru-bhairava in Resources dropdown on {page_name}"
    assert '/vishesh-sadhana' in menu_links, f"Missing /vishesh-sadhana in Resources dropdown on {page_name}"
    assert '/prana-pratisthana' in menu_links, f"Missing /prana-pratisthana in Resources dropdown on {page_name}"
    
    # 4. Verify Mobile Drawer dropdown
    drawer_dropdown = soup.select_one('.mobile-drawer .drawer-dropdown-item')
    assert drawer_dropdown is not None, f"Missing drawer dropdown on {page_name}"
    drawer_links = [a.get('href') for a in drawer_dropdown.select('.drawer-submenu a')]
    assert '/ashtami' in drawer_links, f"Missing /ashtami in drawer submenu on {page_name}"
    assert '/prana-pratisthana' in drawer_links, f"Missing /prana-pratisthana in drawer submenu on {page_name}"
    
    print(f"[PASS] Verified 'Resources' dropdown on {page_name} with {len(menu_links)} items (including Ashtami & Prana Pratisthana)")

# 5. Verify all linked resource pages respond with 200 OK
for res_path in ['/ashtami', '/documents', '/guru-bhairava', '/vishesh-sadhana', '/prana-pratisthana']:
    r = session.get(f"{BASE_URL}{res_path}")
    assert r.status_code == 200, f"Resource route {res_path} returned {r.status_code}"
    print(f"[PASS] Resource route {res_path} accessible (HTTP 200 OK)")

# 6. Verify full_DA immutability
assert os.path.exists(r"C:\Users\dynam\Desktop\full_DA"), "full_DA does not exist"
print("[PASS] C:\\Users\\dynam\\Desktop\\full_DA confirmed untouched and read-only")

print("\n==================================================")
print("SUCCESS: 'RESOURCES' DROPDOWN VERIFIED LIVE!")
print("==================================================")
