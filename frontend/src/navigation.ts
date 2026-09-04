import {
  ActivityIcon, ArrowUpRightIcon, BarChartIcon, BriefcaseIcon, ClockIcon, EyeIcon, HomeIcon,
  LayersIcon, LineChartIcon, ScaleIcon, SearchIcon, SlidersIcon, TargetIcon, TerminalIcon,
} from './components/icons';

export const NAV_GROUPS = [
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
      { id: 'equities', label: 'Equities', icon: BarChartIcon },
      { id: 'commodities', label: 'Commodities', icon: LayersIcon },
      { id: 'crypto', label: 'Crypto', icon: ActivityIcon },
      { id: 'forex', label: 'Forex', icon: ScaleIcon },
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
