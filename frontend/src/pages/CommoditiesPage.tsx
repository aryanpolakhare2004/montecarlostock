import { useEffect, useState } from 'react';
import { api, ApiError } from '../api';
import { StatTable } from '../components/StatTable';
import { ErrorBox } from '../components/ErrorBox';
import { ExportButtons } from '../components/ExportButtons';
import { SubmitButton } from '../components/SubmitButton';
import { Sparkline } from '../components/Sparkline';
import { FanChart } from '../components/charts/FanChart';
import { Histogram } from '../components/charts/Histogram';
import { fmtMoney, fmtPct } from '../format';
import type { Commodity, CommodityQuote, PriceResponse, StrategyRequest, StrategyResponse } from '../types';

export function CommoditiesPage() {
  const [commodityList, setCommodityList] = useState<Commodity[] | null>(null);
  const [quotes, setQuotes] = useState<CommodityQuote[] | null>(null);
  const [quoteErrors, setQuoteErrors] = useState<Record<string, string>>({});
  const [loadError, setLoadError] = useState<Error | null>(null);
  const [symbol, setSymbol] = useState('');

  useEffect(() => {
    api.listCommodities().then((r) => {
      setCommodityList(r.commodities);
      if (r.commodities.length > 0) setSymbol(r.commodities[0].symbol);
    }).catch(setLoadError);
    api.commodityQuotes().then((r) => {
      setQuotes(r.quotes);
      setQuoteErrors(r.errors);
    }).catch(setLoadError);
  }, []);

  return (
    <section>
      <h2>Commodities</h2>
      <p className="hint">
        A curated set of commodity futures (metals, energy, agriculture) via the same Monte Carlo price simulation
        and strategy backtest used for stocks. No fundamentals data here -- futures don't have SEC filings.
      </p>

      {loadError && <ErrorBox error={loadError} />}
      {!loadError && quotes === null && <p>Loading…</p>}
      {!loadError && quotes && quotes.length > 0 && (
        <div className="table-scroll">
          <table className="data-table watchlist-table">
            <thead>
              <tr><th>Name</th><th>Symbol</th><th>Price</th><th>Day change</th><th>30d</th></tr>
            </thead>
            <tbody>
              {quotes.map((q) => (
                <tr
                  key={q.symbol}
                  className={q.symbol === symbol ? 'selected-row' : undefined}
                  onClick={() => setSymbol(q.symbol)}
                  style={{ cursor: 'pointer' }}
                >
                  <td>{q.name}</td>
                  <td>{q.symbol}</td>
                  <td>{fmtMoney(q.last_price)}</td>
                  <td className={q.day_change_pct != null && q.day_change_pct >= 0 ? 'direction up' : 'direction down'}>
                    {fmtPct(q.day_change_pct)}
                  </td>
                  <td>
                    <Sparkline
                      values={q.sparkline}
                      positive={q.sparkline.length > 1 && q.sparkline[q.sparkline.length - 1] >= q.sparkline[0]}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {Object.keys(quoteErrors).length > 0 && (
        <>
          <p className="error">Errors:</p>
          <ul className="error">
            {Object.entries(quoteErrors).map(([sym, e]) => <li key={sym}>{sym}: {e}</li>)}
          </ul>
        </>
      )}

      {commodityList && commodityList.length > 0 && (
        <>
          <label className="commodity-select-label">
            Commodity
            <select value={symbol} onChange={(e) => setSymbol(e.target.value)}>
              {commodityList.map((c) => (
                <option key={c.symbol} value={c.symbol}>{c.name} ({c.symbol})</option>
              ))}
            </select>
          </label>

          <CommoditySimulate symbol={symbol} />
          <CommodityBacktest symbol={symbol} />
        </>
      )}
    </section>
  );
}

function CommoditySimulate({ symbol }: { symbol: string }) {
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
            <ExportButtons runId={result.run_id} csvFilename={`commodity_${symbol}_${result.run_id}.csv`} csvRows={result.bands} />
            <FanChart data={result.bands} yLabel="Price" />
            <Histogram data={result.distribution} xLabel="Final price" referenceValue={result.s0} />
          </>
        )}
      </div>
    </div>
  );
}

function CommodityBacktest({ symbol }: { symbol: string }) {
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
            <ExportButtons runId={result.run_id} csvFilename={`commodity_strategy_${symbol}_${result.run_id}.csv`} csvRows={result.distribution} />
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
