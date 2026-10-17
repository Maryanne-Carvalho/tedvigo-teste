#!/usr/bin/env python3
"""Checks the video player's folder fallback. The test Chromium cannot decode H.264, so it uses
tiny VP9 stand-ins (generated with ffmpeg) inside a temporary copy of the site.
Run from project root: python3 tools/test_video_fallback.py"""
import os, shutil, subprocess, tempfile, threading, functools, http.server, socketserver
from playwright.sync_api import sync_playwright
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tmp = tempfile.mkdtemp()
site = os.path.join(tmp, 'site')
shutil.copytree(ROOT, site, ignore=shutil.ignore_patterns('backup', '*.mp4'))
stub = os.path.join(tmp, 'stub.webm')
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'testsrc=size=320x180:rate=10', '-t', '2', '-c:v', 'libvpx-vp9', stub], check=True)
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
class TS(socketserver.ThreadingTCPServer):
    daemon_threads = True
    def handle_error(self, *a): pass
srv = TS(('127.0.0.1', 0), functools.partial(Q, directory=site)); threading.Thread(target=srv.serve_forever, daemon=True).start()
url = f'http://127.0.0.1:{srv.server_address[1]}/index.html'
vids = os.path.join(site, 'assets', 'videos')
def place(where):
    for d in [vids, site, os.path.join(site, 'videos')]:
        p = os.path.join(d, 'france-1938.mp4')
        if os.path.exists(p): os.remove(p)
    if where:
        os.makedirs(where, exist_ok=True); shutil.copy(stub, os.path.join(where, 'france-1938.mp4'))
results = []
with sync_playwright() as pw:
    br = pw.chromium.launch()
    for label, where, expect in [('in assets/videos', vids, 'assets/videos/france-1938.mp4'),
                                 ('in site root', site, 'france-1938.mp4'),
                                 ('in videos/', os.path.join(site, 'videos'), 'videos/france-1938.mp4'),
                                 ('missing', None, 'ERROR')]:
        place(where)
        pg = br.new_page(); pg.goto(url); pg.wait_for_timeout(400)
        pg.locator('#france-1938-trailer .play-btn').scroll_into_view_if_needed(); pg.click('#france-1938-trailer .play-btn'); pg.wait_for_timeout(2500)
        st = pg.evaluate("(()=>{const d=document.querySelector('#video-modal'),v=d.querySelector('video'),e=d.querySelector('.vid-error');return {src:v.getAttribute('src'),playing:!v.error&&v.readyState>=1,dur:v.duration,err:!e.hidden,msg:e.textContent}})()")
        got = 'ERROR' if st['err'] else st['src']
        good = got == expect and (st['err'] or st['playing'])
        results.append(good)
        print(('PASS' if good else 'FAIL'), f'video {label}: player used {got}', f"(loaded, {st['dur']}s)" if st['playing'] else '', st['msg'].strip() if st['err'] else '')
        pg.close()
    br.close()
srv.shutdown(); shutil.rmtree(tmp)
raise SystemExit(0 if all(results) else 1)
