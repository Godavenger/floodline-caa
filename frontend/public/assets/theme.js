// Runs before the application and styles load; the server permits local scripts.
(() => {
  let preference = 'system';
  try {
    const saved = localStorage.getItem('floodline-theme');
    if (saved === 'light' || saved === 'dark' || saved === 'system') preference = saved;
  } catch { /* Browser storage can be unavailable. */ }
  const theme = preference === 'system' ? matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light' : preference;
  const colour = theme === 'dark' ? '#111111' : '#edf3f5';
  document.documentElement.dataset.theme = theme;
  document.documentElement.dataset.themePreference = preference;
  document.documentElement.style.colorScheme = theme;
  document.documentElement.style.backgroundColor = colour;
  document.querySelector('meta[name="theme-color"]')?.setAttribute('content', colour);
})();
