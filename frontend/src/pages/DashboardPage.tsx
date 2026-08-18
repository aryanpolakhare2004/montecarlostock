import { useEffect, useState } from 'react';
import { api } from '../api';
import { Sparkline } from '../components/Sparkline';
import { fmtPct, fmtScore } from '../format';
import type { ModelRecord, RunRecord, WatchlistEntry } from '../types';
import type { TabId } from '../App';

interface Props {
  onNavigate: (tab: TabId) => void;
}

export function DashboardPage({ onNavigate }: Props) {
  const [watchlist, setWatchlist] = useState<WatchlistEntry[] | null>(null);
  const [runs, setRuns] = useState<RunRecord[] | null>(null);
  const [models, setModels] = useState<ModelRecord[] | null>(null);

  useEffect(() => {
    api.listWatchlist().then((r) => setWatchlist(r.tickers)).catch(() => setWatchlist([]));
    api.listRuns(500).then(setRuns).catch(() => setRuns([]));
    api.listModels().then(setModels).catch(() => setModels([]));
  }, []);

  return (
    <section>
      <h2>Dashboard</h2>
      <p className="hint">Everything at a glance -- jump to a tool below, or check the watchlist for what moved.</p>

      <div className="stat-tile-row">
        <div className="stat-tile">
          <div className="stat-tile-label">Watchlist</div>
          <div className="stat-tile-value">{watchlist === null ? '…' : watchlist.length}</div>
        </div>
        <div className="stat-tile">
          <div className="stat-tile-label">Simulation runs</div>
          <div className="stat-tile-value">{runs === null ? '…' : runs.length}</div>
        </div>
        <div className="stat-tile">
          <div className="stat-tile-label">Trained models</div>
          <div className="stat-tile-value">{models === null ? '…' : models.length}</div>
        </div>
      </div>

      <div className="quick-actions">
        <button type="button" onClick={() => onNavigate('analyst')}>Analyze a company</button>
        <button type="button" onClick={() => onNavigate('terminal')}>Open terminal</button>
        <button type="button" onClick={() => onNavigate('watchlist')}>Manage watchlist</button>
        <button type="button" onClick={() => onNavigate('price')}>Simulate a price</button>
      </div>

      <h3>Watchlist</h3>
      {watchlist === null && <p>Loading…</p>}
      {watchlist !== null && watchlist.length === 0 && (
        <p className="hint">
          Nothing saved yet -- add a ticker from the{' '}
          <a onClick={() => onNavigate('watchlist')} role="button" tabIndex={0}>
            Watchlist tab
          </a>
          .
        </p>
      )}
      {watchlist !== null && watchlist.length > 0 && (
        <div className="table-scroll">
          <table className="data-table watchlist-table">
            <thead>
              <tr><th>Ticker</th><th>Price</th><th>Day change</th><th>30d</th><th>Quality</th><th>Risk</th></tr>
            </thead>
            <tbody>
              {watchlist.map((row) => (
                <tr key={row.ticker}>
                  <td>{row.ticker}</td>
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
                  <td>{row.scores.risk_label}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
