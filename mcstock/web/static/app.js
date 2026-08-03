"use strict";

function switchTab(name) {
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.tab === name);
  });
  document.querySelectorAll(".tab-panel").forEach((panel) => {
    panel.classList.toggle("active", panel.id === `tab-${name}`);
  });
  if (name === "history") loadHistory();
  if (["strategy", "predict", "backtest_ml", "compare"].includes(name)) loadModelOptions();
}

document.querySelectorAll(".tab-btn").forEach((btn) => {
  btn.addEventListener("click", () => switchTab(btn.dataset.tab));
});

function fieldsToObject(form) {
  const data = new FormData(form);
  const obj = {};
  for (const [key, value] of data.entries()) {
    obj[key] = value;
  }
  return obj;
}

function coerceNumber(value, { allowEmpty = false } = {}) {
  if (value === "" || value === undefined || value === null) {
    return allowEmpty ? null : undefined;
  }
  const n = Number(value);
  return Number.isNaN(n) ? undefined : n;
}

async function postJSON(url, body) {
  const resp = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const payload = await resp.json();
  if (!resp.ok) {
    throw new Error(payload.detail || `request failed (${resp.status})`);
  }
  return payload;
}

async function getJSON(url) {
  const resp = await fetch(url);
  const payload = await resp.json();
  if (!resp.ok) throw new Error(payload.detail || `request failed (${resp.status})`);
  return payload;
}

function renderStatTable(summary) {
  const rows = Object.entries(summary)
    .map(([key, value]) => {
      const display = typeof value === "number" ? value.toFixed(4) : String(value);
      return `<tr><td>${key}</td><td>${display}</td></tr>`;
    })
    .join("");
  return `<table class="stat-table"><tbody>${rows}</tbody></table>`;
}

function renderChart(base64Png) {
  return `<img alt="chart" src="data:image/png;base64,${base64Png}">`;
}

function renderError(err) {
  return `<p class="error">${err.message}</p>`;
}

function setBusy(form, busy) {
  form.querySelector("button[type=submit]").disabled = busy;
}

// ---- Price ----

document.getElementById("form-price").addEventListener("submit", async (evt) => {
  evt.preventDefault();
  const form = evt.target;
  const out = document.getElementById("result-price");
  const fields = fieldsToObject(form);
  const body = {
    ticker: fields.ticker,
    period: fields.period || "5y",
    days: coerceNumber(fields.days) ?? 252,
    sims: coerceNumber(fields.sims) ?? 10000,
    seed: coerceNumber(fields.seed, { allowEmpty: true }),
  };
  setBusy(form, true);
  out.innerHTML = "Running…";
  try {
    const result = await postJSON("/api/price", body);
    out.innerHTML =
      `<p>s0=${result.s0.toFixed(2)} mu=${(result.mu * 100).toFixed(2)}%/yr sigma=${(result.sigma * 100).toFixed(2)}%/yr</p>` +
      renderStatTable(result.summary) + renderChart(result.chart_png_base64);
  } catch (err) {
    out.innerHTML = renderError(err);
  } finally {
    setBusy(form, false);
  }
});

// ---- Strategy ----

const strategySelect = document.getElementById("strategy-select");
function updateStrategyFields() {
  const value = strategySelect.value;
  document.querySelectorAll(".strategy-only").forEach((el) => (el.style.display = "none"));
  if (value === "sma-crossover") {
    document.querySelectorAll(".strategy-only.sma").forEach((el) => (el.style.display = "flex"));
  } else if (value === "ml-technical") {
    document.querySelectorAll(".strategy-only.ml-technical").forEach((el) => (el.style.display = "flex"));
  }
}
strategySelect.addEventListener("change", updateStrategyFields);
updateStrategyFields();

