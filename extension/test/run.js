/* Checks for the classifier plugin. Run from the repository root: node extension/test/run.js
   1. parity with the Python reference rules, 2. the taxonomy data matches taxonomy.json,
   3. personal data is set aside and the answer does not change, 4. versions and changes in the case comment,
   5. no network use anywhere in the shipped code, and the permissions stay minimal. */
const fs = require('fs'), path = require('path'), cp = require('child_process');
const EXT = path.join(__dirname, '..'), REPO = path.join(EXT, '..');
require(path.join(EXT, 'taxonomy-data.js')); require(path.join(EXT, 'rules.js'));
const { classify, diff, toComment, stripOwnComments } = require(path.join(EXT, 'classifier.js'));
const { anonymise } = require(path.join(EXT, 'anonymise.js'));
let fail = 0;
const check = (ok, label, detail) => { console.log((ok ? 'ok   ' : 'FAIL ') + label); if (!ok) { fail++; if (detail) console.log('  ' + detail); } };

/* 1. parity */
const fx = JSON.parse(fs.readFileSync(path.join(__dirname, 'fixtures.json'), 'utf8'));
const strip = r => ({ classification: r.classification, evidence: r.evidence.map(e => ({ dimension: e.dimension, value: e.value, code: e.code, quote: e.quote })), confidence: r.confidence });
fx.forEach((f, i) => {
  const got = strip(classify(f.text));
  check(JSON.stringify(got) === JSON.stringify(f.expected), 'parity, case ' + (i + 1) + ': ' + got.classification.modus, 'got ' + JSON.stringify(got).slice(0, 300));
});

/* 2. the bundled names and codes are exactly what build_data.py makes from taxonomy.json */
const built = cp.execFileSync('python3', ['-c', 'import importlib.util,sys;s=importlib.util.spec_from_file_location("b",sys.argv[1]);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);sys.stdout.write(m.build())', path.join(EXT, 'build_data.py')], { encoding: 'utf8' });
check(built === fs.readFileSync(path.join(EXT, 'taxonomy-data.js'), 'utf8'), 'taxonomy-data.js is up to date with taxonomy.json', 'run: python3 extension/build_data.py');
const T = globalThis.EBA_TAXONOMY, codes = new Set();
JSON.parse(fs.readFileSync(path.join(REPO, 'taxonomy.json'), 'utf8'), (k, v) => { if (k === 'code' && typeof v === 'string') codes.add(v); return v; });
const unknown = globalThis.EBA_RULES.filter(r => !T.codes[r.dim] || !T.codes[r.dim][r.value]).map(r => r.dim + ':' + r.value);
check(!unknown.length, 'every rule points at a value that exists in v' + T.version, unknown.join(', '));
const strays = Object.values(T.codes).flatMap(o => Object.values(o)).filter(c => !codes.has(c));
check(!strays.length, 'every code in the plugin exists in taxonomy.json', strays.join(', '));

/* 3. personal data */
const sample = 'Customer Thomas Janssens called on 03/10/2026. EUR 18,400 went to BE68539007547034. Card 4111 1111 1111 1111, phone +32 470 12 34 56, mail t.janssens@example.com.';
const a = anonymise(sample);
check(!/Janssens|BE6853|4111|470 12|example\.com|18,400|03\/10/.test(a.text), 'personal data is set aside', a.text);
check(a.text.includes('[AMOUNT: 10k to 50k]'), 'amounts are kept as a band', a.text);
check(['name', 'IBAN', 'card number', 'phone', 'email', 'amount', 'date'].every(k => a.removed[k] >= 1), 'each kind is counted', JSON.stringify(a.removed));
fx.forEach((f, i) => {
  const raw = classify(f.text).classification, anon = classify(anonymise(f.text).text).classification;
  check(JSON.stringify(raw) === JSON.stringify(anon), 'same answer without personal data, case ' + (i + 1));
});

/* 4. versions: the demo case, before and after the analyst's comment */
const alert = 'On 03/10/2026 a new device was registered and the phone number was changed. The banking app reported an active phone call during the session. At 02:58 an online transfer of EUR 18,400 was approved with two in-app confirmations using the customer\'s own credentials.';
const note = 'He did approve two prompts in his banking app after a call from someone claiming to be from the bank\'s security team. The caller said the money had to be moved to a safe account. He also recalls a text message with a link to a cloned version of the bank\'s login page, two days before the call. The funds went on to a mule account.';
const v1 = classify(anonymise(alert).text), v2 = classify(anonymise(alert + ' ' + note).text);
check(v1.classification.method === 'Phone contact' && v1.classification.modus === 'Pure account takeover', 'version 1 from the alert: phone contact, account takeover', JSON.stringify(v1.classification));
check(v2.classification.method === 'Text message contact' && v2.classification.modus === 'Safe account fraud', 'version 2 with the comment: text message, safe account fraud', JSON.stringify(v2.classification));
const ch = diff(v1.classification, v2.classification).map(x => x.dimension);
check(ch.includes('method') && ch.includes('modus') && ch.includes('labels'), 'the change from version 1 to 2 is reported', ch.join(','));
const c2 = toComment(v2, 2, v1.classification);
check(/^EBA Fraud Taxonomy classification, version 2/.test(c2) && /Changed from version 1: /.test(c2) && /The analyst decides\.$/.test(c2), 'the case comment is versioned and says what changed');
check(!/[–—]/.test(c2), 'no dashes in the case comment');

const c1 = toComment(v1, 1, null), again = stripOwnComments(alert + '\n' + c1 + '\n' + note);
const v2b = classify(anonymise(again.text).text);
check(again.dropped === 1 && JSON.stringify(v2b.classification) === JSON.stringify(v2.classification), "the plugin's own earlier comment is not used as evidence", JSON.stringify(v2b.classification));

/* 5. privacy: no network calls anywhere in the shipped code, minimal permissions */
const banned = /\b(fetch|XMLHttpRequest|WebSocket|sendBeacon|EventSource|importScripts)\b|\.src\s*=|https?:\/\//i;
['background.js', 'classifier.js', 'anonymise.js', 'overlay.js', 'rules.js'].forEach(f => {
  const src = fs.readFileSync(path.join(EXT, f), 'utf8');
  const hit = src.split('\n').findIndex(l => banned.test(l));
  check(hit < 0, 'no network use in ' + f, 'line ' + (hit + 1));
});
const man = JSON.parse(fs.readFileSync(path.join(EXT, 'manifest.json'), 'utf8'));
check((man.permissions || []).join(',') === 'activeTab,scripting' && !man.host_permissions, 'permissions: activeTab and scripting only, no host permissions');

console.log(fail ? '\n' + fail + ' check(s) failed' : '\nall checks passed');
process.exit(fail ? 1 : 0);
