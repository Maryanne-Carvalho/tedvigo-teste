#!/usr/bin/env python3
"""Generates index.html from tools/template.html.

Every English text that existed in the original site is copied *verbatim* from
backup/index.original.html (the file as received) - nothing is retyped by hand.
Run from the project root:  python3 tools/build.py
"""
import json, os, re, html as H
from bs4 import BeautifulSoup
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)
orig = BeautifulSoup(open(P('backup', 'index.original.html'), encoding='utf8').read(), 'html.parser')

def inner(el):            # inner HTML, verbatim
    return el.decode_contents()
def one(sel, i=0):
    return orig.select(sel)[i]

EN = {}                   # key -> inner HTML (content keys)
ATTR = {}                 # key -> plain text (attribute keys)

EN['meta.title'] = inner(orig.title)
ATTR['meta.desc'] = orig.find('meta', attrs={'name': 'description'})['content']
for k, a in zip(['home', 'about', 'books', 'cup', 'peoples', 'audio', 'film', 'contact', 'trailers'], orig.select('.tvh-nav a')):
    EN['nav.' + k] = inner(a)
EN['hero.eyebrow'] = inner(one('.tvh-eyebrow')); EN['hero.h2'] = inner(one('.tvh-h2')); EN['hero.p'] = inner(one('.tvh-p'))
for i, a in enumerate(orig.select('.tvh-buttons a')): EN[f'hero.b{i+1}'] = inner(a)

b = one('#books .section-head')
EN['books.kicker'] = inner(b.select_one('.kicker')); EN['books.title'] = inner(b.h2)
EN['books.lede'] = inner(b.p); EN['books.catalog'] = inner(b.select_one('.catalog-line'))

# ---- book groups -------------------------------------------------------
groups_html = []
GROUP_KEYS = ['novels', 'children', 'cup']
for gi, g in enumerate(orig.select('.book-group')):
    gk = 'group.' + GROUP_KEYS[gi]
    EN[gk + '.h'] = inner(g.select_one('.book-group-head h3'))
    gp = g.select_one('.book-group-head p')
    EN[gk + '.p'] = inner(gp)
    cards = []
    for art in g.select('article.book-card'):
        bid = art['id']; slug = bid[5:]; bk = 'book.' + slug
        img = art.select_one('img.book-cover')
        fn = f'book-{slug}.webp'
        w, h = Image.open(P('assets', 'img', 'covers', fn)).size
        classes = [c for c in img['class']]
        spread = 'front-cover-from-spread' in classes and w > h   # a real back+spine+front spread
        if spread: classes.append('is-spread')
        ATTR[bk + '.alt'] = img['alt']
        EN[bk + '.cat'] = inner(art.select_one('.book-category'))
        title = inner(art.select_one('.book-title'))
        syn = art.select_one('.book-synopsis')
        EN[bk + '.syn'] = inner(syn)
        fallback = inner(art.select_one('.cover-fallback'))
        explore = art.select_one('.book-access')
        cards.append(f'''        <article class="book-card" id="{bid}">
          <div class="book-cover-wrap"><div class="cover-frame{' cover-frame--spread' if spread else ''}"><img alt="{H.escape(img['alt'])}" data-i18n-alt="{bk}.alt" class="{' '.join(classes)}" src="assets/img/covers/{fn}" width="{w}" height="{h}" loading="lazy" decoding="async" onerror="this.hidden=true;this.parentNode.nextElementSibling.hidden=false"></div><div class="cover-fallback" hidden>{fallback}</div></div>
          <div class="book-card-body">
            <div class="book-category" data-i18n="{bk}.cat">{EN[bk + '.cat']}</div>
            <h4 class="book-title">{title}</h4>
            <details class="synopsis-details"><summary><svg aria-hidden="true"><use href="#i-book"/></svg><span data-i18n="ui.readSynopsis">{{{{ui.readSynopsis}}}}</span></summary><p class="book-synopsis expanded-synopsis" id="{syn['id']}" data-i18n="{bk}.syn">{EN[bk + '.syn']}</p></details>
            <a class="book-access" href="{explore['href']}" data-i18n="ui.explore">{{{{ui.explore}}}}</a>
          </div>
        </article>''')
    EN['ui.readSynopsis'] = inner(art.select_one('.synopsis-details summary'))
    EN['ui.explore'] = inner(explore)
    gid = f' id="{g["id"]}"' if g.get('id') else ''
    pclass = ' class="series-tagline"' if 'series-tagline' in (gp.get('class') or []) else ''
    track = f'track-{GROUP_KEYS[gi]}'
    groups_html.append(f'''  <div class="book-group book-group--{GROUP_KEYS[gi]}"{gid}>
    <div class="wrap">
      <div class="book-group-head">
        <div class="group-titles">
          <h3 id="{track}-title" data-i18n="{gk}.h">{EN[gk + '.h']}</h3>
          <p{pclass} data-i18n="{gk}.p">{EN[gk + '.p']}</p>
        </div>
        <div class="car-controls">
          <button class="car-btn prev" type="button" aria-controls="{track}" aria-label="Previous books" data-i18n-aria="ui.prevBooks"><svg aria-hidden="true"><use href="#i-chev-l"/></svg></button>
          <button class="car-btn next" type="button" aria-controls="{track}" aria-label="Next books" data-i18n-aria="ui.nextBooks"><svg aria-hidden="true"><use href="#i-chev-r"/></svg></button>
        </div>
      </div>
      <div class="carousel" role="region" aria-roledescription="carousel" data-i18n-roledesc="ui.carousel" aria-labelledby="{track}-title">
        <div class="car-track" id="{track}" tabindex="0">
{chr(10).join(cards)}
        </div>
        <div class="car-progress" aria-hidden="true"><span></span></div>
      </div>
    </div>
  </div>''')

