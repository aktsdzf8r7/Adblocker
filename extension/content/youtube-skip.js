// Fallback for YouTube ads that still slip through (e.g. server-inserted):
// mutes the ad, jumps to its end and clicks "Skip" as soon as possible.
(() => {
  if (globalThis.__schildYTSkip) return;
  globalThis.__schildYTSkip = true;

  const SKIP_BUTTONS = [
    '.ytp-skip-ad-button',
    '.ytp-ad-skip-button',
    '.ytp-ad-skip-button-modern',
    '.ytp-ad-skip-button-slot button',
    '.ytp-ad-overlay-close-button',
    'button[id^="skip-button"]',
  ].join(',');

  let wasMuted = null;

  function tick() {
    const player = document.querySelector('#movie_player, .html5-video-player');
    if (!player) return;
    const video = player.querySelector('video');
    const adShowing = player.classList.contains('ad-showing') || player.classList.contains('ad-interrupting');

    for (const btn of document.querySelectorAll(SKIP_BUTTONS)) {
      if (btn.offsetParent !== null) btn.click();
    }

    if (adShowing && video) {
      if (wasMuted === null) wasMuted = video.muted;
      video.muted = true;
      if (Number.isFinite(video.duration) && video.duration > 0 && video.currentTime < video.duration - 0.1) {
        video.currentTime = video.duration;
      }
      try { video.playbackRate = 16; } catch { /* unsupported rate */ }
    } else if (!adShowing && video && wasMuted !== null) {
      video.muted = wasMuted;
      video.playbackRate = 1;
      wasMuted = null;
    }
  }

  let scheduled = false;
  const schedule = () => {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(() => {
      scheduled = false;
      tick();
    });
  };
  const observer = new MutationObserver(schedule);
  const start = () => {
    observer.observe(document.documentElement, { subtree: true, attributes: true, attributeFilter: ['class'], childList: true });
    setInterval(tick, 500);
  };
  if (document.documentElement) start();
  else document.addEventListener('DOMContentLoaded', start, { once: true });
})();
