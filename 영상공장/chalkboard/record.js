const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 1280, height: 720 }, recordVideo: { dir: 'rec', size: { width: 1280, height: 720 } } });
  const t0 = Date.now();
  const p = await ctx.newPage();
  await p.goto('file://' + process.cwd() + '/pythagoras-chalkboard.html');
  await p.waitForTimeout(2500);
  await p.addStyleTag({ content: `.wrap{padding:0!important;max-width:none!important;gap:0!important}.wrap>*:not(.frame){display:none!important}.frame{padding:0!important;border-radius:0!important;box-shadow:none!important}.ledge,.start{display:none!important}` });
  const meta = await p.evaluate(() => {
    fit(); voiceOn = false; jump(0);
    return { total: TOTAL, steps: STEPS.map(s => ({ start: s.start, dur: s.dur, say: s.say, scene: SCENES[s.scene].title })) };
  });
  await p.waitForTimeout(500);
  const t1 = Date.now();
  await p.evaluate(() => setPlaying(true));
  await p.waitForFunction(() => ended, null, { timeout: 0, polling: 500 });
  await p.waitForTimeout(2500);
  const vid = await p.video().path();
  await ctx.close(); await b.close();
  meta.offset = (t1 - t0) / 1000; meta.video = vid;
  fs.writeFileSync('meta.json', JSON.stringify(meta, null, 1));
  console.log('done', meta.total, meta.offset, vid);
})();
