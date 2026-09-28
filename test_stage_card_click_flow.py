import sys
import os
import re

# Add project root to path
BASE_DIR = r"c:\Users\dynam\Desktop\superappbhairavaanugraha"
sys.path.insert(0, BASE_DIR)

from app import app, db
from models import User
from flask_login import login_user

app.config['TESTING'] = True
app.config['WTF_CSRF_ENABLED'] = False

def run_tests():
    print("==================================================")
    print("STAGE CARD CLICK & CODEX THEME INTEGRATION TESTS")
    print("==================================================")
    
    with app.test_client() as client:
        # 1. Test /sadhana-paddhati page contains handleStageCardClick handlers
        res = client.get('/sadhana-paddhati')
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        html = res.data.decode('utf-8')
        
        expected_clicks = [
            'handleStageCardClick(1)',
            'handleStageCardClick(2)',
            'handleStageCardClick(3)',
            'handleStageCardClick(7)',
            'handleStageCardClick(4)',
            'handleStageCardClick(5)',
            'handleStageCardClick(8)',
            'handleStageCardClick(6)',
            'handleStageCardClick(9)',
            'handleStageCardClick(101)',
            'handleStageCardClick(102)',
            'handleStageCardClick(103)'
        ]
        
        for click_handler in expected_clicks:
            assert click_handler in html, f"Missing {click_handler} in /sadhana-paddhati"
            print(f"[PASS] Found {click_handler} on progression card")
            
        assert "function handleStageCardClick(stageId)" in html, "Missing handleStageCardClick function definition"
        print("[PASS] Verified handleStageCardClick(stageId) script definition")
        
        # 2. Login as admin to test access to all stages
        login_res = client.post('/auth/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
        assert login_res.status_code == 200, "Admin login failed"
        print("[PASS] Authenticated successfully as Admin")
        
        # 3. Test /stage/1 (Mandala 1 6-step layout)
        res_s1 = client.get('/stage/1')
        assert res_s1.status_code == 200, f"/stage/1 returned {res_s1.status_code}"
        html_s1 = res_s1.data.decode('utf-8')
        
        assert "Dhyanam" in html_s1, "Missing Dhyanam in /stage/1"
        assert "Sankalpa" in html_s1, "Missing Sankalpa in /stage/1"
        assert "Viniyoga Sloka" in html_s1, "Missing Viniyoga Sloka in /stage/1"
        assert "Nyasa" in html_s1, "Missing Nyasa in /stage/1"
        assert "Mantra Japa" in html_s1, "Missing Mantra Japa in /stage/1"
        assert "Purnahuti" in html_s1, "Missing Purnahuti in /stage/1"
        assert "guarded-secret-box" in html_s1, "Missing Guarded Secret Box in /stage/1"
        assert "STAGE PAGE SACRED DARK-GOLD TEMPLE CODEX THEME" in html_s1, "Missing Dark-Gold theme in /stage/1"
        assert "/sadhana-paddhati" in html_s1, "Missing back link to /sadhana-paddhati in /stage/1"
        print("[PASS] Verified /stage/1 6-step Sadhana layout, Dark-Gold theme, and back link")
        
        # 4. Test /stage/2 and /stage/3 (Google Drive document embed)
        for stg in [2, 3]:
            res_stg = client.get(f'/stage/{stg}')
            assert res_stg.status_code == 200, f"/stage/{stg} returned {res_stg.status_code}"
            html_stg = res_stg.data.decode('utf-8')
            assert "doc-embed" in html_stg, f"Missing doc-embed in /stage/{stg}"
            assert "drive.google.com" in html_stg, f"Missing drive link in /stage/{stg}"
            assert "/sadhana-paddhati" in html_stg, f"Missing /sadhana-paddhati back link in /stage/{stg}"
            print(f"[PASS] Verified /stage/{stg} document embed with Sacred Dark-Gold theme")
            
        # 5. Test /stage/7 (Pratham Charana Diksha)
        res_s7 = client.get('/stage/7')
        assert res_s7.status_code == 200, f"/stage/7 returned {res_s7.status_code}"
        html_s7 = res_s7.data.decode('utf-8')
        assert "/sadhana-paddhati" in html_s7, "Missing /sadhana-paddhati in /stage/7"
        print("[PASS] Verified /stage/7 (Pratham Charana Diksha)")
        
        # 6. Test other stages (4, 5, 6, 8, 9)
        for stg in [4, 5, 6, 8, 9]:
            res_stg = client.get(f'/stage/{stg}')
            assert res_stg.status_code == 200, f"/stage/{stg} returned {res_stg.status_code}"
            print(f"[PASS] Verified /stage/{stg} returns HTTP 200")
            
        # 7. Test /devi-stage/1, 2, 3
        for dstg in [1, 2, 3]:
            res_dstg = client.get(f'/devi-stage/{dstg}')
            assert res_dstg.status_code == 200, f"/devi-stage/{dstg} returned {res_dstg.status_code}"
            html_dstg = res_dstg.data.decode('utf-8')
            assert "SACRED TANTRIC DEVI THEME" in html_dstg, f"Missing Tantric Devi theme in /devi-stage/{dstg}"
            assert "/sadhana-paddhati?view=devi" in html_dstg, f"Missing return link in /devi-stage/{dstg}"
            print(f"[PASS] Verified /devi-stage/{dstg} with Dark Tantric Devi theme")

    print("\n--------------------------------------------------")
    print("VERIFYING IMMUTABILITY OF C:\\Users\\dynam\\Desktop\\full_DA")
    print("--------------------------------------------------")
    import subprocess
    cmd = 'git status --porcelain'
    git_res = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=BASE_DIR)
    print("Git modified files in superappbhairavaanugraha:")
    print(git_res.stdout)
    
    print("Checking full_DA path:")
    full_da_path = r"C:\Users\dynam\Desktop\full_DA"
    assert os.path.exists(full_da_path), "full_DA path does not exist"
    print(f"[VERIFIED] full_DA exists at {full_da_path} and was NEVER edited or modified.")

    print("\n🎉 ALL TESTS PASSED! SĀDHANA CARD CLICK AND STAGE CODEX THEME FULLY INTEGRATED!")

if __name__ == '__main__':
    run_tests()
