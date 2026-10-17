#!/usr/bin/env python3
"""Content + behaviour validation. Run from project root:  python3 tools/validate.py [--shots DIR]
Requires: beautifulsoup4, playwright (chromium). Starts its own local HTTP server."""
import base64, hashlib, json, os, re, sys, threading, functools, http.server, socketserver
from collections import Counter
from bs4 import BeautifulSoup, Comment

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)
SHOTS = sys.argv[sys.argv.index('--shots') + 1] if '--shots' in sys.argv else None
report = []; fails = []
def ok(cond, msg):
    report.append(('PASS' if cond else 'FAIL') + '  ' + msg)
    if not cond: fails.append(msg)

orig_html = open(P('backup', 'index.original.html'), encoding='utf8').read()
new_html = open(P('index.html'), encoding='utf8').read()
O = BeautifulSoup(orig_html, 'html.parser'); N = BeautifulSoup(new_html, 'html.parser')

# 1. English text: every text node of the original body must exist, unchanged, in the new page
PREVIEW_NOTICE = 'Prévia leve'   # banner of the lightweight preview file, not site content
def texts(soup):
    s = BeautifulSoup(str(soup.body), 'html.parser')
    for t in s(['script', 'style', 'iframe', 'svg', 'dialog']): t.decompose()
    out = []
    for n in s.find_all(string=True):
        if isinstance(n, Comment): continue
        x = ' '.join(n.split())
        if x and not x.startswith(PREVIEW_NOTICE) and x != 'Your browser does not support this video.': out.append(x)
    return out
to, tn = texts(O), texts(N)
missing = Counter(to) - Counter(tn); extra = Counter(tn) - Counter(to)
ok(not missing, f'English text: {len(to)} original text fragments, {sum(missing.values())} missing/altered' + (f' -> {dict(missing)}' if missing else ''))
report.append('INFO  text fragments only in the new page (new UI labels / repeated nav): ' + json.dumps(dict(extra), ensure_ascii=False))
# attributes with content
for attr in ['alt', 'title']:
    a = Counter(e[attr] for e in O.find_all(attrs={attr: True}) if e.name not in ('iframe',))
    b = Counter(e[attr] for e in N.find_all(attrs={attr: True}))
    ok(not (a - b), f'{attr} attributes preserved' + (f' missing {dict(a-b)}' if a - b else ''))
ok(O.title.string == N.title.string, 'page <title> identical')
ok(O.find('meta', attrs={'name': 'description'})['content'] == N.find('meta', attrs={'name': 'description'})['content'], 'meta description identical')

# 2. synopses complete (each original synopsis id present with identical inner HTML)
syn_ok = all(N.find(id=p['id']) and N.find(id=p['id']).decode_contents() == p.decode_contents() for p in O.select('.book-synopsis'))
ok(syn_ok and len(O.select('.book-synopsis')) == 13, f'13 synopses present and identical ({len(N.select(".book-synopsis"))} in new page)')

# 3. books & categories in order
ob = [(a['id'], a.select_one('.book-title').get_text()) for a in O.select('article.book-card')]
nb = [(a['id'], a.select_one('.book-title').get_text()) for a in N.select('article.book-card')]
ok(ob == nb, f'books: same {len(nb)} titles in the same order')
ok([g.get_text() for g in O.select('.book-group-head h3')] == [g.get_text() for g in N.select('.book-group-head h3')], 'book categories: same names and order')

# 4. ids and links
oid = {e['id'] for e in O.find_all(id=True)}; nid = {e['id'] for e in N.find_all(id=True)}
ok(not (oid - nid), 'all original element ids still exist' + (f' missing {oid - nid}' if oid - nid else ''))
oh = Counter((a['href'], ' '.join(a.get_text().split())) for a in O.find_all('a', href=True))
nh = Counter((a['href'], ' '.join(a.get_text().split())) for a in N.find_all('a', href=True))
ok(not (oh - nh), f'all {sum(oh.values())} original links keep text + destination' + (f' missing {dict(oh-nh)}' if oh - nh else ''))
for href in {a['href'] for a in N.find_all('a', href=True)}:
    if href.startswith('#') and len(href) > 1: ok(N.find(id=href[1:]) is not None, f'anchor {href} resolves')

