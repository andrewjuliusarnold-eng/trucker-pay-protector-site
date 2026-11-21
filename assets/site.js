// Home page: the language menu closes with Escape or a tap outside it.
(function () {
  var d = document.querySelector('details.lang');
  if (!d) return;
  document.addEventListener('click', function (e) { if (d.open && !d.contains(e.target)) d.open = false; });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && d.open) { d.open = false; d.querySelector('summary').focus(); }
  });
})();

// Home page video: it starts by itself, sound on, once the whole video is on the screen.
// Most browsers block sound until the visitor has tapped the page once. When the browser says no,
// the video plays without sound and a big "Tap for sound" button shows; one tap turns the sound on.
// It pauses when it scrolls mostly off the screen and goes on again when it is fully back.
// It never starts again by itself after the visitor pauses it or after it ends, and a mute the visitor chose stays on.
// Visitors who ask their phone or computer for less motion get the plain player: nothing starts by itself.
(function () {
  var v = document.querySelector('.vframe video');
  if (!v || !v.play) return;
  if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  var btn = document.querySelector('.vframe .vsound');
  var stopped = false;   // the visitor paused it, or it ended: leave it alone
  var ours = false;      // the pause in progress is ours, not the visitor's
  var inView = false;
  var refused = false;  // the browser will not start it at all (a phone saving battery): the visitor taps play
  var userMuted = false; // the visitor muted it with the player's own button: keep it muted
  var ourVol = 0;        // sound changes the script made that have not reached volumechange yet
  var trying = false;    // a play() is in progress; some browsers (Safari) fire play then pause when they refuse

  function showBtn(on) { if (btn) btn.hidden = !on; }
  function setMuted(m) { if (v.muted !== m) { ourVol++; v.muted = m; } }
  function done() { trying = false; }

  function start() {
    if (stopped || refused || trying || !v.paused) return;
    setMuted(userMuted);
    trying = true;
    var p = v.play();
    if (!p || !p.then) { done(); return; }
    p.then(done, function () {
      // No sound allowed yet: play without sound and offer the button.
      if (!inView || stopped) { done(); return; }
      setMuted(true);
      var q = v.play();
      if (!q || !q.then) { done(); return; }
      q.then(function () { done(); if (!userMuted) showBtn(true); },
             function () { done(); refused = true; setMuted(userMuted); showBtn(false); });
    });
  }

  function pauseOurs() {
    if (v.paused) return;
    ours = true;
    v.pause();
  }

  // Checked on every scroll and resize. "Fully on screen" means the whole video shows. On a short screen
  // (a phone held sideways) the video can be taller than the screen; then it counts once it fills the screen.
  var queued = false;
  function check() {
    queued = false;
    var r = v.getBoundingClientRect(), h = window.innerHeight || document.documentElement.clientHeight;
    if (!r.height) return;
    var seen = Math.max(0, Math.min(r.bottom, h) - Math.max(r.top, 0));
    if (seen >= Math.min(r.height, h) - 2) { inView = true; start(); }
    else if (seen < r.height / 2) { inView = false; pauseOurs(); }
  }
  function soon() { if (!queued) { queued = true; window.requestAnimationFrame(check); } }
  window.addEventListener('scroll', soon, { passive: true });
  window.addEventListener('resize', soon);
  soon();

  v.addEventListener('pause', function () {
    if (ours) { ours = false; return; }
    if (trying) return;
    if (!v.ended) stopped = true;
  });
  v.addEventListener('ended', function () { stopped = true; showBtn(false); });
  v.addEventListener('play', function () { stopped = false; });
  v.addEventListener('volumechange', function () {
    if (!v.muted) showBtn(false);
    if (ourVol > 0) { ourVol--; return; }
    userMuted = v.muted;
    if (userMuted) showBtn(false);
  });

  if (btn) btn.addEventListener('click', function () {
    userMuted = false;
    setMuted(false);
    showBtn(false);
    if (v.paused) { stopped = false; v.play(); }
  });
})();
