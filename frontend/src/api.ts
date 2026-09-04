import type {
  Alert, AlertCreateRequest,
  BacktestMlRequest, BacktestMlResponse,
  CommoditiesListResponse, CommoditiesQuotesResponse,
  CompareRequest, CompareResponse,
  CryptoListResponse, CryptoQuotesResponse,
  EquitiesListResponse, EquitiesQuotesResponse, EquitySuggestionsResponse,
  ForexListResponse, ForexQuotesResponse,
  FundamentalsCompareRequest, FundamentalsCompareResponse,
  FundamentalsRequest, FundamentalsReport,
  ModelRecord,
  PortfolioCorrelationRequest, PortfolioCorrelationResponse,
  PortfolioOptimizeRequest, PortfolioOptimizeResponse,
  PortfolioRequest, PortfolioResponse,
  PredictRequest, PredictResponse,
  PriceRequest, PriceResponse,
  RunRecord,
  SentimentRequest, SentimentResponse,
  StrategyRequest, StrategyResponse,
  TerminalRequest, TerminalResponse,
  TrainRequest, TrainResponse,
  WatchlistBulkAddResponse,
  WatchlistEntry, WatchlistResponse,
} from './types';

export class ApiError extends Error {}

async function handle<T>(resp: Response): Promise<T> {
  const payload = await resp.json();
  if (!resp.ok) {
    throw new ApiError(payload.detail || `request failed (${resp.status})`);
  }
  return payload as T;
}

async function postJSON<T>(url: string, body: unknown): Promise<T> {
  const resp = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  return handle<T>(resp);
}

async function getJSON<T>(url: string): Promise<T> {
  const resp = await fetch(url);
  return handle<T>(resp);
}

export const api = {
  price: (req: PriceRequest) => postJSON<PriceResponse>('/api/price', req),
  strategy: (req: StrategyRequest) => postJSON<StrategyResponse>('/api/strategy', req),
  compare: (req: CompareRequest) => postJSON<CompareResponse>('/api/compare', req),
  portfolio: (req: PortfolioRequest) => postJSON<PortfolioResponse>('/api/portfolio', req),
  optimizePortfolio: (req: PortfolioOptimizeRequest) =>
    postJSON<PortfolioOptimizeResponse>('/api/portfolio/optimize', req),
  portfolioCorrelation: (req: PortfolioCorrelationRequest) =>
    postJSON<PortfolioCorrelationResponse>('/api/portfolio/correlation', req),
  train: (req: TrainRequest) => postJSON<TrainResponse>('/api/train', req),
  predict: (req: PredictRequest) => postJSON<PredictResponse>('/api/predict', req),
  backtestMl: (req: BacktestMlRequest) => postJSON<BacktestMlResponse>('/api/backtest_ml', req),
  fundamentals: (req: FundamentalsRequest) => postJSON<FundamentalsReport>('/api/fundamentals', req),
  fundamentalsCompare: (req: FundamentalsCompareRequest) =>
    postJSON<FundamentalsCompareResponse>('/api/fundamentals/compare', req),
  sentiment: (req: SentimentRequest) => postJSON<SentimentResponse>('/api/sentiment', req),
  listEquities: () => getJSON<EquitiesListResponse>('/api/equities'),
  equityQuotes: () => getJSON<EquitiesQuotesResponse>('/api/equities/quotes'),
  equitySuggestions: () => getJSON<EquitySuggestionsResponse>('/api/equities/suggestions'),
  listCommodities: () => getJSON<CommoditiesListResponse>('/api/commodities'),
  commodityQuotes: () => getJSON<CommoditiesQuotesResponse>('/api/commodities/quotes'),
  listCrypto: () => getJSON<CryptoListResponse>('/api/crypto'),
  cryptoQuotes: () => getJSON<CryptoQuotesResponse>('/api/crypto/quotes'),
  listForex: () => getJSON<ForexListResponse>('/api/forex'),
  forexQuotes: () => getJSON<ForexQuotesResponse>('/api/forex/quotes'),
  listRuns: (limit = 50) => getJSON<RunRecord[]>(`/api/runs?limit=${limit}`),
  listModels: () => getJSON<ModelRecord[]>('/api/models'),
  listWatchlist: () => getJSON<WatchlistResponse>('/api/watchlist'),
  addWatchlist: (ticker: string) => postJSON<WatchlistEntry>('/api/watchlist', { ticker }),
  bulkAddWatchlist: (tickers: string[]) =>
    postJSON<WatchlistBulkAddResponse>('/api/watchlist/bulk', { tickers }),
  removeWatchlist: (ticker: string) =>
    fetch(`/api/watchlist/${encodeURIComponent(ticker)}`, { method: 'DELETE' }).then((r) => handle<{ removed: string }>(r)),
  listAlerts: () => getJSON<Alert[]>('/api/alerts'),
  addAlert: (req: AlertCreateRequest) => postJSON<Alert>('/api/alerts', req),
  removeAlert: (id: number) =>
    fetch(`/api/alerts/${id}`, { method: 'DELETE' }).then((r) => handle<{ removed: number }>(r)),
  terminal: (req: TerminalRequest) => postJSON<TerminalResponse>('/api/terminal', req),
};

export function runChartUrl(runId: number): string {
  return `/api/runs/${runId}/chart`;
}