# 5. images: every embedded original image exists byte-identical as a file
files = {}
for d, _, fs in os.walk(P('assets', 'img')):
    for f in fs: files[hashlib.md5(open(os.path.join(d, f), 'rb').read()).hexdigest()] = os.path.relpath(os.path.join(d, f), ROOT)
uris = re.findall(r'data:image/(?:png|webp|jpeg|gif);base64,([A-Za-z0-9+/=]+)', orig_html)
srcdoc_orig = O.find('iframe')['srcdoc']
in_teaser = set(re.findall(r'data:image/(?:png|webp|jpeg|gif);base64,([A-Za-z0-9+/=]+)', srcdoc_orig))
outside = [u for u in uris if u not in in_teaser]
miss_img = [u[:20] for u in outside if hashlib.md5(base64.b64decode(u)).hexdigest() not in files]
ok(not miss_img, f'{len(set(outside))} distinct page images (covers, portrait, banner) saved byte-identical in assets/img')
for img in N.find_all('img'):
    ok(os.path.exists(P(img['src'])), f'img exists: {img["src"]}')

# 6. teaser
js = open(P('assets', 'js', 'teaser-srcdoc.js'), encoding='utf8').read()
srcdoc_new = json.loads(js[js.index('=') + 1:].strip().rstrip(';'))
ok(srcdoc_new == srcdoc_orig, f'Captain Quin interactive teaser identical to original ({len(in_teaser)} embedded scene images kept)')

# 7. videos
for v in N.select('.play-btn'):
    ok(os.path.exists(P(v['data-video'])) and os.path.exists(P(v['data-poster'])), f'video + poster exist: {v["data-video"]}')
ok(len(N.select('.play-btn')) == 4, '4 MP4 videos in gallery')

# 8. translations complete
ref = open(P('i18n', 'en.js'), encoding='utf8').read(); ref = json.loads(ref[ref.index('=', ref.index('REFERENCE')) + 1:].strip().rstrip(';'))
for lang in ['pt', 'es']:
    s = open(P('i18n', lang + '.js'), encoding='utf8').read()
    d = json.loads(s[s.index('=', s.index('I18N.' + lang)) + 1:].strip().rstrip(';'))
    mk = [k for k in ref if not str(d.get(k, '')).strip()]; ek = [k for k in d if k not in ref and not k.startswith('_')]
    ok(not mk and not ek, f'{lang}: {len(ref)} keys translated' + (f' missing {mk}' if mk else '') + (f' unknown {ek}' if ek else ''))
    same = [k for k in ref if d.get(k) == ref[k]]
    report.append(f'INFO  {lang}: keys identical to English (proper names, by design): {same}')
    tz = d.get('_teaser', {})
    nf = [k for k in tz if ('>' + k + '<') not in srcdoc_orig and ("'" + k + "'") not in srcdoc_orig]
    ok(not nf, f'{lang}: {len(tz)} teaser lines map onto the original teaser' + (f' not found {nf}' if nf else ''))

# ---------------------------------------------------------------- browser tests
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
class TS(socketserver.ThreadingTCPServer):
    daemon_threads = True
    def handle_error(self, *a): pass
srv = TS(('127.0.0.1', 0), functools.partial(Q, directory=ROOT)); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = f'http://127.0.0.1:{port}/index.html'
from playwright.sync_api import sync_playwright
VIEWS = [(320, 640, 'phone-small'), (375, 667, 'phone'), (390, 844, 'phone-large'), (430, 932, 'phone-xl'),
         (768, 1024, 'tablet-portrait'), (1024, 768, 'tablet-landscape'), (1280, 720, 'laptop-short'),
         (1366, 768, 'laptop'), (1440, 900, 'desktop'), (1920, 1080, 'fullhd'), (2560, 1080, 'ultrawide'), (2560, 1440, 'qhd')]
