// 渡表僧 · 中英两套自检（0.2.6 起）。
// 1. 把 strings.js 两套字导成 bench/strings-bi/zh.txt、en.txt（一行一条：键 Tab 字，两份键的顺序一样）。
// 2. 中文、英文各跑一遍真流程（电脑 1280、手机 390）：空状态 → 有字的 PDF 出表 → 扫描件本地认 → 不是 PDF → 设置；
//    结果页上切一次语言，「再下载」的 Excel 表名跟着换。英文是默认语言；中文是点右上角「中文」再刷新，看记没记住。
// 3. 每一屏查：控制台零报错、按钮没被撑破 / 没挤成两行、字没截断、手机 390 没有横向滚动。截图放 bench/shots-bi/。
// 用法：node tests/bi.js    要 playwright（npm i playwright 或全局装的），页面从 cdn.jsdelivr.net 拉 pdf.js、ExcelJS、onnxruntime，要联网。
// 退出码 0 = 全过；结果另写 tests/out/bi-report.json。
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path'), zlib = require('zlib');

const ROOT = path.join(__dirname, '..');
const STRS = path.join(ROOT, 'bench', 'strings-bi'), SHOTS = path.join(ROOT, 'bench', 'shots-bi'), OUT = path.join(ROOT, 'tests', 'out');
const I = require(path.join(ROOT, 'strings.js'));
const VERSION = (fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8').match(/const VERSION = '([\d.]+)'/) || [])[1];
const S = I.STR;
[STRS, SHOTS, OUT].forEach((d) => fs.mkdirSync(d, { recursive: true }));

// ---------------------------------------------------------------- 1. 导出两套字
const SKIP = new Set(['htmlLang', 'locale', 'listSep']);       // 给程序用的，不是给人看的
const clean = (v) => String(v).replace(/<[^>]+>/g, '').replace(/\n/g, ' ⏎ ');
for (const lang of ['zh', 'en']) {
  const lines = [`# 渡表僧 v${VERSION} ${lang === 'zh' ? '中文' : '英文'}界面文字（从 strings.js 导出）。一行一条：键<Tab>字。{x} 是填进去的数，{n|单数|复数} 按 n 挑一个。`];
  for (const [k, v] of Object.entries(S[lang])) {
    if (SKIP.has(k)) continue;
    if (Array.isArray(v)) v.forEach((x, i) => lines.push(`${k}.${i}\t${clean(x)}`));
    else lines.push(`${k}\t${clean(v)}`);
  }
  fs.writeFileSync(path.join(STRS, `${lang}.txt`), lines.join('\n') + '\n');
}

// ---------------------------------------------------------------- 本机服务（只发静态文件）
const TYPES = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.txt': 'text/plain; charset=utf-8', '.onnx': 'application/octet-stream', '.pdf': 'application/pdf', '.json': 'application/json' };
function serve() {
  const srv = http.createServer((req, res) => {
    const u = decodeURIComponent(new URL(req.url, 'http://x').pathname);
    const f = path.join(ROOT, u === '/' ? 'index.html' : u);
    if (!f.startsWith(ROOT) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404); res.end(); return; }
    res.writeHead(200, { 'Content-Type': TYPES[path.extname(f)] || 'application/octet-stream', 'Cache-Control': 'no-store' });
    fs.createReadStream(f).pipe(res);
  });
  return new Promise((ok) => srv.listen(0, '127.0.0.1', () => ok(srv)));
}

// ---------------------------------------------------------------- xlsx：只看表名和作者（不另装库，自己拆 zip）
function zipText(buf, name) {
  let e = buf.length - 22;
  while (e >= 0 && buf.readUInt32LE(e) !== 0x06054b50) e--;
  let off = buf.readUInt32LE(e + 16);
  for (let i = 0, n = buf.readUInt16LE(e + 10); i < n; i++) {
    const method = buf.readUInt16LE(off + 10), size = buf.readUInt32LE(off + 20), nl = buf.readUInt16LE(off + 28), xl = buf.readUInt16LE(off + 30), cl = buf.readUInt16LE(off + 32), lo = buf.readUInt32LE(off + 42);
    if (buf.toString('utf8', off + 46, off + 46 + nl) === name) {
      const start = lo + 30 + buf.readUInt16LE(lo + 26) + buf.readUInt16LE(lo + 28);
      const data = buf.subarray(start, start + size);
      return (method === 8 ? zlib.inflateRawSync(data) : data).toString('utf8');
    }
    off += 46 + nl + xl + cl;
  }
  return '';
}
function xlsxInfo(file) {
  const b = fs.readFileSync(file);
  const sheets = [...zipText(b, 'xl/workbook.xml').matchAll(/<sheet [^>]*name="([^"]+)"/g)].map((m) => m[1]);
  const creator = (zipText(b, 'docProps/core.xml').match(/<dc:creator>([^<]*)</) || [])[1] || '';
  return { sheets, creator };
}

