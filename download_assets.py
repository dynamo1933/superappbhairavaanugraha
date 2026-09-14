import urllib.request
import ssl
import os

os.makedirs('static/images', exist_ok=True)

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

urls_to_download = {
    'logo.jpeg': 'https://img1.wsimg.com/isteam/ip/5c038251-292d-4e5f-b89c-0804abae124d/_%20(9).jpeg/:/rs=h:139,cg:true,m/qt=q:95',
    'logo_hero.jpeg': 'https://img1.wsimg.com/isteam/ip/5c038251-292d-4e5f-b89c-0804abae124d/_%20(9).jpeg/:/rs=w:1240,h:620,cg:true,m/qt=q:95',
    'book_cover.jpg': 'https://img1.wsimg.com/isteam/ip/5c038251-292d-4e5f-b89c-0804abae124d/PHOTO-2026-07-31-12-03-14.jpg/:/rs=w:806,h:1075,cg:true,m/qt=q:95',
    'kaal_bhairav.jpeg': 'https://img1.wsimg.com/isteam/ip/5c038251-292d-4e5f-b89c-0804abae124d/Kaal%20Bhairav.jpeg/:/cr=t:7.55%25,l:0%25,w:100%25,h:84.91%25/rs=w:600,cg:true',
    'bhairava_1.jpeg': 'https://img1.wsimg.com/isteam/ip/5c038251-292d-4e5f-b89c-0804abae124d/Bhairava%20(1).jpeg/:/cr=t:9.86%25,l:0%25,w:100%25,h:80.28%25/rs=w:600,cg:true',
    'sacred_deities.jpeg': 'https://img1.wsimg.com/isteam/ip/5c038251-292d-4e5f-b89c-0804abae124d/Maa%20Parvati%2C%20Maa%20Durga%2C%20Maa%20Saraswati.jpeg/:/cr=t:43.66%25,l:0%25,w:100%25,h:56.34%25/rs=w:600,cg:true',
    'sadhana_art.png': 'https://img1.wsimg.com/isteam/ip/5c038251-292d-4e5f-b89c-0804abae124d/ChatGPT%20Image%20Apr%2022%2C%202026%2C%2009_32_28%20AM.png/:/rs=w:806,cg:true',
    'kamakhya_tattva.jpeg': 'https://img1.wsimg.com/isteam/ip/5c038251-292d-4e5f-b89c-0804abae124d/_%20(3).jpeg/:/cr=t:0%25,l:0%25,w:100%25,h:100%25/rs=w:600,cg:true',
    'rudraksha_journey.jpg': 'https://img1.wsimg.com/isteam/getty/1767112357/:/cr=t:0%25,l:0%25,w:100%25,h:100%25/rs=w:984,h:519,cg:true',
}

headers = {'User-Agent': 'Mozilla/5.0'}
for fname, u in urls_to_download.items():
    dest = os.path.join('static', 'images', fname)
    try:
        req = urllib.request.Request(u, headers=headers)
        with urllib.request.urlopen(req, context=ctx) as resp, open(dest, 'wb') as out_f:
            out_f.write(resp.read())
        print(f"Downloaded {fname} ({os.path.getsize(dest)} bytes)")
    except Exception as e:
        print(f"Error downloading {fname}: {e}")
