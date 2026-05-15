(function () {
  const $ = (sel, root = document) => root.querySelector(sel);

  const toastEl = $("#toast");
  let toastTimer;

  function showToast(message, type) {
    toastEl.textContent = message;
    toastEl.className = "toast is-visible " + (type || "success");
    toastEl.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
      toastEl.classList.remove("is-visible");
      toastEl.hidden = true;
    }, 4500);
  }

  function parseErrorDetail(data) {
    if (!data) return "Request failed";
    if (typeof data.detail === "string") return data.detail;
    if (Array.isArray(data.detail)) {
      return data.detail
        .map((d) => (typeof d === "object" && d.msg ? d.msg : JSON.stringify(d)))
        .join("; ");
    }
    return JSON.stringify(data);
  }

  /* Tabs */
  const tabs = document.querySelectorAll(".tab");
  const panels = document.querySelectorAll(".panel");

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      const id = tab.dataset.tab;
      tabs.forEach((t) => {
        const on = t === tab;
        t.classList.toggle("is-active", on);
        t.setAttribute("aria-selected", on ? "true" : "false");
      });
      panels.forEach((p) => {
        const on = p.id === "panel-" + id;
        p.classList.toggle("is-active", on);
        p.hidden = !on;
      });
    });
  });

  /* Upload dropzone label */
  const fileInput = $("#upload-file");
  const fileLabel = $("#file-label");
  const dropzone = $("#dropzone");

  fileInput.addEventListener("change", () => {
    const f = fileInput.files[0];
    fileLabel.textContent = f ? f.name : "No file selected";
  });

  ["dragenter", "dragover"].forEach((ev) => {
    dropzone.addEventListener(ev, (e) => {
      e.preventDefault();
      dropzone.style.borderColor = "var(--accent)";
    });
  });
  ["dragleave", "drop"].forEach((ev) => {
    dropzone.addEventListener(ev, (e) => {
      e.preventDefault();
      dropzone.style.borderColor = "";
    });
  });
  dropzone.addEventListener("drop", (e) => {
    const dt = e.dataTransfer;
    if (dt.files.length) {
      fileInput.files = dt.files;
      fileLabel.textContent = dt.files[0].name;
    }
  });

  /* Forms */
  const formUpload = $("#form-upload");
  const formQuery = $("#form-query");
  const btnUpload = $("#btn-upload");
  const btnQuery = $("#btn-query");
  const queryName = $("#query-name");
  const uploadName = $("#upload-name");

  function setLoading(btn, loading) {
    const sp = btn.querySelector(".btn-spinner");
    const lb = btn.querySelector(".btn-label");
    btn.disabled = loading;
    sp.hidden = !loading;
    lb.style.opacity = loading ? "0.85" : "1";
  }

  formUpload.addEventListener("submit", async (e) => {
    e.preventDefault();
    const name = uploadName.value.trim();
    const file = fileInput.files[0];
    if (!name || !file) {
      showToast("Please enter a knowledge base name and choose a file.", "error");
      return;
    }
    const body = new FormData();
    body.append("name", name);
    body.append("file", file);

    setLoading(btnUpload, true);
    try {
      const res = await fetch("/create_knowledge_base", { method: "POST", body });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        showToast(parseErrorDetail(data), "error");
        return;
      }
      showToast("Indexed successfully — \"" + data.file_name + "\" added to \"" + data.name + "\".", "success");
      queryName.value = name;
      $("#tab-query").click();
    } catch (err) {
      showToast(err.message || "Network error", "error");
    } finally {
      setLoading(btnUpload, false);
    }
  });

  const queryOutput = $("#query-output");
  const outputMeta = $("#output-meta");
  const outputAnswer = $("#output-answer");
  const outputSources = $("#output-sources");
  const sourcesCount = $("#sources-count");

  function formatAnswerText(text) {
    if (!text) return "<p><em>No answer returned.</em></p>";
    const escaped = text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
    const parts = escaped.split(/\n\n+/).filter(Boolean);
    return parts.map((p) => "<p>" + p.replace(/\n/g, "<br/>") + "</p>").join("");
  }

  formQuery.addEventListener("submit", async (e) => {
    e.preventDefault();
    const name = queryName.value.trim();
    const query = $("#query-text").value.trim();
    if (!name || !query) {
      showToast("Please enter the knowledge base name and your question.", "error");
      return;
    }
    const body = new FormData();
    body.append("name", name);
    body.append("query", query);

    setLoading(btnQuery, true);
    queryOutput.hidden = true;
    try {
      const res = await fetch("/query_document", { method: "POST", body });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        showToast(parseErrorDetail(data), "error");
        return;
      }
      outputMeta.textContent = data.message || "";
      outputAnswer.innerHTML = formatAnswerText(data.ai_answer);
      outputSources.innerHTML = "";
      const results = data.results || [];
      sourcesCount.textContent = "(" + results.length + ")";
      results.forEach((r) => {
        const li = document.createElement("li");
        li.className = "source-item";
        const fn = r.original_filename || "Document";
        const score = typeof r.score === "number" ? r.score.toFixed(4) : "";
        const txt = (r.text || "").slice(0, 1200) + ((r.text || "").length > 1200 ? "…" : "");
        li.innerHTML =
          '<span class="src-score">' +
          (score ? "score " + score : "") +
          "</span>" +
          '<div class="src-file">' +
          fn +
          "</div>" +
          '<div class="src-text">' +
          (txt.replace(/</g, "&lt;").replace(/>/g, "&gt;") || "—") +
          "</div>";
        outputSources.appendChild(li);
      });
      queryOutput.hidden = false;
      queryOutput.scrollIntoView({ behavior: "smooth", block: "nearest" });
    } catch (err) {
      showToast(err.message || "Network error", "error");
    } finally {
      setLoading(btnQuery, false);
    }
  });
})();