// ---------------------------------------------------------------- 每一屏的检查
async function audit(page) {
  return page.evaluate(() => {
    const bad = [];
    const vw = document.documentElement.clientWidth;
    if (document.documentElement.scrollWidth > vw + 1) bad.push(`横向滚动：页面 ${document.documentElement.scrollWidth} 宽，屏幕 ${vw}`);
    const shown = (el) => el.getClientRects().length > 0 && getComputedStyle(el).visibility !== 'hidden';
    const lines = (el) => {
      const r = document.createRange(); r.selectNodeContents(el);
      const tops = new Set([...r.getClientRects()].filter((q) => q.width > 0).map((q) => Math.round(q.top)));
      return tops.size;
    };
    const name = (el) => `${el.tagName.toLowerCase()}${el.id ? '#' + el.id : ''}${el.className && typeof el.className === 'string' ? '.' + el.className.trim().split(/\s+/).join('.') : ''}「${el.textContent.trim().slice(0, 40)}」`;
    // 按钮：字不出框、不折行、不出屏
    for (const el of document.querySelectorAll('.btn, .lang button, .icon-btn, #set-ok')) {
      if (!shown(el)) continue;
      const r = el.getBoundingClientRect();
      if (el.scrollWidth > el.clientWidth + 1) bad.push(`按钮撑破：${name(el)} 字宽 ${el.scrollWidth} > 框 ${el.clientWidth}`);
      if (el.textContent.trim() && lines(el) > 1) bad.push(`按钮折成 ${lines(el)} 行：${name(el)}`);
      if (r.right > vw + 1 || r.left < -1) bad.push(`按钮出屏：${name(el)} ${Math.round(r.left)}–${Math.round(r.right)} / ${vw}`);
    }
    // 字：不截断（框比字小又藏了溢出）、不出屏。文件名本来就是省略号收尾，不算
    for (const el of document.querySelectorAll('h1, h2, h3, p, label, .t, .h, .by, .hint, footer, .brand, .tt b, .tt span, .more, .err')) {
      if (!shown(el) || el.matches('.file .n')) continue;
      const r = el.getBoundingClientRect(), cs = getComputedStyle(el);
      if (cs.overflowX !== 'visible' && el.scrollWidth > el.clientWidth + 1) bad.push(`字被截：${name(el)}`);
      if (r.right > vw + 1 && !el.closest('.scroll')) bad.push(`字出屏：${name(el)} 右边 ${Math.round(r.right)} / ${vw}`);
    }
    // 输入框里的提示字不被截
    const cv = document.createElement('canvas').getContext('2d');
    for (const el of document.querySelectorAll('input.field')) {
      if (!shown(el) || el.value || !el.placeholder) continue;
      const cs = getComputedStyle(el);
      cv.font = `${cs.fontWeight} ${cs.fontSize} ${cs.fontFamily}`;
      const need = cv.measureText(el.placeholder).width, room = el.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight);
      if (need > room + 1) bad.push(`提示字被截：#${el.id}「${el.placeholder}」要 ${Math.round(need)}，只有 ${Math.round(room)}`);
    }
    // 顶栏：98% 不透明
    const nav = document.querySelector('.nav');
    const a = (getComputedStyle(nav).backgroundColor.match(/rgba?\([^)]*,\s*([\d.]+)\)$/) || [])[1];
    if (a && +a < 0.98) bad.push(`顶栏底色透明度 ${a}（要 ≥ 0.98）`);
    return bad;
  });
}

