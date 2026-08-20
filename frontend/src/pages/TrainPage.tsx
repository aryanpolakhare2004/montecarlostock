import { useState } from 'react';
import { api, ApiError } from '../api';
import { ErrorBox } from '../components/ErrorBox';
import { SubmitButton } from '../components/SubmitButton';
import { useToast } from '../components/toast';
import type { TrainRequest, TrainResponse } from '../types';

export function TrainPage({ onTrained }: { onTrained: () => void }) {
  const [ticker, setTicker] = useState('AAPL');
  const [model, setModel] = useState<TrainRequest['model']>('logreg');
  const [sentiment, setSentiment] = useState<TrainRequest['sentiment']>('none');
  const [useVolume, setUseVolume] = useState(true);
  const [period, setPeriod] = useState('5y');
  const [horizon, setHorizon] = useState(1);
  const [testSize, setTestSize] = useState(0.2);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<TrainResponse | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const { showToast } = useToast();

  async function onSubmit(evt: React.FormEvent) {
    evt.preventDefault();
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const response = await api.train({
        ticker, model, sentiment, use_volume: useVolume, period, horizon, test_size: testSize,
      });
      setResult(response);
      onTrained();
      showToast(`Trained model #${response.model_id} for ${ticker.toUpperCase()}`, 'success');
    } catch (err) {
      const errorObj = err instanceof ApiError ? err : new Error(String(err));
      setError(errorObj);
      showToast(`Training failed: ${errorObj.message}`, 'error');
    } finally {
      setBusy(false);
    }
  }

  return (
    <section>
      <h2>Train an ML classifier (binary up/down)</h2>
      <form className="run-form" onSubmit={onSubmit}>
        <fieldset disabled={busy} className="run-form-fields">
          <label>
            Ticker
            <input value={ticker} onChange={(e) => setTicker(e.target.value)} required placeholder="AAPL" />
          </label>
          <label>
            Model
            <select value={model} onChange={(e) => setModel(e.target.value as TrainRequest['model'])}>
              <option value="logreg">logreg</option>
              <option value="random_forest">random_forest</option>
              <option value="gradient_boosting">gradient_boosting</option>
            </select>
          </label>
          <label>
            Sentiment
            <select value={sentiment} onChange={(e) => setSentiment(e.target.value as TrainRequest['sentiment'])}>
              <option value="none">none</option>
              <option value="yfinance">yfinance</option>
              <option value="rss">rss</option>
              <option value="reddit">reddit</option>
              <option value="all">all</option>
            </select>
          </label>
          <label className="checkbox">
            <input type="checkbox" checked={useVolume} onChange={(e) => setUseVolume(e.target.checked)} />
            Use volume features
          </label>
          <details className="advanced-fields">
            <summary>Advanced options</summary>
            <div className="advanced-fields-grid">
              <label>
                Period
                <input value={period} onChange={(e) => setPeriod(e.target.value)} />
              </label>
              <label>
                Horizon (days ahead)
                <input type="number" min={1} value={horizon} onChange={(e) => setHorizon(Number(e.target.value))} />
              </label>
              <label>
                Test size
                <input
                  type="number" min={0.05} max={0.5} step={0.05} value={testSize}
                  onChange={(e) => setTestSize(Number(e.target.value))}
                />
              </label>
            </div>
          </details>
          <SubmitButton busy={busy} busyLabel="Training…">Train</SubmitButton>
        </fieldset>
      </form>
      <p className="hint">
        Tip: to later use a model with strategy <code>ml-technical</code>, train with sentiment{' '}
        <code>none</code> and volume features unchecked.
      </p>
      <div className="result">
        {busy && <p className="hint">Training… this can take a while (fetching data/news, fitting the model).</p>}
        {error && <ErrorBox error={error} />}
        {result && (
          <>
            <p>
              Saved as model #{result.model_id} &mdash; train_accuracy={result.train_accuracy.toFixed(4)}, test_accuracy=
              {result.test_accuracy.toFixed(4)}
            </p>
            <pre className="report">{result.test_report}</pre>
          </>
        )}
      </div>
    </section>
  );
}