# ---- People's Cup --------------------------------------------------------
lore = one('#peoples-cup')
EN['lore.kicker'] = inner(lore.select_one('.kicker')); EN['lore.title'] = inner(lore.h2); EN['lore.lede'] = inner(lore.select_one('.section-head p'))
for i, p in enumerate(lore.select('.lore-body p')): EN[f'lore.p{i+1}'] = inner(p)
pr = []
for i, d in enumerate(lore.select('.lore-principle')):
    EN[f'lore.pr{i+1}.h'] = inner(d.h4); EN[f'lore.pr{i+1}.p'] = inner(d.p)
    pr.append(f'''        <li class="lore-principle"><h3 data-i18n="lore.pr{i+1}.h">{EN[f'lore.pr{i+1}.h']}</h3><p data-i18n="lore.pr{i+1}.p">{EN[f'lore.pr{i+1}.p']}</p></li>''')

# ---- Audiobooks ----------------------------------------------------------
au = one('#audiobooks')
EN['audio.kicker'] = inner(au.select_one('.kicker')); EN['audio.title'] = inner(au.h2); EN['audio.lede'] = inner(au.select_one('.section-head p'))
EN['audio.btn'] = inner(au.select_one('.audio-contact a'))
ac = []
for i, c in enumerate(au.select('.audio-card')):
    k = f'audio.c{i+1}'
    EN[k + '.e'] = inner(c.select_one('.eyebrow')); EN[k + '.p'] = inner(c.p); h3 = inner(c.h3)
    trans_h = h3 != 'Cup &amp; Mystery'          # series name stays as is
    if trans_h: EN[k + '.h'] = h3
    hattr = f' data-i18n="{k}.h"' if trans_h else ''
    ac.append(f'''      <article class="audio-card">
        <div aria-hidden="true" class="audio-wave"><span></span><span></span><span></span><span></span><span></span><span></span><span></span></div>
        <p class="eyebrow" data-i18n="{k}.e">{EN[k + '.e']}</p>
        <h3{hattr}>{h3}</h3>
        <p data-i18n="{k}.p">{EN[k + '.p']}</p>
      </article>''')

