import os
import re

full_da_path = r"C:\Users\dynam\Desktop\full_DA"
superapp_path = r"c:\Users\dynam\Desktop\superappbhairavaanugraha"

print("--- FULL_DA SEARCH FOR VISHESH ---")
if os.path.exists(full_da_path):
    # Search in templates
    templates = os.listdir(os.path.join(full_da_path, "templates"))
    vishesh_templates = [t for t in templates if "vishesh" in t.lower()]
    print("Vishesh templates in full_DA:", vishesh_templates)
    
    # Check app.py in full_DA
    full_da_app = open(os.path.join(full_da_path, "app.py"), encoding='utf-8').read()
    for line in full_da_app.splitlines():
        if "vishesh" in line.lower():
            print("full_DA app.py match:", line)

print("\n--- SUPERAPP SEARCH FOR VISHESH ---")
superapp_templates = os.listdir(os.path.join(superapp_path, "templates"))
vishesh_superapp = [t for t in superapp_templates if "vishesh" in t.lower()]
print("Vishesh templates in superapp:", vishesh_superapp)

superapp_app = open(os.path.join(superapp_path, "app.py"), encoding='utf-8').read()
for line in superapp_app.splitlines():
    if "vishesh" in line.lower():
        print("superapp app.py match:", line)
