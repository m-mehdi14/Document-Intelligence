(function () {
  const chatMessages = document.getElementById("chat-messages");
  const welcome = document.getElementById("welcome");
  const form = document.getElementById("chat-form");
  const queryInput = document.getElementById("query-input");
  const btnSubmit = document.getElementById("btn-submit");
  const btnReindex = document.getElementById("btn-reindex");
  const filterFolder = document.getElementById("filter-folder");
  const filterDoctype = document.getElementById("filter-doctype");

  function hideWelcome() {
    if (welcome) welcome.style.display = "none";
  }

  function addMessage(role, content, sources, usedLlm) {
    hideWelcome();
    const isUser = role === "user";

    const wrap = document.createElement("div");
    wrap.className = "message-in mb-6";
    wrap.setAttribute("role", "article");

    const roleLabel = document.createElement("div");
    roleLabel.className = isUser
      ? "mb-1 text-xs font-semibold uppercase tracking-wider text-sky-400"
      : "mb-1 text-xs font-semibold uppercase tracking-wider text-slate-500";
    roleLabel.textContent = isUser ? "You" : "Document Intelligence";

    const contentDiv = document.createElement("div");
    if (isUser) {
      contentDiv.className = "max-w-[85%] rounded-xl border border-slate-700 bg-slate-800 p-4 text-[15px] leading-relaxed whitespace-pre-wrap break-words";
    } else {
      contentDiv.className = "rounded-xl border border-slate-700 border-l-4 border-l-sky-500 bg-slate-800 p-4 text-[15px] leading-relaxed shadow-lg whitespace-pre-wrap break-words";
      if (usedLlm) {
        const badge = document.createElement("span");
        badge.className = "inline-flex mb-2 rounded px-2 py-1 text-xs font-semibold uppercase tracking-wide bg-sky-500/15 text-sky-400";
        badge.textContent = "AI summary";
        contentDiv.appendChild(badge);
        contentDiv.appendChild(document.createTextNode("\n"));
      }
    }
    contentDiv.appendChild(document.createTextNode(content));

    wrap.appendChild(roleLabel);
    wrap.appendChild(contentDiv);

    if (!isUser && sources && sources.length > 0) {
      const sourcesBlock = document.createElement("div");
      sourcesBlock.className = "mt-4 border-t border-slate-700 pt-4";
      sourcesBlock.innerHTML = "<div class=\"mb-2 text-xs font-semibold uppercase tracking-wider text-slate-500\">Cited sources</div>";
      sources.forEach(function (s) {
        const item = document.createElement("div");
        item.className = "border-b border-slate-700/80 py-2.5 text-sm text-slate-400 last:border-0";
        var meta = [];
        if (s.page_or_sheet) meta.push("Page/Sheet: " + escapeHtml(s.page_or_sheet));
        if (s.folder_tag) meta.push("Folder: " + escapeHtml(s.folder_tag));
        item.innerHTML =
          "<span class=\"font-semibold text-slate-200\">" + escapeHtml(s.source_name || "—") + "</span>" +
          (meta.length ? " <span class=\"ml-1 text-[11px] text-slate-500\">" + meta.join(" · ") + "</span>" : "") +
          (s.source_path ? "<div class=\"font-mono mt-1 break-all text-xs text-slate-500\">" + escapeHtml(s.source_path) + "</div>" : "");
        sourcesBlock.appendChild(item);
      });
      wrap.appendChild(sourcesBlock);
    }

    chatMessages.appendChild(wrap);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return wrap;
  }

  function escapeHtml(s) {
    if (s == null) return "";
    const div = document.createElement("div");
    div.textContent = s;
    return div.innerHTML;
  }

  function setLoading(on) {
    btnSubmit.disabled = on;
    if (on) {
      const wrap = document.createElement("div");
      wrap.className = "mb-6";
      wrap.id = "loading-msg";
      wrap.innerHTML =
        "<div class=\"flex items-center gap-2 p-4 text-sm text-slate-400\">" +
        "<span class=\"flex gap-1\">" +
        "<span class=\"h-1.5 w-1.5 rounded-full bg-sky-500 animate-bounce\"></span>" +
        "<span class=\"h-1.5 w-1.5 rounded-full bg-sky-500 animate-bounce bounce-delay-1\"></span>" +
        "<span class=\"h-1.5 w-1.5 rounded-full bg-sky-500 animate-bounce bounce-delay-2\"></span>" +
        "</span> Searching documents<span class=\"loading-dots\"></span></div>";
      hideWelcome();
      chatMessages.appendChild(wrap);
      chatMessages.scrollTop = chatMessages.scrollHeight;
    } else {
      const el = document.getElementById("loading-msg");
      if (el) el.remove();
    }
  }

  function showError(msg) {
    setLoading(false);
    addMessage("assistant", "Error: " + msg, [], false);
    const wrap = chatMessages.querySelector(".message-in:last-child");
    if (wrap && wrap.children.length >= 2) {
      const contentDiv = wrap.children[1];
      contentDiv.classList.remove("border-l-sky-500");
      contentDiv.classList.add("border-l-red-500", "bg-red-500/10", "text-red-400");
    }
  }

  async function loadFilters() {
    try {
      const r = await fetch("/api/filters");
      const data = await r.json();
      if (data.folders && data.folders.length) {
        filterFolder.innerHTML = "<option value=\"\">All folders</option>";
        data.folders.forEach(function (f) {
          filterFolder.innerHTML += "<option value=\"" + escapeHtml(f) + "\">" + escapeHtml(f) + "</option>";
        });
      }
      if (data.doc_types && data.doc_types.length) {
        filterDoctype.innerHTML = "<option value=\"\">All types</option>";
        data.doc_types.forEach(function (t) {
          filterDoctype.innerHTML += "<option value=\"" + escapeHtml(t) + "\">" + escapeHtml(t) + "</option>";
        });
      }
    } catch (e) {
      console.warn("Could not load filters", e);
    }
  }

  function submitQuery(query) {
    if (!query || !query.trim()) return;
    queryInput.value = "";
    queryInput.style.height = "auto";
    addMessage("user", query, null, false);
    setLoading(true);
    var folder = filterFolder.value || null;
    var docType = filterDoctype.value || null;
    fetch("/api/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: query, folder: folder, doc_type: docType }),
    })
      .then(function (res) {
        if (!res.ok) return res.json().then(function (err) { throw new Error(err.detail || res.statusText); });
        return res.json();
      })
      .then(function (data) {
        setLoading(false);
        addMessage("assistant", data.answer, data.sources || [], data.used_llm);
      })
      .catch(function (err) {
        showError(err.message || "Request failed");
      });
  }

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    var query = (queryInput.value || "").trim();
    if (!query) return;
    submitQuery(query);
  });

  document.querySelectorAll(".chip").forEach(function (chip) {
    chip.addEventListener("click", function () {
      var q = chip.getAttribute("data-query");
      if (q) submitQuery(q);
    });
  });

  btnReindex.addEventListener("click", function () {
    btnReindex.disabled = true;
    var origHtml = btnReindex.innerHTML;
    btnReindex.innerHTML = "<span class=\"opacity-80\">↻</span> Indexing…";
    fetch("/api/index", { method: "POST" })
      .then(function (res) { return res.json(); })
      .then(function (data) {
        btnReindex.innerHTML = "<span class=\"opacity-80\">↻</span> Indexed (" + data.chunks_indexed + ")";
        setTimeout(function () {
          btnReindex.innerHTML = origHtml;
          btnReindex.disabled = false;
        }, 2500);
      })
      .catch(function () {
        btnReindex.innerHTML = origHtml;
        btnReindex.disabled = false;
        alert("Re-index failed. Check console.");
      });
  });

  queryInput.addEventListener("input", function () {
    this.style.height = "auto";
    this.style.height = Math.min(this.scrollHeight, 144) + "px";
  });

  queryInput.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      form.requestSubmit();
    }
  });

  loadFilters();
})();
