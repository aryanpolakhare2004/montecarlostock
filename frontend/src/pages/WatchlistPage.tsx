import { useCallback, useEffect, useRef, useState } from 'react';
import { api, ApiError } from '../api';
import { ErrorBox } from '../components/ErrorBox';
import { Sparkline } from '../components/Sparkline';
import { SubmitButton } from '../components/SubmitButton';
import { useToast } from '../components/toast';
import { fmtMoney, fmtPct, fmtScore } from '../format';
import { parseCsvTickerColumn, parseTickerListText } from '../utils/tickers';
import type { Alert, WatchlistResponse } from '../types';

const ALERT_POLL_MS = 60_000;

export function WatchlistPage() {
  const [data, setData] = useState<WatchlistResponse | null>(null);
  const [loadError, setLoadError] = useState<Error | null>(null);
  const [newTicker, setNewTicker] = useState('');
  const [busy, setBusy] = useState(false);
  const [addError, setAddError] = useState<Error | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [alertFormTicker, setAlertFormTicker] = useState<string | null>(null);
  const [alertMetric, setAlertMetric] = useState<Alert['metric']>('price');
  const [alertOperator, setAlertOperator] = useState<Alert['operator']>('above');
  const [alertThreshold, setAlertThreshold] = useState('');
  const [bulkText, setBulkText] = useState('');
  const [importing, setImporting] = useState(false);
  const seenTriggeredIds = useRef<Set<number>>(new Set());
  const alertsInitialized = useRef(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { showToast } = useToast();

  const load = useCallback(() => {
    setLoadError(null);
    api.listWatchlist().then(setData).catch(setLoadError);
  }, []);

  const loadAlerts = useCallback(() => {
    api
      .listAlerts()
      .then((next) => {
        for (const alert of next) {
          if (alert.triggered_at) {
            if (!seenTriggeredIds.current.has(alert.id) && alertsInitialized.current) {
              showToast(`${alert.ticker}: ${alert.metric} ${alert.operator} ${alert.threshold} triggered`, 'info');
            }
            seenTriggeredIds.current.add(alert.id);
          }
        }
        alertsInitialized.current = true;
        setAlerts(next);
      })
      .catch(() => {});
  }, [showToast]);

  useEffect(() => {
    load();
    loadAlerts();
    const interval = setInterval(loadAlerts, ALERT_POLL_MS);
    return () => clearInterval(interval);
  }, [load, loadAlerts]);

  async function onAdd(evt: React.FormEvent) {
    evt.preventDefault();
    if (!newTicker.trim()) return;
    setBusy(true);
    setAddError(null);
    try {
      const added = await api.addWatchlist(newTicker.trim());
      setNewTicker('');
      load();
      showToast(`Added ${added.ticker} to watchlist`, 'success');
    } catch (err) {
      const error = err instanceof ApiError ? err : new Error(String(err));
      setAddError(error);
      showToast(`Couldn't add ${newTicker.trim().toUpperCase()}: ${error.message}`, 'error');
    } finally {
      setBusy(false);
    }
  }

  function onFileSelected(evt: React.ChangeEvent<HTMLInputElement>) {
    const file = evt.target.files?.[0];
    evt.target.value = '';
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      const content = typeof reader.result === 'string' ? reader.result : '';
      const csvTickers = parseCsvTickerColumn(content);
      if (csvTickers.length === 0) {
        showToast('No tickers found in that file', 'error');
        return;
      }
      setBulkText((prev) => {
        const existing = prev.trim();
        return existing ? `${existing}, ${csvTickers.join(', ')}` : csvTickers.join(', ');
      });
    };
    reader.readAsText(file);
  }

  async function onImport() {
    const tickerList = parseTickerListText(bulkText);
    if (tickerList.length === 0) {
      showToast('No valid tickers found to import', 'error');
      return;
    }
    setImporting(true);
    try {
      const response = await api.bulkAddWatchlist(tickerList);
      setBulkText('');
      load();
      const failCount = Object.keys(response.errors).length;
      const message = failCount > 0
        ? `Imported ${response.added.length} tickers, ${failCount} failed (${Object.keys(response.errors).join(', ')})`
        : `Imported ${response.added.length} tickers`;
      showToast(message, failCount > 0 ? 'info' : 'success');
    } catch (err) {
      const error = err instanceof ApiError ? err : new Error(String(err));
      showToast(`Import failed: ${error.message}`, 'error');
    } finally {
      setImporting(false);
    }
  }

  async function onRemove(ticker: string) {
    await api.removeWatchlist(ticker);
    load();
    showToast(`Removed ${ticker} from watchlist`, 'info');
  }

  function alertsFor(ticker: string): Alert[] {
    return alerts.filter((a) => a.ticker === ticker);
  }

  function openAlertForm(ticker: string) {
    setAlertFormTicker(ticker);
    setAlertMetric('price');
    setAlertOperator('above');
    setAlertThreshold('');
  }

  async function onAddAlert(evt: React.FormEvent, ticker: string) {
    evt.preventDefault();
    if (!alertThreshold.trim()) return;
    try {
      await api.addAlert({
        ticker,
        metric: alertMetric,
        operator: alertOperator,
        threshold: Number(alertThreshold),
      });
      setAlertFormTicker(null);
      loadAlerts();
      showToast(`Alert added for ${ticker}`, 'success');
    } catch (err) {
      const error = err instanceof ApiError ? err : new Error(String(err));
      showToast(`Couldn't add alert: ${error.message}`, 'error');
    }
  }

  async function onRemoveAlert(id: number) {
    await api.removeAlert(id);
    loadAlerts();
  }

  return (
    <section>
      <h2>Watchlist</h2>
      <p className="hint">
        Quick glance across the tickers you follow: last price, day change, a 30-day sparkline, the same
        quality/growth/financial-strength/valuation scorecard as the Analyst tab (computed from cached SEC data,
        so repeat visits load fast), and price/volatility alerts checked in the background.
      </p>

      <form className="run-form" onSubmit={onAdd}>
        <fieldset disabled={busy} className="run-form-fields">
          <label>
            Add ticker
            <input value={newTicker} onChange={(e) => setNewTicker(e.target.value)} placeholder="AAPL" />
          </label>
          <SubmitButton busy={busy}>Add</SubmitButton>
        </fieldset>
      </form>
      {addError && <ErrorBox error={addError} />}

      <details className="advanced-fields">
        <summary>Bulk import (paste or upload CSV)</summary>
        <div className="advanced-fields-grid bulk-import">
          <textarea
            className="bulk-import-textarea"
            value={bulkText}
            onChange={(e) => setBulkText(e.target.value)}
            placeholder={'Paste tickers separated by commas or one per line -- CSV works too (first column is used)\nAAPL, MSFT, GOOG'}
            rows={5}
          />
          <div className="bulk-import-actions">
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv,text/csv"
              onChange={onFileSelected}
              style={{ display: 'none' }}
            />
            <button type="button" className="refresh-btn" onClick={() => fileInputRef.current?.click()}>
              Upload CSV
            </button>
            <button type="button" className="refresh-btn" onClick={onImport} disabled={importing}>
              {importing ? 'Importing…' : 'Import'}
            </button>
          </div>
        </div>
      </details>

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
                  <th>Quality</th><th>Growth</th><th>Fin. strength</th><th>Valuation</th><th>Risk</th>
                  <th>Alerts</th><th></th>
                </tr>
              </thead>
              <tbody>
                {data.tickers.map((row) => (
                  <tr key={row.ticker}>
                    <td>{row.ticker}</td>
                    <td>{row.company_name}</td>
                    <td>{fmtMoney(row.last_price)}</td>
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
                      <div className="alert-cell">
                        {alertsFor(row.ticker).map((a) => (
                          <span key={a.id} className={`alert-chip${a.triggered_at ? ' triggered' : ''}`}>
                            {a.metric} {a.operator === 'above' ? '>' : '<'} {a.threshold}
                            <button type="button" onClick={() => onRemoveAlert(a.id)} aria-label="Remove alert">×</button>
                          </span>
                        ))}
                        {alertFormTicker === row.ticker ? (
                          <form className="alert-form" onSubmit={(e) => onAddAlert(e, row.ticker)}>
                            <select value={alertMetric} onChange={(e) => setAlertMetric(e.target.value as Alert['metric'])}>
                              <option value="price">Price</option>
                              <option value="volatility">Volatility</option>
                            </select>
                            <select value={alertOperator} onChange={(e) => setAlertOperator(e.target.value as Alert['operator'])}>
                              <option value="above">above</option>
                              <option value="below">below</option>
                            </select>
                            <input
                              type="number"
                              step="any"
                              value={alertThreshold}
                              onChange={(e) => setAlertThreshold(e.target.value)}
                              placeholder="threshold"
                              required
                            />
                            <button type="submit">Add</button>
                            <button type="button" onClick={() => setAlertFormTicker(null)}>Cancel</button>
                          </form>
                        ) : (
                          <button type="button" className="refresh-btn" onClick={() => openAlertForm(row.ticker)}>+ alert</button>
                        )}
                      </div>
                    </td>
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