with sync_playwright() as pw:
    br = pw.chromium.launch()
    for w, h, name in VIEWS:
        ctx = br.new_context(viewport={'width': w, 'height': h}); pg = ctx.new_page(); errs = []
        pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None); pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.goto(URL); pg.wait_for_timeout(600)
        sw = pg.evaluate('document.documentElement.scrollWidth')
        ok(sw <= w, f'[{name} {w}x{h}] no horizontal scroll (scrollWidth {sw})')
        # header fit: nav items on one line and not overlapping tools
        fit = pg.evaluate("""(()=>{const t=document.querySelector('.header-tools').getBoundingClientRect(),b=document.querySelector('.brand').getBoundingClientRect();
          const nav=document.querySelector('#main-nav'); if(getComputedStyle(document.querySelector('#menu-toggle')).display!=='none') return 'hamburger';
          const as=[...nav.querySelectorAll('a')].map(a=>a.getBoundingClientRect()); const tops=new Set(as.map(r=>Math.round(r.top)));
          return (tops.size===1 && as[as.length-1].right<=t.left && as[0].left>=b.right)?'inline-ok':'overlap'})()""")
        ok(fit in ('hamburger', 'inline-ok'), f'[{name}] header layout: {fit}')
        # elements wider than viewport
        wide = pg.evaluate("""[...document.querySelectorAll('main *, header *, footer *')].filter(e=>{if(e.closest('.car-track')||e.closest('dialog')||e.closest('.film-media')) return false; const r=e.getBoundingClientRect(); return r.width>0 && (r.right>innerWidth+1||r.left<-1)}).slice(0,5).map(e=>e.className||e.tagName)""")
        ok(not wide, f'[{name}] no element overflows the viewport' + (f' {wide}' if wide else ''))
        small = pg.evaluate("""[...document.querySelectorAll('a,button,summary')].filter(e=>{const r=e.getBoundingClientRect();const cs=getComputedStyle(e);return r.width>0&&r.height>0&&cs.visibility!=='hidden'&&!e.closest('[hidden]')&&!e.closest('dialog')&&!e.closest('.main-nav:not(.is-open)')&&(r.height<40&&r.width<40)}).map(e=>e.textContent.trim().slice(0,20)||e.className)""")
        ok(not small, f'[{name}] tap targets >= 40px' + (f' {small}' if small else ''))
        minfont = pg.evaluate("""Math.min(...[...document.querySelectorAll('main p, main h3, main h4, main a, main summary, main .book-category')].filter(e=>e.offsetParent).map(e=>parseFloat(getComputedStyle(e).fontSize)))""")
        ok(minfont >= 12, f'[{name}] smallest text {minfont}px')
        # hero height sanity (banner never more than the screen)
        hh = pg.evaluate("document.querySelector('.tvh-hero').getBoundingClientRect().height")
        report.append(f'INFO  [{name}] banner height {hh:.0f}px of {h}px viewport')
        # carousel
        cr = pg.evaluate("""(async()=>{const g=document.querySelector('.book-group--novels'),t=g.querySelector('.car-track'),n=g.querySelector('.next');
            if(g.classList.contains('is-static')) return 'static'; const b=t.scrollLeft; n.click(); await new Promise(r=>setTimeout(r,900)); return t.scrollLeft>b?'moved':'stuck'})()""")
        ok(cr in ('moved', 'static'), f'[{name}] novels carousel next button: {cr}')
        # mobile menu
        if fit == 'hamburger':
            pg.click('#menu-toggle'); pg.wait_for_timeout(350)
            vis = pg.evaluate("getComputedStyle(document.querySelector('#main-nav')).visibility")
            ok(vis == 'visible' and pg.get_attribute('#menu-toggle', 'aria-expanded') == 'true', f'[{name}] mobile menu opens')
            pg.click('#main-nav a[href="#books"]'); pg.wait_for_timeout(900)
            ok(pg.get_attribute('#menu-toggle', 'aria-expanded') == 'false', f'[{name}] mobile menu closes after choosing a link')
        # language menu inside viewport
        pg.evaluate('scrollTo(0,0)'); pg.click('#lang-btn'); pg.wait_for_timeout(150)
        r = pg.evaluate("(()=>{const r=document.querySelector('#lang-menu').getBoundingClientRect();return [r.left,r.right,r.bottom]})()")
        ok(r[0] >= 0 and r[1] <= w and r[2] <= h, f'[{name}] language menu fully on screen {[round(x) for x in r]}')
        pg.keyboard.press('Escape')
        if SHOTS:
            os.makedirs(SHOTS, exist_ok=True)
            pg.evaluate("document.querySelectorAll('img[loading=lazy]').forEach(i=>i.loading='eager')"); pg.wait_for_timeout(900)
            pg.evaluate('scrollTo(0,0)'); pg.wait_for_timeout(300)
            pg.screenshot(path=f'{SHOTS}/{name}-top.png')
            pg.screenshot(path=f'{SHOTS}/{name}-full.png', full_page=True)
        ok(not errs, f'[{name}] no console errors' + (f' {errs}' if errs else ''))
        ctx.close()

    # ---- functional checks (desktop + phone) ----
    for w, h in [(1440, 900), (390, 844)]:
        ctx = br.new_context(viewport={'width': w, 'height': h}); pg = ctx.new_page(); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.goto(URL); pg.wait_for_timeout(500)
        tag = f'[{w}px]'
        # synopsis dialog
        pg.locator('#book-father-allan summary').scroll_into_view_if_needed(); pg.click('#book-father-allan summary'); pg.wait_for_timeout(400)
        st = pg.evaluate("(()=>{const d=document.querySelector('#synopsis-modal');return [d.open,d.querySelector('.syn-body').textContent.trim(),d.querySelector('.syn-explore').getAttribute('href')]})()")
        full = O.select_one('#book-father-allan-synopsis').get_text()
        ok(st[0] and st[1] == full and st[2] == '#book-father-allan', f'{tag} synopsis dialog shows the full text + Explore link')
        if SHOTS: pg.screenshot(path=f'{SHOTS}/synopsis-{w}.png')
        pg.keyboard.press('Escape'); pg.wait_for_timeout(300)
        foc = pg.evaluate("document.activeElement.closest('#book-father-allan')!==null")
        ok(not pg.evaluate("document.querySelector('#synopsis-modal').open") and foc, f'{tag} Esc closes the dialog and focus returns to the card')
        # video dialog
        pg.locator('#france-1938-trailer .play-btn').scroll_into_view_if_needed(); pg.click('#france-1938-trailer .play-btn'); pg.wait_for_timeout(600)
        vs = pg.evaluate("(()=>{const d=document.querySelector('#video-modal'),v=d.querySelector('video');return [d.open,v.getAttribute('src')||'',v.controls]})()")
        # (this test Chromium cannot decode H.264, so the player may fall through its folder list; tools/test_video_fallback.py tests that part)
        ok(vs[0] and vs[1].endswith('france-1938.mp4') and vs[2], f'{tag} video player opens with controls: {vs[1]}')
        if SHOTS: pg.screenshot(path=f'{SHOTS}/video-{w}.png')
        pg.click('#video-modal .modal-close'); pg.wait_for_timeout(300)
        ok(pg.evaluate("(()=>{const v=document.querySelector('#video-modal video');return !document.querySelector('#video-modal').open && !v.getAttribute('src')})()"), f'{tag} closing the player stops and unloads the video')
        # teaser loads lazily with original document
        pg.locator('#teaser-frame').scroll_into_view_if_needed(); pg.wait_for_timeout(1500)
        ok(pg.evaluate("document.querySelector('#teaser-frame').srcdoc===window.TEASER_SRCDOC"), f'{tag} teaser iframe loaded with the original document (English)')
        # language: switch to PT
        pg.evaluate('scrollTo(0,0)'); pg.click('#lang-btn'); pg.wait_for_timeout(150); pg.click('#lang-menu [data-lang="pt"]'); pg.wait_for_timeout(1200)
        res = pg.evaluate("""(()=>{const D=window.I18N.pt;const bad=[];document.querySelectorAll('[data-i18n]').forEach(e=>{const t=document.createElement('div');t.innerHTML=D[e.dataset.i18n];if(e.innerHTML!==t.innerHTML)bad.push(e.dataset.i18n)});
           return {lang:document.documentElement.lang,bad:bad,title:document.title,btn:document.querySelector('.lang-btn .lang-code').textContent,teaser:document.querySelector('#teaser-frame').srcdoc.includes('O Atlântico muda tudo.'),
           alt:document.querySelector('#book-crackland img').alt,checked:document.querySelector('#lang-menu [data-lang=pt]').getAttribute('aria-checked')}})()""")
        ok(res['lang'] == 'pt-BR' and not res['bad'] and res['btn'] == 'PT' and res['checked'] == 'true', f'{tag} Portuguese applied to every translatable element ({res["title"]})' + (f' not applied: {res["bad"]}' if res['bad'] else ''))
        ok(res['teaser'] and res['alt'] == 'Capa do livro Crackland', f'{tag} Portuguese also applied to teaser text and image alt text')
        if SHOTS: pg.screenshot(path=f'{SHOTS}/pt-top-{w}.png')
        pg.reload(); pg.wait_for_timeout(800)
        ok(pg.evaluate("document.documentElement.lang") == 'pt-BR', f'{tag} language choice persists after reload')
        # keyboard: open menu with keyboard, pick Español
        pg.focus('#lang-btn'); pg.keyboard.press('Enter'); pg.wait_for_timeout(120)
        pg.keyboard.press('ArrowDown'); pg.keyboard.press('Enter'); pg.wait_for_timeout(800)
        es = pg.evaluate("[document.documentElement.lang, document.querySelector('#books-title').textContent, document.querySelector('#book-crackland-synopsis').textContent.slice(0,30)]")
        ok(es[0] == 'es' and es[1] == 'Libros', f'{tag} keyboard-only language change to Español works: {es}')
        if SHOTS and w == 1440:
            pg.locator('#peoples-cup').scroll_into_view_if_needed(); pg.wait_for_timeout(300); pg.screenshot(path=f'{SHOTS}/es-lore-{w}.png')
        # back to English restores the exact original text
        pg.locator('#teaser-frame').scroll_into_view_if_needed(); pg.wait_for_timeout(1500)
        pg.evaluate('scrollTo(0,0)'); pg.click('#lang-btn'); pg.click('#lang-menu [data-lang="en"]'); pg.wait_for_timeout(1000)
        en_back = pg.evaluate("document.querySelector('main').textContent")
        ok(' '.join(O.select_one('#book-crackland-synopsis').get_text().split()) in ' '.join(en_back.split()) and pg.evaluate("document.querySelector('#teaser-frame').srcdoc===window.TEASER_SRCDOC"), f'{tag} switching back to English restores the original text and teaser')
        ok(not errs, f'{tag} no JavaScript errors during interaction' + (f' {errs}' if errs else ''))
        ctx.close()

    # reduced motion + file:// opening
    ctx = br.new_context(viewport={'width': 1280, 'height': 800}, reduced_motion='reduce'); pg = ctx.new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' and 'autoplay' not in m.text else None)
    pg.goto('file://' + P('index.html')); pg.wait_for_timeout(800)
    ok(not errs and pg.evaluate("document.fonts.check('16px Jost') && [...document.fonts].some(f=>f.status==='loaded')"), 'opening index.html directly from disk works (fonts load, no errors)' + (f' {errs}' if errs else ''))
    ok(pg.evaluate("getComputedStyle(document.documentElement).scrollBehavior") == 'auto', 'prefers-reduced-motion disables smooth scrolling/animation')
    ctx.close(); br.close()
srv.shutdown()

print('\n'.join(report)); print(f'\n{len([r for r in report if r.startswith("PASS")])} passed, {len(fails)} failed')
open(P('tools', 'last-validation.txt'), 'w').write('\n'.join(report) + f'\n\n{len(fails)} failed\n')
sys.exit(1 if fails else 0)
