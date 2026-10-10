/* Reference classifier. Phrase rules with weights, deterministic, every value carries the words that produced it.
   Port of the Python reference rules; test/run.js checks the two give the same answers. */
(function (root) {
  const DIMS_CONF = ['method', 'modus', 'initiator', 'instrument'];

  function classify(text, tax, rules) {
    tax = tax || root.EBA_TAXONOMY;
    rules = rules || root.EBA_RULES;
    const scores = new Map();
    const evidence = [];
    for (const rule of rules) {
      for (const p of rule.pats) {
        const m = new RegExp(p, 'i').exec(text);
        if (m) {
          const key = rule.dim + '\u0000' + rule.value;
          scores.set(key, (scores.get(key) || 0) + rule.w);
          evidence.push({ dimension: rule.dim, value: rule.value, code: tax.codes[rule.dim][rule.value], quote: m[0].trim(), weight: rule.w });
          break;
        }
      }
    }
    const result = {};
    for (const dim of tax.dims) {
      const picks = [...scores.entries()]
        .filter(([k]) => k.startsWith(dim + '\u0000'))
        .map(([k, s]) => [k.split('\u0000')[1], s])
        .sort((a, b) => (b[1] - a[1]) || (a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0));
      if (!picks.length) result[dim] = tax.multi.includes(dim) ? [] : null;
      else if (tax.multi.includes(dim)) {
        const top = picks[0][1];
        result[dim] = picks.filter(([, s]) => s >= Math.max(2, top - 1)).map(([v]) => v);
      } else result[dim] = picks[0][0];
    }
    if (result.modus === null) {            // the standard's own escape hatch
      result.modus = tax.newModus;
      evidence.push({ dimension: 'modus', value: tax.newModus, code: tax.codes.modus[tax.newModus], quote: 'no modus phrase matched', weight: 0 });
    }
    const confidence = {};
    for (const dim of DIMS_CONF) {
      const s = [...scores.entries()].filter(([k]) => k.startsWith(dim + '\u0000')).map(([, v]) => v).sort((a, b) => b - a);
      if (!s.length) confidence[dim] = 'none';
      else if (s.length === 1 || s[0] - s[1] >= 2) confidence[dim] = s[0] >= 4 ? 'high' : 'moderate';
      else confidence[dim] = 'contested';
    }
    const out = Object.assign({}, result);
    out.high_level_classification = tax.hlcOf[out.modus] || null;
    out.codes = {};
    for (const d of tax.dims) {
      out.codes[d] = Array.isArray(out[d]) ? out[d].map(v => tax.codes[d][v]) : (out[d] ? tax.codes[d][out[d]] : null);
    }
    return { classification: out, evidence, confidence };
  }

  function isChosen(c, e) {
    const v = c[e.dimension];
    return Array.isArray(v) ? v.includes(e.value) : v === e.value;
  }

  /* what goes on the clipboard: structured, with the version, and clearly advice */
  function toPayload(res, tax) {
    tax = tax || root.EBA_TAXONOMY;
    return {
      taxonomy: tax.taxonomy, version: tax.version,
      classification: res.classification,
      evidence: res.evidence.map(e => ({ dimension: e.dimension, value: e.value, code: e.code, quote: e.quote, chosen: isChosen(res.classification, e) })),
      confidence: res.confidence,
      note: 'Suggested by reference rules. The analyst accepts or changes it.'
    };
  }

  function toSummary(res, tax) {
    tax = tax || root.EBA_TAXONOMY;
    const c = res.classification, cd = c.codes;
    const part = (label, v, code) => v ? (label + ': ' + v + ' (' + code + ')') : (label + ': not determined');
    return [
      'EBA Fraud Taxonomy v' + tax.version + ' (suggested)',
      part('Modus', c.modus, cd.modus),
      part('Method', c.method, cd.method),
      part('Initiator', c.initiator, cd.initiator),
      part('Instrument', c.instrument, cd.instrument),
      'Labels: ' + (c.labels.length ? c.labels.map((v, i) => v + ' (' + cd.labels[i] + ')').join(', ') : 'none')
    ].join('\n');
  }

  /* what moved between two classifications of the same case */
  function diff(prev, cur) {
    if (!prev) return [];
    const out = [];
    const fmt = v => Array.isArray(v) ? (v.length ? v.join(', ') : 'none') : (v || 'not determined');
    for (const d of ['method', 'modus', 'initiator', 'instrument']) {
      if ((prev[d] || null) !== (cur[d] || null)) out.push({ dimension: d, from: fmt(prev[d]), to: fmt(cur[d]) });
    }
    const added = cur.labels.filter(l => !prev.labels.includes(l)), dropped = prev.labels.filter(l => !cur.labels.includes(l));
    if (added.length || dropped.length) out.push({ dimension: 'labels', from: fmt(prev.labels), to: fmt(cur.labels), added, dropped });
    return out;
  }

  /* the structured comment the analyst pastes into the case thread: versioned, with the words behind it, clearly advice */
  function toComment(res, version, prev, tax) {
    tax = tax || root.EBA_TAXONOMY;
    const c = res.classification, cd = c.codes, cf = res.confidence;
    const line = (label, v, code, conf) => label + ': ' + (v ? v + ' (' + code + ')' + (conf && conf !== 'none' ? ', ' + conf : '') : 'not determined');
    const chosen = new Set([c.modus, c.method, c.initiator, c.instrument].concat(c.labels).filter(Boolean));
    const one = new Set();   // one quote per value, the first that matched
    const words = [...new Set(res.evidence.filter(e => chosen.has(e.value) && e.quote !== 'no modus phrase matched')
      .filter(e => { const k = e.dimension + '\u0000' + e.value; if (one.has(k)) return false; one.add(k); return true; }).map(e => '"' + e.quote + '"'))];
    const lines = [
      'EBA Fraud Taxonomy classification, version ' + version + ' (classifier plugin, EBA Fraud Taxonomy v' + tax.version + ')',
      line('Method', c.method, cd.method, cf.method),
      line('Modus', c.modus, cd.modus, cf.modus),
      line('Initiator', c.initiator, cd.initiator, cf.initiator),
      line('Instrument', c.instrument, cd.instrument, cf.instrument),
      'Labels: ' + (c.labels.length ? c.labels.map((v, i) => v + ' (' + cd.labels[i] + ')').join(', ') : 'none'),
      'Words behind it: ' + (words.length ? words.join(', ') : 'none matched')
    ];
    const ch = diff(prev, c);
    if (version > 1) lines.push('Changed from version ' + (version - 1) + ': ' + (ch.length ? ch.map(x => x.dimension + ' ' + x.from + ' -> ' + x.to).join('; ') : 'nothing'));
    lines.push('Advice from a plugin. The analyst decides.');
    return lines.join('\n');
  }

  /* the plugin's own earlier comments are not evidence: drop them before classifying again */
  const OWN = /EBA Fraud Taxonomy classification, version \d+[\s\S]*?The analyst decides\./g;
  function stripOwnComments(text) {
    let n = 0;
    const out = String(text || '').replace(OWN, () => { n++; return ' '; });
    return { text: out, dropped: n };
  }

  const api = { classify, toPayload, toSummary, diff, toComment, stripOwnComments };
  root.EBA_CLASSIFIER = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
