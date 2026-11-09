// Render out/pathology.html -> PDF with Chromium.
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const root = path.resolve(__dirname, '..');
  const out = process.argv[2] || path.join(root, 'out', 'Pathology_Revision_Notes.pdf');
  const b = await chromium.launch();
  const p = await b.newPage();
  await p.goto('file://' + path.join(root, 'out', 'pathology.html'), { waitUntil: 'networkidle' });
  await p.evaluate(() => document.fonts.ready);
  await p.waitForTimeout(800);
  await p.pdf({ path: out, format: 'A4', printBackground: true, preferCSSPageSize: true, outline: true, tagged: true });
  await b.close();
  console.log('pdf ok', out);
})();
