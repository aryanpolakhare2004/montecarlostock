import { useState } from 'react';
import { useModels } from './hooks/useModels';
import { ToastProvider } from './components/toast';
import { DashboardPage } from './pages/DashboardPage';
import { PricePage } from './pages/PricePage';
import { StrategyPage } from './pages/StrategyPage';
import { ComparePage } from './pages/ComparePage';
import { PortfolioPage } from './pages/PortfolioPage';
import { TrainPage } from './pages/TrainPage';
import { PredictPage } from './pages/PredictPage';
import { BacktestMlPage } from './pages/BacktestMlPage';
import { AnalystPage } from './pages/AnalystPage';
import { AnalystComparePage } from './pages/AnalystComparePage';
import { SentimentPage } from './pages/SentimentPage';
import { WatchlistPage } from './pages/WatchlistPage';
import { TerminalPage } from './pages/TerminalPage';
import { HistoryPage } from './pages/HistoryPage';
import { ThemeToggle } from './components/ThemeToggle';
import {
  ActivityIcon, ArrowUpRightIcon, BriefcaseIcon, ClockIcon, EyeIcon, HomeIcon,
  LayersIcon, LineChartIcon, ScaleIcon, SearchIcon, SlidersIcon, TargetIcon, TerminalIcon,
} from './components/icons';

const NAV_GROUPS = [
  {
    label: 'Overview',
    items: [{ id: 'dashboard', label: 'Dashboard', icon: HomeIcon }],
  },
  {
    label: 'Simulate',
    items: [
      { id: 'price', label: 'Price', icon: LineChartIcon },
      { id: 'strategy', label: 'Strategy', icon: TargetIcon },
      { id: 'compare', label: 'Compare', icon: ScaleIcon },
      { id: 'portfolio', label: 'Portfolio', icon: BriefcaseIcon },
    ],
  },
  {
    label: 'Machine learning',
    items: [
      { id: 'train', label: 'Train', icon: SlidersIcon },
      { id: 'predict', label: 'Predict', icon: ArrowUpRightIcon },
      { id: 'backtest_ml', label: 'Backtest ML', icon: ActivityIcon },
    ],
  },
  {
    label: 'Analyst',
    items: [
      { id: 'analyst', label: 'Analyst', icon: SearchIcon },
      { id: 'analyst_compare', label: 'Analyst compare', icon: LayersIcon },
      { id: 'sentiment', label: 'Sentiment', icon: ActivityIcon },
      { id: 'watchlist', label: 'Watchlist', icon: EyeIcon },
    ],
  },
  {
    label: 'Tools',
    items: [
      { id: 'terminal', label: 'Terminal', icon: TerminalIcon },
      { id: 'history', label: 'History', icon: ClockIcon },
    ],
  },
] as const;

export type TabId = (typeof NAV_GROUPS)[number]['items'][number]['id'];

function AppShell() {
  const [tab, setTab] = useState<TabId>('dashboard');
  const [visited, setVisited] = useState<Set<TabId>>(new Set(['dashboard']));
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const modelOptions = useModels();

  function navigate(next: TabId) {
    setTab(next);
    setVisited((prev) => (prev.has(next) ? prev : new Set(prev).add(next)));
    setSidebarOpen(false);
  }

  function pane(id: TabId, node: React.ReactNode) {
    if (!visited.has(id)) return null;
    return <div className={tab === id ? '' : 'tab-hidden'}>{node}</div>;
  }

  return (
    <div className="app-shell">
      <button
        type="button" className="sidebar-toggle" onClick={() => setSidebarOpen((v) => !v)}
        aria-label="Toggle navigation"
      >
        ☰
      </button>

      <aside className={`sidebar${sidebarOpen ? ' open' : ''}`}>
        <div className="sidebar-header">
          <div>
            <h1>mcstock</h1>
            <p className="subtitle">Monte Carlo &middot; ML &middot; AI analyst</p>
          </div>
          <ThemeToggle />
        </div>
        <nav>
          {NAV_GROUPS.map((group) => (
            <div className="nav-group" key={group.label}>
              <div className="nav-group-label">{group.label}</div>
              {group.items.map((item) => {
                const Icon = item.icon;
                return (
                  <button
                    key={item.id}
                    className={`nav-btn${tab === item.id ? ' active' : ''}`}
                    onClick={() => navigate(item.id)}
                  >
                    <Icon />
                    <span>{item.label}</span>
                  </button>
                );
              })}
            </div>
          ))}
        </nav>
      </aside>

      <main>
        {pane('dashboard', <DashboardPage onNavigate={navigate} />)}
        {pane('price', <PricePage />)}
        {pane('strategy', <StrategyPage modelOptions={modelOptions} />)}
        {pane('compare', <ComparePage modelOptions={modelOptions} />)}
        {pane('portfolio', <PortfolioPage />)}
        {pane('train', <TrainPage onTrained={modelOptions.reload} />)}
        {pane('predict', <PredictPage modelOptions={modelOptions} />)}
        {pane('backtest_ml', <BacktestMlPage modelOptions={modelOptions} />)}
        {pane('analyst', <AnalystPage />)}
        {pane('analyst_compare', <AnalystComparePage />)}
        {pane('sentiment', <SentimentPage />)}
        {pane('watchlist', <WatchlistPage />)}
        {pane('terminal', <TerminalPage />)}
        {pane('history', <HistoryPage />)}
      </main>
    </div>
  );
}

export default function App() {
  return (
    <ToastProvider>
      <AppShell />
    </ToastProvider>
  );
}
