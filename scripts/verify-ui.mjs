// End-to-end browser acceptance against an isolated synthetic database.
// Requires Node 22+, the backend requirements and a built frontend.
import assert from 'node:assert/strict';
import { spawn, spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { copyFileSync, existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { Browser, delay } from './lib/browser.mjs';
import { deviceTheme, verifyThemes } from './lib/theme-checks.mjs';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
process.chdir(root);
const port = Number(process.env.FLOODLINE_TEST_PORT || 8011);
assert(Number.isInteger(port) && port > 1024 && port < 65536, 'Choose a valid test port.');
const base = 'http://127.0.0.1:' + port;
const run = join(root, '.verification', 'runs', new Date().toISOString().replace(/[:.]/g, '-'));
const captures = join(root, '.impeccable', 'review');
mkdirSync(run, { recursive: true });
mkdirSync(captures, { recursive: true });
assert(existsSync(join(root, 'frontend', 'dist', 'assets')), 'Run npm run build in frontend first.');
const python = process.env.PYTHON_EXECUTABLE || [
  join(root, '.venv', 'Scripts', 'python.exe'), join(root, '.venv', 'bin', 'python'),
].find(existsSync) || 'python';
const env = { ...process.env, FLOODLINE_RUNTIME: join(run, 'runtime'), DATABASE_URL: '',
  ADMIN_USERNAME: 'moderator', ADMIN_PASSWORD: 'floodline-demo', APP_MODE: 'synthetic' };
const record = { status: 'running', started_at: new Date().toISOString(), mode: 'synthetic',
  frontend_sha256: createHash('sha256').update(readFileSync(join(root, 'frontend', 'dist', 'index.html'))).digest('hex'),
  theme_bootstrap_sha256: createHash('sha256').update(readFileSync(join(root, 'frontend', 'dist', 'assets', 'theme.js'))).digest('hex'),
  checks: [], screenshots: [], javascript_errors: [] };
const check = (name, detail = {}) => { record.checks.push({ name, passed: true, ...detail }); console.log('PASS ' + name); };
const sampleImage = join(run, 'synthetic-qa-image.png');
const imageResult = spawnSync(python, ['-c',
  "from PIL import Image, ImageDraw; import sys; image=Image.new('RGB',(320,200),'#edf3f5'); draw=ImageDraw.Draw(image); draw.rectangle((25,75,295,135),fill='#9fc5c5'); draw.text((20,20),'SYNTHETIC QA IMAGE',fill='#21343d'); draw.text((20,165),'Software test only - no field evidence',fill='#21343d'); image.save(sys.argv[1])",
  sampleImage], { cwd: root, env, windowsHide: true, encoding: 'utf8' });
assert.equal(imageResult.status, 0, imageResult.stderr);
const evaluation = spawnSync(python, ['-m', 'backend.floodline', 'evaluate'], {
  cwd: root, env, windowsHide: true, encoding: 'utf8', timeout: 60000,
});
assert.equal(evaluation.status, 0, evaluation.stderr);
let log = '';
const server = spawn(python, ['-c',
  "import os, uvicorn; from backend.floodline.config import Settings; from backend.floodline.main import create_app; uvicorn.run(create_app(Settings(worker_enabled=False)),host='127.0.0.1',port=int(os.environ['FLOODLINE_TEST_PORT']),log_level='warning')"],
  { cwd: root, env: { ...env, FLOODLINE_TEST_PORT: String(port) }, windowsHide: true, stdio: ['ignore', 'pipe', 'pipe'] });
server.stdout.on('data', chunk => { log = (log + String(chunk)).slice(-12000); });
server.stderr.on('data', chunk => { log = (log + String(chunk)).slice(-12000); });
let browser;
let page;

async function navigate(screen, heading) {
  await page.viewport(1440, 900);
  await page.click('.sidebar a[href="#' + screen + '"]');
  await page.waitFor('document.querySelector("h1")?.textContent === ' + JSON.stringify(heading));
  await delay(200);
}
async function capture(name, width = 1440, height = 900) {
  await page.viewport(width, height);
  await page.evaluate(() => document.fonts.ready);
  for (const theme of ['light', 'dark']) {
    await deviceTheme(page, theme);
    await delay(350);
    const variant = theme === 'light' ? name : name + '-dark';
    const content = await page.evaluate(() => ({
      heading: document.querySelector('h1')?.textContent,
      text: document.body.innerText.slice(0, 250),
      horizontal_overflow: Math.max(0, document.documentElement.scrollWidth - innerWidth),
      loading: !!document.querySelector('.first-load, .first-load-map, .first-load-screen, .loading-map'),
      map_paths: document.querySelectorAll('.leaflet-overlay-pane path').length,
      open_dialog: !!document.querySelector('dialog[open]'),
      theme: document.documentElement.dataset.theme,
    }));
    assert.equal(content.horizontal_overflow, 0, variant + ' has horizontal overflow.');
    assert(!content.loading, variant + ' captured a loading screen.');
    const path = join(captures, variant + '.png');
    await page.screenshot(path, !content.open_dialog);
    record.screenshots.push({ name: variant, path: relative(root, path).replaceAll('\\', '/'), width, height,
      sha256: createHash('sha256').update(readFileSync(path)).digest('hex'), ...content });
  }
}
async function request(path, body) {
  return page.evaluate(async ({ path, body }) => {
    const response = await fetch('/api' + path, { credentials: 'include',
      headers: { 'X-Floodline-Client': 'web', ...(body ? { 'Content-Type': 'application/json' } : {}) },
      method: body ? 'POST' : 'GET', ...(body ? { body: JSON.stringify(body) } : {}) });
    const result = await response.json();
    if (!response.ok) throw new Error(JSON.stringify(result));
    return result;
  }, { path, body });
}
async function clickLabel(text) {
  await page.evaluate(text => {
    const label = [...document.querySelectorAll('label')].find(label => label.innerText.includes(text));
    if (!label) throw new Error('Missing labelled control: ' + text);
    label.click();
  }, text);
  await delay(100);
}
async function login() {
  await page.click('.moderator-gate button');
  await page.fill('#login-password', 'floodline-demo');
  await page.clickText('Sign in');
  await page.waitFor(() => document.querySelector('h1')?.textContent === 'Evidence review' && !!document.querySelector('.review-queue .queue-row, .review-queue .empty-state'));
}
async function resident() {
  await page.viewport(1440, 900);
  await page.click('.sidebar button[aria-label="Return to resident"]');
  await page.waitFor(() => document.querySelector('.sidebar .account-row')?.innerText.includes('Resident session'));
}

try {
  const start = Date.now();
  let ready = false;
  while (Date.now() - start < 40000) {
    if (server.exitCode != null) throw new Error('Test server stopped: ' + log);
    try {
      const health = await fetch(base + '/api/health', { signal: AbortSignal.timeout(1500) }).then(response => response.json());
      assert.equal(health.worker, false, 'The test port is occupied by a different server.');
      assert.equal(health.storage, 'sqlite-local');
      ready = true; break;
    } catch (error) { if (error.name === 'AssertionError') throw error; await delay(250); }
  }
  assert(ready, 'Test server did not start: ' + log);
  browser = await Browser.launch();
  page = await browser.page();
  await page.send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-color-scheme', value: 'light' }] });
  await page.send('Page.addScriptToEvaluateOnNewDocument', { source:
    "window.__qaResponses=[]; const originalFetch=window.fetch; window.fetch=async function(...args){const response=await originalFetch(...args); if(String(args[0]).includes('/api/')){try{window.__qaResponses.push({path:String(args[0]),method:args[1]?.method||'GET',status:response.status,data:await response.clone().json()});}catch{}} return response;};" });
  await page.goto(base);
  await page.waitFor(() => document.querySelector('h1')?.textContent === 'Community flood map' && document.querySelectorAll('.leaflet-overlay-pane path').length >= 9);
  await page.waitFor(() => document.querySelector('.sidebar .account-row')?.innerText.includes('Resident session'));
  const initial = await request('/dashboard');
  assert.equal(initial.mode, 'synthetic'); assert.equal(initial.forecast_validated, false);
  assert.equal(initial.summary.cells, 9); assert.equal(initial.wards.length, 3);
  assert.equal(initial.summary.unknown, 1);
  assert((await page.evaluate(() => document.querySelector('.title-row p').textContent)).includes('3 of 8 cells with current evidence'));
  record.theme_acceptance = await verifyThemes(browser, page, base);
  check('Light and dark appearance, saved preferences, cross-tab synchronization and contrast', record.theme_acceptance);
  await capture('desktop');
  await capture('tablet', 1024, 900);
  await capture('mobile', 390, 844);
  await capture('small-phone', 320, 800);
  check('Map, evidence, synthetic scope and responsive layout', initial.summary);
  await page.viewport(390, 844);
  await page.click('button[aria-label="Open navigation"]');
  await page.waitFor(() => document.querySelector('dialog.mobile-nav-overlay')?.open);
  await capture('mobile-navigation', 390, 844);
  for (let index = 0; index < 15; index++) {
    await page.send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Tab', code: 'Tab', windowsVirtualKeyCode: 9 });
    await page.send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Tab', code: 'Tab', windowsVirtualKeyCode: 9 });
    assert(await page.evaluate(() => !!document.querySelector('dialog.mobile-nav-overlay')?.contains(document.activeElement)), 'Navigation focus escaped the modal.');
  }
  await page.send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Escape', code: 'Escape', windowsVirtualKeyCode: 27 });
  await page.send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Escape', code: 'Escape', windowsVirtualKeyCode: 27 });
  await page.waitFor(() => !document.querySelector('dialog.mobile-nav-overlay'));
  assert(await page.evaluate(() => document.activeElement?.getAttribute('aria-label') === 'Open navigation'));
  check('Mobile navigation traps focus, closes with Escape and restores focus');
  await navigate('routes', 'Route around known hazards');
  await page.fill('#route-end', 'island');
  await page.clickText('Find route');
  await page.waitFor(() => document.querySelector('.route-result h3')?.textContent === 'Route unavailable');
  await capture('route-unavailable');
  await page.fill('#route-end', 'n4-1');
  await page.clickText('Find route');
  await page.waitFor(() => document.querySelector('.route-result h3')?.textContent === 'Route found');
  const before = await page.evaluate(() => window.__qaResponses.filter(item => item.path === '/api/routes' && item.status === 200).at(-1).data);
  assert.equal(before.status, 'available');
  assert(!before.edge_ids.some(id => before.excluded_edge_ids.includes(id)));
  const segment = initial.network.features.find(edge => edge.properties.edge_ids.includes(before.edge_ids.at(-1)));
  assert(segment, 'The returned route must match mapped road segments.');
  await capture('route-before');
  check('Route excludes seeded hazard and handles disconnected destination');
  await navigate('reports', 'Waterlogging reports');
  await page.waitFor(() => !!document.querySelector('#report-description'));
  const description = 'Synthetic QA observation: water affects the eastern junction. This is software test evidence, not a field report.';
  await page.fill('#report-description', description);
  await page.fill('#report-longitude', '88.8');
  await page.clickText('Submit for review');
  await page.waitFor(() => !!document.querySelector('.report-form-panel [role="alert"]'));
  await capture('report-validation-error');
  await page.fill('#report-landmark', 'n4-1');
  assert(await page.evaluate(() => !document.querySelector('.report-form-panel [role="alert"]')), 'A corrected landmark must clear its location error.');
  await page.fill('#report-longitude', '88.8');
  await page.clickText('Submit for review');
  await page.waitFor(() => !!document.querySelector('.report-form-panel [role="alert"]'));
  await page.fill('#report-longitude', '88.354');
  assert(await page.evaluate(() => !document.querySelector('.report-form-panel [role="alert"]')), 'Corrected coordinates must clear their location error.');
  await page.fill('#report-longitude', '88.8');
  await page.clickText('Submit for review');
  await page.waitFor(() => !!document.querySelector('.report-form-panel [role="alert"]'));
  await page.click('.report-location-panel .leaflet-container');
  assert(await page.evaluate(() => !document.querySelector('.report-form-panel [role="alert"]')), 'Choosing a map pin must clear its location error.');
  await page.fill('#report-landmark', 'n4-1');
  assert((await page.evaluate(() => document.querySelector('.report-form-panel .form-actions').textContent)).includes('Will be saved as pending'));
  const documentNode = await page.send('DOM.getDocument');
  const input = await page.send('DOM.querySelector', { nodeId: documentNode.root.nodeId, selector: '#report-image' });
  await page.send('DOM.setFileInputFiles', { nodeId: input.nodeId, files: [sampleImage] });
  await capture('report-form');
  await capture('report-form-mobile', 390, 844);
  await page.viewport(1440, 900);
  await page.send('Network.enable');
  await page.send('Network.setBlockedURLs', { urls: ['*/api/reports*'] });
  await page.clickText('Submit for review');
  await page.waitFor(() => !!document.querySelector('.report-form-panel [role="alert"]'));
  const serviceError = await page.evaluate(() => document.querySelector('.report-form-panel [role="alert"]').textContent);
  await page.fill('#report-landmark', 'n3-2');
  assert.equal(await page.evaluate(() => document.querySelector('.report-form-panel [role="alert"]')?.textContent), serviceError, 'A location change must preserve an unrelated service error.');
  await page.fill('#report-landmark', 'n4-1');
  await page.send('Network.setBlockedURLs', { urls: [] });
  await page.clickText('Submit for review');
  await page.waitFor(() => document.querySelector('.report-list-row')?.innerText.includes('Synthetic QA observation'));
  let own = (await request('/reports?mine=true')).items.find(item => item.description === description);
  assert(own && own.status === 'pending' && own.has_image && own.image_available);
  const anonymous = await fetch(base + '/api/reports').then(response => response.json());
  assert(!anonymous.items.some(item => item.id === own.id));
  assert.equal((await fetch(base + own.image_url)).status, 404);
  assert.equal((await request('/dashboard')).summary.active_hazards, initial.summary.active_hazards);
  await page.clickText('Correct');
  const corrected = description + ' Correction: the pin is at the East shelter approach.';
  await page.fill('.inline-edit textarea', corrected);
  await page.clickText('Save correction');
  await page.waitFor('document.querySelector(".report-list-row")?.innerText.includes(' + JSON.stringify(corrected) + ') && !document.querySelector(".inline-edit")');
  await capture('report-pending');
  check('Report with image stays private, validates location and supports correction');
  await navigate('review', 'Report review');
  await capture('moderator-gate');
  await page.click('.moderator-gate button');
  await page.fill('#login-password', 'wrong-password');
  await page.clickText('Sign in');
  await page.waitFor(() => !!document.querySelector('.login-dialog [role="alert"]'));
  await capture('moderator-login-error');
  await page.fill('#login-password', 'floodline-demo');
  await page.clickText('Sign in');
  await page.waitFor(() => document.querySelector('h1')?.textContent === 'Evidence review' && !!document.querySelector('.queue-row'));
  await page.evaluate(description => [...document.querySelectorAll('.queue-row')].find(row => row.innerText.includes(description)).click(), corrected);
  await page.waitFor('document.querySelector(".review-description")?.textContent === ' + JSON.stringify(corrected));
  await page.fill('#review-reason', 'Reviewed the synthetic test pin, timestamp and image. The affected mapped approach is corroborated by the fixture.');
  await clickLabel('Create a 2-hour road restriction');
  await page.fill('#review-road', segment.properties.id);
  await clickLabel('I reviewed this image');
  await clickLabel('Publish the privacy-reviewed image');
  await page.waitFor(() => [...document.images].every(image => image.complete));
  await capture('moderation');
  await capture('moderation-mobile', 390, 844);
  await page.viewport(1440, 900);
  await page.clickText('Verify report');
  await page.waitFor(() => document.querySelector('.notice')?.innerText.includes('Review recorded'));
  own = (await request('/reports')).items.find(item => item.id === own.id);
  assert.equal(own.status, 'verified');
  const published = await fetch(base + '/api/reports?status=verified').then(response => response.json());
  const publicReport = published.items.find(item => item.id === own.id);
  assert(publicReport && publicReport.image_available);
  assert.equal((await fetch(base + publicReport.image_url)).status, 200);
  assert(!('user_id' in publicReport));
  await navigate('routes', 'Route around known hazards');
  await page.clickText('Find route');
  await page.waitFor(() => document.querySelector('.route-result h3')?.textContent === 'Route found');
  const after = await page.evaluate(() => window.__qaResponses.filter(item => item.path === '/api/routes' && item.status === 200).at(-1).data);
  assert(!after.edge_ids.some(id => segment.properties.edge_ids.includes(id)));
  assert.notDeepEqual(after.edge_ids, before.edge_ids);
  assert(!after.edge_ids.some(id => after.excluded_edge_ids.includes(id)));
  await capture('route-after');
  await capture('route-mobile', 390, 844);
  record.route_comparison = { before: { distance_m: before.distance_m, edge_ids: before.edge_ids },
    after: { distance_m: after.distance_m, edge_ids: after.edge_ids, excluded_edge_ids: after.excluded_edge_ids } };
  check('Authenticated, privacy-reviewed publication changes route exclusions');
  await resident();
  await navigate('reports', 'Waterlogging reports');
  await page.clickText('Close form');
  await page.waitFor(() => !!document.querySelector('.report-list-row'));
  assert((await request('/reports?mine=true')).items.some(item => item.id === own.id));
  await capture('resident-verified-report');
  check('Moderator logout preserves resident report ownership');
  await navigate('alerts', 'Your area alerts');
  await page.waitFor(() => !!document.querySelector('.alert-history-panel .empty-state'));
  assert(await page.evaluate(() => [...document.querySelectorAll('button')].find(button => button.textContent.trim() === 'Subscribe').disabled));
  await capture('alerts-empty');
  await clickLabel('I agree to receive in-app alerts');
  await page.clickText('Subscribe');
  await page.waitFor(() => document.querySelectorAll('.alert-row').length > 0);
  await page.fill('#alert-ward', 'B');
  await clickLabel('I agree to receive in-app alerts');
  await page.clickText('Subscribe');
  await page.waitFor(() => document.querySelectorAll('.subscription-row').length === 2);
  const firstAlerts = (await request('/alerts')).items;
  await capture('alerts-active');
  await capture('alerts-mobile', 390, 844);
  await navigate('review', 'Report review');
  await login();
  await page.clickText('Process again');
  await page.waitFor(() => document.querySelector('.notice')?.innerText.includes('Cycle complete'));
  await page.clickText('Process again');
  await page.waitFor(() => document.querySelector('.notice')?.innerText.includes('Cycle complete'));
  await resident();
  assert.equal((await request('/alerts')).items.length, firstAlerts.length);
  check('Opt-in subscriptions and repeated-cycle alert deduplication', { initial_alerts: firstAlerts.length });
  await navigate('review', 'Report review');
  await login();
  await page.clickText('Heavy rain');
  await page.waitFor(() => document.querySelector('.demo-controls .meta')?.innerText === 'Scenario: storm');
  await navigate('map', 'Community flood map');
  const storm = await request('/dashboard');
  assert(storm.summary.warnings > initial.summary.warnings);
  await capture('heavy-rain-map');
  await navigate('review', 'Evidence review');
  await page.clickText('Feed outage');
  await page.waitFor(() => document.querySelector('.demo-controls .meta')?.innerText === 'Scenario: outage');
  await navigate('map', 'Community flood map');
  const outage = await request('/dashboard');
  assert.equal(outage.summary.unknown, 9);
  assert(outage.risk.every(risk => risk.index == null && risk.stale));
  const outageHeading = await page.evaluate(() => document.querySelector('.title-row p').textContent);
  assert(outageHeading.includes('All 9 cells have unknown conditions') && !outageHeading.includes('0 of 9'));
  assert((await page.evaluate(() => document.querySelector('.metrics-strip').textContent)).includes('Unavailable'));
  await capture('feed-outage');
  await capture('feed-outage-mobile', 390, 844);
  await navigate('review', 'Evidence review');
  await page.clickText('Recover feed');
  await page.waitFor(() => document.querySelector('.demo-controls .meta')?.innerText === 'Scenario: recovery');
  await navigate('map', 'Community flood map');
  const recovery = await request('/dashboard');
  assert.equal(recovery.summary.unknown, 0);
  assert(recovery.risk.every(risk => !risk.stale && risk.forecast_validated === false));
  await capture('feed-recovery');
  check('Storm, stale-feed outage, expiry and recovery preserve honest data support');
  await resident();
  await navigate('alerts', 'Your area alerts');
  await page.waitFor('document.querySelectorAll(".alert-row").length > ' + firstAlerts.length);
  const finalAlerts = (await request('/alerts')).items;
  assert(finalAlerts.some(alert => alert.state === 'expired'));
  assert(finalAlerts.some(alert => alert.state === 'sent' && alert.evidence_current));
  await capture('alerts-history');
  await page.click('button[aria-label="Unsubscribe from ' + initial.wards.find(ward => ward.id === 'B').name + '"]');
  await page.waitFor(() => document.querySelectorAll('.subscription-row').length === 1);
  check('Alert history distinguishes expired evidence and supports unsubscribe');
  await navigate('reports', 'Waterlogging reports');
  await page.clickText('Close form');
  await page.waitFor(() => !!document.querySelector('.report-list-row'));
  await page.clickText('Withdraw evidence');
  await page.waitFor(() => !!document.querySelector('.withdraw-confirm'));
  await capture('withdraw-confirmation');
  await page.clickText('Withdraw report');
  await page.waitFor(() => !!document.querySelector('.report-list-panel .empty-state'));
  assert(!(await request('/reports?mine=true')).items.some(item => item.id === own.id));
  await capture('reports-empty');
  check('Resident evidence withdrawal removes owned text and image');
  await navigate('data', 'Data and model evidence');
  await page.waitFor(() => document.querySelectorAll('.source-row').length === 2);
  await page.click('.model-panel summary');
  await page.waitFor(() => !!document.querySelector('.split-summary'));
  await capture('data-model');
  await capture('data-model-mobile', 390, 844);
  const experiment = await request('/evaluation');
  assert.equal(experiment.mode, 'synthetic'); assert.equal(experiment.candidate_promoted, false);
  assert.equal(experiment.historical_accuracy_established, false);
  const reference = await fetch(base + '/docs').then(response => response.text());
  assert(reference.includes('/openapi.json') && !reference.includes('cdn.jsdelivr.net'));
  check('Synthetic model evidence, unpromoted candidate and offline API reference');
  await navigate('map', 'Community flood map');
  await page.send('Network.enable');
  await page.send('Network.setBlockedURLs', { urls: ['*/api/dashboard*'] });
  await page.click('button[aria-label="Refresh map data"]');
  await page.waitFor(() => document.querySelector('main > [role="alert"]')?.innerText.includes('Could not refresh'));
  await capture('connection-error');
  await page.send('Network.setBlockedURLs', { urls: [] });
  await page.click('button[aria-label="Refresh map data"]');
  await page.waitFor(() => !document.querySelector('main > [role="alert"]'));
  check('Refresh failure retains the timestamped map and recovers');
  assert.deepEqual(page.errors, []);
  record.status = 'passed';
  record.javascript_errors = page.errors;
  check('No uncaught JavaScript errors in the complete workflow');
} catch (error) {
  record.status = 'failed';
  record.error = error.stack || String(error);
  record.javascript_errors = page?.errors || [];
  if (page) { try { await page.screenshot(join(run, 'failure.png'), true); } catch {} }
  console.error(record.error);
  process.exitCode = 1;
} finally {
  if (browser) await browser.close();
  if (server.exitCode == null) {
    server.kill();
    await Promise.race([new Promise(resolveExit => server.once('exit', resolveExit)), delay(2500)]);
  }
  record.finished_at = new Date().toISOString();
  writeFileSync(join(run, 'browser-acceptance.json'), JSON.stringify(record, null, 2) + '\n');
  copyFileSync(join(run, 'browser-acceptance.json'), join(root, '.verification', 'browser-acceptance.json'));
  writeFileSync(join(run, 'server.log'), log);
  console.log('Browser acceptance: ' + record.status + '. Evidence: .verification/browser-acceptance.json');
}
