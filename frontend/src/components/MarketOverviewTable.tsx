import { Sparkline } from './Sparkline';
import { fmtMoney, fmtPct } from '../format';
import type { MarketAssetQuote } from '../types';

interface Props {
  quotes: MarketAssetQuote[];
  errors: Record<string, string>;
  selectedSymbol: string;
  onSelect: (symbol: string) => void;
}

export function MarketOverviewTable({ quotes, errors, selectedSymbol, onSelect }: Props) {
  return (
    <>
      {quotes.length > 0 && (
        <div className="table-scroll">
          <table className="data-table watchlist-table">
            <thead>
              <tr><th>Name</th><th>Symbol</th><th>Price</th><th>Day change</th><th>30d</th></tr>
            </thead>
            <tbody>
              {quotes.map((q) => (
                <tr
                  key={q.symbol}
                  className={q.symbol === selectedSymbol ? 'selected-row' : undefined}
                  onClick={() => onSelect(q.symbol)}
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
      {Object.keys(errors).length > 0 && (
        <>
          <p className="error">Errors:</p>
          <ul className="error">
            {Object.entries(errors).map(([sym, e]) => <li key={sym}>{sym}: {e}</li>)}
          </ul>
        </>
      )}
    </>
  );
}
