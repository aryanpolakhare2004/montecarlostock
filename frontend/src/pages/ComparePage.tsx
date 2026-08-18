import { useState } from 'react';
import { api, ApiError } from '../api';
import { ErrorBox } from '../components/ErrorBox';
import { ExportButtons } from '../components/ExportButtons';
import { CategoricalBarChart } from '../components/charts/CategoricalBarChart';
import type { useModels } from '../hooks/useModels';
import type { CompareResponse } from '../types';

type ModelOptions = ReturnType<typeof useModels>;

export function ComparePage({ modelOptions }: { modelOptions: ModelOptions }) {
  const [ticker, setTicker] = useState('AAPL');
  const [period, setPeriod] = useState('5y');
  const [days, setDays] = useState(252);
  const [sims, setSims] = useState(5000);
  const [blockSize, setBlockSize] = useState(5);
  const [fast, setFast] = useState(20);
  const [slow, setSlow] = useState(50);
  const [seed, setSeed] = useState('');
  const [modelIds, setModelIds] = useState<number[]>([]);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<CompareResponse | null>(null);
  const [error, setError] = useState<Error | null>(null);

  function onModelIdsChange(evt: React.ChangeEvent<HTMLSelectElement>) {
    const ids = Array.from(evt.target.selectedOptions).map((opt) => Number(opt.value));
    setModelIds(ids);
  }

  async function onSubmit(evt: React.FormEvent) {
    evt.preventDefault();
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const response = await api.compare({
        ticker,
        period,
        days,
        sims,
        block_size: blockSize,
        fast,
        slow,
        seed: seed === '' ? null : Number(seed),
        model_ids: modelIds,
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
      <h2>Compare algorithms on one stock</h2>
      <p className="hint">
        Runs buy-and-hold, sma-crossover, and any trained <code>ml-technical</code>-eligible models
        (technical-only: sentiment none, volume unchecked) on the <em>same</em> resampled price paths, so the
        ranking reflects strategy skill, not lucky scenarios.
      </p>
      <form className="run-form" onSubmit={onSubmit}>
        <label>
          Ticker
          <input value={ticker} onChange={(e) => setTicker(e.target.value)} required placeholder="AAPL" />
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
          Block size
          <input type="number" value={blockSize} onChange={(e) => setBlockSize(Number(e.target.value))} />
        </label>
        <label>
          Fast SMA
          <input type="number" value={fast} onChange={(e) => setFast(Number(e.target.value))} />
        </label>
        <label>
          Slow SMA
          <input type="number" value={slow} onChange={(e) => setSlow(Number(e.target.value))} />
        </label>
        <label>
          Seed
          <input value={seed} onChange={(e) => setSeed(e.target.value)} placeholder="optional" />
        </label>
        <label>
          Include ML models
          <select multiple size={4} value={modelIds.map(String)} onChange={onModelIdsChange}>
            {modelOptions.technicalOnly.map((m) => (
              <option key={m.id} value={m.id}>
                #{m.id} {m.ticker} {m.model_type} (test acc {m.test_accuracy.toFixed(2)})
              </option>
            ))}
          </select>
        </label>
        <button type="submit" disabled={busy}>Compare</button>
      </form>
      <div className="result">
        {busy && 'Running…'}
        {error && <ErrorBox error={error} />}
        {result && (
          <>
            <ExportButtons
              runId={result.run_id}
              csvFilename={`compare_${ticker}_${result.run_id}.csv`}
              csvRows={result.ranking.map((name, i) => ({ rank: i + 1, strategy: name, ...result.results[name] }))}
            />
            <div className="table-scroll">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Rank</th><th>Strategy</th><th>Mean return</th><th>Std return</th>
                    <th>Prob profit</th><th>Mean max drawdown</th>
                  </tr>
                </thead>
                <tbody>
                  {result.ranking.map((name, i) => {
                    const s = result.results[name];
                    return (
                      <tr key={name}>
                        <td>{i + 1}</td>
                        <td>{name}</td>
                        <td>{s.mean_return.toFixed(4)}</td>
                        <td>{s.std_return.toFixed(4)}</td>
                        <td>{s.prob_profit.toFixed(3)}</td>
                        <td>{s.mean_max_drawdown.toFixed(4)}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            <CategoricalBarChart
              yLabel="Mean return"
              formatValue={(v) => `${(v * 100).toFixed(1)}%`}
              data={result.ranking.map((name) => {
                const s = result.results[name];
                return {
                  name,
                  value: s.mean_return,
                  extra: [
                    { label: 'std return', value: s.std_return.toFixed(4) },
                    { label: 'prob profit', value: s.prob_profit.toFixed(3) },
                    { label: 'mean max drawdown', value: s.mean_max_drawdown.toFixed(4) },
                  ],
                };
              })}
            />
          </>
        )}
      </div>
    </section>
  );
}