// ---------------------------------------------------------------- 跑
const report = { version: VERSION, at: new Date().toISOString(), langs: {} };
let problems = 0;
const note = (lang, what, list) => { if (list.length) { problems += list.length; (report.langs[lang].problems ||= []).push(...list.map((x) => `${what}：${x}`)); } };

async function newPage(browser, lang, mobile, errs) {
  const ctx = await browser.newContext(mobile
    ? { viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true, acceptDownloads: true }
    : { viewport: { width: 1280, height: 900 }, acceptDownloads: true });
  const page = await ctx.newPage();
  page.on('console', (m) => { if (m.type() === 'error') errs.push(`${mobile ? '390' : '1280'} console：${m.text()}`); });
  page.on('pageerror', (e) => errs.push(`${mobile ? '390' : '1280'} pageerror：${e.message}`));
  await page.goto(`${BASE}/index.html`);
  await page.waitForFunction(() => window.__pabiao && window.__pabiao.ready);
  if (lang === 'zh') {                // 默认英文；点「中文」再刷新，要还是中文
    await page.click('.lang [data-lang="zh"]');
    await page.reload();
    await page.waitForFunction(() => window.__pabiao && window.__pabiao.ready);
  }
  return { ctx, page };
}
async function head(page) {
  return page.evaluate(() => ({ lang: document.documentElement.lang, title: document.title, desc: document.querySelector('meta[name=description]').content,
    pressed: [...document.querySelectorAll('.lang [aria-pressed="true"]')].map((b) => b.dataset.lang), font: getComputedStyle(document.body).fontFamily.split(',')[2] }));
}
async function runFile(page, file, expectDownload = true) {
  const t0 = Date.now();
  let dl = null;
  // 文件按内容交过去：路径里有中文时，有的机器上 setInputFiles(路径) 悄悄什么都不做
  const payload = { name: path.basename(file), mimeType: file.endsWith('.pdf') ? 'application/pdf' : 'text/plain', buffer: fs.readFileSync(file) };
  if (expectDownload) {
    const [d] = await Promise.all([page.waitForEvent('download', { timeout: 600000 }), page.setInputFiles('#pick', payload)]);
    dl = d;
  } else await page.setInputFiles('#pick', payload);
  await page.waitForFunction(() => window.__pabiao.phase === 'done' && window.__pabiao.result, null, { timeout: 600000 });
  const res = await page.evaluate(() => window.__pabiao.result);
  res.seconds = +((Date.now() - t0) / 1000).toFixed(1);
  if (dl) { res.xlsx = path.join(OUT, `bi-${path.basename(file, '.pdf')}-${res.lang}.xlsx`); await dl.saveAs(res.xlsx); Object.assign(res, xlsxInfo(res.xlsx)); }
  return res;
}
const shot = (page, lang, w, state, full = true) => page.screenshot({ path: path.join(SHOTS, `${lang}-${w}-${state}.png`), fullPage: full });

