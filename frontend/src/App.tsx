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
import { WatchlistPage } from './pages/WatchlistPage';
import { TerminalPage } from './pages/TerminalPage';
import { HistoryPage } from './pages/HistoryPage';
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
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const modelOptions = useModels();

  function navigate(next: TabId) {
    setTab(next);
    setSidebarOpen(false);
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
          <h1>mcstock</h1>
          <p className="subtitle">Monte Carlo &middot; ML &middot; AI analyst</p>
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
        {tab === 'dashboard' && <DashboardPage onNavigate={navigate} />}
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
