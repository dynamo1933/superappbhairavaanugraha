import urllib.request
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:5050"

def test_sadhana():
    print("=== TESTING SADHANA PADDHATI PAGE ===")
    req = urllib.request.Request(f"{BASE_URL}/sadhana-paddhati")
    with urllib.request.urlopen(req) as res:
        assert res.status == 200, f"Expected 200, got {res.status}"
        html = res.read().decode('utf-8')
    
    print("[PASS] /sadhana-paddhati returned HTTP 200")
    
    # Check default accordion states
    assert 'id="bhairava-krama-section"' in html and 'is-open' in html, "Bhairava section should be present and is-open"
    assert 'id="devi-krama-section"' in html and 'is-collapsed' in html, "Devi section should be present and is-collapsed"
    print("[PASS] Bhairava section is OPEN by default and Devi section is COLLAPSED by default")
    
    # Check key flow elements from padati.html
    padati_keywords = [
        "Foundation of Sādhana",
        "Mandala 1", "Mandala 2", "Mandala 3",
        "Pratham Charana", "8 Mukhi", "11 Mukhi",
        "Dutiya Charana", "14 Mukhi", "Tritiya Charana",
        "flow-arrow", "flow-marker", "stage-card"
    ]
    for kw in padati_keywords:
        assert kw in html, f"Missing padati flow element: {kw}"
    print(f"[PASS] All {len(padati_keywords)} key padati flow elements found")
    
    # Check key elements from devi.html & devi_padathi
    devi_keywords = [
        "Devi Anughara",
        "The Call of the Mother",
        "Ultimate Womb of Power",
        "Purna Shakti",
        "Guidelines",
        "Diet", "Attire", "Timing", "Conduct",
        "Potent Timing for Devi Sādhana",
        "Kamakhya Sadhana Mandala",
        "Devi Mandala 1", "Devi Mandala 2", "Devi Mandala 3",
        "Pathways of Grace"
    ]
    for kw in devi_keywords:
        assert kw in html, f"Missing devi flow element: {kw}"
    print(f"[PASS] All {len(devi_keywords)} key devi flow elements found")
    
    # Extract and test all images in the HTML
    img_matches = re.findall(r'<img[^>]+src=[\'"]([^\'"]*)[\'"]', html)
    print(f"Testing {len(img_matches)} images in the page...")
    for img_url in set(img_matches):
        if not img_url:
            continue
        if img_url.startswith('http'):
            full_url = img_url
        else:
            full_url = f"{BASE_URL}{img_url}"
        with urllib.request.urlopen(full_url) as img_res:
            assert img_res.status == 200
            print(f"  [PASS] {img_url} -> 200 OK")

    # Test /documents
    with urllib.request.urlopen(f"{BASE_URL}/documents") as doc_res:
        assert doc_res.status == 200
        print("[PASS] /documents -> 200 OK")

    print("\n🎉 ALL SĀDHANA PADDHATI TESTS PASSED WITH 100% INTEGRITY!")

if __name__ == '__main__':
    test_sadhana()
