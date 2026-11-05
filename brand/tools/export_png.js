// Export PNG copies of the SVG masters with headless Chromium (Playwright).
// Usage: node export_png.js   (run from brand/tools; writes ../masters/png/*.png)
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const masters = path.join(__dirname, '..', 'masters'), out = path.join(masters, 'png');
const files = ['lens-horizontal', 'lens-horizontal-reverse', 'lens-stacked', 'lens-mark', 'lens-mark-reverse'];
(async () => {
  fs.mkdirSync(out, { recursive: true });
  const b = await chromium.launch(); const p = await b.newPage();
  for (const name of files) {
    const svg = fs.readFileSync(path.join(masters, name + '.svg'), 'utf8');
    const [, w, h] = svg.match(/viewBox="0 0 ([\d.]+) ([\d.]+)"/).map(Number);
    const scale = 1200 / Math.max(w, h);
    await p.setViewportSize({ width: Math.ceil(w * scale), height: Math.ceil(h * scale) });
    await p.setContent(`<html><body style="margin:0;background:transparent">${svg.replace(/width="[\d.]+" height="[\d.]+"/, 'width="100%" height="100%"')}</body></html>`);
    await p.screenshot({ path: path.join(out, name + '.png'), omitBackground: true });
  }
  await b.close(); console.log(files.length, 'PNGs in', out);
})();
