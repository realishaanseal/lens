// Records a narrated walkthrough of Lens and writes the timing log the script is built from.
// Usage: node record_demo.js <app-url> <out-dir>      (see demo/README.md for the full setup)
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const URL = process.argv[2] || 'http://localhost:8599', OUT = process.argv[3] || 'out';
const W = 1600, H = 900, WPS = 2.5;   // narration pace: words per second

const CURSOR = `(() => {
  const add = () => {
    if (document.getElementById('demo-cursor')) return;
    const c = document.createElement('div'); c.id = 'demo-cursor';
    c.innerHTML = '<svg width="26" height="26" viewBox="0 0 26 26"><path d="M3 2l18 9.5-8 1.8-3.6 7.7z" fill="#0B1118" stroke="#fff" stroke-width="1.6" stroke-linejoin="round"/></svg>';
    Object.assign(c.style, {position:'fixed', left:'0', top:'0', zIndex:2147483647, pointerEvents:'none',
      transform:'translate(-100px,-100px)', transition:'transform 0s', filter:'drop-shadow(0 2px 4px rgba(0,0,0,.25))'});
    document.documentElement.appendChild(c);
    addEventListener('mousemove', e => { c.style.transform = 'translate(' + (e.clientX - 3) + 'px,' + (e.clientY - 2) + 'px)'; }, true);
    addEventListener('mousedown', e => {
      const r = document.createElement('div');
      Object.assign(r.style, {position:'fixed', left:(e.clientX - 18) + 'px', top:(e.clientY - 18) + 'px', width:'36px', height:'36px',
        borderRadius:'50%', border:'2px solid #C9761A', zIndex:2147483646, pointerEvents:'none', opacity:'.9',
        transition:'transform .45s cubic-bezier(.16,1,.3,1), opacity .45s'});
      document.documentElement.appendChild(r);
      requestAnimationFrame(() => { r.style.transform = 'scale(1.8)'; r.style.opacity = '0'; });
      setTimeout(() => r.remove(), 600);
    }, true);
  };
  if (document.readyState === 'loading') addEventListener('DOMContentLoaded', add); else add();
})();`;

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: W, height: H }, acceptDownloads: true,
    recordVideo: { dir: OUT, size: { width: W, height: H } } });
  await ctx.addInitScript(CURSOR);
  const page = await ctx.newPage();
  const t0 = Date.now(); const now = () => (Date.now() - t0) / 1000;
  const sleep = ms => page.waitForTimeout(ms);
  let mx = W / 2, my = H / 2;
  const moveTo = async (x, y, steps = 28) => { await page.mouse.move(x, y, { steps }); mx = x; my = y; };
  const moveToEl = async (loc, dx = 0.5, dy = 0.5) => {
    await loc.scrollIntoViewIfNeeded(); const b = await loc.boundingBox();
    await moveTo(b.x + b.width * dx, b.y + b.height * dy); return b;
  };
  const click = async (loc) => { await moveToEl(loc); await sleep(250); await page.mouse.down(); await page.mouse.up(); };
  const scroll = async (px, ms = 1200) => {                // smooth wheel scroll of the main area
    await moveTo(W * 0.62, H * 0.55, 10); const n = Math.max(6, Math.round(ms / 40));
    for (let i = 0; i < n; i++) { await page.mouse.wheel(0, px / n); await sleep(ms / n); }
  };
  const text = async (sel) => (await page.locator(sel).first().textContent().catch(() => '')).trim();

  const scenes = []; const facts = {};
  // Optional: real voice-over lengths (seconds per scene, from voiceover.py --clips-only), so each scene
  // is held for its actual narration plus a breath instead of an estimate.
  const VOICE = process.env.SCENE_SECONDS ? JSON.parse(fs.readFileSync(process.env.SCENE_SECONDS, 'utf8')) : null;
  // Each scene: narration (template, filled from facts at the end) and actions. The scene lasts at least
  // as long as its narration takes to read.
  async function scene(title, onScreen, narration, actions) {
    const start = now(); await actions(); await sleep(150);
    const words = narration.replace(/\{\w+\}/g, 'xx').split(/\s+/).length;
    const i = scenes.length;
    const need = VOICE && VOICE[i] ? VOICE[i] + 1.1 : words / WPS + 0.8; const spent = now() - start;
    if (spent < need) await sleep((need - spent) * 1000);
    scenes.push({ title, onScreen, narration, start, end: now() });
    console.log(`${start.toFixed(1)}s  ${title}`);
  }

  await page.goto(URL); await page.waitForSelector('input[type=password]', { timeout: 60000 });
  await sleep(800);

  await scene('Introduction', 'Sign-in screen with the Lens by Varaxis logo',
    'This is Lens, by Varaxis. When a customer asks ChatGPT, Gemini or Perplexity for the best place near them, Lens tells you whether your business is the one they recommend.',
    async () => { await moveTo(W * 0.5, H * 0.32, 40); await sleep(1500); });

  await scene('Sign in', 'Type the password, press Enter; the loading screen brings the workspace into focus',
    'Sign in, and Lens brings your workspace into focus.',
    async () => {
      const pw = page.locator('input[type=password]'); await click(pw);
      await pw.type('demo-lens', { delay: 90 }); await page.keyboard.press('Enter');
      await page.waitForSelector('.lx-stats', { timeout: 60000 });
    });

  await scene('The headline numbers', 'Dashboard: mention rate, questions tested, top competitor, visits from AI',
    'Here is {client} in {city}. In {month}, AI tools named it in {rate} of answers, {change}. The competitor AI recommends most is {competitor}, and Lens tracks the visits that came from AI assistants too.',
    async () => {
      facts.client = (await text('.lx-id h1')); facts.rate = await page.locator('.lx-stat:nth-child(1) .v').getAttribute('title');
      facts.changeText = await text('.lx-stat:nth-child(1) .f'); facts.competitor = await page.locator('.lx-stat:nth-child(3) .v').getAttribute('title');
      const pills = await page.locator('.lx-pill').allTextContents(); facts.city = (pills[1] || '').split(',')[0]; facts.month = (pills[pills.length - 1] || 'the latest month').split(' ')[0];
      await moveToEl(page.locator('.lx-stat').nth(0)); await sleep(1800);
      await moveToEl(page.locator('.lx-stat').nth(2)); await sleep(1500);
      await moveToEl(page.locator('.lx-stat').nth(3)); await sleep(800);
    });

  await scene('Trend by month', 'Mention-rate chart; switch Overall to By tool',
    'The trend shows how often AI has named you, month by month. Switch to By tool to see how ChatGPT, Gemini and Perplexity each treat you.',
    async () => {
      await moveToEl(page.locator('[data-testid="stVegaLiteChart"]').first(), 0.7, 0.5); await sleep(1600);
      await click(page.locator('[data-testid="stButtonGroup"] button', { hasText: 'By tool' })); await sleep(2200);
    });

  await scene('Suggested fixes', 'Suggested fixes column, high-priority items first',
    'Suggested fixes turn the answers into a to-do list: pages to add, schema to mark up, phone numbers that don\'t match. The most important ones are flagged first.',
    async () => { await moveToEl(page.locator('.lx-fix').first(), 0.3, 0.4); await sleep(1500);
      await moveToEl(page.locator('.lx-fix').nth(1), 0.3, 0.4); });

  await scene('Breakdowns', 'Scroll down: mention rate by AI tool, by language, and who AI recommends instead',
    'Below that, the mention rate by AI tool and by language, and the businesses AI recommends instead of you.',
    async () => { await scroll(620, 1600); await sleep(600);
      await moveToEl(page.locator('.lx-h', { hasText: 'Recommended instead' }), 0.3, 0.5); });

  await scene('Every answer', 'Scroll to the answers; open one to read exactly what the AI said',
    'Every answer is kept and dated, so you can read exactly what each AI said, and who it named.',
    async () => { await scroll(900, 1500); const ex = page.locator('[data-testid="stExpander"] summary');
      const n = await ex.count(); await click(ex.nth(Math.min(1, n - 1))); await sleep(1800); });

  await scene('Run a check', 'Back to top; Run check opens the dialog; start it and watch the status lines',
    'Running this month\'s check takes one click. Lens runs free with a Gemini key, and ChatGPT and Perplexity are optional. While it works, Lens tells you what it is doing, question by question.',
    async () => {
      await page.evaluate(() => document.querySelector('[data-testid="stMain"]')?.scrollTo({ top: 0, behavior: 'smooth' }));
      await sleep(900); await click(page.locator('button', { hasText: 'Run check' }).first());
      await page.waitForSelector('[role="dialog"]'); await sleep(1600);
      await moveToEl(page.locator('[role="dialog"] [data-testid="stButtonGroup"]')); await sleep(1200);
      await click(page.locator('[role="dialog"] button', { hasText: 'Start check' }));
      await page.waitForSelector('[role="dialog"] [data-testid="stProgress"]', { timeout: 20000 });
      await page.waitForSelector('[role="dialog"]', { state: 'detached', timeout: 120000 });
      await page.waitForSelector('.lx-stats', { timeout: 60000 }); await sleep(1200);
    });

  await scene('Website check', 'Website check page: run it; AI readiness score and fixes by area',
    'The Website check is free and needs no AI at all. Lens reads the site the way AI crawlers do. Here it scores {score}, finds that robots.txt blocks ChatGPT\'s crawler, and lists each fix.',
    async () => {
      await click(page.locator('[data-testid="stSidebarNav"] a', { hasText: 'Website check' }));
      await page.waitForSelector('button:has-text("Check website")'); await sleep(1200);
      await click(page.locator('button', { hasText: 'Check website' }));
      await page.waitForSelector('.lx-stats', { timeout: 60000 }); await sleep(900);
      facts.score = await page.locator('.lx-stat:nth-child(1) .v').getAttribute('title');
      await moveToEl(page.locator('.lx-stat').first()); await sleep(1500);
      await scroll(520, 1400); await moveToEl(page.locator('.lx-fix').first(), 0.25, 0.4); await sleep(1500);
    });

  await scene('Clients', 'Clients list; open a client to show the editor sections',
    'On Clients you set up each business: its name, city, services, competitors and question languages. Lens writes the questions for you.',
    async () => {
      await click(page.locator('[data-testid="stSidebarNav"] a', { hasText: 'Clients' }));
      await page.waitForSelector('button:has-text("Edit")'); await sleep(1400);
      await click(page.locator('button', { hasText: 'Edit' }).first()); await sleep(1800);
      await scroll(700, 1800); await sleep(500);
    });

  await scene('Settings', 'Settings: Gemini marked Free; ChatGPT and Perplexity optional',
    'In Settings, connect a free Gemini key from Google AI Studio. No card needed.',
    async () => {
      await click(page.locator('[data-testid="stSidebarNav"] a', { hasText: 'Settings' }));
      await page.waitForSelector('text=Gemini'); await sleep(900);
      await moveToEl(page.locator('.lx-tag', { hasText: 'Free' }).first()); await sleep(1200);
    });

  await scene('Report and close', 'Dashboard; Export PDF downloads the monthly report',
    'The new month is already on the dashboard, and you can export a one-page report to share with the client. Lens, by Varaxis. Know if AI recommends you.',
    async () => {
      await click(page.locator('[data-testid="stSidebarNav"] a', { hasText: 'Dashboard' }));
      await page.waitForSelector('.lx-stats', { timeout: 60000 }); await sleep(1200);
      const dl = page.waitForEvent('download', { timeout: 30000 }).catch(() => null);
      await click(page.locator('button', { hasText: 'Export PDF' })); const d = await dl;
      if (d) await d.saveAs(path.join(OUT, 'report.pdf'));
      await moveTo(W * 0.5, H * 0.45, 40); await sleep(1500);
    });

  await sleep(800);
  const video = page.video(); await ctx.close(); await browser.close();
  const ct = facts.changeText || '';
  facts.change = /([+-]\d+) pts from (\w+)/.test(ct)
    ? ct.replace(/([+-])(\d+) pts from (\w+)/, (_, s, n, m) => `${s === '+' ? 'up' : 'down'} ${n} points from ${m}`)
    : /No change from (\w+)/.test(ct) ? ct.replace(/No change from (\w+)/, 'the same as in $1')
    : 'its first month on Lens';
  fs.writeFileSync(path.join(OUT, 'timeline.json'), JSON.stringify({ video: await video.path(), facts, scenes }, null, 2));
  console.log('done', JSON.stringify(facts));
})();
