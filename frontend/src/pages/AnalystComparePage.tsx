import { useState } from 'react';
import { api, ApiError } from '../api';
import { ErrorBox } from '../components/ErrorBox';
import { SubmitButton } from '../components/SubmitButton';
import { fmtScore } from '../format';
import type { FundamentalsCompareResponse } from '../types';

export function AnalystComparePage() {
  const [tickers, setTickers] = useState('MU,WDC,STX');
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<FundamentalsCompareResponse | null>(null);
  const [error, setError] = useState<Error | null>(null);

  async function onSubmit(evt: React.FormEvent) {
    evt.preventDefault();
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const tickerList = tickers.split(',').map((t) => t.trim()).filter(Boolean);
      const response = await api.fundamentalsCompare({ tickers: tickerList });
      setResult(response);
    } catch (err) {
      setError(err instanceof ApiError ? err : new Error(String(err)));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section>
      <h2>Compare companies</h2>
      <p className="hint">
        e.g. Micron vs Western Digital vs Seagate &mdash; ranked by a simple composite of quality, growth, financial
        strength, and valuation, minus a risk penalty.
      </p>
      <form className="run-form" onSubmit={onSubmit}>
        <fieldset disabled={busy} className="run-form-fields">
          <label>
            Tickers (comma-separated)
            <input value={tickers} onChange={(e) => setTickers(e.target.value)} required placeholder="MU,WDC,STX" />
          </label>
          <SubmitButton busy={busy} busyLabel="Analyzing…">Compare</SubmitButton>
        </fieldset>
      </form>
      <div className="result">
        {error && <ErrorBox error={error} />}
        {result && (
          <>
            <div className="table-scroll">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Rank</th><th>Ticker</th><th>Company</th><th>Composite</th><th>Quality</th>
                    <th>Growth</th><th>Fin. strength</th><th>Valuation</th><th>Risk</th>
                    <th>Revenue</th><th>FCF</th><th>Debt</th><th>Confidence</th>
                  </tr>
                </thead>
                <tbody>
                  {result.rows.map((r, i) => (
                    <tr key={r.ticker}>
                      <td>{i + 1}</td>
                      <td>{r.ticker}</td>
                      <td>{r.company_name}</td>
                      <td>{fmtScore(r.composite)}</td>
                      <td>{fmtScore(r.business_quality)}</td>
                      <td>{fmtScore(r.growth)}</td>
                      <td>{fmtScore(r.financial_strength)}</td>
                      <td>{fmtScore(r.valuation)}</td>
                      <td>{r.risk_label || 'n/a'}</td>
                      <td>{r.revenue_trend}</td>
                      <td>{r.fcf_status}</td>
                      <td>{r.debt_position}</td>
                      <td>{r.confidence}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {Object.keys(result.errors).length > 0 && (
              <>
                <p className="error">Errors:</p>
                <ul className="error">
                  {Object.entries(result.errors).map(([t, e]) => (
                    <li key={t}>
                      {t}: {e}
                    </li>
                  ))}
                </ul>
              </>
            )}
          </>
        )}
      </div>
    </section>
  );
}
