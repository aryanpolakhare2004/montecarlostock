import { ref, watchEffect } from 'vue';

export type Theme = 'system' | 'light' | 'dark';

const STORAGE_KEY = 'mcstock-theme';

function applyTheme(theme: Theme) {
  if (theme === 'system') {
    delete document.documentElement.dataset.theme;
  } else {
    document.documentElement.dataset.theme = theme;
  }
}

function readStoredTheme(): Theme {
  const stored = localStorage.getItem(STORAGE_KEY);
  return stored === 'light' || stored === 'dark' ? stored : 'system';
}

const theme = ref<Theme>(readStoredTheme());

watchEffect(() => {
  applyTheme(theme.value);
});

function setTheme(next: Theme) {
  theme.value = next;
  localStorage.setItem(STORAGE_KEY, next);
}

function cycleTheme() {
  setTheme(theme.value === 'system' ? 'light' : theme.value === 'light' ? 'dark' : 'system');
}

export function useTheme() {
  return { theme, setTheme, cycleTheme };
}
