import { useEffect, useState } from 'react';
import { api } from '../api';
import { ErrorBox } from '../components/ErrorBox';
import { MarketOverviewTable } from '../components/MarketOverviewTable';
import { AssetSimulate } from '../components/AssetSimulate';
import { AssetBacktest } from '../components/AssetBacktest';
import type { MarketAsset, MarketAssetQuote } from '../types';

export function ForexPage() {
  const [forexList, setForexList] = useState<MarketAsset[] | null>(null);
  const [quotes, setQuotes] = useState<MarketAssetQuote[] | null>(null);
  const [quoteErrors, setQuoteErrors] = useState<Record<string, string>>({});
  const [loadError, setLoadError] = useState<Error | null>(null);
  const [symbol, setSymbol] = useState('');

  useEffect(() => {
    api.listForex().then((r) => {
      setForexList(r.forex);
      if (r.forex.length > 0) setSymbol(r.forex[0].symbol);
    }).catch(setLoadError);
    api.forexQuotes().then((r) => {
      setQuotes(r.quotes);
      setQuoteErrors(r.errors);
    }).catch(setLoadError);
  }, []);

  return (
    <section>
      <h2>Forex</h2>
      <p className="hint">
        A curated set of major currency pairs via the same Monte Carlo price simulation and strategy backtest used
        for stocks. No fundamentals data here -- currency pairs aren't companies.
      </p>

      {loadError && <ErrorBox error={loadError} />}
      {!loadError && quotes === null && <p>Loading…</p>}
      {!loadError && quotes && (
        <MarketOverviewTable quotes={quotes} errors={quoteErrors} selectedSymbol={symbol} onSelect={setSymbol} />
      )}

      {forexList && forexList.length > 0 && (
        <>
          <label className="commodity-select-label">
            Currency pair
            <select value={symbol} onChange={(e) => setSymbol(e.target.value)}>
              {forexList.map((c) => (
                <option key={c.symbol} value={c.symbol}>{c.name} ({c.symbol})</option>
              ))}
            </select>
          </label>

          <AssetSimulate symbol={symbol} />
          <AssetBacktest symbol={symbol} />
        </>
      )}
    </section>
  );
}
