import { useCallback, useEffect, useState } from 'react';
import { api, ApiError } from '../api';
import { ErrorBox } from '../components/ErrorBox';
import { Sparkline } from '../components/Sparkline';
import { fmtPct, fmtScore } from '../format';
import type { WatchlistResponse } from '../types';

export function WatchlistPage() {
  const [data, setData] = useState<WatchlistResponse | null>(null);
  const [loadError, setLoadError] = useState<Error | null>(null);
  const [newTicker, setNewTicker] = useState('');
  const [busy, setBusy] = useState(false);
  const [addError, setAddError] = useState<Error | null>(null);

  const load = useCallback(() => {
    setLoadError(null);
    api.listWatchlist().then(setData).catch(setLoadError);
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function onAdd(evt: React.FormEvent) {
    evt.preventDefault();
    if (!newTicker.trim()) return;
    setBusy(true);
    setAddError(null);
    try {
      await api.addWatchlist(newTicker.trim());
      setNewTicker('');
      load();
    } catch (err) {
      setAddError(err instanceof ApiError ? err : new Error(String(err)));
    } finally {
      setBusy(false);
    }
  }

  async function onRemove(ticker: string) {
    await api.removeWatchlist(ticker);
    load();
  }

  return (
    <section>
      <h2>Watchlist</h2>
      <p className="hint">
        Quick glance across the tickers you follow: last price, day change, a 30-day sparkline, and the same
        quality/growth/financial-strength/valuation scorecard as the Analyst tab (computed from cached SEC data,
        so repeat visits load fast).
      </p>

      <form className="run-form" onSubmit={onAdd}>
        <label>
          Add ticker
          <input value={newTicker} onChange={(e) => setNewTicker(e.target.value)} placeholder="AAPL" />
        </label>
        <button type="submit" disabled={busy}>Add</button>
      </form>
      {addError && <ErrorBox error={addError} />}

      <div className="result">
        {loadError && <ErrorBox error={loadError} />}
        {!loadError && data === null && <p>Loading…</p>}
        {!loadError && data && data.tickers.length === 0 && <p className="hint">No tickers yet -- add one above.</p>}
        {!loadError && data && data.tickers.length > 0 && (
          <div className="table-scroll">
            <table className="data-table watchlist-table">
              <thead>
                <tr>
                  <th>Ticker</th><th>Company</th><th>Price</th><th>Day change</th><th>30d</th>
                  <th>Quality</th><th>Growth</th><th>Fin. strength</th><th>Valuation</th><th>Risk</th><th></th>
                </tr>
              </thead>
              <tbody>
                {data.tickers.map((row) => (
                  <tr key={row.ticker}>
                    <td>{row.ticker}</td>
                    <td>{row.company_name}</td>
                    <td>${row.last_price.toFixed(2)}</td>
                    <td className={row.day_change_pct != null && row.day_change_pct >= 0 ? 'direction up' : 'direction down'}>
                      {fmtPct(row.day_change_pct)}
                    </td>
                    <td>
                      <Sparkline
                        values={row.sparkline}
                        positive={row.sparkline.length > 1 && row.sparkline[row.sparkline.length - 1] >= row.sparkline[0]}
                      />
                    </td>
                    <td>{fmtScore(row.scores.business_quality)}</td>
                    <td>{fmtScore(row.scores.growth)}</td>
                    <td>{fmtScore(row.scores.financial_strength)}</td>
                    <td>{fmtScore(row.scores.valuation)}</td>
                    <td>{row.scores.risk_label}</td>
                    <td>
                      <button type="button" className="refresh-btn" onClick={() => onRemove(row.ticker)}>
                        remove
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {data && Object.keys(data.errors).length > 0 && (
          <>
            <p className="error">Errors:</p>
            <ul className="error">
              {Object.entries(data.errors).map(([t, e]) => (
                <li key={t}>
                  {t}: {e}
                </li>
              ))}
            </ul>
          </>
        )}
      </div>
    </section>
  );
}
