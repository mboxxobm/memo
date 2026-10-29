import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const { marked } = await import(process.env.BLOG_MARKED_MODULE || 'marked');

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const stem = 'ブログの書き方テンプレ_田中栄二風';
const markdown = await fs.readFile(path.join(root, `${stem}.md`), 'utf8');
const promptSection = markdown.split('## 6. コピペ用の依頼文')[1]?.split('## 7.')[0];
const prompt = promptSection?.match(/```text\n([\s\S]*?)\n```/)?.[1];
if (!prompt) throw new Error('The reusable prompt is missing.');
const promptRules = prompt.split('【元の文章・メモ】')[0].trim();
const documentBody = marked.parse(markdown.replace(/^# .*\n/, ''), { gfm: true });
const payload = JSON.stringify({ markdown, promptRules, stem }).replace(/</g, '\\u003c');

const html = `<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light">
<meta name="description" content="田中栄二さんの提供文をもとにした、回想・脱線・自分へのツッコミの分析とブログ執筆テンプレート。">
<title>ブログの書き方テンプレ｜田中栄二風</title>
<style>
:root{--paper:#f7f5ef;--card:#fffefb;--ink:#25362f;--muted:#5e6b64;--line:#d8ddd4;--accent:#955137;--wash:#edf0e7;--serif:'Hiragino Mincho ProN','Yu Mincho',serif;--sans:-apple-system,BlinkMacSystemFont,'Hiragino Kaku Gothic ProN','Yu Gothic',Meiryo,sans-serif}
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:28px}body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.9 var(--sans);overflow-wrap:anywhere}a{color:var(--accent);text-underline-offset:4px}button,input,select,textarea{font:inherit}button,a,input,select,textarea{ -webkit-tap-highlight-color:transparent}button{cursor:pointer}button:disabled{opacity:.45;cursor:default}button:focus-visible,a:focus-visible,input:focus-visible,select:focus-visible,textarea:focus-visible{outline:3px solid var(--accent);outline-offset:4px}button,input,select,textarea{border-radius:6px}.skip{position:absolute;left:20px;top:-80px;z-index:9;padding:10px 18px;background:var(--card)}.skip:focus{top:12px}.layout{max-width:1400px;margin:auto;display:grid;grid-template-columns:254px minmax(0,1fr);min-height:100vh}.rail{border-right:1px solid var(--line);padding:44px 28px}.rail-inner{position:sticky;top:32px;max-height:calc(100vh - 64px);overflow-y:auto}.brand{font-size:12px;font-weight:750;letter-spacing:.16em}.brand span{color:var(--accent)}.edition{font-size:11px;letter-spacing:.12em;color:var(--muted);margin:5px 0 32px}.rail-label{font-size:10px;letter-spacing:.18em;color:var(--muted);margin:32px 0 12px}.rail nav a{display:block;color:var(--muted);font-size:12px;text-decoration:none;padding:7px 0;line-height:1.7}.rail nav a:hover{color:var(--accent)}.rail .writer-link{color:var(--ink);font-weight:700}.rail-foot{font-size:11px;color:var(--muted);margin-top:36px;padding-top:20px;border-top:1px solid var(--line)}.main{min-width:0;padding:48px 64px 64px}.eyebrow{font-size:11px;letter-spacing:.18em;color:var(--accent);font-weight:700;margin:0 0 20px}.hero h1{font-family:var(--serif);font-size:clamp(32px,4vw,47px);font-weight:650;line-height:1.55;letter-spacing:.025em;margin:0 0 20px}.hero .lead{font-size:15px;color:var(--muted);line-height:2;max-width:42em;margin:0 0 24px}.meta{display:flex;gap:8px;flex-wrap:wrap;margin:24px 0 32px}.tag{border:1px solid var(--line);padding:3px 10px;font-size:10px;letter-spacing:.04em;border-radius:30px}.rhythm{display:flex;gap:10px;flex-wrap:wrap;align-items:center;border-block:1px solid var(--line);padding:18px 0;font-size:12px;margin-bottom:38px}.rhythm b{font-weight:650}.rhythm span{color:var(--accent)}.panel{border:1px solid var(--line);background:var(--card);border-radius:12px;padding:28px;margin-bottom:42px;box-shadow:0 6px 25px #25362f04}.panel-title{display:flex;align-items:center;justify-content:space-between;gap:16px;margin-bottom:10px}.panel h2{font-size:23px;margin:0;letter-spacing:.02em}.index{color:var(--accent);font-size:11px;letter-spacing:.12em}.help{color:var(--muted);font-size:12px;line-height:1.9;margin:0 0 22px}.fields{display:grid;grid-template-columns:1fr 1fr;gap:16px 18px}.field-wide{grid-column:1/-1}label{display:block;font-size:12px;font-weight:650;margin-bottom:7px}.optional{color:var(--muted);font-weight:400;font-size:10px;margin-left:6px}input,select,textarea{color:var(--ink);border:1px solid var(--line);background:#fff;width:100%;padding:10px 12px;min-height:43px;line-height:1.7}textarea{resize:vertical;min-height:170px;font-size:13px}input::placeholder,textarea::placeholder{color:#78837b;opacity:1}select{appearance:auto}.actions{display:flex;align-items:center;flex-wrap:wrap;gap:10px;margin-top:20px}button,.download{display:inline-flex;align-items:center;justify-content:center;gap:7px;padding:10px 16px;border:1px solid var(--line);background:var(--card);color:var(--ink);text-decoration:none;font-size:12px;font-weight:650;min-height:42px}button:hover,.download:hover{border-color:var(--ink)}button.primary{background:var(--ink);border-color:var(--ink);color:#fff}button.primary:hover{background:#3a4e43}button.quiet{padding-inline:10px;border:0;background:transparent;color:var(--accent);text-decoration:underline;text-underline-offset:4px}.status{font-size:12px;margin:12px 0 0;min-height:22px;color:var(--accent)}.result{margin-top:10px;padding-top:22px;border-top:1px solid var(--line)}.result textarea{min-height:330px;background:#f6f7f2;font-size:12px}.result-top{display:flex;align-items:center;justify-content:space-between;gap:10px}.count{font-size:10px;color:var(--muted)}.guide-label{display:flex;justify-content:space-between;align-items:center;gap:20px;margin-bottom:28px;border-bottom:1px solid var(--line);padding-bottom:18px}.guide-label p{margin:0;font-size:11px;letter-spacing:.15em;color:var(--muted)}.guide{font-size:14px;line-height:2.1}.guide>p:first-child{font-size:19px;line-height:1.9;color:var(--ink);margin-top:0}.guide>p:nth-child(2),.guide>p:nth-child(3){font-size:12px;color:var(--muted)}.guide h2{font-family:var(--serif);font-size:25px;line-height:1.65;margin:58px 0 22px;padding-top:16px;border-top:1px solid var(--line)}.guide h3{font-size:16px;line-height:1.9;margin:32px 0 14px}.guide p{margin:0 0 20px}.guide strong{font-weight:700}.guide ul,.guide ol{padding-left:1.5em;margin:18px 0 26px}.guide li{margin:7px 0}.guide li input[type=checkbox]{display:inline-block;width:14px;min-height:14px;margin:0 6px 0 0;accent-color:var(--accent)}.guide blockquote{margin:26px 0;padding:20px 24px;border-left:3px solid var(--accent);background:var(--wash);border-radius:0 6px 6px 0}.guide blockquote p:last-child{margin-bottom:0}.guide pre{background:#eaece4;border:1px solid #d5dace;border-radius:8px;padding:22px;font:12px/2 var(--sans);white-space:pre-wrap;overflow-wrap:anywhere;overflow-x:auto;margin:24px 0}.guide code{font-family:inherit}.table-wrap{overflow-x:auto;margin:24px 0 30px;outline-offset:3px}.guide table{border-collapse:collapse;width:100%;font-size:12px;line-height:1.9;text-align:left;min-width:540px}.guide th{background:#e9ede3;font-weight:700}.guide th,.guide td{padding:12px 14px;vertical-align:top;border-bottom:1px solid var(--line)}.guide td:first-child{font-weight:600;min-width:95px}.endnote{border-top:1px solid var(--line);margin-top:50px;padding-top:20px;display:flex;gap:15px;justify-content:space-between;flex-wrap:wrap;font-size:11px;color:var(--muted)}[hidden]{display:none!important}noscript p{padding:16px;background:#f8e7d8;border-radius:6px}::selection{background:#d6ddc9}
@media(min-width:1450px){.layout{border-inline:1px solid var(--line)}}
@media(max-width:1100px){.main{padding:40px 36px}.layout{grid-template-columns:220px minmax(0,1fr)}.rail{padding:40px 20px}.panel{padding:24px}}
@media(max-width:760px){.layout{display:block}.rail{border-right:0;border-bottom:1px solid var(--line);padding:17px 22px}.rail-inner{position:static;max-height:none;overflow:visible;display:flex;justify-content:space-between;align-items:center;gap:15px}.edition,.rail-label,.rail nav,.rail-foot{display:none}.rail .brand{font-size:11px}.main{padding:30px 22px 40px}.hero h1{font-size:34px}.eyebrow{font-size:10px;margin-bottom:16px}.hero .lead{font-size:13px}.rhythm{font-size:11px;gap:8px;margin-bottom:28px}.panel{padding:20px;margin-bottom:30px}.panel h2{font-size:21px}.fields{grid-template-columns:1fr}.field-wide{grid-column:auto}.guide h2{font-size:22px;margin-top:42px}.guide{font-size:13px}.guide-label{align-items:flex-start}.guide-label .download{font-size:11px;padding:8px 10px;white-space:nowrap}.guide pre{padding:16px;font-size:11px}.meta{margin:22px 0}.actions button{flex-grow:1}.guide blockquote{padding:18px}.table-wrap{margin-right:-2px}.guide table{min-width:510px}.hero .lead br{display:none}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
@media print{body{background:white;font-size:10pt;color:#111}.layout{display:block;max-width:none}.rail,.skip,.actions,.guide-label,.download,.writer-form,.help,.status,.result,.rhythm,.index{display:none!important}.main{padding:0}.hero h1{font-size:27pt}.hero .lead{font-size:10pt}.panel{display:none}.hero{margin-bottom:25px}.meta{margin:14px 0}.tag{font-size:8pt}.guide{font-size:10pt;line-height:1.8}.guide h2{font-size:17pt;margin-top:24px;break-after:avoid}.guide h3{font-size:12pt;break-after:avoid}.guide pre{font-size:9pt;white-space:pre-wrap;box-shadow:none}.guide table{font-size:9pt;min-width:0}.table-wrap{overflow:visible}.guide tr{break-inside:avoid}.guide blockquote{break-inside:avoid}.endnote{font-size:8pt}a{color:inherit}}
</style>
</head>
<body>
<a class="skip" href="#writer">依頼文をつくる欄へ</a>
<div class="layout">
<aside class="rail" aria-label="ページ案内">
<div class="rail-inner">
<div><div class="brand">ことばの型 <span>／</span> NOTE</div><p class="edition">WRITING TEMPLATE · 01</p></div>
<nav aria-label="目次"><a class="writer-link" href="#writer">まずは、自分の文章で使う ↗</a><p class="rail-label">このガイドの内容</p><div id="toc"><a href="#analysis">解析とテンプレート</a></div></nav>
<p class="rail-foot">田中栄二さんの提供文から<br>回想・脱線・自分へのツッコミ<br><br>保存日 2026.10.29</p>
</div>
</aside>
<main class="main" id="main">
<header class="hero">
<p class="eyebrow">BLOG WRITING / 田中栄二風</p>
<h1>話を少し、<br>遠回りさせる。</h1>
<p class="lead">ブログの書き方テンプレート。<br>回想と脱線、そして自分へのツッコミ。<br>元の文章を、誰かに話しかけるような一篇に。</p>
<div class="meta"><span class="tag">原文からの解析</span><span class="tag">繰り返し使える依頼文</span><span class="tag">MD / HTML</span></div>
<div class="rhythm" aria-label="文章の基本的な流れ"><b>書く理由</b><span>→</span><b>回想</b><span>→</span><b>脱線とツッコミ</b><span>→</span><b>元の場面へ</b></div>
</header>
<section class="panel" id="writer" aria-labelledby="writer-title">
<div class="panel-title"><h2 id="writer-title">自分の文章で使う</h2><span class="index">TRY IT</span></div>
<p class="help">文章やメモを入れると、この型での書き換えを頼む依頼文を作れます。<br>コピーしてCodexに送ってください。入力内容はこのページ内で処理します。</p>
<noscript><p>入力から依頼文を作るにはJavaScriptを有効にしてください。下の「6. コピペ用の依頼文」はそのまま使えます。</p></noscript>
<form id="writer-form" class="writer-form">
<div class="fields">
<div class="field-wide"><label for="material">元の文章・出来事のメモ</label><textarea id="material" name="material" required placeholder="ここに文章や箇条書きを貼り付けてください。&#10;例：久しぶりに友人と会った日のこと、初めて挑戦したこと、仕事のちょっとした出来事。"></textarea></div>
<div><label for="length">希望の長さ</label><select id="length"><option value="800〜1,200字程度">標準 · 800〜1,200字</option><option value="400〜600字程度">短め · 400〜600字</option><option value="1,500〜2,000字程度。素材の量を優先する">長め · 1,500〜2,000字</option><option value="元の文章の長さに合わせる">元の文章に合わせる</option></select></div>
<div><label for="humor">笑いの強さ</label><select id="humor"><option value="標準。小さな自慢と訂正を一組">標準 · 自慢とツッコミを一組</option><option value="控えめ。自分への小さなツッコミを一つ">控えめ · 軽く一言</option><option value="多め。比喩を一つ使って後半で回収する">多め · 比喩をあとで回収</option></select></div>
<div class="field-wide"><label for="keep">残したい言葉・伝えたい気持ち<span class="optional">任意</span></label><input id="keep" placeholder="例：「また会おう」という言葉、うれしかった気持ち"></div>
<div class="field-wide"><label for="fiction">素材の扱い</label><select id="fiction"><option value="事実を変えない。元にない体験・感情・会話を実話として追加しない">事実を保って書き換える</option><option value="架空の話として創作してよい。冒頭に創作例であることを明記する">架空の話として創作する</option></select></div>
</div>
<div class="actions"><button class="primary" type="submit">依頼文をつくる <span aria-hidden="true">↗</span></button><button class="quiet" type="button" id="example">例文を入れる</button></div>
</form>
<p class="status" id="status" role="status" aria-live="polite"></p>
<div class="result" id="result" hidden>
<div class="result-top"><label for="prompt-output">Codexに送る依頼文</label><span class="count" id="count"></span></div>
<textarea id="prompt-output" readonly spellcheck="false"></textarea>
<div class="actions"><button class="primary" type="button" id="copy-prompt">依頼文をコピー</button><button type="button" id="save-prompt">TXTで保存</button></div>
</div>
</section>
<section id="analysis" aria-label="解析と再利用のガイド">
<div class="guide-label"><p>ANALYSIS & REUSABLE GUIDE</p><button class="download" id="download-md" type="button">ガイドをMDで保存 ↓</button></div>
<article class="guide">${documentBody}</article>
</section>
<footer class="endnote"><span>ことばの型 ／ ブログの書き方テンプレ（田中栄二風）</span><span>LOCAL EDITION · 2026.10.29</span></footer>
</main>
</div>
<script type="application/json" id="guide-data">${payload}</script>
<script>
(() => {
  'use strict';
  const data = JSON.parse(document.getElementById('guide-data').textContent);
  const $ = id => document.getElementById(id);
  const toc = $('toc');
  toc.replaceChildren();
  document.querySelectorAll('.guide h2').forEach((heading, i) => {
    heading.id = 'guide-' + (i + 1);
    const link = document.createElement('a');
    link.href = '#' + heading.id;
    link.textContent = heading.textContent;
    toc.append(link);
  });
  document.querySelectorAll('.guide table').forEach(table => {
    const wrapper = document.createElement('div');
    wrapper.className = 'table-wrap';
    wrapper.setAttribute('tabindex', '0');
    wrapper.setAttribute('role', 'region');
    wrapper.setAttribute('aria-label', '左右にスクロールできる比較表');
    table.replaceWith(wrapper);
    wrapper.append(table);
  });
  const notify = message => { $('status').textContent = message; };
  const download = (text, name, type) => {
    const blob = new Blob([text], { type });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = name;
    document.body.append(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  };
  $('writer-form').addEventListener('submit', event => {
    event.preventDefault();
    const material = $('material').value.trim();
    if (!material) { $('material').focus(); notify('元の文章や出来事のメモを入力してください。'); return; }
    const keep = $('keep').value.trim() || '特に指定なし。元の文章にある気持ちと結論を保つ。';
    const output = data.promptRules + '\\n\\n【元の文章・メモ】\\n' + material
      + '\\n\\n【希望字数】' + $('length').value
      + '\\n【笑いの強さ】' + $('humor').value
      + '\\n【残したい言葉・伝えたい気持ち】' + keep
      + '\\n【創作の可否】' + $('fiction').value;
    $('prompt-output').value = output;
    $('count').textContent = Array.from(output).length.toLocaleString('ja-JP') + '文字';
    $('result').hidden = false;
    notify('依頼文ができました。コピーしてCodexに送ってください。');
    $('result').scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth', block: 'nearest' });
  });
  $('writer-form').addEventListener('input', () => {
    if (!$('result').hidden) {
      $('result').hidden = true;
      notify('内容を変更しました。「依頼文をつくる」で更新してください。');
    }
  });
  $('example').addEventListener('click', () => {
    if ($('material').value.trim()) {
      notify('入力した内容を保つため、例文は挿入していません。空欄にしてから使えます。');
      return;
    }
    $('material').value = '先週の日曜日、札幌の喫茶店で高校時代の友人と10年ぶりに会った。私は10分早く着いた。友人は昔と同じアイスコーヒーを注文した。仕事の話をした。帰り際に「また会おう」と言われてうれしかった。';
    $('keep').value = '「また会おう」という言葉、うれしかった気持ち';
    $('result').hidden = true;
    notify('ガイドの架空の素材を入れました。「依頼文をつくる」で試せます。');
    $('material').focus();
  });
  $('copy-prompt').addEventListener('click', async () => {
    try {
      if (!navigator.clipboard?.writeText) throw new Error('Clipboard unavailable');
      await navigator.clipboard.writeText($('prompt-output').value);
      notify('コピーしました。Codexに貼り付けて送信してください。');
    } catch {
      $('prompt-output').focus();
      $('prompt-output').select();
      let copied = false;
      try { copied = document.execCommand('copy'); } catch {}
      notify(copied ? 'コピーしました。Codexに貼り付けて送信してください。' : '依頼文を選択しました。⌘C または Ctrl+C でコピーしてください。');
    }
  });
  $('save-prompt').addEventListener('click', () => download($('prompt-output').value, 'ブログ書き換えの依頼文.txt', 'text/plain;charset=utf-8'));
  $('download-md').addEventListener('click', () => download(data.markdown, data.stem + '.md', 'text/markdown;charset=utf-8'));
})();
</script>
</body>
</html>
`;
await fs.writeFile(path.join(root, `${stem}.html`), html, 'utf8');
console.log(JSON.stringify({ html: path.join(root, `${stem}.html`), bytes: Buffer.byteLength(html), markdownBytes: Buffer.byteLength(markdown) }));