let BASE = '';
(async () => {
  const srv = await serve();
  BASE = `http://127.0.0.1:${srv.address().port}`;
  const browser = await chromium.launch();
  const bad = path.join(OUT, 'bi-不是PDF.txt');
  fs.writeFileSync(bad, 'hello');
  for (const lang of ['en', 'zh']) {
    const L = S[lang], other = lang === 'en' ? 'zh' : 'en';
    const R = report.langs[lang] = { flows: {} };
    const errs = [];
    for (const mobile of [false, true]) {
      const w = mobile ? 390 : 1280;
      const { ctx, page } = await newPage(browser, lang, mobile, errs);
      // 空状态
      const h = await head(page);
      R.head = h;
      const want = { lang: L.htmlLang, title: L.title, desc: L.desc };
      for (const k of Object.keys(want)) if (h[k] !== want[k]) note(lang, `${w} <head>`, [`${k} 是「${h[k]}」，应为「${want[k]}」`]);
      if (h.pressed.join() !== lang) note(lang, `${w} 切换`, [`按下的是 ${h.pressed.join()}`]);
      if (await page.textContent('h1') !== L.name) note(lang, `${w} 大标题`, [await page.textContent('h1')]);
      note(lang, `${w} 空状态`, await audit(page));
      await shot(page, lang, w, 'empty', false);

      // 有字的 PDF：出表
      const r1 = await runFile(page, path.join(ROOT, 'samples', 's4_合并表头.pdf'));
      R.flows[`${w} 有字 s4`] = { title: r1.title, tables: r1.tables, rows: r1.rows, sheets: r1.sheets, creator: r1.creator, seconds: r1.seconds };
      if (r1.error || !r1.tables) note(lang, `${w} s4`, [`没出表：${r1.error}`]);
      if (r1.sheets[r1.sheets.length - 1] !== L.logSheet || !r1.sheets[0].startsWith(I.fmt(L.sheetT, { n: 1 }))) note(lang, `${w} s4 Excel 表名`, [r1.sheets.join(' / ')]);
      if (r1.creator !== L.creator) note(lang, `${w} s4 Excel 作者`, [r1.creator]);
      note(lang, `${w} 结果`, await audit(page));
      await shot(page, lang, w, 'result');

      // 结果页上换语言：字跟着换，「再下载」的 Excel 也换
      if (!mobile) {
        await page.click(`.lang [data-lang="${other}"]`);
        await page.waitForFunction((t) => document.querySelector('#d-title').textContent.startsWith(t), S[other].doneTitle.split('{')[0]);
        const [d] = await Promise.all([page.waitForEvent('download'), page.click('#d-save')]);
        const f = path.join(OUT, `bi-s4-switched-${other}.xlsx`);
        await d.saveAs(f);
        const x = xlsxInfo(f), t = await page.textContent('#d-title'), hh = await head(page);
        R.flows['1280 结果页换语言'] = { to: other, title: t, sheets: x.sheets, htmlLang: hh.lang };
        if (x.sheets[x.sheets.length - 1] !== S[other].logSheet) note(lang, '换语言后 Excel', [x.sheets.join(' / ')]);
        if (hh.lang !== S[other].htmlLang) note(lang, '换语言后 <html lang>', [hh.lang]);
        note(lang, '换语言后的结果页', await audit(page));
        await page.click(`.lang [data-lang="${lang}"]`);
        await page.waitForFunction((t) => document.querySelector('#d-title').textContent.startsWith(t), L.doneTitle.split('{')[0]);
      }

      // 扫描件，没钥匙：本地认，钥匙框出来
      const r2 = await runFile(page, path.join(ROOT, 'samples', 's6_扫描版.pdf'));
      R.flows[`${w} 扫描 s6`] = { title: r2.title, line2: r2.line2, flags: r2.flags, via: r2.via, sheets: r2.sheets, seconds: r2.seconds };
      if (!r2.tables || !r2.via.every((v) => v[1] === 'local')) note(lang, `${w} s6`, [`没本地认出表：${JSON.stringify(r2.via)} ${r2.error}`]);
      if (!(await page.isVisible('#d-key'))) note(lang, `${w} s6`, ['钥匙框没出来']);
      if (!r2.line2.includes(I.fmt(L.hintLocal, { x: '1', n: 1 }).slice(-8))) note(lang, `${w} s6 提示`, [r2.line2]);
      note(lang, `${w} 扫描结果`, await audit(page));
      await shot(page, lang, w, 'scan');

      // 不是 PDF
      const r3 = await runFile(page, bad, false);
      const errText = await page.textContent('#d-err');
      R.flows[`${w} 不是 PDF`] = { title: r3.title, err: errText };
      if (errText !== I.fmt(L.notPdf, { name: path.basename(bad) })) note(lang, `${w} 不是 PDF`, [errText]);
      note(lang, `${w} 出错`, await audit(page));
      await shot(page, lang, w, 'error', false);

      // 设置
      await page.click('#gear');
      await page.waitForSelector('#dlg-set[open]');
      note(lang, `${w} 设置`, await audit(page));
      await shot(page, lang, w, 'settings', false);
      await page.click('#set-ok');
      await ctx.close();
    }
    note(lang, '控制台', errs);
    R.consoleErrors = errs.length;
  }
  await browser.close();
  srv.close();
  report.problems = problems;
  fs.writeFileSync(path.join(OUT, 'bi-report.json'), JSON.stringify(report, null, 1));
  console.log(JSON.stringify(report, null, 1));
  console.log(problems ? `有 ${problems} 处毛病` : '中英两套全过');
  process.exit(problems ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(2); });