# ---- Trailers ------------------------------------------------------------
tr = one('#trailers')
sh = tr.select_one('.section-head')
EN['tr.kicker'] = inner(sh.select_one('.kicker')); EN['tr.title'] = inner(sh.h2); EN['tr.lede'] = inner(sh.p)
def hp(sel):
    e = tr.select_one(sel); return inner(e.h3), inner(e.p)
EN['tr.brazil.h'], EN['tr.brazil.p'] = hp('#brazil-2014-trailer')
EN['tr.france.h'], EN['tr.france.p'] = hp('#france-1938-trailer')
EN['tr.quinTeaser.h'], EN['tr.quinTeaser.p'] = hp('#captain-quin-teaser')
gcards = tr.select('#trailer-grid .trailer-card')
quin_h, EN['tr.quinVideo.p'] = inner(gcards[0].h3), inner(gcards[0].p)
EN['tr.cs1.h'], EN['tr.cs1.p'] = inner(gcards[1].h3), inner(gcards[1].p)
EN['tr.cs2.h'], EN['tr.cs2.p'] = inner(gcards[2].h3), inner(gcards[2].p)
EN['tr.coming'] = inner(gcards[1].select_one('.trailer-placeholder span'))
EN['tr.note'] = inner(tr.select_one('.trailer-note'))
# Mexico 1986: no slot existed in the original - text follows the pattern of the
# Brazil/France blocks and is flagged in README as "pending confirmation".
MEX_H = 'Cup &amp; Mystery — Mexico 1986 Trailer'; MEX_P = 'Watch the Mexico 1986 trailer.'
VIDEOS = [  # slug, id, title-key or None, title html, desc key, desc html
    ('brazil-2014', 'brazil-2014-trailer', 'tr.brazil.h', EN['tr.brazil.h'], 'tr.brazil.p', EN['tr.brazil.p']),
    ('france-1938', 'france-1938-trailer', 'tr.france.h', EN['tr.france.h'], 'tr.france.p', EN['tr.france.p']),
    ('captain-quin', 'captain-quin-video', None, quin_h, 'tr.quinVideo.p', EN['tr.quinVideo.p']),
    ('mexico-1986', 'mexico-1986-trailer', 'tr.mexico.h', MEX_H, 'tr.mexico.p', MEX_P),
]
vc = []
for slug, vid, hk, h, pk, p in VIDEOS:
    hattr = f' data-i18n="{hk}"' if hk else ''
    vc.append(f'''      <article class="video-card" id="{vid}">
        <button class="play-btn" type="button" data-video="assets/videos/{slug}.mp4" data-poster="assets/img/posters/{slug}.webp" aria-describedby="{vid}-h">
          <img src="assets/img/posters/{slug}.webp" alt="" width="1024" height="576" loading="lazy" decoding="async">
          <span class="play-icon" aria-hidden="true"><svg><use href="#i-play"/></svg></span>
          <span class="visually-hidden" data-i18n="ui.play">Play video</span>
        </button>
        <div class="trailer-copy"><h3 id="{vid}-h"{hattr}>{h}</h3><p data-i18n="{pk}">{p}</p></div>
      </article>''')

# ---- Film / About / Contact / Footer ------------------------------------
fi = one('#film')
EN['film.eyebrow'] = inner(fi.select_one('.film-intro .eyebrow')); EN['film.title'] = inner(fi.h2); EN['film.lede'] = inner(fi.select_one('.film-intro p'))
for k, c in zip(['q', 'c'], fi.select('.film-card')):
    ATTR[f'film.{k}.alt'] = c.img['alt']
    EN[f'film.{k}.eyebrow'] = inner(c.select_one('.eyebrow')); EN[f'film.{k}.h'] = inner(c.h3)
    EN[f'film.{k}.p'] = inner(c.select_one('.film-card-copy p')); EN[f'film.{k}.btn'] = inner(c.a)