document.getElementById("form-strategy").addEventListener("submit", async (evt) => {
  evt.preventDefault();
  const form = evt.target;
  const out = document.getElementById("result-strategy");
  const fields = fieldsToObject(form);
  const body = {
    ticker: fields.ticker,
    strategy: fields.strategy,
    fast: coerceNumber(fields.fast) ?? 20,
    slow: coerceNumber(fields.slow) ?? 50,
    period: fields.period || "5y",
    days: coerceNumber(fields.days) ?? 252,
    sims: coerceNumber(fields.sims) ?? 5000,
    block_size: coerceNumber(fields.block_size) ?? 5,
    seed: coerceNumber(fields.seed, { allowEmpty: true }),
    model_id: fields.model_id ? Number(fields.model_id) : null,
  };
  setBusy(form, true);
  out.innerHTML = "Running…";
  try {
    const result = await postJSON("/api/strategy", body);
    out.innerHTML = renderStatTable(result.summary) + renderChart(result.chart_png_base64);
  } catch (err) {
    out.innerHTML = renderError(err);
  } finally {
    setBusy(form, false);
  }
});

// ---- Portfolio ----

document.getElementById("form-portfolio").addEventListener("submit", async (evt) => {
  evt.preventDefault();
  const form = evt.target;
  const out = document.getElementById("result-portfolio");
  const fields = fieldsToObject(form);
  const tickers = fields.tickers.split(",").map((t) => t.trim()).filter(Boolean);
  const weights = fields.weights
    ? fields.weights.split(",").map((w) => Number(w.trim())).filter((w) => !Number.isNaN(w))
    : null;
  const body = {
    tickers,
    weights,
    value: coerceNumber(fields.value) ?? 10000,
    period: fields.period || "5y",
    days: coerceNumber(fields.days) ?? 252,
    sims: coerceNumber(fields.sims) ?? 5000,
    seed: coerceNumber(fields.seed, { allowEmpty: true }),
  };
  setBusy(form, true);
  out.innerHTML = "Running…";
  try {
    const result = await postJSON("/api/portfolio", body);
    const weightsLine = Object.entries(result.weights)
      .map(([t, w]) => `${t}: ${w.toFixed(3)}`)
      .join(", ");
    out.innerHTML = `<p>${weightsLine}</p>` + renderStatTable(result.summary) + renderChart(result.chart_png_base64);
  } catch (err) {
    out.innerHTML = renderError(err);
  } finally {
    setBusy(form, false);
  }
});

// ---- Train ----

document.getElementById("form-train").addEventListener("submit", async (evt) => {
  evt.preventDefault();
  const form = evt.target;
  const out = document.getElementById("result-train");
  const fields = fieldsToObject(form);
  const body = {
    ticker: fields.ticker,
    model: fields.model,
    sentiment: fields.sentiment,
    use_volume: form.querySelector("[name=use_volume]").checked,
    period: fields.period || "5y",
    horizon: coerceNumber(fields.horizon) ?? 1,
    test_size: coerceNumber(fields.test_size) ?? 0.2,
  };
  setBusy(form, true);
  out.innerHTML = "Training… this can take a while (fetching data/news, fitting the model).";
  try {
    const result = await postJSON("/api/train", body);
    out.innerHTML =
      `<p>Saved as model #${result.model_id} &mdash; train_accuracy=${result.train_accuracy.toFixed(4)}, ` +
      `test_accuracy=${result.test_accuracy.toFixed(4)}</p>` +
      `<pre class="report">${result.test_report}</pre>`;
    loadModelOptions();
  } catch (err) {
    out.innerHTML = renderError(err);
  } finally {
    setBusy(form, false);
  }
});

// ---- Predict ----

document.getElementById("form-predict").addEventListener("submit", async (evt) => {
  evt.preventDefault();
  const form = evt.target;
  const out = document.getElementById("result-predict");
  const modelId = Number(fieldsToObject(form).model_id);
  if (!modelId) {
    out.innerHTML = renderError(new Error("choose a trained model first"));
    return;
  }
  setBusy(form, true);
  out.innerHTML = "Predicting…";
  try {
    const result = await postJSON("/api/predict", { model_id: modelId });
    const cls = result.direction === "UP" ? "up" : "down";
    out.innerHTML =
      `<p>${result.ticker}: <span class="direction ${cls}">${result.direction}</span> ` +
      `next ${result.horizon}-day move &mdash; P(up)=${result.prob_up.toFixed(3)}</p>`;
  } catch (err) {
    out.innerHTML = renderError(err);
  } finally {
    setBusy(form, false);
  }
});

// ---- Backtest ML ----

