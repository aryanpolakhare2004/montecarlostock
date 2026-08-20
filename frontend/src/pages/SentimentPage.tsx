import { useState } from 'react';
import { api, ApiError } from '../api';
import { ErrorBox } from '../components/ErrorBox';
import type { SentimentRequest, SentimentResponse } from '../types';

function fmtScore(v: number): string {
  return v >= 0 ? `+${v.toFixed(3)}` : v.toFixed(3);
}

function directionClass(v: number): string {
  return v >= 0 ? 'direction up' : 'direction down';
}

export function SentimentPage() {
  const [ticker, setTicker] = useState('AAPL');
  const [sourceGroup, setSourceGroup] = useState<NonNullable<SentimentRequest['source_group']>>('all');
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<SentimentResponse | null>(null);
  const [error, setError] = useState<Error | null>(null);

  async function onSubmit(evt: React.FormEvent) {
    evt.preventDefault();
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const response = await api.sentiment({ ticker, source_group: sourceGroup });
      setResult(response);
    } catch (err) {
      setError(err instanceof ApiError ? err : new Error(String(err)));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section>
      <h2>News &amp; social sentiment</h2>
      <p className="hint">
        Scores recent headlines with VADER sentiment analysis, per source and aggregated by day. The same source
        groups used for ML training features (yfinance needs no key; RSS is free; Reddit needs
        <code> REDDIT_CLIENT_ID</code>/<code>REDDIT_CLIENT_SECRET</code>).
      </p>
      <form className="run-form" onSubmit={onSubmit}>
        <label>
          Ticker
          <input value={ticker} onChange={(e) => setTicker(e.target.value)} required placeholder="AAPL" />
        </label>
        <label>
          Sources
          <select
            value={sourceGroup}
            onChange={(e) => setSourceGroup(e.target.value as NonNullable<SentimentRequest['source_group']>)}
          >
            <option value="all">all</option>
            <option value="yfinance">yfinance</option>
            <option value="rss">rss</option>
            <option value="reddit">reddit</option>
          </select>
        </label>
        <button type="submit" disabled={busy}>Analyze</button>
      </form>
      <div className="result">
        {busy && 'Fetching and scoring headlines…'}
        {error && <ErrorBox error={error} />}
        {result && (
          <>
            <div className="stat-tile-row">
              <div className="stat-tile">
                <div className="stat-tile-label">Overall sentiment</div>
                <div className={`stat-tile-value ${result.overall_sentiment != null ? directionClass(result.overall_sentiment) : ''}`}>
                  {result.overall_sentiment != null ? fmtScore(result.overall_sentiment) : 'n/a'}
                </div>
              </div>
              <div className="stat-tile">
                <div className="stat-tile-label">Headlines</div>
                <div className="stat-tile-value">{result.item_count}</div>
              </div>
              <div className="stat-tile">
                <div className="stat-tile-label">Sources</div>
                <div className="stat-tile-value">{result.source_group}</div>
              </div>
            </div>

            {result.item_count === 0 && <p className="hint">No headlines found for this ticker/source combination.</p>}

            {result.daily.length > 0 && (
              <div className="table-scroll">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Date</th><th>Mean</th><th>Count</th><th>% positive</th><th>% negative</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.daily.map((d) => (
                      <tr key={d.date}>
                        <td>{d.date}</td>
                        <td className={directionClass(d.sentiment_mean)}>{fmtScore(d.sentiment_mean)}</td>
                        <td>{d.sentiment_count}</td>
                        <td>{(d.pct_positive * 100).toFixed(0)}%</td>
                        <td>{(d.pct_negative * 100).toFixed(0)}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {result.items.length > 0 && (
              <div className="table-scroll">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Published</th><th>Source</th><th>Score</th><th>Title</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.items.map((item, i) => (
                      <tr key={i}>
                        <td>{new Date(item.published).toLocaleString()}</td>
                        <td>{item.source}</td>
                        <td className={directionClass(item.score)}>{fmtScore(item.score)}</td>
                        <td>{item.title}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}
      </div>
    </section>
  );
}
