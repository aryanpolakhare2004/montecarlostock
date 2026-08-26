const TICKER_SHAPE = /^[A-Z][A-Z0-9.\-]{0,9}$/;
const HEADER_WORDS = new Set(['TICKER', 'SYMBOL']);

function isValidTicker(token: string): boolean {
  return TICKER_SHAPE.test(token) && !HEADER_WORDS.has(token);
}

/** Parses a free-form paste: tickers separated by commas, whitespace, and/or newlines. */
export function parseTickerListText(text: string): string[] {
  const seen = new Set<string>();
  const tickers: string[] = [];
  for (const rawToken of text.split(/[,\s]+/)) {
    const token = rawToken.trim().toUpperCase();
    if (!token || !isValidTicker(token)) continue;
    if (seen.has(token)) continue;
    seen.add(token);
    tickers.push(token);
  }
  return tickers;
}

/** Parses raw CSV text, taking only the first column of each row (e.g. "AAPL,Apple Inc,..."). */
export function parseCsvTickerColumn(text: string): string[] {
  const seen = new Set<string>();
  const tickers: string[] = [];
  for (const rawLine of text.split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line) continue;
    const firstField = line.split(',')[0].trim().toUpperCase();
    if (!firstField || !isValidTicker(firstField)) continue;
    if (seen.has(firstField)) continue;
    seen.add(firstField);
    tickers.push(firstField);
  }
  return tickers;
}
