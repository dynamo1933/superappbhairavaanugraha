import sys
sys.stdout.reconfigure(encoding='utf-8')
from bs4 import BeautifulSoup
import re

# ==================== 1. PREPARE QNA TEMPLATE ====================
with open(r'C:\Users\dynam\Desktop\Bhairva\index.html', 'r', encoding='utf-8', errors='ignore') as f:
    bhairva_html = f.read()

# In Bhairva, let's replace the chrome header nav with our unified superapp navigation:
# Replace <nav class="nav">...</nav>
old_nav_pattern = r'<nav class="nav">.*?</nav>'
new_nav = '''<nav class="nav">
        <a href="/" title="Return to Landing Page">Home</a>
        <a class="is-active" href="/qna" title="Bhairava QnA Codex">☸ QnA</a>
        <a href="/bhairav-loka" title="Bhairav Loka Sahasralinga">✦ Bhairav Loka</a>
        <a href="#categories" data-scroll=".categories">Folios</a>
        <a href="#recent" data-scroll=".recent">Recent</a>
        <a href="#guruji" data-scroll="#guruji">Guruji</a>
      </nav>'''

qna_html = re.sub(old_nav_pattern, new_nav, bhairva_html, flags=re.DOTALL)

# In header left link, change href="#" data-scroll="top" to href="/"
qna_html = qna_html.replace(
    '<a class="left" href="#" data-scroll="top">',
    '<a class="left" href="/" title="Bhairava Anugraha Super App">'
)
# Add Super App badge after </em></span>
qna_html = qna_html.replace(
    '<em>Anugraha</em></span>',
    '<em>Anugraha</em></span> <span class="mono" style="font-size:9px; letter-spacing:0.18em; padding:2px 6px; background:rgba(212,166,74,0.15); color:var(--gold-3); border:1px solid rgba(212,166,74,0.35); border-radius:3px; margin-left:6px;">SUPER APP</span>'
)

with open(r'templates\qna.html', 'w', encoding='utf-8') as f:
    f.write(qna_html)

print("Created templates/qna.html successfully!")

# ==================== 2. PREPARE BHAIRAV LOKA TEMPLATE ====================
with open(r'C:\Users\dynam\Desktop\instagram_scrap\templates\index.html', 'r', encoding='utf-8', errors='ignore') as f:
    loka_html = f.read()

# In instagram_scrap index.html, update header to include Superapp nav
old_chrome_pattern = r'<header class="chrome" id="site-chrome">.*?</header>'
new_chrome = '''<header class="chrome" id="site-chrome">
    <div class="chrome-inner">
      <div class="left" style="display:flex; align-items:center; gap:10px;">
        <a href="/" style="display:flex; align-items:center; gap:8px; text-decoration:none; color:inherit;">
          <span class="om">ॐ</span>
          <span class="b">Bhairava <em>Loka</em></span>
          <span class="mono" style="font-size:9px; letter-spacing:0.18em; padding:2px 6px; background:rgba(212,166,74,0.15); color:var(--gold-3); border:1px solid rgba(212,166,74,0.35); border-radius:3px;">SUPER APP</span>
        </a>
      </div>

      <nav class="nav" style="display:flex; align-items:center; gap:8px;">
        <a href="/" style="padding:6px 12px; color:var(--ink-mute); font-size:15px; border-radius:4px; text-decoration:none;">Home</a>
        <a href="/qna" style="padding:6px 12px; color:var(--gold-3); font-size:15px; border-radius:4px; border:1px solid rgba(212,166,74,0.3); background:rgba(212,166,74,0.08); text-decoration:none;">☸ QnA</a>
        <a href="/bhairav-loka" style="padding:6px 12px; color:var(--gold-3); font-weight:600; font-size:15px; border-radius:4px; border-bottom:2px solid var(--gold); text-decoration:none;">✦ Bhairav Loka</a>
        <a href="/sadhana-paddhati" style="padding:6px 12px; color:var(--ink-mute); font-size:15px; border-radius:4px; text-decoration:none;">Sādhana</a>
      </nav>

      <div class="nav-actions">
        <div class="stat-badge">
          <span class="dot"></span>
          <span id="header-total-count">{{ total_posts }} Bhairav Swarupa</span>
        </div>
        <button class="audio-toggle" id="audio-toggle-btn" type="button" title="Toggle Temple Bell Chime">
          <span>🔕 Audio Off</span>
        </button>
        <button class="search-btn" id="chrome-search-btn" type="button" aria-haspopup="dialog">
          <span>Search Codex</span>
          <span class="kbd">⌘K</span>
        </button>
      </div>
    </div>
  </header>'''

loka_html = re.sub(old_chrome_pattern, new_chrome, loka_html, flags=re.DOTALL)

with open(r'templates\bhairav_loka.html', 'w', encoding='utf-8') as f:
    f.write(loka_html)

print("Created templates/bhairav_loka.html successfully!")
