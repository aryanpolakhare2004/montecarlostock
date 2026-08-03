import { useState } from 'react';
import { api, ApiError } from '../api';
import { StatTable } from '../components/StatTable';
import { ChartImage } from '../components/ChartImage';
import { ErrorBox } from '../components/ErrorBox';
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
        <label>
          Days
          <input type="number" value={days} onChange={(e) => setDays(Number(e.target.value))} />
        </label>
        <label>
          Sims
          <input type="number" value={sims} onChange={(e) => setSims(Number(e.target.value))} />
        </label>
        <label>
          Block size
          <input type="number" value={blockSize} onChange={(e) => setBlockSize(Number(e.target.value))} />
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
            <StatTable summary={result.summary} />
            <ChartImage base64Png={result.chart_png_base64} />
          </>
        )}
      </div>
    </section>
  );
}
