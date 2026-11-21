// Checks the home page video's start-by-itself rules (assets/site.js) in Chromium.
// Run from the repo root:  node tools/test/video-autoplay.test.cjs
// Needs Playwright with Chromium. The real mp4 is not loaded: a stand-in player fakes play and pause,
// so the rules can be checked for a browser that allows sound, one that blocks it, and one (Safari, by report)
// that fires "play" then "pause" when it refuses sound.
const { chromium } = require('playwright');
const http = require('http');
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..', '..');
const TYPES = { '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript', '.svg': 'image/svg+xml', '.webp': 'image/webp', '.jpg': 'image/jpeg', '.png': 'image/png' };

function serve() {
  return new Promise(res => {
    const s = http.createServer((q, r) => {
      let f = path.join(ROOT, decodeURIComponent(q.url.split('?')[0]));
      if (!f.startsWith(ROOT)) { r.writeHead(403); return r.end(); }
      if (f.endsWith('/')) f += 'index.html';
      if (f.endsWith('.mp4') || !fs.existsSync(f)) { r.writeHead(404); return r.end(); }
      r.writeHead(200, { 'Content-Type': TYPES[path.extname(f)] || 'application/octet-stream' });
      fs.createReadStream(f).pipe(r);
    }).listen(0, () => res(s));
  });
}

// mode: 'allow' (sound allowed), 'block' (sound refused before a tap), 'safari' (refused, with play then pause events)
function standIn(mode) {
  const st = new WeakMap();
  const get = el => { if (!st.has(el)) st.set(el, { paused: true }); return st.get(el); };
  let tapped = false;
  addEventListener('pointerdown', () => { tapped = true; }, true);
  Object.defineProperty(HTMLMediaElement.prototype, 'paused', { configurable: true, get() { return get(this).paused; } });
  Object.defineProperty(HTMLMediaElement.prototype, 'ended', { configurable: true, get() { return false; } });
  HTMLMediaElement.prototype.play = function () {
    const s = get(this);
    if (mode !== 'allow' && !this.muted && !tapped) {
      if (mode === 'safari') {
        s.paused = false; this.dispatchEvent(new Event('play'));
        s.paused = true; this.dispatchEvent(new Event('pause'));
      }
      return Promise.reject(new DOMException('no sound yet', 'NotAllowedError'));
    }
    if (s.paused) { s.paused = false; this.dispatchEvent(new Event('play')); }
    return Promise.resolve();
  };
  HTMLMediaElement.prototype.pause = function () {
    const s = get(this);
    if (!s.paused) { s.paused = true; this.dispatchEvent(new Event('pause')); }
  };
}

const state = p => p.evaluate(() => {
  const v = document.querySelector('.vframe video'), b = document.querySelector('.vsound');
  return { playing: !v.paused, muted: v.muted, button: !b.hidden };
});
const toVideo = p => p.evaluate(() => document.querySelector('.vframe video').scrollIntoView({ block: 'center', behavior: 'instant' }));
const toTop = p => p.evaluate(() => window.scrollTo({ top: 0, behavior: 'instant' }));
const wait = p => p.waitForTimeout(400);

let failed = 0;
function expect(name, got, want) {
  const bad = Object.keys(want).filter(k => got[k] !== want[k]);
  console.log((bad.length ? 'FAIL ' : 'ok   ') + name + (bad.length ? '  got ' + JSON.stringify(got) + ' want ' + JSON.stringify(want) : ''));
  if (bad.length) failed++;
}

(async () => {
  const server = await serve();
  const url = `http://localhost:${server.address().port}/`;
  const browser = await chromium.launch();
  async function page(mode) {
    const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, reducedMotion: 'no-preference' });
    const p = await ctx.newPage();
    p.on('pageerror', e => { console.log('FAIL page error: ' + e.message); failed++; });
    await p.addInitScript(standIn, mode);
    await p.goto(url);
    return p;
  }

  let p = await page('allow');
  await wait(p); expect('allow: nothing plays at the top', await state(p), { playing: false });
  await toVideo(p); await wait(p); expect('allow: fully in view plays with sound', await state(p), { playing: true, muted: false, button: false });
  await p.evaluate(() => { document.querySelector('.vframe video').muted = true; }); await wait(p);
  await toTop(p); await wait(p); expect('allow: scrolled away pauses', await state(p), { playing: false });
  await toVideo(p); await wait(p); expect("allow: the visitor's own mute is kept on return", await state(p), { playing: true, muted: true, button: false });
  await p.evaluate(() => document.querySelector('.vframe video').pause()); await toTop(p); await wait(p); await toVideo(p); await wait(p);
  expect('allow: stays paused after the visitor pauses it', await state(p), { playing: false });
  await p.context().close();

  p = await page('block');
  await toVideo(p); await wait(p); expect('block: plays muted with the button', await state(p), { playing: true, muted: true, button: true });
  await p.click('.vsound'); await wait(p); expect('block: one tap turns sound on', await state(p), { playing: true, muted: false, button: false });
  await p.evaluate(() => { document.querySelector('.vframe video').muted = true; }); await wait(p);
  await toTop(p); await wait(p); await toVideo(p); await wait(p);
  expect("block: tap for sound, visitor mutes, away and back: mute kept", await state(p), { playing: true, muted: true, button: false });
  await p.context().close();

  p = await page('safari');
  await toVideo(p); await wait(p); expect('safari-style refusal: still plays muted with the button', await state(p), { playing: true, muted: true, button: true });
  await toTop(p); await wait(p); await toVideo(p); await wait(p);
  expect('safari-style refusal: away and back still plays', await state(p), { playing: true, muted: true, button: true });
  await p.context().close();

  await browser.close(); server.close();
  console.log(failed ? `${failed} failed` : 'all passed');
  process.exit(failed ? 1 : 0);
})();
