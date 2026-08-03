import { useState } from 'react';
import { api, ApiError } from '../api';
import { StatTable } from '../components/StatTable';
import { ChartImage } from '../components/ChartImage';
import { ErrorBox } from '../components/ErrorBox';
import type { useModels } from '../hooks/useModels';
import type { StrategyRequest, StrategyResponse } from '../types';

type ModelOptions = ReturnType<typeof useModels>;

export function StrategyPage({ modelOptions }: { modelOptions: ModelOptions }) {
  const [ticker, setTicker] = useState('AAPL');
  const [strategy, setStrategy] = useState<StrategyRequest['strategy']>('buy-and-hold');
  const [fast, setFast] = useState(20);
  const [slow, setSlow] = useState(50);
  const [modelId, setModelId] = useState('');
  const [period, setPeriod] = useState('5y');
  const [days, setDays] = useState(252);
  const [sims, setSims] = useState(5000);
  const [blockSize, setBlockSize] = useState(5);
  const [seed, setSeed] = useState('');
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<StrategyResponse | null>(null);
  const [error, setError] = useState<Error | null>(null);

  async function onSubmit(evt: React.FormEvent) {
    evt.preventDefault();
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const response = await api.strategy({
        ticker,
        strategy,
        fast,
        slow,
        period,
        days,
        sims,
        block_size: blockSize,
        seed: seed === '' ? null : Number(seed),
        model_id: modelId ? Number(modelId) : null,
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
      <h2>Monte Carlo backtest a trading strategy</h2>
      <form className="run-form" onSubmit={onSubmit}>
        <label>
          Ticker
          <input value={ticker} onChange={(e) => setTicker(e.target.value)} required placeholder="AAPL" />
        </label>
        <label>
          Strategy
          <select value={strategy} onChange={(e) => setStrategy(e.target.value as StrategyRequest['strategy'])}>
            <option value="buy-and-hold">buy-and-hold</option>
            <option value="sma-crossover">sma-crossover</option>
            <option value="ml-technical">ml-technical</option>
          </select>
        </label>
        {strategy === 'sma-crossover' && (
          <>
            <label>
              Fast SMA
              <input type="number" value={fast} onChange={(e) => setFast(Number(e.target.value))} />
            </label>
            <label>
              Slow SMA
              <input type="number" value={slow} onChange={(e) => setSlow(Number(e.target.value))} />
            </label>
          </>
        )}
        {strategy === 'ml-technical' && (
          <label>
            Model
            <select value={modelId} onChange={(e) => setModelId(e.target.value)}>
              <option value="">(load models first)</option>
              {modelOptions.technicalOnly.map((m) => (
                <option key={m.id} value={m.id}>
                  #{m.id} {m.ticker} {m.model_type} (test acc {m.test_accuracy.toFixed(2)})
                </option>
              ))}
            </select>
          </label>
        )}
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
