/* Sets personal data aside before the case text is classified. Runs in the browser; nothing is sent anywhere.
   The taxonomy rules never need personal data, so the classification is the same with or without it
   (test/run.js checks that on every fixture). What was set aside is counted, never stored. */
(function (root) {
  const BANDS = [[1000, 'under 1k'], [10000, '1k to 10k'], [50000, '10k to 50k'], [250000, '50k to 250k'], [Infinity, 'over 250k']];
  const band = s => {
    const n = parseFloat(String(s).replace(/[^\d.,]/g, '').replace(/[.,](?=\d{3}\b)/g, '').replace(',', '.'));
    if (!isFinite(n)) return 'amount';
    return BANDS.find(([max]) => n < max)[1];
  };
  /* order matters: the longer, more specific patterns go first */
  const PATTERNS = [
    ['email', /\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/gi, () => '[EMAIL]'],
    ['IBAN', /\b[A-Z]{2}\d{2}(?:[ ]?[A-Z0-9]{4}){2,7}(?:[ ]?[A-Z0-9]{1,4})?\b/g, () => '[IBAN]'],
    ['card number', /\b(?:\d[ -]?){12,18}\d\b/g, () => '[CARD]'],
    ['date', /\b\d{1,2}[./]\d{1,2}[./]\d{2,4}\b|\b\d{4}-\d{2}-\d{2}\b/g, () => '[DATE]'],
    ['amount', /(?:\b(?:EUR|USD|GBP|CHF|SEK|NOK|DKK|PLN)\s?|[€£$]\s?)\d(?:\d|[.,](?=\d)|\s(?=\d{3}\b))*|\b\d(?:\d|[.,](?=\d)|\s(?=\d{3}\b))*\s?(?:EUR|euros?)\b/g, m => '[AMOUNT: ' + band(m) + ']'],
    ['phone', /(?:\+|\b00)\d[\d\s()-]{6,}\d\b/g, () => '[PHONE]'],
    ['name', /\b(?:[Cc]ustomer|[Cc]lient|Mr\.?|Mrs\.?|Ms\.?|Dr\.?)\s+([A-Z][a-zÀ-ſ'-]+(?:\s+[A-Z][a-zÀ-ſ'-]+){0,2})/g, (m, name) => m.replace(name, '[NAME]')]
  ];

  function anonymise(text) {
    let out = String(text || '');
    const removed = {};
    for (const [kind, re, fn] of PATTERNS) {
      out = out.replace(re, function () {
        removed[kind] = (removed[kind] || 0) + 1;
        return fn.apply(null, arguments);
      });
    }
    return { text: out, removed };
  }

  const api = { anonymise };
  root.EBA_ANON = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
