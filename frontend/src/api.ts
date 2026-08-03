import type {
  BacktestMlRequest, BacktestMlResponse,
  CompareRequest, CompareResponse,
  FundamentalsCompareRequest, FundamentalsCompareResponse,
  FundamentalsRequest, FundamentalsReport,
  ModelRecord,
  PortfolioRequest, PortfolioResponse,
  PredictRequest, PredictResponse,
  PriceRequest, PriceResponse,
  RunRecord,
  StrategyRequest, StrategyResponse,
  TrainRequest, TrainResponse,
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
  train: (req: TrainRequest) => postJSON<TrainResponse>('/api/train', req),
  predict: (req: PredictRequest) => postJSON<PredictResponse>('/api/predict', req),
  backtestMl: (req: BacktestMlRequest) => postJSON<BacktestMlResponse>('/api/backtest_ml', req),
  fundamentals: (req: FundamentalsRequest) => postJSON<FundamentalsReport>('/api/fundamentals', req),
  fundamentalsCompare: (req: FundamentalsCompareRequest) =>
    postJSON<FundamentalsCompareResponse>('/api/fundamentals/compare', req),
  listRuns: (limit = 50) => getJSON<RunRecord[]>(`/api/runs?limit=${limit}`),
  listModels: () => getJSON<ModelRecord[]>('/api/models'),
};

export function runChartUrl(runId: number): string {
  return `/api/runs/${runId}/chart`;
}
