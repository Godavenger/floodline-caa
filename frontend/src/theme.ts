import { useEffect, useState } from 'react';

export type ThemePreference = 'system' | 'light' | 'dark';
type Theme = Exclude<ThemePreference, 'system'>;

// Keep this key and the frame colours in sync with public/assets/theme.js.
const storageKey = 'floodline-theme';
const frameColours: Record<Theme, string> = { light: '#edf3f5', dark: '#111111' };

function readPreference(): ThemePreference {
  try {
    const saved = localStorage.getItem(storageKey);
    if (saved === 'light' || saved === 'dark' || saved === 'system') return saved;
  } catch { /* Appearance still works when browser storage is unavailable. */ }
  return 'system';
}

function resolveTheme(preference: ThemePreference): Theme {
  return preference === 'system' ? window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light' : preference;
}

function applyTheme(preference: ThemePreference): Theme {
  const theme = resolveTheme(preference);
  const root = document.documentElement;
  root.dataset.theme = theme;
  root.dataset.themePreference = preference;
  root.style.colorScheme = theme;
  root.style.backgroundColor = frameColours[theme];
  document.querySelector('meta[name="theme-color"]')?.setAttribute('content', frameColours[theme]);
  return theme;
}

export function useTheme() {
  const [preference, setPreference] = useState<ThemePreference>(readPreference);
  const [theme, setTheme] = useState<Theme>(() => resolveTheme(preference));

  useEffect(() => {
    const device = window.matchMedia('(prefers-color-scheme: dark)');
    const updateDevice = () => setTheme(applyTheme(preference));
    const updateStorage = (event: StorageEvent) => {
      if (event.key !== storageKey && event.key !== null) return;
      const next = readPreference();
      setPreference(next);
      setTheme(applyTheme(next));
    };
    updateDevice();
    device.addEventListener('change', updateDevice);
    window.addEventListener('storage', updateStorage);
    return () => {
      device.removeEventListener('change', updateDevice);
      window.removeEventListener('storage', updateStorage);
    };
  }, [preference]);

  function selectTheme(next: ThemePreference) {
    try { localStorage.setItem(storageKey, next); } catch { /* Keep this tab's choice. */ }
    setPreference(next);
    setTheme(applyTheme(next));
  }

  return { theme, preference, selectTheme };
}
