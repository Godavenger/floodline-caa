import assert from 'node:assert/strict';

export async function deviceTheme(page, theme) {
  await page.send('Page.bringToFront');
  await page.send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-color-scheme', value: theme }] });
  await page.waitFor(`document.documentElement.dataset.theme === ${JSON.stringify(theme)}`);
}

async function contrastEvidence(page) {
  return page.evaluate(() => {
    const styles = getComputedStyle(document.documentElement);
    const colour = name => styles.getPropertyValue(name).trim();
    const luminance = hex => {
      let value = hex.replace('#', '');
      if (value.length === 3) value = [...value].map(channel => channel + channel).join('');
      if (!/^[\da-f]{6}$/i.test(value)) throw new Error('Expected a resolved theme colour: ' + hex);
      const channels = [0, 2, 4].map(index => parseInt(value.slice(index, index + 2), 16) / 255)
        .map(value => value <= .04045 ? value / 12.92 : ((value + .055) / 1.055) ** 2.4);
      return channels[0] * .2126 + channels[1] * .7152 + channels[2] * .0722;
    };
    const pairs = ['--ground', '--surface', '--raised', '--active'].flatMap(background =>
      ['--text', '--muted', '--faint'].map(foreground => [foreground, background, 4.5]));
    pairs.push(['--primary-ink', '--primary', 4.5], ['--primary-ink', '--primary-hover', 4.5],
      ['--positive', '--status-positive-bg', 4.5], ['--negative', '--status-negative-bg', 4.5],
      ['--warning', '--status-warning-bg', 4.5], ['--status-neutral-text', '--status-neutral-bg', 4.5],
      ['--error-text', '--error-bg', 4.5], ['--text', '--selection-bg', 4.5],
      ['--control', '--surface', 3], ['--control', '--raised', 3], ['--accent', '--surface', 3]);
    const results = pairs.map(([foreground, background, minimum]) => {
      const first = luminance(colour(foreground)), second = luminance(colour(background));
      const ratio = (Math.max(first, second) + .05) / (Math.min(first, second) + .05);
      return { foreground, background, minimum, ratio: Math.round(ratio * 1000) / 1000, passed: ratio >= minimum };
    });
    return { theme: document.documentElement.dataset.theme, pairs: results };
  });
}

