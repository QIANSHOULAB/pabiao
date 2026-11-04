/* 渡表僧 · 界面文字。页面上、Excel 里给人看的字全在这一个文件里：英文一套、中文一套，键一一对应。改字只改这里。
   默认英文，第二语言中文（Song 11-03 22:19）。右上角 EN / 中文 切换，选过就记住（localStorage pabiao.lang），不跟浏览器语言走；
   网址带 ?lang=en|zh 时这一次先听网址（不记）。英文不是翻译，是照英文用户的习惯重写的；中文照 _ops/文案规范.md。
   占位：{x} 换成参数；{n|one|many} 按 n 是不是 1 挑一边（中文用不上）。
   HTML 里 data-t（字）、data-t-html（带标签的字，只用这个文件里写死的）、data-t-ph（placeholder）、data-t-aria（aria-label）指到这里的键。
   tests/bi.js 把两套导成 bench/strings-bi/zh.txt、en.txt，一行一条，顺手中英各跑一遍真流程。 */
(function (root) {
'use strict';

const STR = {
en: {
  htmlLang: 'en', locale: 'en-US', listSep: ', ',
  title: 'Dubiao · PDF to Excel',
  desc: 'Drop in a PDF, get an Excel file back. Scans too. Runs in your browser, on phone or computer, and your file isn’t uploaded.',
  name: 'Dubiao',
  langAria: 'Language', langEN: 'EN', langZH: '中文', settings: 'Settings',

  // 首屏
  heroSub: 'Drop the PDF. Go play. Your tables find enlightenment.',
  heroLead: 'PDF in, Excel out. Scans too.',
  dropT: 'Drop a PDF here',
  dropH: 'Hundreds of pages? Fine. Tables split across pages get stitched back together.',
  dropBtn: 'Choose PDF',
  privacy: 'Your file never leaves your browser. Scans go to Google only if you add a key.',

  // 干活中
  workSay: 'Go look busy somewhere. I’ve got this.',
  opening: 'Opening PDF…',
  metaPages: ' · {n} {n|page|pages}',
  pageOf: 'Page {p} of {n}',
  geminiStart: '{n} scanned {n|page|pages}. Google reads each one twice and compares notes',
  geminiProg: 'Scanned pages: {done} of {n}',
  ocrDownload: 'First scan: downloading the scan reader ({mb} MB, one time only) · {pct}%',
  ocrPage: 'Reading page {no} locally ({i} of {n})',
  picPage: 'Page {no} has an image in it. Checking it for tables',
  writing: 'Writing Excel…',

  // 干完
  errTitle: 'Couldn’t convert this one',
  doneTitle: 'Got {n} {n|table|tables}, {rows} {rows|row|rows}',
  doneFlags: '{n} {n|cell|cells} I’m not sure about, marked {colors}. Excel’s downloaded.',
  doneClean: 'Excel’s downloaded. Nothing flagged.',
  cY: 'yellow', cO: 'orange', cR: 'red',
  noTableTitle: 'Looked everywhere. No tables.',
  noTableText: 'The text went into Excel line by line. Better than nothing.',
  noText: 'This PDF has no text in it at all.',
  scanTitle: 'This one’s a scan',
  noTableOnText: 'No tables on the text pages',
  pageErr: 'Page {no}: {err}',
  hint404: 'Google doesn’t know that model (details below), so {n|page|pages} {x} got read locally. Pick another model under ⚙ at top right and drop the file again for a sharper read.',
  hintGErr: 'Google hit a snag (details below), so {n|page|pages} {x} got read locally.',
  hintLocal: '{n|Page|Pages} {x} {n|is a scan|are scans}, read right here in your browser. Nothing uploaded. Add a key for sharper eyes.',
  hintLeft: 'Couldn’t read {n|page|pages} {x}. Reasons below.',
  keyRetryH: 'Try another key',
  keyRetryP: 'Paste a key that works. Google rereads the scans and a fresh Excel downloads.',
  keyNewH: 'Want a sharper read?',
  keyNewP: 'Paste a Gemini key. Google reads each page twice and compares, then a fresh Excel downloads.',
  keyPh: 'Paste a key (AIza… or AQ.…)',
  getKey: 'Get a key',
  saveAgain: 'Download again',
  another: 'Another PDF',

  // 预览
  pvTitle: 'What came out',
  pvNote: 'First few rows of each table. <i class="hl y">Yellow</i> means not sure, <i class="hl o">orange</i> means letters got turned back into digits, <i class="hl r">red</i> means the reads disagreed. Excel has the same colors; hover a cell for the reason.',
  pvMeta: '{pn|Page|Pages} {x} · {r} {r|row|rows} × {c} {c|column|columns}',
  pvFlags: '{n} to check',
  pvMoreRows: '…{n} more {n|row|rows} in Excel',
  pvMoreTables: '{n} more {n|table|tables} in the Excel file only.',

  // 设置
  key1: 'Key 1', key1Ph: 'Only needed for scans',
  key2: 'Key 2', key2Ph: 'Spare, usually blank',
  keyHint: 'When key 1 runs out for the day, key 2 takes over. Keys stay in this browser. ',
  model: 'Model',
  madeBy: 'Made by Shishou, the abbot',
  labHome: 'More tools', mailAbbot: 'Email the abbot', setDone: 'Done',
  footLab: 'QIANSHOU LAB', footHome: 'More tools',

  // 出错
  notPdf: '“{name}” isn’t a PDF. I only do PDFs.',
  pdfLocked: 'This PDF is password-protected, and I don’t pick locks. Remove the password in another app, then drop it in again.',
  pdfOpen: 'Couldn’t open this PDF: {msg}',
  libPdf: 'The PDF reader didn’t load from cdn.jsdelivr.net. Refresh once your connection is back.',
  libXlsx: 'The Excel writer didn’t load from cdn.jsdelivr.net. Refresh once your connection is back.',
  ocrStart: 'The local reader didn’t start: {msg}',
  ocrStartWhy: 'probably a bad connection, the library didn’t download',
  ocrDl: '{file} didn’t download: HTTP {status}',
  ocrDict: 'Dictionary doesn’t match the model: {c} classes vs {n} characters',
  imgFail: 'Couldn’t render the page image',
  pageName: 'Page {no}',

  // 谷歌那条路（报错原话照搬谷歌的，前面加一句人话）
  http: 'HTTP {status}: {msg}',
  netErr: 'Network error: {msg}',
  netTimeout: 'no reply after {s} s',
  notJson: 'Response wasn’t JSON: ',
  modelEmpty: 'Model returned nothing: {why}',
  modelEmptyWhy: 'empty',
  modelNotJson: 'Model’s reply wasn’t JSON: ',
  modelNoTables: 'Model’s JSON has no tables: ',
  allKeysOut: 'Every key is out of quota for today. Resets {when}',
  minuteWait: 'Hit the per-minute limit. Waiting {s} s',
  keyFatal: 'Key {i} · {raw}',
  keyDayOut: 'Key {i} is out of quota for today · {raw}',
  keyMinute: 'Key {i} hit the per-minute limit · {raw}',
  noSchema: 'Model won’t do structured output, switching to plain JSON · {raw}',
  retryIn: '{name} · {raw} · retrying in {w} s',

  // 拿不准的格子：为什么（Excel 批注、预览里鼠标放上去）
  wDate: 'Looks like a date, but that day doesn’t exist',
  wWeird: 'Looks almost like a number. Kept as text',
  spill: 'Text runs into the next column. The column split may be off',
  crammed: '{n} numbers crammed into one cell. The rows probably didn’t split',
  readDiff: 'Read {n} times, got different answers: {vals}',
  blankVal: '(blank)',
  shapeDiff: 'The reads disagree on the table’s shape, so the whole table is marked',
  unreadable: 'Unreadable characters (□)',
  fixedNum: 'Read as “{v}”, changed to the number “{fixed}”',
  lowConf: 'Read locally, low confidence ({n}/100)',
  missed: 'The rest of this column has numbers. This one’s blank, maybe missed',
  decimals: 'The rest of this column has {m} decimal {m|place|places}. This one has {d}',

  // Excel
  creator: 'Dubiao',
  sheetT: 'Table {n}', sheetFallback: 'Table',
  logSheet: 'Log',
  logSummary: '{p} {p|page|pages}, {n} {n|table|tables} found. {date}',
  logHead: ['Sheet', 'Pages', 'Rows (excl. header)', 'Columns', 'Line above the table', 'Cells to check'],
  logFlagsH: 'Cells to check (colored in the tables too; hover for the reason)',
  logFlagsHead: ['Sheet', 'Cell', 'What I read', 'Why'],
  logScans: 'Scanned pages',
  logNoTable: 'No tables found. Here’s the text, line by line',
  isPic: 'Has an image; {n} {n|table|tables} in it read locally',
  isFail: 'Scan, couldn’t read it: {err}',
  isFailWhy: 'no idea why',
  isGemini: 'Scan, read by Google (twice, compared)',
  isGFail: 'Scan, Google failed ({g}), read locally instead',
  isLocal: 'Scan, read locally (no key)',
},

zh: {
  htmlLang: 'zh-CN', locale: 'zh-CN', listSep: '、',
  title: '渡表僧 · 表丢来，你去玩，贫僧超度',
  desc: 'PDF 丢进来，Excel 自己下载，扫描件也认得。电脑、手机打开就用，文件不上传。',
  name: '渡表僧',
  langAria: '语言', langEN: 'EN', langZH: '中文', settings: '设置',

  heroSub: '表丢来，你去玩，贫僧超度',
  heroLead: 'PDF 丢进来，Excel 自己下载。扫描件也认得。',
  dropT: '把 PDF 丢这儿',
  dropH: '几十上百页也行，表跨页了贫僧给你接上',
  dropBtn: '选 PDF',
  privacy: '文件就在你浏览器里拆，不上传。贴了钥匙，扫描件才借谷歌的眼睛看。',

  workSay: '你可以去摸鱼了，剩下的交给老衲。',
  opening: '打开 PDF…',
  metaPages: ' · {n} 页',
  pageOf: '第 {p} / {n} 页',
  geminiStart: '扫描件 {n} 页，借谷歌的眼睛看，每页认两遍对答案',
  geminiProg: '扫描件 {done} / {n} 页',
  ocrDownload: '第一次认扫描件，先下 {mb} MB 的眼珠子，存进浏览器，下回不用再下 · {pct}%',
  ocrPage: '贫僧本地认字：第 {no} 页（{i} / {n}）',
  picPage: '第 {no} 页贴着张图，贫僧看看里面有没有表',
  writing: '写 Excel…',

  errTitle: '这份没扒成',
  doneTitle: '扒出 {n} 张表，{rows} 行',
  doneFlags: '{n} 格拿不准，表里标了{colors}。Excel 已经下载。干完你核对就好了。',
  doneClean: 'Excel 已经下载。干完你核对就好了。',
  cY: '黄', cO: '橙', cR: '红',
  noTableTitle: '翻遍了，没找到表',
  noTableText: '正文按行放进 Excel 了，凑合看。',
  noText: '这份 PDF 里一个字都没有。',
  scanTitle: '这份是扫描件',
  noTableOnText: '有字的页里没找到表',
  pageErr: '第 {no} 页：{err}',
  hint404: '谷歌说模型名不对（原话在下面），第 {x} 页先本地认了。点右上角 ⚙ 换个模型，再丢一次更准。',
  hintGErr: '谷歌那边出了岔子（原话在下面），第 {x} 页先本地认了。',
  hintLocal: '第 {x} 页是扫描件，贫僧本地认的，没上传。眼神差点，贴把钥匙更准。',
  hintLeft: '第 {x} 页没认成，原因在下面。',
  keyRetryH: '换把钥匙，重认一遍',
  keyRetryP: '换一把能用的钥匙贴进来，贫僧借谷歌的眼睛重认，Excel 再下一次。',
  keyNewH: '贴把钥匙，重认一遍',
  keyNewP: '借谷歌的眼睛重认，每页认两遍对答案，Excel 再下一次。',
  keyPh: '粘贴钥匙（AIza… 或 AQ.…）',
  getKey: '免费领钥匙',
  saveAgain: '再下载',
  another: '换一份',

  pvTitle: '扒出来的样子',
  pvNote: '每张表只放前几行。<i class="hl y">黄格</i>拿不准，<i class="hl o">橙格</i>是字母改回了数字，<i class="hl r">红格</i>几遍认得不一样。Excel 里同样标着，鼠标放上去看原因。',
  pvMeta: '第 {x} 页 · {r} 行 × {c} 列',
  pvFlags: '{n} 格要看',
  pvMoreRows: '…还有 {n} 行，在 Excel 里',
  pvMoreTables: '另外 {n} 张表只在 Excel 里。',

  key1: '钥匙 1', key1Ph: '只有扫描件才用得上',
  key2: '钥匙 2', key2Ph: '备胎，平时空着',
  keyHint: '1 号今天用完了自动换 2 号。钥匙只存在这个浏览器里。',
  model: '模型',
  madeBy: '制作人：千手院方丈释手',
  labHome: '千手院总舵', mailAbbot: '方丈邮箱', setDone: '完成',
  footLab: '千手院 · QIANSHOU LAB', footHome: '千手院总舵',

  notPdf: '「{name}」不是 PDF。贫僧只吃 PDF。',
  pdfLocked: '这份 PDF 上了密码锁，贫僧撬不开。先用别的软件去掉密码再丢进来。',
  pdfOpen: '这份 PDF 打不开：{msg}',
  libPdf: '读 PDF 的库没从网上下载下来（cdn.jsdelivr.net），网络好了刷新再试',
  libXlsx: 'Excel 的库没从网上下载下来（cdn.jsdelivr.net），网络好了刷新再试',
  ocrStart: '本地认字的程序没跑起来：{msg}',
  ocrStartWhy: '多半是网不好，库没下载下来',
  ocrDl: '{file} 没下载下来：HTTP {status}',
  ocrDict: '字典对不上模型：模型 {c} 类，字典 {n} 个字',
  imgFail: '图片没生成出来',
  pageName: '第 {no} 页',

  http: 'HTTP {status}：{msg}',
  netErr: '网络错误：{msg}',
  netTimeout: '等了 {s} 秒没回音',
  notJson: '返回的不是 JSON：',
  modelEmpty: '模型没回内容：{why}',
  modelEmptyWhy: '空的',
  modelNotJson: '模型回的不是 JSON：',
  modelNoTables: '模型回的 JSON 里没有 tables：',
  allKeysOut: '所有钥匙今天的额度都用完了，{when} 刷新',
  minuteWait: '每分钟次数到顶，等 {s} 秒',
  keyFatal: '钥匙{i} · {raw}',
  keyDayOut: '钥匙{i} 今天的额度用完了 · {raw}',
  keyMinute: '钥匙{i} 每分钟次数到顶 · {raw}',
  noSchema: '模型不认结构化输出，改用纯 JSON 提示 · {raw}',
  retryIn: '{name} · {raw} · {w} 秒后重试',

  wDate: '像日期，可没有这一天',
  wWeird: '像数字又不太像，照原样当文字放了',
  spill: '这格的字跨到了隔壁列，分列可能不对',
  crammed: '一格里挤着 {n} 个数，多半是行没切开',
  readDiff: '认了 {n} 遍不一样：{vals}',
  blankVal: '（空）',
  shapeDiff: '几遍认出来的表格形状对不上，整张标黄',
  unreadable: '有看不清的字（□）',
  fixedNum: '认出来是「{v}」，按数字改成了「{fixed}」',
  lowConf: '本地认的，这格没把握（{n} 分）',
  missed: '这列别的行都有数，这格空着，可能漏认了',
  decimals: '这列别的都是 {m} 位小数，这格是 {d} 位',

  creator: '渡表僧',
  sheetT: '表{n}', sheetFallback: '表',
  logSheet: '扒表记录',
  logSummary: '共 {p} 页，扒出 {n} 张表。{date}',
  logHead: ['表', '在第几页', '行（不算表头）', '列', '表上方那行字', '要看一眼的格子'],
  logFlagsH: '要看一眼的格子（表里同样标了颜色，鼠标放上去能看原因）',
  logFlagsHead: ['表', '格子', '扒到的字', '为什么'],
  logScans: '扫描页',
  logNoTable: '没找到表，正文按行放在下面',
  isPic: '这页贴着张图，图里的 {n} 张表是本地认字认的',
  isFail: '扫描件，没认成：{err}',
  isFailWhy: '不知道为啥',
  isGemini: '扫描件，谷歌认的（认两遍对答案）',
  isGFail: '扫描件，谷歌没认成（{g}），改成本地认的',
  isLocal: '扫描件，本地认的（没钥匙）',
},
};

const KEY = 'pabiao.lang';
const LANGS = Object.keys(STR);
let lang = 'en';
try { const v = root.localStorage && root.localStorage.getItem(KEY); if (v && STR[v]) lang = v; } catch (e) { /* 存不了就用英文 */ }
try { const q = root.location && new URLSearchParams(root.location.search).get('lang'); if (q && STR[q]) lang = q; } catch (e) { /* 没网址就算了 */ }

function fmt(s, v) {
  v = v || {};
  return String(s)
    .replace(/\{(\w+)\|([^|}]*)\|([^}]*)\}/g, (_, k, one, many) => (String(v[k]) === '1' ? one : many))
    .replace(/\{(\w+)\}/g, (m, k) => (v[k] != null ? String(v[k]) : m));
}
function raw(k) { const s = STR[lang][k]; return s == null ? STR.en[k] : s; }
function t(k, v) { const s = raw(k); return s == null ? k : (Array.isArray(s) ? s : fmt(s, v)); }
function list(items) {
  if (lang === 'en' && typeof Intl !== 'undefined' && Intl.ListFormat) {
    try { return new Intl.ListFormat('en', { style: 'long', type: 'conjunction' }).format(items); } catch (e) { /* 老浏览器 */ }
  }
  return items.join(STR[lang].listSep);
}
function head(doc) {
  doc.documentElement.lang = t('htmlLang');
  doc.title = t('title');
  const d = doc.querySelector('meta[name="description"]');
  if (d) d.setAttribute('content', t('desc'));
}
function apply(doc) {
  head(doc);
  doc.querySelectorAll('[data-t]').forEach((el) => { el.textContent = t(el.dataset.t); });
  doc.querySelectorAll('[data-t-html]').forEach((el) => { el.innerHTML = t(el.dataset.tHtml); });
  doc.querySelectorAll('[data-t-ph]').forEach((el) => { el.placeholder = t(el.dataset.tPh); });
  doc.querySelectorAll('[data-t-aria]').forEach((el) => { el.setAttribute('aria-label', t(el.dataset.tAria)); });
  doc.querySelectorAll('[data-lang]').forEach((el) => { el.setAttribute('aria-pressed', String(el.dataset.lang === lang)); });
}
function set(l) {
  if (!STR[l]) return false;
  lang = l;
  try { root.localStorage.setItem(KEY, l); } catch (e) { /* 记不住就这次有效 */ }
  if (root.document) apply(root.document);
  return true;
}

const I18N = { STR, LANGS, t, fmt, list, apply, set, get lang() { return lang; }, get locale() { return STR[lang].locale; } };
root.I18N = I18N;
if (typeof module !== 'undefined' && module.exports) module.exports = I18N;
if (root.document) head(root.document);       // 在 <head> 里一加载就把 lang、标题、描述换好，不闪
})(typeof window !== 'undefined' ? window : globalThis);