document.getElementById("form-backtest_ml").addEventListener("submit", async (evt) => {
  evt.preventDefault();
  const form = evt.target;
  const out = document.getElementById("result-backtest_ml");
  const fields = fieldsToObject(form);
  const modelId = Number(fields.model_id);
  if (!modelId) {
    out.innerHTML = renderError(new Error("choose a trained model first"));
    return;
  }
  const body = {
    model_id: modelId,
    days: coerceNumber(fields.days) ?? 60,
    sims: coerceNumber(fields.sims) ?? 10000,
    block_size: coerceNumber(fields.block_size) ?? 5,
    seed: coerceNumber(fields.seed, { allowEmpty: true }),
  };
  setBusy(form, true);
  out.innerHTML = "Running…";
  try {
    const result = await postJSON("/api/backtest_ml", body);
    out.innerHTML = renderStatTable(result.summary) + renderChart(result.chart_png_base64);
  } catch (err) {
    out.innerHTML = renderError(err);
  } finally {
    setBusy(form, false);
  }
});

// ---- Compare ----

document.getElementById("form-compare").addEventListener("submit", async (evt) => {
  evt.preventDefault();
  const form = evt.target;
  const out = document.getElementById("result-compare");
  const fields = fieldsToObject(form);
  const modelIds = Array.from(document.getElementById("compare-model-select").selectedOptions)
    .map((opt) => Number(opt.value))
    .filter((id) => !Number.isNaN(id) && id);
  const body = {
    ticker: fields.ticker,
    period: fields.period || "5y",
    days: coerceNumber(fields.days) ?? 252,
    sims: coerceNumber(fields.sims) ?? 5000,
    block_size: coerceNumber(fields.block_size) ?? 5,
    fast: coerceNumber(fields.fast) ?? 20,
    slow: coerceNumber(fields.slow) ?? 50,
    seed: coerceNumber(fields.seed, { allowEmpty: true }),
    model_ids: modelIds,
  };
  setBusy(form, true);
  out.innerHTML = "Running…";
  try {
    const result = await postJSON("/api/compare", body);
    const rows = result.ranking
      .map((name, i) => {
        const s = result.results[name];
        return (
          `<tr><td>${i + 1}</td><td>${name}</td><td>${s.mean_return.toFixed(4)}</td>` +
          `<td>${s.std_return.toFixed(4)}</td><td>${s.prob_profit.toFixed(3)}</td>` +
          `<td>${s.mean_max_drawdown.toFixed(4)}</td></tr>`
        );
      })
      .join("");
    out.innerHTML =
      '<table class="data-table"><thead><tr><th>Rank</th><th>Strategy</th><th>Mean return</th>' +
      "<th>Std return</th><th>Prob profit</th><th>Mean max drawdown</th></tr></thead>" +
      `<tbody>${rows}</tbody></table>` +
      renderChart(result.chart_png_base64);
  } catch (err) {
    out.innerHTML = renderError(err);
  } finally {
    setBusy(form, false);
  }
});

// ---- Fundamentals analyst ----

function fmtScore(x) {
  return x === null || x === undefined ? "n/a" : Number(x).toFixed(1);
}

function fmtPct(x) {
  return x === null || x === undefined ? "n/a" : `${(x * 100).toFixed(1)}%`;
}

