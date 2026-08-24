import { useTheme } from '../hooks/useTheme';
import { MonitorIcon, MoonIcon, SunIcon } from './icons';

const LABELS = { system: 'System', light: 'Light', dark: 'Dark' } as const;

export function ThemeToggle() {
  const { theme, cycleTheme } = useTheme();
  const Icon = theme === 'light' ? SunIcon : theme === 'dark' ? MoonIcon : MonitorIcon;

  return (
    <button type="button" className="theme-toggle" onClick={cycleTheme} title="Cycle theme (System / Light / Dark)">
      <Icon size={14} />
      <span>{LABELS[theme]}</span>
    </button>
  );
}
