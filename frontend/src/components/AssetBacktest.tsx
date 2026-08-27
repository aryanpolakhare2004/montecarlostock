import { useState } from 'react';
import { api, ApiError } from '../api';
import { StatTable } from './StatTable';
import { ErrorBox } from './ErrorBox';
import { ExportButtons } from './ExportButtons';
import { SubmitButton } from './SubmitButton';
import { Histogram } from './charts/Histogram';
import type { StrategyRequest, StrategyResponse } from '../types';

export function AssetBacktest({ symbol }: { symbol: string }) {
  const [strategy, setStrategy] = useState<'buy-and-hold' | 'sma-crossover' | 'mean-reversion'>('buy-and-hold');
  const [fast, setFast] = useState(20);
  const [slow, setSlow] = useState(50);
  const [rsiPeriod, setRsiPeriod] = useState(14);
  const [oversold, setOversold] = useState(30);
  const [overbought, setOverbought] = useState(70);
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
    setError(null);
    if (strategy === 'mean-reversion' && oversold >= overbought) {
      setError(new Error('Oversold threshold must be smaller than overbought threshold'));
      return;
    }
    setBusy(true);
    setResult(null);
    try {
      const response = await api.strategy({
        ticker: symbol,
        strategy: strategy as StrategyRequest['strategy'],
        fast, slow, rsi_period: rsiPeriod, oversold, overbought,
        period, days, sims, block_size: blockSize,
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
    <div className="commodity-block">
      <h3>Backtest a strategy</h3>
      <form className="run-form" onSubmit={onSubmit}>
        <fieldset disabled={busy} className="run-form-fields">
          <label>
            Strategy
            <select value={strategy} onChange={(e) => setStrategy(e.target.value as typeof strategy)}>
              <option value="buy-and-hold">buy-and-hold</option>
              <option value="sma-crossover">sma-crossover</option>
              <option value="mean-reversion">mean-reversion</option>
            </select>
          </label>
          {strategy === 'sma-crossover' && (
            <>
              <label>
                Fast SMA
                <input type="number" min={1} value={fast} onChange={(e) => setFast(Number(e.target.value))} />
              </label>
              <label>
                Slow SMA
                <input type="number" min={1} value={slow} onChange={(e) => setSlow(Number(e.target.value))} />
              </label>
            </>
          )}
          {strategy === 'mean-reversion' && (
            <>
              <label>
                RSI period
                <input type="number" min={1} value={rsiPeriod} onChange={(e) => setRsiPeriod(Number(e.target.value))} />
              </label>
              <label>
                Oversold
                <input type="number" min={0} max={100} value={oversold} onChange={(e) => setOversold(Number(e.target.value))} />
              </label>
              <label>
                Overbought
                <input type="number" min={0} max={100} value={overbought} onChange={(e) => setOverbought(Number(e.target.value))} />
              </label>
            </>
          )}
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
            <ExportButtons runId={result.run_id} csvFilename={`strategy_${symbol}_${result.run_id}.csv`} csvRows={result.distribution} />
            <Histogram
              data={result.distribution} xLabel="Total return" referenceValue={0}
              formatValue={(v) => `${(v * 100).toFixed(1)}%`}
            />
          </>
        )}
      </div>
    </div>
  );
}
