import { useState } from 'react';
import { api, ApiError } from '../api';
import { StatTable } from '../components/StatTable';
import { ErrorBox } from '../components/ErrorBox';
import { ExportButtons } from '../components/ExportButtons';
import { SubmitButton } from '../components/SubmitButton';
import { FanChart } from '../components/charts/FanChart';
import type { useModels } from '../hooks/useModels';
import type { BacktestMlResponse } from '../types';

type ModelOptions = ReturnType<typeof useModels>;

export function BacktestMlPage({ modelOptions }: { modelOptions: ModelOptions }) {
  const [modelId, setModelId] = useState('');
  const [days, setDays] = useState(60);
  const [sims, setSims] = useState(10000);
  const [blockSize, setBlockSize] = useState(5);
  const [seed, setSeed] = useState('');
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<BacktestMlResponse | null>(null);
  const [error, setError] = useState<Error | null>(null);

  async function onSubmit(evt: React.FormEvent) {
    evt.preventDefault();
    if (!modelId) {
      setError(new Error('choose a trained model first'));
      return;
    }
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const response = await api.backtestMl({
        model_id: Number(modelId), days, sims, block_size: blockSize, seed: seed === '' ? null : Number(seed),
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
      <h2>Monte Carlo project a trained model's robustness</h2>
      <form className="run-form" onSubmit={onSubmit}>
        <fieldset disabled={busy} className="run-form-fields">
          <label>
            Model
            <select value={modelId} onChange={(e) => setModelId(e.target.value)}>
              <option value="">(load models first)</option>
              {modelOptions.models.map((m) => (
                <option key={m.id} value={m.id}>
                  #{m.id} {m.ticker} {m.model_type} (test acc {m.test_accuracy.toFixed(2)})
                </option>
              ))}
            </select>
          </label>
          <details className="advanced-fields">
            <summary>Advanced options</summary>
            <div className="advanced-fields-grid">
              <label>
                Days
                <input type="number" min={1} value={days} onChange={(e) => setDays(Number(e.target.value))} />
              </label>
              <label>
                Sims
                <input type="number" min={1} value={sims} onChange={(e) => setSims(Number(e.target.value))} />
              </label>
              <label>
                Block size
                <input type="number" min={1} value={blockSize} onChange={(e) => setBlockSize(Number(e.target.value))} />
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
            <StatTable summary={result.summary} />
            <ExportButtons runId={result.run_id} csvFilename={`backtest_ml_${result.run_id}.csv`} csvRows={result.bands} />
            <FanChart data={result.bands} yLabel="Equity (starting at 1.0)" />
          </>
        )}
      </div>
    </section>
  );
}