export async function verifyThemes(browser, page, base) {
  await page.viewport(1440, 900);
  await page.fill('.sidebar select[aria-label="Appearance"]', 'system');
  await deviceTheme(page, 'light');
  const light = await contrastEvidence(page);
  await page.evaluate(() => {
    window.__qaMap = document.querySelector('.leaflet-container');
    window.__qaFill = getComputedStyle(document.querySelector('.leaflet-overlay-pane path')).fill;
  });
  await deviceTheme(page, 'dark');
  const dark = await contrastEvidence(page);
  for (const result of [light, dark]) {
    assert(result.pairs.every(pair => pair.passed), `${result.theme} theme contrast failures: ${JSON.stringify(result.pairs.filter(pair => !pair.passed))}`);
  }
  assert(await page.evaluate(() => window.__qaMap === document.querySelector('.leaflet-container') &&
    window.__qaFill !== getComputedStyle(document.querySelector('.leaflet-overlay-pane path')).fill),
  'A theme change must repaint the existing map without remounting it.');
  assert.equal(await page.evaluate(() => document.querySelector('meta[name="theme-color"]').content), '#111111');
  assert.equal(await page.evaluate(() => getComputedStyle(document.documentElement).colorScheme), 'dark');
  await page.click('button[aria-label="Dark mode"]');
  await page.waitFor(() => document.documentElement.dataset.theme === 'light');
  assert.equal(await page.evaluate(() => localStorage.getItem('floodline-theme')), 'light');
  await page.send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-color-scheme', value: 'light' }] });
  await page.send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-color-scheme', value: 'dark' }] });
  assert.equal(await page.evaluate(() => document.documentElement.dataset.theme), 'light', 'An explicit choice must override the device.');
  // Delay the application itself: the head bootstrap must apply the saved theme independently of React.
  await page.send('Network.enable');
  await page.send('Network.setCacheDisabled', { cacheDisabled: true });
  await page.send('Network.setBlockedURLs', { urls: ['*/assets/index-*.js'] });
  await page.goto(base);
  assert.equal(await page.evaluate(() => document.documentElement.dataset.theme), 'light', 'Saved appearance must be applied before the application loads.');
  assert.equal(await page.evaluate(() => document.querySelector('.theme-toggle')), null, 'The delayed application must not have mounted.');
  assert.equal(await page.evaluate(() => document.querySelector('meta[name="theme-color"]').content), '#edf3f5');
  await page.send('Network.setBlockedURLs', { urls: [] });
  await page.send('Network.setCacheDisabled', { cacheDisabled: false });
  await page.goto(base);
  await page.waitFor(() => !!document.querySelector('.theme-toggle') && !!document.querySelector('.leaflet-overlay-pane path'));
  assert.equal(await page.evaluate(() => document.documentElement.dataset.theme), 'light');

  const otherTab = await browser.page();
  await otherTab.send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-color-scheme', value: 'light' }] });
  await otherTab.goto(base);
  await otherTab.waitFor(() => !!document.querySelector('.theme-toggle'));
  await otherTab.click('button[aria-label="Dark mode"]');
  await page.waitFor(() => document.documentElement.dataset.theme === 'dark' && document.documentElement.dataset.themePreference === 'dark');
  await otherTab.fill('.sidebar select[aria-label="Appearance"]', 'system');
  await page.waitFor(() => document.documentElement.dataset.themePreference === 'system');
  await otherTab.waitFor(() => document.documentElement.dataset.theme === 'light');
  assert.equal(await page.evaluate(() => document.documentElement.dataset.theme), 'dark', 'Each system-mode tab must follow its own device setting.');
  await otherTab.fill('.sidebar select[aria-label="Appearance"]', 'light');
  await page.waitFor(() => document.documentElement.dataset.theme === 'light');
  await otherTab.evaluate(() => localStorage.clear());
  await page.waitFor(() => document.documentElement.dataset.theme === 'dark' && document.documentElement.dataset.themePreference === 'system');
  await otherTab.evaluate(() => localStorage.setItem('floodline-theme', 'invalid-preference'));
  await otherTab.goto(base);
  await otherTab.waitFor(() => !!document.querySelector('.theme-toggle'));
  assert.equal(await otherTab.evaluate(() => document.documentElement.dataset.themePreference), 'system');
  await otherTab.fill('.sidebar select[aria-label="Appearance"]', 'system');

  const noStorage = await browser.page();
  await noStorage.send('Page.addScriptToEvaluateOnNewDocument', { source:
    "Storage.prototype.getItem = Storage.prototype.setItem = function () { throw new DOMException('Storage unavailable', 'SecurityError'); };" });
  await noStorage.send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-color-scheme', value: 'dark' }] });
  await noStorage.goto(base);
  await noStorage.waitFor(() => !!document.querySelector('.theme-toggle'));
  assert.equal(await noStorage.evaluate(() => document.documentElement.dataset.theme), 'dark');
  await noStorage.click('button[aria-label="Dark mode"]');
  await noStorage.waitFor(() => document.documentElement.dataset.theme === 'light');
  assert.deepEqual([...otherTab.errors, ...noStorage.errors], [], 'Appearance must work without uncaught storage or cross-tab errors.');

  for (const tab of [otherTab, noStorage]) {
    const { targetInfo } = await tab.send('Target.getTargetInfo');
    await browser.send('Target.closeTarget', { targetId: targetInfo.targetId });
  }

  await page.fill('.sidebar select[aria-label="Appearance"]', 'system');
  await deviceTheme(page, 'dark');
  return { status: 'passed', light, dark, behaviour: [
    'live device appearance changes', 'map repaints without remounting', 'explicit preference overrides device',
    'pre-paint bootstrap without React', 'cross-tab synchronization', 'system restore and storage clearing',
    'invalid stored preference fallback', 'storage-disabled fallback', 'browser colour scheme and theme colour',
  ] };
}
