import { useState } from 'react';
import { api, ApiError } from '../api';
import { StatTable } from '../components/StatTable';
import { ErrorBox } from '../components/ErrorBox';
import { ExportButtons } from '../components/ExportButtons';
import { SubmitButton } from '../components/SubmitButton';
import { useToast } from '../components/toast';
import { FanChart } from '../components/charts/FanChart';
import { fmtPct } from '../format';
import type { PortfolioCorrelationResponse, PortfolioOptimizeRequest, PortfolioResponse } from '../types';

function corrClass(v: number): string {
  if (v <= -0.5) return 'corr-strong-neg';
  if (v <= -0.1) return 'corr-weak-neg';
  if (v < 0.1) return 'corr-neutral';
  if (v < 0.5) return 'corr-weak-pos';
  return 'corr-strong-pos';
}

export function PortfolioPage() {
  const [tickers, setTickers] = useState('AAPL,MSFT,GOOG');
  const [weights, setWeights] = useState('');
  const [objective, setObjective] = useState<PortfolioOptimizeRequest['objective']>('max_sharpe');
  const [riskFreeRate, setRiskFreeRate] = useState(0);
  const [optimizing, setOptimizing] = useState(false);
  const [correlating, setCorrelating] = useState(false);
  const [correlation, setCorrelation] = useState<PortfolioCorrelationResponse | null>(null);
  const [value, setValue] = useState(10000);
  const [period, setPeriod] = useState('5y');
  const [days, setDays] = useState(252);
  const [sims, setSims] = useState(5000);
  const [seed, setSeed] = useState('');
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<PortfolioResponse | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const { showToast } = useToast();

  function parsedTickers(): string[] {
    return tickers.split(',').map((t) => t.trim()).filter(Boolean);
  }

  async function onOptimize() {
    const tickerList = parsedTickers();
    if (tickerList.length < 2) {
      showToast('Enter at least two tickers to optimize weights', 'error');
      return;
    }
    setOptimizing(true);
    try {
      const response = await api.optimizePortfolio({
        tickers: tickerList,
        period,
        objective,
        risk_free_rate: riskFreeRate,
      });
      setWeights(tickerList.map((t) => response.weights[t].toFixed(3)).join(','));
      const sharpeText = response.sharpe_ratio != null ? response.sharpe_ratio.toFixed(2) : 'n/a';
      showToast(
        `Optimized: expected return ${fmtPct(response.expected_return)}, ` +
          `volatility ${fmtPct(response.expected_volatility)}, Sharpe ${sharpeText}`,
        'success',
      );
    } catch (err) {
      const errorObj = err instanceof ApiError ? err : new Error(String(err));
      showToast(`Optimization failed: ${errorObj.message}`, 'error');
    } finally {
      setOptimizing(false);
    }
  }

  async function onCorrelate() {
    const tickerList = parsedTickers();
    if (tickerList.length < 2) {
      showToast('Enter at least two tickers to show correlation', 'error');
      return;
    }
    setCorrelating(true);
    try {
      const response = await api.portfolioCorrelation({ tickers: tickerList, period });
      setCorrelation(response);
    } catch (err) {
      const errorObj = err instanceof ApiError ? err : new Error(String(err));
      showToast(`Correlation failed: ${errorObj.message}`, 'error');
    } finally {
      setCorrelating(false);
    }
  }

  async function onSubmit(evt: React.FormEvent) {
    evt.preventDefault();
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const tickerList = parsedTickers();
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
        <fieldset disabled={busy} className="run-form-fields">
          <label>
            Tickers (comma-separated)
            <input value={tickers} onChange={(e) => setTickers(e.target.value)} required placeholder="AAPL,MSFT,GOOG" />
          </label>
          <label>
            Weights (comma-separated, optional)
            <input value={weights} onChange={(e) => setWeights(e.target.value)} placeholder="0.5,0.3,0.2" />
          </label>
          <label>
            Optimize for
            <select
              value={objective}
              onChange={(e) => setObjective(e.target.value as PortfolioOptimizeRequest['objective'])}
            >
              <option value="max_sharpe">max Sharpe ratio</option>
              <option value="min_variance">min variance</option>
            </select>
          </label>
          <label>
            Risk-free rate
            <input
              type="number" step={0.01} value={riskFreeRate}
              onChange={(e) => setRiskFreeRate(Number(e.target.value))}
            />
          </label>
          <button type="button" className="refresh-btn" onClick={onOptimize} disabled={optimizing}>
            {optimizing ? 'Optimizing…' : 'Optimize weights'}
          </button>
          <button type="button" className="refresh-btn" onClick={onCorrelate} disabled={correlating}>
            {correlating ? 'Loading…' : 'Show correlation'}
          </button>
          <label>
            Starting value
            <input type="number" min={0} value={value} onChange={(e) => setValue(Number(e.target.value))} />
          </label>
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
      {correlation && (
        <div className="table-scroll">
          <table className="data-table corr-table">
            <thead>
              <tr><th></th>{correlation.tickers.map((t) => <th key={t}>{t}</th>)}</tr>
            </thead>
            <tbody>
              {correlation.tickers.map((rowTicker, i) => (
                <tr key={rowTicker}>
                  <th>{rowTicker}</th>
                  {correlation.tickers.map((colTicker, j) => (
                    <td key={colTicker} className={i === j ? 'corr-diagonal' : corrClass(correlation.matrix[i][j])}>
                      {correlation.matrix[i][j].toFixed(2)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <div className="result">
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
