import { useEffect, useState } from 'react';
import { api } from '../api';
import { ErrorBox } from '../components/ErrorBox';
import { MarketOverviewTable } from '../components/MarketOverviewTable';
import { AssetSimulate } from '../components/AssetSimulate';
import { AssetBacktest } from '../components/AssetBacktest';
import type { MarketAsset, MarketAssetQuote } from '../types';

export function CryptoPage() {
  const [cryptoList, setCryptoList] = useState<MarketAsset[] | null>(null);
  const [quotes, setQuotes] = useState<MarketAssetQuote[] | null>(null);
  const [quoteErrors, setQuoteErrors] = useState<Record<string, string>>({});
  const [loadError, setLoadError] = useState<Error | null>(null);
  const [symbol, setSymbol] = useState('');

  useEffect(() => {
    api.listCrypto().then((r) => {
      setCryptoList(r.crypto);
      if (r.crypto.length > 0) setSymbol(r.crypto[0].symbol);
    }).catch(setLoadError);
    api.cryptoQuotes().then((r) => {
      setQuotes(r.quotes);
      setQuoteErrors(r.errors);
    }).catch(setLoadError);
  }, []);

  return (
    <section>
      <h2>Crypto</h2>
      <p className="hint">
        A curated set of cryptocurrencies via the same Monte Carlo price simulation and strategy backtest used for
        stocks. No fundamentals data here -- these aren't companies.
      </p>

      {loadError && <ErrorBox error={loadError} />}
      {!loadError && quotes === null && <p>Loading…</p>}
      {!loadError && quotes && (
        <MarketOverviewTable quotes={quotes} errors={quoteErrors} selectedSymbol={symbol} onSelect={setSymbol} />
      )}

      {cryptoList && cryptoList.length > 0 && (
        <>
          <label className="commodity-select-label">
            Crypto asset
            <select value={symbol} onChange={(e) => setSymbol(e.target.value)}>
              {cryptoList.map((c) => (
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
