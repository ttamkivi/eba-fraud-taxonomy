/* The plugin panel. It opens from the top-right corner of the page the analyst is working in and shows its
   work in four steps: what it read, what personal data it set aside, which words matched which rule, and
   the result. The result goes back into the case as a structured comment, numbered version 1, 2, 3 for the
   same case. Nothing leaves the browser. */
(function () {
  const HOST_ID = 'eba-taxonomy-panel';
  const old = document.getElementById(HOST_ID);
  if (old) old.remove();
  const TAX = globalThis.EBA_TAXONOMY, CL = globalThis.EBA_CLASSIFIER, AN = globalThis.EBA_ANON;

  /* 1. what to read: the selected text, or the selected part of the field the analyst is typing in */
  const isEditable = el => el && (el.tagName === 'TEXTAREA' || (el.tagName === 'INPUT' && /^(text|search|)$/i.test(el.type || '')) || el.isContentEditable);
  const ae = document.activeElement;
  let editable = isEditable(ae) ? ae : null;
  let sel = String(window.getSelection ? window.getSelection() : '').trim();
  if (!sel && editable && 'value' in editable && editable.selectionEnd > editable.selectionStart) sel = editable.value.slice(editable.selectionStart, editable.selectionEnd).trim();

  /* versions are kept per page, in this extension's own memory, for as long as the page is open */
  const RUNS = globalThis.__EBA_RUNS = globalThis.__EBA_RUNS || {};
  const key = location.origin + location.pathname;

  const host = document.createElement('div');
  host.id = HOST_ID;
  host.style.cssText = 'all:initial;position:fixed;top:12px;right:12px;z-index:2147483647;';
  const root = host.attachShadow({ mode: 'closed' });
  const css = `
    .p{font:13px/1.45 -apple-system,Segoe UI,Roboto,sans-serif;color:#2b2c40;background:#fff;border:1px solid #d6d9e6;border-radius:12px;box-shadow:0 14px 40px rgba(43,44,64,.28);width:420px;max-width:92vw;max-height:86vh;overflow:auto;
       transform-origin:top right;animation:pop .9s cubic-bezier(.2,.8,.2,1)}
    @keyframes pop{from{transform:scale(.05);opacity:0}to{transform:none;opacity:1}}
    @media (prefers-reduced-motion:reduce){.p{animation:none}}
    .h{background:#f3f4f8;border-bottom:1px solid #d6d9e6;padding:9px 12px;display:flex;gap:8px;align-items:center;border-radius:12px 12px 0 0;position:sticky;top:0}
    .logo{font:700 10px ui-monospace,Menlo,monospace;background:#f24abd;color:#fff;border-radius:5px;padding:3px 6px}
    .h b{font-size:13px}.h .v{font-size:11px;color:#7f849c}
    .h button{all:unset;cursor:pointer;margin-left:auto;padding:0 6px;font-size:17px;color:#7f849c}
    .b{padding:10px 12px;display:flex;flex-direction:column;gap:10px}
    .st{display:grid;grid-template-columns:22px 1fr;gap:8px}
    .n{width:20px;height:20px;border-radius:50%;background:#37384c;color:#fff;font:700 10.5px ui-monospace,Menlo,monospace;display:flex;align-items:center;justify-content:center}
    .st b.t{font-size:12.5px;display:block;margin-bottom:2px}
    .kv{display:flex;justify-content:space-between;gap:10px;font-size:12px;color:#5d6179}.kv span:last-child{font-weight:600;color:#2b2c40}
    .chips{display:flex;flex-wrap:wrap;gap:4px}.chips span{font:600 10.5px ui-monospace,Menlo,monospace;background:#f3f4f8;border:1px solid #d6d9e6;border-radius:4px;padding:1px 6px;color:#5d6179}
    .m{font-size:11px;color:#7f849c}
    table{border-collapse:collapse;width:100%;font-size:12px}
    td{padding:3px 2px;border-top:1px solid #eef0f6;vertical-align:top}tr:first-child td{border-top:0}
    td.q{font-weight:600;width:45%}td.a{color:#f24abd;font-weight:700;width:14px}
    td.k{width:74px;font-size:10px;letter-spacing:.06em;text-transform:uppercase;color:#7f849c;font-weight:700}
    .c{font:10.5px ui-monospace,Menlo,monospace;color:#7f849c;margin-left:4px}
    .cf{font-size:9.5px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;color:#7f849c;margin-left:6px}
    .dim{font-size:9.5px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:#7f849c}
    .none{color:#7f849c;font-style:italic}
    .chg div{font-size:12px;padding:2px 0}.chg s{color:#7f849c}
    .row{display:flex;gap:6px;flex-wrap:wrap}
    .btn{all:unset;cursor:pointer;border:1px solid #d6d9e6;border-radius:7px;padding:6px 10px;font-weight:600;font-size:12px;background:#fff}
    .btn.pri{background:#37384c;border-color:#37384c;color:#fff}
    .btn[disabled]{opacity:.45;cursor:default}
    .ok{color:#1a8d47;font-weight:600}
  `;
  const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  function shell(inner, version) {
    root.innerHTML = '<style>' + css + '</style><div class="p" role="dialog" aria-label="EBA Fraud Taxonomy classifier"><div class="h"><span class="logo">EBA</span><b>Fraud Taxonomy classifier</b><span class="v">v' + esc(TAX.version) + (version ? ' &middot; version ' + version : '') + '</span><button id="x" aria-label="Close">&times;</button></div><div class="b">' + inner + '</div></div>';
    root.getElementById('x').onclick = () => host.remove();
  }
  document.documentElement.appendChild(host);
  document.addEventListener('keydown', function onKey(e) { if (e.key === 'Escape') { host.remove(); document.removeEventListener('keydown', onKey, true); } }, true);

  if (!sel) {
    shell('<div>Select the text of the case first: the alert, the recorded facts and any comments. Then press the hotkey again.</div><div class="m">Runs in this browser. Nothing is sent anywhere.</div>');
    return;
  }

  /* 2. set personal data aside, 3. match the words, 4. result */
  const own = CL.stripOwnComments(sel);
  const anon = AN.anonymise(own.text);
  const res = CL.classify(anon.text);
  const prevRuns = RUNS[key] || [];
  const prev = prevRuns.length ? prevRuns[prevRuns.length - 1] : null;
  const version = prevRuns.length + 1;
  const c = res.classification, cd = c.codes, cf = res.confidence;
  const changes = CL.diff(prev && prev.classification, c);
  const comment = CL.toComment(res, version, prev && prev.classification);
  const json = JSON.stringify(Object.assign({ version }, CL.toPayload(res), { personal_data_set_aside: anon.removed }), null, 2);

  const sentences = sel.split(/(?<=[.!?])\s+/).filter(s => s.trim()).length;
  const removedKinds = Object.keys(anon.removed);
  const chosen = new Set([c.modus, c.method, c.initiator, c.instrument].concat(c.labels).filter(Boolean));
  const seen = new Set();
  const matches = res.evidence.filter(e => chosen.has(e.value) && e.quote !== 'no modus phrase matched').filter(e => { const k = e.dimension + e.value; if (seen.has(k)) return false; seen.add(k); return true; });
  const cell = (v, code, conf) => v ? esc(v) + '<span class="c">' + esc(code) + '</span>' + (conf && conf !== 'none' ? '<span class="cf">' + esc(conf) + '</span>' : '') : '<span class="none">not determined</span>';

  let h = '';
  h += '<div class="st"><span class="n">1</span><div><b class="t">Read the case</b>' +
    '<div class="kv"><span>Selected text</span><span>' + sentences + ' sentence' + (sentences === 1 ? '' : 's') + ', ' + sel.length + ' characters</span></div>' +
    '<div class="kv"><span>Earlier versions on this page</span><span>' + (prev ? prevRuns.length : 'none') + '</span></div>' +
    (own.dropped ? '<div class="kv"><span>Earlier plugin comments in the selection</span><span>' + own.dropped + ', not used as evidence</span></div>' : '') + '</div></div>';
  h += '<div class="st"><span class="n">2</span><div><b class="t">Set personal data aside</b>' +
    (removedKinds.length ? '<div class="chips">' + removedKinds.map(k => '<span>' + esc(k) + (anon.removed[k] > 1 ? ' &times;' + anon.removed[k] : '') + '</span>').join('') + '</div>' : '<div class="m">None found.</div>') +
    '<div class="m">Classified on the text without them. Nothing leaves this browser.</div></div></div>';
  h += '<div class="st"><span class="n">3</span><div><b class="t">Match the words to taxonomy rules</b>' +
    (matches.length ? '<table>' + matches.map(e => '<tr><td class="q">&ldquo;' + esc(e.quote) + '&rdquo;</td><td class="a">&rarr;</td><td><span class="dim">' + esc(e.dimension) + '</span> ' + esc(e.value) + '<span class="c">' + esc(e.code) + '</span></td></tr>').join('') + '</table>'
      : '<div class="none">No phrase matched. The standard\'s catch-all is shown for modus.</div>') + '</div></div>';
  if (prev) {
    h += '<div class="st"><span class="n">&Delta;</span><div><b class="t">What changes from version ' + (version - 1) + '</b><div class="chg">' +
      (changes.length ? changes.map(x => '<div><span class="dim">' + esc(x.dimension) + '</span> <s>' + esc(x.from) + '</s> &rarr; <b>' + esc(x.to) + '</b></div>').join('') : '<div class="m">Nothing changed.</div>') + '</div></div></div>';
  }
  h += '<div class="st"><span class="n">4</span><div><b class="t">Result: version ' + version + '</b><table>' +
    '<tr><td class="k">Method</td><td>' + cell(c.method, cd.method, cf.method) + '</td></tr>' +
    '<tr><td class="k">Modus</td><td>' + cell(c.modus, cd.modus, cf.modus) + '</td></tr>' +
    '<tr><td class="k">Class</td><td>' + (c.high_level_classification ? esc(c.high_level_classification) : '<span class="none">not determined</span>') + '</td></tr>' +
    '<tr><td class="k">Initiator</td><td>' + cell(c.initiator, cd.initiator, cf.initiator) + '</td></tr>' +
    '<tr><td class="k">Instrument</td><td>' + cell(c.instrument, cd.instrument, cf.instrument) + '</td></tr>' +
    '<tr><td class="k">Labels</td><td>' + (c.labels.length ? c.labels.map((v, i) => esc(v) + '<span class="c">' + esc(cd.labels[i]) + '</span>').join('<br>') : '<span class="none">none</span>') + '</td></tr></table></div></div>';
  h += '<div class="row"><button class="btn pri" id="ins"' + (editable ? '' : ' disabled') + '>Insert as case comment</button><button class="btn" id="cc">Copy as case comment</button><button class="btn" id="cj">Copy JSON</button></div>' +
    '<div class="m" id="st">' + (editable ? 'Advice from reference rules. The analyst decides.' : 'To insert, click into the comment field of the case; this panel stays open. Advice from reference rules. The analyst decides.') + '</div>';
  shell(h, version);

  /* the analyst can click into the comment field after the panel opens; the panel follows that field */
  document.addEventListener('focusin', e => {
    if (!host.isConnected || !isEditable(e.target)) return;
    editable = e.target; const b = root.getElementById('ins'); if (b) b.disabled = false;
  }, true);

  /* the version counts once the analyst keeps it: inserted or copied */
  let kept = false;
  const keep = () => { if (kept) return; kept = true; (RUNS[key] = prevRuns).push({ classification: c }); };
  const status = (t, ok) => { const el = root.getElementById('st'); el.textContent = t; el.className = ok ? 'm ok' : 'm'; };
  const copy = (text, label) => {
    const done = () => { keep(); status(label + ' copied. Paste it into the case thread.', true); };
    const fallback = () => {
      const ta = document.createElement('textarea'); ta.value = text; ta.style.cssText = 'position:fixed;opacity:0;';
      document.body.appendChild(ta); ta.select();
      let ok = false; try { ok = document.execCommand('copy'); } catch (e) {}
      ta.remove(); ok ? done() : status('Could not copy. Select the text and copy it manually.', false);
    };
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(text).then(done, fallback); else fallback();
  };
  root.getElementById('cc').onclick = () => copy(comment, 'Case comment');
  root.getElementById('cj').onclick = () => copy(json, 'JSON');
  root.getElementById('ins').onclick = () => {
    if (!editable) return;
    editable.focus();
    let ok = false;
    try { ok = document.execCommand('insertText', false, comment); } catch (e) {}
    if (!ok && 'value' in editable) {
      const s = editable.selectionStart || 0, e2 = editable.selectionEnd || 0;
      editable.setRangeText(comment, s, e2, 'end');
      editable.dispatchEvent(new Event('input', { bubbles: true }));
      ok = true;
    }
    if (ok) keep();
    status(ok ? 'Inserted as version ' + version + '. Check it, then save the comment.' : 'This field would not accept the text. Use Copy as case comment.', ok);
  };
})();
