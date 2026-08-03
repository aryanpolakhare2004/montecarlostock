import { useState } from 'react';
import { useModels } from './hooks/useModels';
import { PricePage } from './pages/PricePage';
import { StrategyPage } from './pages/StrategyPage';
import { ComparePage } from './pages/ComparePage';
import { PortfolioPage } from './pages/PortfolioPage';
import { TrainPage } from './pages/TrainPage';
import { PredictPage } from './pages/PredictPage';
import { BacktestMlPage } from './pages/BacktestMlPage';
import { AnalystPage } from './pages/AnalystPage';
import { AnalystComparePage } from './pages/AnalystComparePage';
import { WatchlistPage } from './pages/WatchlistPage';
import { TerminalPage } from './pages/TerminalPage';
import { HistoryPage } from './pages/HistoryPage';

const TABS = [
  { id: 'price', label: 'Price' },
  { id: 'strategy', label: 'Strategy' },
  { id: 'compare', label: 'Compare' },
  { id: 'portfolio', label: 'Portfolio' },
  { id: 'train', label: 'Train' },
  { id: 'predict', label: 'Predict' },
  { id: 'backtest_ml', label: 'Backtest ML' },
  { id: 'analyst', label: 'Analyst' },
  { id: 'analyst_compare', label: 'Analyst compare' },
  { id: 'watchlist', label: 'Watchlist' },
  { id: 'terminal', label: 'Terminal' },
  { id: 'history', label: 'History' },
] as const;

type TabId = (typeof TABS)[number]['id'];

export default function App() {
  const [tab, setTab] = useState<TabId>('price');
  const modelOptions = useModels();

  return (
    <>
      <header>
        <h1>mcstock</h1>
        <p className="subtitle">
          Monte Carlo stock simulation, ML trading models, sentiment, and an AI fundamentals analyst &mdash; local
          dashboard
        </p>
      </header>

      <nav id="tabs">
        {TABS.map((t) => (
          <button
            key={t.id}
            className={`tab-btn${tab === t.id ? ' active' : ''}`}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </nav>

      <main>
        {tab === 'price' && <PricePage />}
        {tab === 'strategy' && <StrategyPage modelOptions={modelOptions} />}
        {tab === 'compare' && <ComparePage modelOptions={modelOptions} />}
        {tab === 'portfolio' && <PortfolioPage />}
        {tab === 'train' && <TrainPage onTrained={modelOptions.reload} />}
        {tab === 'predict' && <PredictPage modelOptions={modelOptions} />}
        {tab === 'backtest_ml' && <BacktestMlPage modelOptions={modelOptions} />}
        {tab === 'analyst' && <AnalystPage />}
        {tab === 'analyst_compare' && <AnalystComparePage />}
        {tab === 'watchlist' && <WatchlistPage />}
        {tab === 'terminal' && <TerminalPage />}
        {tab === 'history' && <HistoryPage />}
      </main>
    </>
  );
}
