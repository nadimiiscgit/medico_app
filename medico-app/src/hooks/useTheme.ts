import { useState, useEffect } from 'react';

export type Theme = 'light' | 'dark' | 'system';

function resolveIsDark(theme: Theme): boolean {
  if (theme === 'dark') return true;
  if (theme === 'light') return false;
  return window.matchMedia('(prefers-color-scheme: dark)').matches;
}

export function useTheme() {
  const [theme, setThemeState] = useState<Theme>(() => {
    return (localStorage.getItem('neetpg_theme') as Theme) ?? 'system';
  });

  const isDark = resolveIsDark(theme);

  useEffect(() => {
    const root = document.documentElement;
    if (resolveIsDark(theme)) {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
  }, [theme]);

  // Listen for system theme changes when in 'system' mode
  useEffect(() => {
    if (theme !== 'system') return;
    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    const handler = () => {
      if (resolveIsDark('system')) {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }
    };
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, [theme]);

  const setTheme = (newTheme: Theme) => {
    localStorage.setItem('neetpg_theme', newTheme);
    setThemeState(newTheme);
  };

  return { theme, setTheme, isDark };
}