function fmtMoney(x) {
  return x === null || x === undefined
    ? "n/a"
    : `$${Number(x).toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
}

function renderEvidenceList(items) {
  if (!items || !items.length) return "<p class=\"hint\">No evidence available.</p>";
  return `<ul class="evidence">${items.map((i) => `<li>${i}</li>`).join("")}</ul>`;
}

function renderScoreCard(report) {
  const s = report.scores;
  const t = report.trends;
  const tile = (label, value) =>
    `<div class="score-tile"><div class="score-label">${label}</div><div class="score-value">${fmtScore(value)}</div></div>`;

  const grid =
    tile("Business quality", s.business_quality) +
    tile("Financial strength", s.financial_strength) +
    tile("Growth", s.growth) +
    tile("Valuation", s.valuation) +
    `<div class="score-tile"><div class="score-label">Risk</div>` +
    `<div class="score-value risk-${(s.risk_label || "unknown").toLowerCase()}">${s.risk_label || "n/a"}</div></div>`;

  const trendsRow = `<div class="trend-row">
      <span>Revenue trend: <strong>${t.revenue_trend}</strong></span>
      <span>Free cash flow: <strong>${t.fcf_status}</strong></span>
      <span>Debt position: <strong>${t.debt_position}</strong></span>
      <span>Share dilution: <strong>${t.share_dilution}</strong></span>
    </div>`;

  const evidence = `
    <details><summary>Business quality evidence</summary>${renderEvidenceList(report.evidence.business_quality)}</details>
    <details><summary>Growth evidence</summary>${renderEvidenceList(report.evidence.growth)}</details>
    <details><summary>Financial strength evidence</summary>${renderEvidenceList(report.evidence.financial_strength)}</details>
    <details><summary>Valuation evidence</summary>${renderEvidenceList(report.evidence.valuation)}</details>
    <details><summary>Risk evidence</summary>${renderEvidenceList(report.evidence.risk)}</details>`;

  const fv = report.fair_value;
  const fvLine =
    fv.low != null && fv.high != null
      ? `${fmtMoney(fv.low)} &ndash; ${fmtMoney(fv.high)} (current price ${fmtMoney(fv.current_price)}, ` +
        `upside ${fmtPct(fv.upside_low_pct)} to ${fmtPct(fv.upside_high_pct)})`
      : "n/a (insufficient data)";

  return `
    <h3>${report.company_name} (${report.ticker})</h3>
    <div class="score-grid">${grid}</div>
    ${trendsRow}
    ${evidence}
    <div class="case-box bull"><strong>Bull case:</strong> ${report.bull_case}</div>
    <div class="case-box bear"><strong>Bear case:</strong> ${report.bear_case}</div>
    <div class="case-box flags"><strong>Major red flags:</strong>
      <ul>${report.red_flags.map((f) => `<li>${f}</li>`).join("")}</ul>
    </div>
    <p><strong>Estimated fair-value range:</strong> ${fvLine}</p>
    <p><strong>Confidence:</strong> ${report.confidence}%
      <span class="hint">&mdash; narrative source: ${report.narrative_source}</span></p>`;
}

document.getElementById("form-analyst").addEventListener("submit", async (evt) => {
  evt.preventDefault();
  const form = evt.target;
  const out = document.getElementById("result-analyst");
  const fields = fieldsToObject(form);
  const body = {
    ticker: fields.ticker,
    llm_backend: fields.llm_backend || null,
    force_refresh: form.querySelector("[name=force_refresh]").checked,
  };
  setBusy(form, true);
  out.innerHTML = "Fetching filings and scoring…";
  try {
    const result = await postJSON("/api/fundamentals", body);
    out.innerHTML = renderScoreCard(result) + (result.chart_png_base64 ? renderChart(result.chart_png_base64) : "");
  } catch (err) {
    out.innerHTML = renderError(err);
  } finally {
    setBusy(form, false);
  }
});

// ---- Fundamentals compare ----

document.getElementById("form-analyst-compare").addEventListener("submit", async (evt) => {
  evt.preventDefault();
  const form = evt.target;
  const out = document.getElementById("result-analyst-compare");
  const fields = fieldsToObject(form);
  const tickers = fields.tickers.split(",").map((t) => t.trim()).filter(Boolean);
  setBusy(form, true);
  out.innerHTML = "Analyzing each ticker…";
  try {
    const result = await postJSON("/api/fundamentals/compare", { tickers });
    const rows = result.rows
      .map(
        (r, i) => `<tr>
          <td>${i + 1}</td><td>${r.ticker}</td><td>${r.company_name}</td>
          <td>${fmtScore(r.composite)}</td>
          <td>${fmtScore(r.business_quality)}</td><td>${fmtScore(r.growth)}</td>
          <td>${fmtScore(r.financial_strength)}</td><td>${fmtScore(r.valuation)}</td>
          <td>${r.risk_label || "n/a"}</td>
          <td>${r.revenue_trend}</td><td>${r.fcf_status}</td><td>${r.debt_position}</td>
          <td>${r.confidence}%</td>
        </tr>`
      )
      .join("");
    const errorLines = Object.entries(result.errors)
      .map(([t, e]) => `<li>${t}: ${e}</li>`)
      .join("");
    out.innerHTML =
      '<div class="table-scroll"><table class="data-table"><thead><tr><th>Rank</th><th>Ticker</th><th>Company</th>' +
      "<th>Composite</th><th>Quality</th><th>Growth</th><th>Fin. strength</th><th>Valuation</th>" +
      "<th>Risk</th><th>Revenue</th><th>FCF</th><th>Debt</th><th>Confidence</th></tr></thead>" +
      `<tbody>${rows}</tbody></table></div>` +
      (errorLines ? `<p class="error">Errors:</p><ul class="error">${errorLines}</ul>` : "");
  } catch (err) {
    out.innerHTML = renderError(err);
  } finally {
    setBusy(form, false);
  }
});

// ---- Model dropdowns ----

function modelOptionsHTML(models) {
  return models.length
    ? models
        .map(
          (m) =>
            `<option value="${m.id}">#${m.id} ${m.ticker} ${m.model_type} (test acc ${m.test_accuracy.toFixed(2)})</option>`
        )
        .join("")
    : "";
}

