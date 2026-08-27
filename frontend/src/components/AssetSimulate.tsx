import { useState } from 'react';
import { api, ApiError } from '../api';
import { StatTable } from './StatTable';
import { ErrorBox } from './ErrorBox';
import { ExportButtons } from './ExportButtons';
import { SubmitButton } from './SubmitButton';
import { FanChart } from './charts/FanChart';
import { Histogram } from './charts/Histogram';
import { fmtMoney, fmtPct } from '../format';
import type { PriceResponse } from '../types';

export function AssetSimulate({ symbol }: { symbol: string }) {
  const [period, setPeriod] = useState('5y');
  const [days, setDays] = useState(252);
  const [sims, setSims] = useState(10000);
  const [seed, setSeed] = useState('');
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<PriceResponse | null>(null);
  const [error, setError] = useState<Error | null>(null);

  async function onSubmit(evt: React.FormEvent) {
    evt.preventDefault();
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const response = await api.price({ ticker: symbol, period, days, sims, seed: seed === '' ? null : Number(seed) });
      setResult(response);
    } catch (err) {
      setError(err instanceof ApiError ? err : new Error(String(err)));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="commodity-block">
      <h3>Simulate future price (GBM)</h3>
      <form className="run-form" onSubmit={onSubmit}>
        <fieldset disabled={busy} className="run-form-fields">
          <details className="advanced-fields">
            <summary>Advanced options</summary>
            <div className="advanced-fields-grid">
              <label>
                Period
                <input value={period} onChange={(e) => setPeriod(e.target.value)} />
              </label>
              <label>
                Days
                <input type="number" min={1} value={days} onChange={(e) => setDays(Number(e.target.value))} />
              </label>
              <label>
                Sims
                <input type="number" min={1} value={sims} onChange={(e) => setSims(Number(e.target.value))} />
              </label>
              <label>
                Seed
                <input value={seed} onChange={(e) => setSeed(e.target.value)} placeholder="optional" />
              </label>
            </div>
          </details>
          <SubmitButton busy={busy}>Run</SubmitButton>
        </fieldset>
      </form>
      <div className="result">
        {error && <ErrorBox error={error} />}
        {result && (
          <>
            <p>
              s0={fmtMoney(result.s0)} mu={fmtPct(result.mu)}/yr sigma={fmtPct(result.sigma)}/yr
            </p>
            <StatTable summary={result.summary} />
            <ExportButtons runId={result.run_id} csvFilename={`price_${symbol}_${result.run_id}.csv`} csvRows={result.bands} />
            <FanChart data={result.bands} yLabel="Price" />
            <Histogram data={result.distribution} xLabel="Final price" referenceValue={result.s0} />
          </>
        )}
      </div>
    </div>
  );
}
