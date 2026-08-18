// Shared request/response shapes for the mcstock FastAPI backend (mcstock/web/app.py).

export type StatSummary = Record<string, number>;

export interface BandPoint {
  step: number;
  p5: number;
  p25: number;
  p50: number;
  p75: number;
  p95: number;
}

export interface HistogramBin {
  bin_start: number;
  bin_end: number;
  count: number;
}

export interface StrategySummary {
  mean_return: number;
  median_return: number;
  std_return: number;
  p05_return: number;
  p95_return: number;
  prob_profit: number;
  mean_max_drawdown: number;
  worst_max_drawdown: number;
}

// ---- Price ----

export interface PriceRequest {
  ticker: string;
  period?: string;
  days?: number;
  sims?: number;
  seed?: number | null;
}

export interface PriceResponse {
  run_id: number;
  s0: number;
  mu: number;
  sigma: number;
  summary: StatSummary;
  chart_png_base64: string;
  bands: BandPoint[];
  distribution: HistogramBin[];
}

// ---- Strategy ----

export interface StrategyRequest {
  ticker: string;
  strategy: 'buy-and-hold' | 'sma-crossover' | 'ml-technical';
  fast?: number;
  slow?: number;
  period?: string;
  days?: number;
  sims?: number;
  block_size?: number;
  seed?: number | null;
  model_id?: number | null;
}

export interface StrategyResponse {
  run_id: number;
  summary: StrategySummary;
  chart_png_base64: string;
  distribution: HistogramBin[];
}

// ---- Compare (strategies) ----

export interface CompareRequest {
  ticker: string;
  period?: string;
  days?: number;
  sims?: number;
  block_size?: number;
  fast?: number;
  slow?: number;
  seed?: number | null;
  model_ids: number[];
}

export interface CompareResponse {
  run_id: number;
  ranking: string[];
  results: Record<string, StrategySummary>;
  chart_png_base64: string;
}

// ---- Portfolio ----

export interface PortfolioRequest {
  tickers: string[];
  weights?: number[] | null;
  value?: number;
  period?: string;
  days?: number;
  sims?: number;
  seed?: number | null;
}

export interface PortfolioResponse {
  run_id: number;
  weights: Record<string, number>;
  summary: StatSummary;
  chart_png_base64: string;
  bands: BandPoint[];
}

// ---- Train / Predict / Backtest ML ----

export interface TrainRequest {
  ticker: string;
  model: 'logreg' | 'random_forest' | 'gradient_boosting';
  sentiment: 'none' | 'yfinance' | 'rss' | 'reddit' | 'all';
  use_volume: boolean;
  period?: string;
  horizon?: number;
  test_size?: number;
}

export interface TrainResponse {
  model_id: number;
  train_accuracy: number;
  test_accuracy: number;
  test_report: string;
}

export interface PredictRequest {
  model_id: number;
}

export interface PredictResponse {
  ticker: string;
  direction: 'UP' | 'DOWN';
  prob_up: number;
  horizon: number;
}

export interface BacktestMlRequest {
  model_id: number;
  days?: number;
  sims?: number;
  block_size?: number;
  seed?: number | null;
}

export interface BacktestMlResponse {
  run_id: number;
  summary: StatSummary;
  chart_png_base64: string;
  bands: BandPoint[];
}

// ---- Fundamentals (AI investment analyst) ----

export interface FundamentalsRequest {
  ticker: string;
  force_refresh?: boolean;
  llm_backend?: string | null;
}

export interface Scores {
  business_quality: number | null;
  growth: number | null;
  financial_strength: number | null;
  valuation: number | null;
  risk_score: number | null;
  risk_label: string;
}

export interface Trends {
  revenue_trend: string;
  fcf_status: string;
  debt_position: string;
  share_dilution: string;
}

export interface Evidence {
  business_quality: string[];
  growth: string[];
  financial_strength: string[];
  valuation: string[];
  risk: string[];
}

export interface ValuationMultiples {
  market_cap: number | null;
  price_to_earnings: number | null;
  price_to_fcf: number | null;
  price_to_sales: number | null;
  price_to_book: number | null;
}

export interface FairValue {
  low: number | null;
  high: number | null;
  current_price: number | null;
  methods: Record<string, { low: number; high: number }>;
  upside_low_pct: number | null;
  upside_high_pct: number | null;
}

export interface PriceStats {
  last_price: number | null;
  annualized_drift: number | null;
  annualized_volatility: number | null;
}

export interface FundamentalsReport {
  ticker: string;
  company_name: string;
  scores: Scores;
  trends: Trends;
  evidence: Evidence;
  valuation_multiples: ValuationMultiples;
  fair_value: FairValue;
  price_stats: PriceStats;
  confidence: number;
  bull_case: string;
  bear_case: string;
  red_flags: string[];
  narrative_source: string;
  annual_history: Record<string, number>[];
  metrics_history: Record<string, number>[];
  chart_png_base64: string | null;
}

export interface FundamentalsCompareRequest {
  tickers: string[];
  llm_backend?: string | null;
}

export interface ComparisonRow {
  ticker: string;
  company_name: string;
  composite: number | null;
  business_quality: number | null;
  growth: number | null;
  financial_strength: number | null;
  valuation: number | null;
  risk_label: string;
  revenue_trend: string;
  fcf_status: string;
  debt_position: string;
  confidence: number;
}

export interface FundamentalsCompareResponse {
  rows: ComparisonRow[];
  reports: Record<string, FundamentalsReport>;
  errors: Record<string, string>;
}

// ---- Watchlist ----

export interface WatchlistScores {
  business_quality: number | null;
  growth: number | null;
  financial_strength: number | null;
  valuation: number | null;
  risk_score: number | null;
  risk_label: string;
}

export interface WatchlistEntry {
  ticker: string;
  company_name: string;
  last_price: number;
  day_change_pct: number | null;
  sparkline: number[];
  scores: WatchlistScores;
  composite: number | null;
}

export interface WatchlistResponse {
  tickers: WatchlistEntry[];
  errors: Record<string, string>;
}

// ---- Alerts ----

export interface Alert {
  id: number;
  ticker: string;
  metric: 'price' | 'volatility';
  operator: 'above' | 'below';
  threshold: number;
  created_at: string;
  triggered_at: string | null;
}

export interface AlertCreateRequest {
  ticker: string;
  metric: 'price' | 'volatility';
  operator: 'above' | 'below';
  threshold: number;
}

// ---- Terminal ----

export interface TerminalRequest {
  command: string;
}

export interface TerminalResponse {
  output: string;
}

// ---- History ----

export interface RunRecord {
  id: number;
  run_type: string;
  ticker: string;
  params: Record<string, unknown>;
  summary: Record<string, unknown>;
  created_at: string;
  has_chart: boolean;
}

export interface ModelRecord {
  id: number;
  ticker: string;
  model_type: string;
  sentiment_sources: string[] | null;
  use_volume: boolean;
  horizon: number;
  train_accuracy: number;
  test_accuracy: number;
  model_path: string;
  created_at: string;
}