async function loadModelOptions() {
  let models;
  try {
    models = await getJSON("/api/models");
  } catch (err) {
    return;
  }
  const allOptions = modelOptionsHTML(models) || '<option value="">(no trained models yet)</option>';
  const technicalOnly = models.filter((m) => !m.sentiment_sources && !m.use_volume);
  const technicalOptions =
    modelOptionsHTML(technicalOnly) || '<option value="">(no technical-only models yet)</option>';

  ["predict-model-select", "backtest-model-select"].forEach((id) => {
    const select = document.getElementById(id);
    const current = select.value;
    select.innerHTML = allOptions;
    if (current) select.value = current;
  });

  document.getElementById("strategy-model-select").innerHTML = technicalOptions;
  document.getElementById("compare-model-select").innerHTML = modelOptionsHTML(technicalOnly);
}

// ---- History ----

async function loadHistory() {
  const runsDiv = document.getElementById("runs-table");
  const modelsDiv = document.getElementById("models-table");
  runsDiv.textContent = "Loading…";
  modelsDiv.textContent = "Loading…";

  try {
    const runs = await getJSON("/api/runs");
    if (!runs.length) {
      runsDiv.innerHTML = "<p>No runs yet.</p>";
    } else {
      const rows = runs
        .map(
          (r) =>
            `<tr><td>${r.id}</td><td>${r.run_type}</td><td>${r.ticker}</td>` +
            `<td>${r.created_at.replace("T", " ").slice(0, 19)}</td>` +
            `<td>${r.has_chart ? `<a href="/api/runs/${r.id}/chart" target="_blank">view</a>` : ""}</td></tr>`
        )
        .join("");
      runsDiv.innerHTML =
        '<table class="data-table"><thead><tr><th>ID</th><th>Type</th><th>Ticker</th><th>When</th><th>Chart</th></tr></thead>' +
        `<tbody>${rows}</tbody></table>`;
    }
  } catch (err) {
    runsDiv.innerHTML = renderError(err);
  }

  try {
    const models = await getJSON("/api/models");
    if (!models.length) {
      modelsDiv.innerHTML = "<p>No trained models yet.</p>";
    } else {
      const rows = models
        .map(
          (m) =>
            `<tr><td>${m.id}</td><td>${m.ticker}</td><td>${m.model_type}</td>` +
            `<td>${m.sentiment_sources ? m.sentiment_sources.join(",") : "none"}</td>` +
            `<td>${m.use_volume ? "yes" : "no"}</td>` +
            `<td>${m.train_accuracy.toFixed(3)}</td><td>${m.test_accuracy.toFixed(3)}</td>` +
            `<td>${m.created_at.replace("T", " ").slice(0, 19)}</td></tr>`
        )
        .join("");
      modelsDiv.innerHTML =
        '<table class="data-table"><thead><tr><th>ID</th><th>Ticker</th><th>Model</th><th>Sentiment</th>' +
        "<th>Volume</th><th>Train acc</th><th>Test acc</th><th>When</th></tr></thead>" +
        `<tbody>${rows}</tbody></table>`;
    }
  } catch (err) {
    modelsDiv.innerHTML = renderError(err);
  }
}

document.getElementById("refresh-history").addEventListener("click", loadHistory);

loadModelOptions();
