import { useState } from 'react';
import { api, ApiError } from '../api';
import { ErrorBox } from '../components/ErrorBox';
import { ScoreCard } from '../components/ScoreCard';
import { SubmitButton } from '../components/SubmitButton';
import type { FundamentalsReport } from '../types';

export function AnalystPage() {
  const [ticker, setTicker] = useState('MSFT');
  const [llmBackend, setLlmBackend] = useState('');
  const [forceRefresh, setForceRefresh] = useState(false);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<FundamentalsReport | null>(null);
  const [error, setError] = useState<Error | null>(null);

  async function onSubmit(evt: React.FormEvent) {
    evt.preventDefault();
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const response = await api.fundamentals({
        ticker,
        llm_backend: llmBackend || null,
        force_refresh: forceRefresh,
      });
      setResult(response);
    } catch (err) {
      setError(err instanceof ApiError ? err : new Error(String(err)));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section>
      <h2>AI investment analyst</h2>
      <p className="hint">
        Pulls structured financials straight from SEC EDGAR, engineers ratios, and scores the business numerically.
        Bull/bear case and red flags are rendered from that same evidence &mdash; by a local template unless a local
        LLM backend (e.g. Ollama) is configured.
      </p>
      <form className="run-form" onSubmit={onSubmit}>
        <fieldset disabled={busy} className="run-form-fields">
          <label>
            Ticker
            <input value={ticker} onChange={(e) => setTicker(e.target.value)} required placeholder="MSFT" />
          </label>
          <label>
            LLM backend
            <select value={llmBackend} onChange={(e) => setLlmBackend(e.target.value)}>
              <option value="">(server default)</option>
              <option value="stub">stub (no LLM)</option>
              <option value="ollama">ollama</option>
            </select>
          </label>
          <label className="checkbox">
            <input type="checkbox" checked={forceRefresh} onChange={(e) => setForceRefresh(e.target.checked)} />
            Force refresh from SEC
          </label>
          <SubmitButton busy={busy} busyLabel="Fetching filings…">Analyze</SubmitButton>
        </fieldset>
      </form>
      <div className="result">
        {error && <ErrorBox error={error} />}
        {result && <ScoreCard report={result} />}
      </div>
    </section>
  );
}
