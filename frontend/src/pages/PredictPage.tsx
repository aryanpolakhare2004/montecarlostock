import { useState } from 'react';
import { api, ApiError } from '../api';
import { ErrorBox } from '../components/ErrorBox';
import type { useModels } from '../hooks/useModels';
import type { PredictResponse } from '../types';

type ModelOptions = ReturnType<typeof useModels>;

export function PredictPage({ modelOptions }: { modelOptions: ModelOptions }) {
  const [modelId, setModelId] = useState('');
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<PredictResponse | null>(null);
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
      const response = await api.predict({ model_id: Number(modelId) });
      setResult(response);
    } catch (err) {
      setError(err instanceof ApiError ? err : new Error(String(err)));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section>
      <h2>Predict next-period direction</h2>
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
        <button type="submit" disabled={busy}>Predict</button>
      </form>
      <div className="result">
        {busy && 'Predicting…'}
        {error && <ErrorBox error={error} />}
        {result && (
          <p>
            {result.ticker}:{' '}
            <span className={`direction ${result.direction === 'UP' ? 'up' : 'down'}`}>{result.direction}</span>{' '}
            next {result.horizon}-day move &mdash; P(up)={result.prob_up.toFixed(3)}
          </p>
        )}
      </div>
    </section>
  );
}
