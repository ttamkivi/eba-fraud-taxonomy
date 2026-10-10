# Classifier plugin (reference MVP)

A small browser extension that classifies a fraud case against the EBA Fraud Taxonomy, in the browser the analyst
already works in. Select the text of a case, press a hotkey, and the plugin opens from the top-right corner and shows
its work in four steps:

1. **Read the case.** Only the text you selected, only when you press the hotkey or the toolbar button.
2. **Set personal data aside.** Names, IBANs, card numbers, phone numbers, email addresses, dates and exact amounts
   (kept as a band, such as "10k to 50k") are removed before classifying. The rules never need them, and the tests
   check that the answer is the same with or without them.
3. **Match the words to taxonomy rules.** Each value comes with the words of the case that produced it.
4. **Result.** Method, modus, initiator, instrument and labels, each with its code from this repository's
   `taxonomy.json`.

The result goes back into the case as a **structured comment**: "Insert as case comment" writes it into the comment
field the analyst clicks into, "Copy as case comment" puts it on the clipboard. Comments are numbered **version 1,
version 2, ...** for the same page. When the analyst has added to the case and runs the plugin again, the new version
says what changed from the previous one. The plugin's own earlier comments are recognised and never used as evidence.

**It runs entirely in the browser. It sends nothing anywhere.** The taxonomy codes and the rules are bundled with it.

Status: reference MVP, version 0.2.0. A proposal for the EBA Fraud Taxonomy Implementation Guidance Group. Not reviewed
by any bank's security team. Not an EBA product.

## Try it

1. Open `chrome://extensions`, switch on Developer mode, choose **Load unpacked** and pick this `extension` folder.
2. Open `extension/demo/case.html` in the browser. It is an invented case with an alert, recorded facts and a case thread.
   (For a local file, allow "Allow access to file URLs" on the extension's details page.)
3. Press **Select the case**, then `Ctrl+Shift+Y` (`Command+Shift+Y` on a Mac). Version 1 appears.
4. Click into the comment box, press **Insert as case comment** in the plugin, then **Add comment**.
5. Add the sample analyst note, select the case again and press the hotkey. Version 2 shows what changed.

Change the hotkey at `chrome://extensions/shortcuts`. Use invented or anonymised cases while this is a prototype.

## A structured comment

```
EBA Fraud Taxonomy classification, version 2 (classifier plugin, EBA Fraud Taxonomy v7.0)
Method: Text message contact (T0016), high
Modus: Safe account fraud (T0019), high
Initiator: Customer (T0049), high
Instrument: Account-to-account transaction (T0115), moderate
Labels: Money muling (T0124), Phishing (T0089), Smishing (T0098), Vishing (T0103), Fake bank / financial institution (T0065)
Words behind it: "text message", "safe account", "approve two prompts", ...
Changed from version 1: method Phone contact -> Text message contact; modus Pure account takeover -> Safe account fraud; labels none -> ...
Advice from a plugin. The analyst decides.
```

"Copy JSON" gives the same result as data, with the version and the kinds of personal data that were set aside.

## Files

| File | Purpose |
|---|---|
| `manifest.json` | Chrome extension manifest. Permissions: `activeTab` and `scripting` only. |
| `background.js` | Injects the plugin into the active tab when the hotkey or the toolbar button is pressed. Nothing else. |
| `taxonomy-data.js` | Names and codes of v7.0, generated from `../taxonomy.json` by `build_data.py`. Do not edit by hand. |
| `rules.js` | The reference rules: phrase patterns with weights, one taxonomy value each. |
| `anonymise.js` | Sets personal data aside before classifying. |
| `classifier.js` | Scores the rules, picks the values, builds the comment and the version-to-version changes. |
| `overlay.js` | The panel on the page. |
| `demo/case.html` | An invented case to try the plugin on. |
| `test/run.js` | All checks. |

## Checks

Run from the repository root:

```bash
python3 extension/build_data.py   # after taxonomy.json changes
node extension/test/run.js
```

`test/run.js` checks parity with the Python reference rules on six cases, that `taxonomy-data.js` is exactly what
`build_data.py` makes from `taxonomy.json`, that every rule and code exists in v7.0, that personal data is set aside
without changing any answer, that versions and changes are reported, and that there is no network code anywhere and no
permission beyond `activeTab` and `scripting`.

## What it can see and do

- It reads only the text you have selected, only when you ask (`activeTab`). It has no permission to read pages in the
  background and no host permissions.
- It has no network code, and the checks fail if any appears.
- Versions are kept in the extension's own memory for the open page, and only once the analyst keeps a result by
  inserting or copying it. Nothing is written to the page's storage. Reloading the page starts again at version 1;
  the earlier comments stay in the case thread, where they belong.

## Known limits

- It works on text in the page you are looking at. Embedded frames, desktop-only tools and remote desktops are out of
  reach unless the extension is installed where the text is shown.
- The personal-data step is pattern based. It removes the common formats and is not a guarantee: review before sharing
  anything outside the bank.
- The rules cover the clear cases. A case they do not recognise comes back as the taxonomy's catch-all, "New fraud type
  (describe)". Accuracy has not been measured on labelled cases; do not quote accuracy figures.
- "Insert as case comment" works for ordinary text fields. Some custom widgets refuse it; copy and paste always works.
- Managed browsers often allow only approved extensions. Expect a security review, or try it on a test machine.

## Where this fits

Classifying a case consistently is the first step. Passing information to other banks is a separate step, with several
options: the FRIDA alerts under the EPC rulebook, networks that exchange details of a case between banks, or none. The
author works at Salv, which runs one such network (Bridge). This plugin does not call it and does not depend on it.

## Taxonomy, authorship and licence

- Taxonomy content: EBA Fraud Taxonomy v7.0, Euro Banking Association, CC BY 4.0, as stated in `../taxonomy.json`.
  The catch-all's label "Not covered by the taxonomy" is the plugin's own wording, not EBA text.
- Code: licence not yet chosen. Proposed: a permissive open licence, decided together with the EBA.
- Created by Taavi Tamkivi (Salv Technologies) as a proposal for the EBA Fraud Taxonomy Implementation Guidance Group,
  intended to be handed to the EBA's stewardship.