ab = one('#about')
ATTR['about.alt'] = ab.img['alt']; EN['about.eyebrow'] = inner(ab.select_one('.eyebrow')); EN['about.h'] = inner(ab.h2)
for i, p in enumerate(ab.select('.about-copy p')): EN[f'about.p{i+1}'] = inner(p)
co = one('#contact')
EN['contact.eyebrow'] = inner(co.select_one('.eyebrow')); EN['contact.h'] = inner(co.h2)
EN['contact.p'] = inner(co.select('p')[0]); EN['contact.btn'] = inner(co.select_one('a.btn'))
EN['footer'] = inner(orig.footer.select_one('.container'))

# ---- assemble -------------------------------------------------------------
t = open(P('tools', 'template.html'), encoding='utf8').read()
t = t.replace('{{BOOK_GROUPS}}', '\n'.join(groups_html)).replace('{{PRINCIPLES}}', '\n'.join(pr))
t = t.replace('{{AUDIO_CARDS}}', '\n'.join(ac)).replace('{{VIDEO_CARDS}}', '\n'.join(vc))
def sub(m):
    k = m.group(1)
    if k in ATTR: return H.escape(ATTR[k])
    if k in EN: return EN[k]
    raise KeyError(k)
t = re.sub(r'\{\{([\w.]+)\}\}', sub, t)
open(P('index.html'), 'w', encoding='utf8').write(t)

# ---- teaser: srcdoc kept byte-identical, loaded lazily from a JS file -------
srcdoc = orig.find('iframe')['srcdoc']
open(P('assets', 'js', 'teaser-srcdoc.js'), 'w', encoding='utf8').write(
    '/* Captain Quin interactive teaser - original srcdoc, unmodified (JSON-encoded). */\n'
    'window.TEASER_SRCDOC=' + json.dumps(srcdoc, ensure_ascii=False) + ';\n')

# ---- English reference dictionary (generated from the final page) ---------
out = BeautifulSoup(t, 'html.parser'); ref = {}
for el in out.select('[data-i18n]'): ref[el['data-i18n']] = el.decode_contents()
for a, attr in [('alt', 'alt'), ('aria', 'aria-label'), ('title', 'title'), ('content', 'content'), ('roledesc', 'aria-roledescription')]:
    for el in out.select(f'[data-i18n-{a}]'): ref[el[f'data-i18n-{a}']] = el[attr]
open(P('i18n', 'en.js'), 'w', encoding='utf8').write(
    '/* English reference (generated by tools/build.py). The page itself is the source of\n'
    '   English text; this file is NOT loaded by the site - it is the list translators fill. */\n'
    'window.I18N=window.I18N||{};window.I18N_EN_REFERENCE=' + json.dumps(ref, ensure_ascii=False, indent=1) + ';\n')
# ---- fonts.css: self-hosted fonts embedded as data URIs (works on file:// too) ----
import base64
FONTS = [('Cormorant Garamond', 'cormorant-garamond.woff', 'normal', '300 700'),
         ('Cormorant Garamond', 'cormorant-garamond-italic.woff', 'italic', '300 700'),
         ('Lora', 'lora.woff', 'normal', '400 700'),
         ('Jost', 'jost.woff', 'normal', '300 700'),
         ('Cinzel', 'cinzel.woff', 'normal', '400 700')]
css = '/* Generated by tools/build.py from assets/fonts/*.woff (SIL Open Font License, see assets/fonts). */\n'
for fam, fn, style, wt in FONTS:
    b64 = base64.b64encode(open(P('assets', 'fonts', fn), 'rb').read()).decode()
    css += f'@font-face{{font-family:"{fam}";src:url(data:font/woff;base64,{b64}) format("woff");font-weight:{wt};font-style:{style};font-display:swap}}\n'
open(P('assets', 'css', 'fonts.css'), 'w').write(css)
print('index.html written;', len(ref), 'translatable keys')
