import { useState } from 'react';
import { api, ApiError } from '../api';
import { StatTable } from '../components/StatTable';
import { ErrorBox } from '../components/ErrorBox';
import { ExportButtons } from '../components/ExportButtons';
import { FanChart } from '../components/charts/FanChart';
import type { PortfolioResponse } from '../types';

export function PortfolioPage() {
  const [tickers, setTickers] = useState('AAPL,MSFT,GOOG');
  const [weights, setWeights] = useState('');
  const [value, setValue] = useState(10000);
  const [period, setPeriod] = useState('5y');
  const [days, setDays] = useState(252);
  const [sims, setSims] = useState(5000);
  const [seed, setSeed] = useState('');
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<PortfolioResponse | null>(null);
  const [error, setError] = useState<Error | null>(null);

  async function onSubmit(evt: React.FormEvent) {
    evt.preventDefault();
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const tickerList = tickers.split(',').map((t) => t.trim()).filter(Boolean);
      const weightList = weights
        ? weights.split(',').map((w) => Number(w.trim())).filter((w) => !Number.isNaN(w))
        : null;
      const response = await api.portfolio({
        tickers: tickerList,
        weights: weightList,
        value,
        period,
        days,
        sims,
        seed: seed === '' ? null : Number(seed),
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
      <h2>Simulate a multi-asset portfolio</h2>
      <form className="run-form" onSubmit={onSubmit}>
        <label>
          Tickers (comma-separated)
          <input value={tickers} onChange={(e) => setTickers(e.target.value)} required placeholder="AAPL,MSFT,GOOG" />
        </label>
        <label>
          Weights (comma-separated, optional)
          <input value={weights} onChange={(e) => setWeights(e.target.value)} placeholder="0.5,0.3,0.2" />
        </label>
        <label>
          Starting value
          <input type="number" value={value} onChange={(e) => setValue(Number(e.target.value))} />
        </label>
        <label>
          Period
          <input value={period} onChange={(e) => setPeriod(e.target.value)} />
        </label>
        <label>
          Days
          <input type="number" value={days} onChange={(e) => setDays(Number(e.target.value))} />
        </label>
        <label>
          Sims
          <input type="number" value={sims} onChange={(e) => setSims(Number(e.target.value))} />
        </label>
        <label>
          Seed
          <input value={seed} onChange={(e) => setSeed(e.target.value)} placeholder="optional" />
        </label>
        <button type="submit" disabled={busy}>Run</button>
      </form>
      <div className="result">
        {busy && 'Running…'}
        {error && <ErrorBox error={error} />}
        {result && (
          <>
            <p>{Object.entries(result.weights).map(([t, w]) => `${t}: ${w.toFixed(3)}`).join(', ')}</p>
            <StatTable summary={result.summary} />
            <ExportButtons runId={result.run_id} csvFilename={`portfolio_${result.run_id}.csv`} csvRows={result.bands} />
            <FanChart data={result.bands} yLabel="Portfolio value" />
          </>
        )}
      </div>
    </section>
  );
}
