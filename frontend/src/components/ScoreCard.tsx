import { fmtMoney, fmtPct, fmtScore } from '../format';
import { TrendLineChart, type FundamentalsTrendRow } from './charts/TrendLineChart';
import type { FundamentalsReport } from '../types';

function EvidenceList({ items }: { items: string[] | undefined }) {
  if (!items || !items.length) return <p className="hint">No evidence available.</p>;
  return (
    <ul className="evidence">
      {items.map((item, i) => (
        <li key={i}>{item}</li>
      ))}
    </ul>
  );
}

export function ScoreCard({ report }: { report: FundamentalsReport }) {
  const s = report.scores;
  const t = report.trends;
  const fv = report.fair_value;

  return (
    <div className="scorecard">
      <h3>
        {report.company_name} ({report.ticker})
      </h3>
      <div className="score-grid">
        <div className="score-tile">
          <div className="score-label">Business quality</div>
          <div className="score-value">{fmtScore(s.business_quality)}</div>
        </div>
        <div className="score-tile">
          <div className="score-label">Financial strength</div>
          <div className="score-value">{fmtScore(s.financial_strength)}</div>
        </div>
        <div className="score-tile">
          <div className="score-label">Growth</div>
          <div className="score-value">{fmtScore(s.growth)}</div>
        </div>
        <div className="score-tile">
          <div className="score-label">Valuation</div>
          <div className="score-value">{fmtScore(s.valuation)}</div>
        </div>
        <div className="score-tile">
          <div className="score-label">Risk</div>
          <div className={`score-value risk-${(s.risk_label || 'unknown').toLowerCase()}`}>
            {s.risk_label || 'n/a'}
          </div>
        </div>
      </div>

      <div className="trend-row">
        <span>
          Revenue trend: <strong>{t.revenue_trend}</strong>
        </span>
        <span>
          Free cash flow: <strong>{t.fcf_status}</strong>
        </span>
        <span>
          Debt position: <strong>{t.debt_position}</strong>
        </span>
        <span>
          Share dilution: <strong>{t.share_dilution}</strong>
        </span>
      </div>

      {report.metrics_history.length > 0 && (
        <TrendLineChart data={report.metrics_history as unknown as FundamentalsTrendRow[]} />
      )}

      <details>
        <summary>Business quality evidence</summary>
        <EvidenceList items={report.evidence.business_quality} />
      </details>
      <details>
        <summary>Growth evidence</summary>
        <EvidenceList items={report.evidence.growth} />
      </details>
      <details>
        <summary>Financial strength evidence</summary>
        <EvidenceList items={report.evidence.financial_strength} />
      </details>
      <details>
        <summary>Valuation evidence</summary>
        <EvidenceList items={report.evidence.valuation} />
      </details>
      <details>
        <summary>Risk evidence</summary>
        <EvidenceList items={report.evidence.risk} />
      </details>

      <div className="case-box bull">
        <strong>Bull case:</strong> {report.bull_case}
      </div>
      <div className="case-box bear">
        <strong>Bear case:</strong> {report.bear_case}
      </div>
      <div className="case-box flags">
        <strong>Major red flags:</strong>
        <ul>
          {report.red_flags.map((flag, i) => (
            <li key={i}>{flag}</li>
          ))}
        </ul>
      </div>

      <p>
        <strong>Estimated fair-value range:</strong>{' '}
        {fv.low != null && fv.high != null ? (
          <>
            {fmtMoney(fv.low)} &ndash; {fmtMoney(fv.high)} (current price {fmtMoney(fv.current_price)}, upside{' '}
            {fmtPct(fv.upside_low_pct)} to {fmtPct(fv.upside_high_pct)})
          </>
        ) : (
          'n/a (insufficient data)'
        )}
      </p>
      <p>
        <strong>Confidence:</strong> {report.confidence}%{' '}
        <span className="hint">&mdash; narrative source: {report.narrative_source}</span>
      </p>
    </div>
  );
}
