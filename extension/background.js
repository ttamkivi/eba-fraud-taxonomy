/* Runs only when the analyst presses the hotkey or the toolbar button.
   It injects the classifier into the active tab and does nothing else. No network. */
async function run(tab) {
  if (!tab || !tab.id) return;
  try {
    await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      files: ['taxonomy-data.js', 'rules.js', 'anonymise.js', 'classifier.js', 'overlay.js']
    });
  } catch (e) {
    console.warn('Could not run on this page (browser pages and some stores block extensions):', e && e.message);
  }
}
chrome.commands.onCommand.addListener((command, tab) => { if (command === 'classify-selection') run(tab); });
chrome.action.onClicked.addListener(run);
