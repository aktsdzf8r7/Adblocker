// Element picker: hover to highlight, click to hide the element permanently
// (adds a "host##selector" custom filter). Esc cancels.
(() => {
  if (globalThis.__schildPicker) return;
  globalThis.__schildPicker = true;

  const host = location.hostname.replace(/^www\./, '');
  const root = document.createElement('schild-picker');
  const shadow = root.attachShadow({ mode: 'closed' });
  shadow.innerHTML = `
    <style>
      .box { position: fixed; pointer-events: none; z-index: 2147483646; background: rgba(217,48,37,.25);
             outline: 2px solid #d93025; border-radius: 2px; transition: all .05s; }
      .bar { position: fixed; left: 50%; bottom: 16px; transform: translateX(-50%); z-index: 2147483647;
             font: 13px/1.4 system-ui, sans-serif; background: #202124; color: #fff; padding: 10px 14px;
             border-radius: 10px; box-shadow: 0 4px 16px rgba(0,0,0,.35); display: flex; gap: 10px;
             align-items: center; max-width: calc(100vw - 32px); }
      code { background: #3c4043; padding: 2px 6px; border-radius: 4px; max-width: 50vw; overflow: hidden;
             text-overflow: ellipsis; white-space: nowrap; display: inline-block; vertical-align: middle; }
      button { font: inherit; border: 0; border-radius: 6px; padding: 5px 10px; cursor: pointer; }
      .ok { background: #d93025; color: #fff; } .no { background: #5f6368; color: #fff; }
      .hint { opacity: .8; }
    </style>
    <div class="box" hidden></div>
    <div class="bar"><span class="hint">Element anklicken, das ausgeblendet werden soll · Esc = Abbrechen</span></div>`;
  const box = shadow.querySelector('.box');
  const bar = shadow.querySelector('.bar');
  document.documentElement.appendChild(root);

  let current = null;
  let locked = false;

  const cssEscape = (s) => (globalThis.CSS?.escape ? CSS.escape(s) : s.replace(/[^\w-]/g, '\\$&'));

  function isStableClass(c) {
    // Skip generated/hash-like class names.
    return /^[a-zA-Z][\w-]{1,40}$/.test(c) && !/\d{3,}/.test(c) && !/^(css|sc|jsx|emotion)-/.test(c);
  }

  function partFor(el) {
    if (el.id && /^[a-zA-Z][\w-]*$/.test(el.id) && !/\d{4,}/.test(el.id)) return `#${cssEscape(el.id)}`;
    let part = el.localName;
    const classes = [...el.classList].filter(isStableClass).slice(0, 3);
    if (classes.length) part += classes.map((c) => `.${cssEscape(c)}`).join('');
    return part;
  }

  function selectorFor(el) {
    const parts = [];
    let node = el;
    while (node && node.nodeType === 1 && node !== document.documentElement && parts.length < 5) {
      let part = partFor(node);
      const parent = node.parentElement;
      if (!part.startsWith('#') && parent) {
        const same = [...parent.children].filter((c) => c.matches(part));
        if (same.length > 1) part += `:nth-of-type(${[...parent.children].filter((c) => c.localName === node.localName).indexOf(node) + 1})`;
      }
      parts.unshift(part);
      const sel = parts.join(' > ');
      try {
        if (document.querySelectorAll(sel).length === 1) return sel;
      } catch {
        // continue with a longer selector
      }
      if (part.startsWith('#')) break;
      node = parent;
    }
    return parts.join(' > ');
  }

  function highlight(el) {
    const r = el.getBoundingClientRect();
    Object.assign(box.style, { left: `${r.left}px`, top: `${r.top}px`, width: `${r.width}px`, height: `${r.height}px` });
    box.hidden = false;
  }

  function onMove(e) {
    if (locked) return;
    const el = document.elementFromPoint(e.clientX, e.clientY);
    if (!el || el === root || el === document.body || el === document.documentElement) return;
    current = el;
    highlight(el);
  }

  function confirmSelection(el) {
    locked = true;
    const selector = selectorFor(el);
    highlight(el);
    bar.innerHTML = '';
    const label = document.createElement('span');
    label.textContent = 'Ausblenden:';
    const code = document.createElement('code');
    code.textContent = selector;
    code.title = selector;
    const parentBtn = document.createElement('button');
    parentBtn.className = 'no';
    parentBtn.textContent = 'Größer';
    parentBtn.title = 'Übergeordnetes Element wählen';
    const ok = document.createElement('button');
    ok.className = 'ok';
    ok.textContent = 'Ausblenden';
    const no = document.createElement('button');
    no.className = 'no';
    no.textContent = 'Abbrechen';
    bar.append(label, code, parentBtn, ok, no);
    parentBtn.onclick = () => {
      const p = el.parentElement;
      if (p && p !== document.body && p !== document.documentElement) {
        current = p;
        confirmSelection(p);
      }
    };
    no.onclick = cleanup;
    ok.onclick = async () => {
      el.style.setProperty('display', 'none', 'important');
      try {
        await chrome.runtime.sendMessage({ type: 'addFilter', filter: `${host}##${selector}` });
      } finally {
        cleanup();
      }
    };
  }

  function onClick(e) {
    if (e.composedPath().includes(root)) return;
    e.preventDefault();
    e.stopPropagation();
    e.stopImmediatePropagation();
    if (!locked && current) confirmSelection(current);
  }

  function onKey(e) {
    if (e.key === 'Escape') cleanup();
  }

  function cleanup() {
    document.removeEventListener('mousemove', onMove, true);
    document.removeEventListener('click', onClick, true);
    document.removeEventListener('keydown', onKey, true);
    root.remove();
    globalThis.__schildPicker = false;
  }

  document.addEventListener('mousemove', onMove, true);
  document.addEventListener('click', onClick, true);
  document.addEventListener('keydown', onKey, true);
})();
