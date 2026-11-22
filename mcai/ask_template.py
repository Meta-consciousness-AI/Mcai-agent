"""公开问答页模板。占位符 __API_BASE__ 由 site.py 替换。"""

ASK_TEMPLATE = r"""<main class="ask-page">
<section class="wrap ask-hero">
  <span class="cat">公开问答</span>
  <h1>问元意识学说</h1>
  <p class="lead">输入一个问题，答案来自知识库，附原文出处。无需安装，无需登录。</p>
</section>

<section class="wrap ask-panel">
  <form id="ask-form" class="ask-form">
    <label for="ask-input" class="sr-only">你的问题</label>
    <textarea id="ask-input" rows="3" placeholder="例如：什么是元识？"></textarea>
    <div class="ask-actions">
      <span class="muted">首次查询可能需要 30–90 秒</span>
      <button id="ask-submit" type="submit">提问</button>
    </div>
  </form>

  <div class="ask-examples" id="ask-examples">
    <span class="muted">试试：</span>
    <button type="button" data-q="什么是元识？">什么是元识？</button>
    <button type="button" data-q="元识和元知有什么区别？">元识和元知有什么区别？</button>
    <button type="button" data-q="序生智能体是什么？">序生智能体是什么？</button>
    <button type="button" data-q="山岳、星辰也有元灵吗？">山岳、星辰也有元灵吗？</button>
  </div>

  <p id="ask-status" class="ask-status" role="status"></p>

  <article id="ask-result" class="ask-result" hidden>
    <div id="ask-meta" class="ask-meta"></div>
    <div id="ask-answer" class="ask-answer"></div>
    <div id="ask-next" class="ask-next"></div>
    <div id="ask-citations" class="ask-citations"></div>
    <div class="ask-share">
      <button type="button" id="ask-copy">复制本页链接</button>
    </div>
  </article>

  <p class="muted ask-note">答案来自元意识学说知识库；引用请保留术语名与出处。知识库未涉及的问题，不会编造。</p>
</section>

<section class="wrap ask-faq-static">
  <h2>常见问题</h2>
  <p class="muted">以下答案来自知识库，可直接阅读；要追问，用上面的输入框。</p>
  <div class="faq-mini">__ASK_FAQ__</div>
</section>
</main>

<style>
.ask-page{padding:28px 0 56px;background:radial-gradient(circle at 12% 0,#eef3ff 0,transparent 42%),radial-gradient(circle at 88% 8%,#f4efe6 0,transparent 38%)}
.ask-hero h1{font-size:clamp(30px,5vw,48px);margin:10px 0 8px;letter-spacing:-.02em}
.ask-hero .lead{max-width:720px}
.ask-panel{max-width:860px;margin:22px auto 0;background:#fff;border:1px solid var(--line,#e6e2da);border-radius:20px;padding:22px;box-shadow:0 18px 50px rgba(28,32,44,.08)}
.ask-form textarea{width:100%;box-sizing:border-box;border:1px solid var(--line,#dcd7cd);border-radius:14px;padding:14px 16px;font:inherit;font-size:17px;line-height:1.6;resize:vertical;min-height:92px;background:#fcfbf8;color:var(--ink,#1f2430)}
.ask-form textarea:focus{outline:2px solid #2f5bd766;border-color:#2f5bd7}
.ask-actions{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-top:10px}
.ask-actions button{border:0;border-radius:12px;background:#1f2430;color:#fff;font:inherit;font-weight:600;padding:11px 26px;cursor:pointer}
.ask-actions button:disabled{opacity:.55;cursor:wait}
.ask-examples{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:16px 0 4px}
.ask-examples button{border:1px solid var(--line,#dcd7cd);background:#faf8f3;color:inherit;border-radius:999px;padding:7px 12px;font:inherit;font-size:13px;cursor:pointer}
.ask-examples button:hover{border-color:#2f5bd7;color:#2f5bd7}
.ask-status{min-height:22px;margin:12px 0 0;color:#8a6d3b;font-size:14px}
.ask-result{margin-top:18px;border-top:1px solid var(--line,#e6e2da);padding-top:18px}
.ask-meta{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:10px}
.ask-meta span{font-size:12px;padding:4px 9px;border-radius:999px;background:#eef3ff;color:#2f5bd7}
.ask-answer{font-size:17px;line-height:1.85;color:var(--ink,#1f2430)}
.ask-answer p{margin:0 0 12px}
.ask-next{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0}
.ask-next a{font-size:13px;padding:6px 11px;border:1px solid var(--line,#dcd7cd);border-radius:999px;text-decoration:none;color:inherit}
.ask-next a:hover{border-color:#2f5bd7;color:#2f5bd7}
.ask-citations{margin-top:16px;padding-top:12px;border-top:1px dashed var(--line,#dcd7cd);font-size:13px;color:#5b6270}
.ask-citations h3{font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:#8a8f99;margin:0 0 8px}
.ask-citations ul{margin:0;padding-left:18px}
.ask-citations li{margin:0 0 10px}
.ask-citations blockquote{margin:4px 0 0;padding-left:10px;border-left:2px solid #dcd7cd;color:#6b7280;font-size:12px;line-height:1.6}
.ask-share{margin-top:16px}
.ask-share button{border:1px solid var(--line,#dcd7cd);background:#fff;border-radius:10px;padding:8px 14px;font:inherit;font-size:13px;cursor:pointer}
.ask-note{margin-top:18px;font-size:12px}
.ask-faq-static{max-width:860px;margin:34px auto 0}
.ask-faq-static h2{font-size:24px;margin:0 0 6px}
.faq-mini{display:grid;gap:10px;margin-top:14px}
.faq-mini details{background:#fff;border:1px solid var(--line,#e6e2da);border-radius:12px;padding:12px 14px}
.faq-mini summary{cursor:pointer;font-weight:600;line-height:1.6}
.faq-mini p{margin:10px 0 6px;line-height:1.75;color:#3b4150}
.faq-mini a{font-size:13px;color:#2f5bd7;text-decoration:none}
.faq-mini a:hover{text-decoration:underline}
.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}
@media(max-width:640px){.ask-panel{padding:16px;border-radius:16px;margin-top:14px}.ask-actions{align-items:stretch;flex-direction:column}.ask-actions button{width:100%}}
</style>

<script>
(function () {
  var API = "__API_BASE__";
  var form = document.getElementById("ask-form");
  var input = document.getElementById("ask-input");
  var submit = document.getElementById("ask-submit");
  var statusEl = document.getElementById("ask-status");
  var result = document.getElementById("ask-result");
  var metaEl = document.getElementById("ask-meta");
  var answerEl = document.getElementById("ask-answer");
  var nextEl = document.getElementById("ask-next");
  var citeEl = document.getElementById("ask-citations");
  var copyBtn = document.getElementById("ask-copy");
  var examples = document.getElementById("ask-examples");

  function setStatus(text) { statusEl.textContent = text || ""; }

  function clear(node) { while (node.firstChild) node.removeChild(node.firstChild); }

  function addTextParagraphs(node, text) {
    var parts = String(text || "").split(/\n+/);
    parts.forEach(function (part) {
      var t = part.trim();
      if (!t) return;
      var p = document.createElement("p");
      p.textContent = t;
      node.appendChild(p);
    });
  }

  function render(data) {
    clear(metaEl); clear(answerEl); clear(nextEl); clear(citeEl);

    var labels = { concept: "术语", faq: "问答", relation: "关系", multi: "多概念", none: "未涉及", policy: "说明" };
    if (data.type) {
      var s = document.createElement("span");
      s.textContent = labels[data.type] || data.type;
      metaEl.appendChild(s);
    }
    if (data.confidence) {
      var c = document.createElement("span");
      c.textContent = "置信度 " + data.confidence;
      metaEl.appendChild(c);
    }

    addTextParagraphs(answerEl, data.answer || data.context || "知识库没有返回内容。");

    var next = data.next || data.related || [];
    if (Array.isArray(next)) {
      next.slice(0, 8).forEach(function (item) {
        if (!item) return;
        var href = item.href || "";
        var slug = item.slug || (href ? href.split("/").filter(Boolean).pop() : "");
        if (!slug) return;
        var a = document.createElement("a");
        a.href = "/concepts/" + encodeURIComponent(slug) + ".html";
        a.textContent = item.term || slug;
        nextEl.appendChild(a);
      });
    }

    var cites = data.citations || [];
    if (Array.isArray(cites) && cites.length) {
      var h = document.createElement("h3");
      h.textContent = "出处";
      citeEl.appendChild(h);
      var ul = document.createElement("ul");
      cites.forEach(function (ref) {
        var li = document.createElement("li");
        var title = document.createElement("strong");
        title.textContent = ref.doc || ref.doc_title || "知识库";
        li.appendChild(title);
        if (ref.section) {
          li.appendChild(document.createTextNode(" · " + ref.section));
        }
        if (ref.quote) {
          var q = document.createElement("blockquote");
          q.textContent = ref.quote;
          li.appendChild(q);
        }
        ul.appendChild(li);
      });
      citeEl.appendChild(ul);
    }

    result.hidden = false;
  }

  async function ask(question) {
    var q = String(question || "").trim();
    if (!q) { setStatus("请先输入一个问题。"); input.focus(); return; }
    submit.disabled = true;
    setStatus("正在查询知识库…（首次可能 30–90 秒）");
    result.hidden = true;
    try {
      var controller = new AbortController();
      var timer = setTimeout(function () { controller.abort(); }, 95000);
      var resp = await fetch(API + "/answer", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-MCAI-Client": "ask-page" },
        body: JSON.stringify({ question: q }),
        signal: controller.signal
      });
      clearTimeout(timer);
      if (!resp.ok) throw new Error("HTTP " + resp.status);
      var data = await resp.json();
      if (data.ok === false) throw new Error(data.error || "查询失败");
      render(data);
      setStatus("");
      try {
        var url = new URL(location.href);
        url.searchParams.set("q", q);
        history.replaceState(null, "", url.toString());
      } catch (e) {}
    } catch (err) {
      var msg = err && err.name === "AbortError"
        ? "查询超时，请稍后重试。"
        : "知识库暂时不可用，请稍后重试。";
      setStatus(msg);
    } finally {
      submit.disabled = false;
    }
  }

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    ask(input.value);
  });

  examples.addEventListener("click", function (e) {
    var btn = e.target.closest("button[data-q]");
    if (!btn) return;
    input.value = btn.getAttribute("data-q");
    ask(input.value);
  });

  copyBtn.addEventListener("click", function () {
    var text = location.href;
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function () { setStatus("链接已复制。"); });
    } else {
      var t = document.createElement("textarea");
      t.value = text; document.body.appendChild(t); t.select();
      try { document.execCommand("copy"); setStatus("链接已复制。"); } catch (e) {}
      document.body.removeChild(t);
    }
  });

  var params = new URLSearchParams(location.search);
  var initial = params.get("q");
  if (initial) { input.value = initial; ask(initial); }
})();
</script>"""
