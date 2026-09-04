import { onMounted, onUnmounted, ref, watch } from 'vue';
import { useTheme } from './useTheme';

/** Bumps whenever the resolved color theme changes (explicit toggle, or the OS
 * preference changing while "system" is selected), so chart components can
 * recompute canvas colors that were read from CSS custom properties.
 */
export function useThemeVersion() {
  const { theme } = useTheme();
  const version = ref(0);
  let mql: MediaQueryList | null = null;

  function bump() {
    version.value++;
  }

  onMounted(() => {
    mql = window.matchMedia('(prefers-color-scheme: dark)');
    mql.addEventListener('change', bump);
  });

  onUnmounted(() => {
    mql?.removeEventListener('change', bump);
  });

  watch(theme, bump);

  return version;
}
