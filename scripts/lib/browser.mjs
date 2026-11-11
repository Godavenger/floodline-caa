// Local, dependency-free headless Chromium driver for reproducible UI checks.
import { spawn, execFileSync } from 'node:child_process';
import { existsSync, mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { resolve, join } from 'node:path';

export const delay = ms => new Promise(resolve => setTimeout(resolve, ms));

export class Browser {
  static async launch() {
    const executables = [process.env.BROWSER_EXECUTABLE,
      'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
      'C:/Program Files/Google/Chrome/Application/chrome.exe',
      '/usr/bin/google-chrome', '/usr/bin/chromium', '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'];
    const executable = executables.find(value => value && existsSync(value));
    if (!executable) throw new Error('Install Chrome/Edge or set BROWSER_EXECUTABLE for UI verification.');
    const root = resolve('.verification/browser-profiles');
    mkdirSync(root, { recursive: true });
    const profile = mkdtempSync(join(root, 'run-'));
    if (!resolve(profile).startsWith(root + (process.platform === 'win32' ? '\\' : '/'))) throw new Error('Unsafe browser profile path.');
    const processHandle = spawn(executable, ['--headless=new', '--no-sandbox', '--disable-gpu', '--remote-debugging-port=0',
      `--user-data-dir=${profile}`, '--no-first-run', '--no-default-browser-check', '--disable-background-networking',
      '--disable-background-timer-throttling', '--disable-renderer-backgrounding', '--hide-scrollbars', '--mute-audio', 'about:blank'],
      { windowsHide: true, stdio: ['ignore', 'ignore', 'pipe'] });
    const address = await new Promise((resolveAddress, reject) => {
      let output = '';
      const timeout = setTimeout(() => reject(new Error('The headless browser did not start.')), 20000);
      processHandle.stderr.on('data', chunk => { output += String(chunk); const match = output.match(/DevTools listening on (ws:\/\/[^\s]+)/); if (match) { clearTimeout(timeout); resolveAddress(match[1]); } });
      processHandle.on('exit', code => { clearTimeout(timeout); reject(new Error(`Browser exited before startup (${code}).`)); });
    });
    const browser = new Browser();
    browser.process = processHandle; browser.profile = profile; browser.root = root; browser.sequence = 0;
    browser.requests = new Map(); browser.listeners = new Map();
    browser.socket = new WebSocket(address);
    await new Promise((resolveOpen, reject) => { browser.socket.onopen = resolveOpen; browser.socket.onerror = () => reject(new Error('Browser protocol socket failed.')); });
    browser.socket.onmessage = event => {
      const message = JSON.parse(String(event.data));
      const request = browser.requests.get(message.id);
      if (request) { clearTimeout(request.timeout); browser.requests.delete(message.id); message.error ? request.reject(new Error(message.error.message)) : request.resolve(message.result); }
      else if (message.method) for (const callback of browser.listeners.get(`${message.sessionId || ''}:${message.method}`) || []) callback(message.params);
    };
    return browser;
  }

  send(method, params = {}, sessionId, timeoutMs = 30000) {
    const id = ++this.sequence;
    return new Promise((resolveResponse, reject) => {
      const timeout = setTimeout(() => { this.requests.delete(id); reject(new Error(`Browser protocol timed out: ${method}`)); }, timeoutMs);
      this.requests.set(id, { resolve: resolveResponse, reject, timeout });
      this.socket.send(JSON.stringify({ id, method, params, ...(sessionId ? { sessionId } : {}) }));
    });
  }

  on(sessionId, method, callback) {
    const key = `${sessionId}:${method}`;
    const callbacks = this.listeners.get(key) || [];
    callbacks.push(callback); this.listeners.set(key, callbacks);
  }

  async page(width = 1440, height = 900) {
    const { targetId } = await this.send('Target.createTarget', { url: 'about:blank' });
    const { sessionId } = await this.send('Target.attachToTarget', { targetId, flatten: true });
    const page = new Page(this, sessionId);
    await page.send('Page.enable'); await page.send('Runtime.enable');
    await page.viewport(width, height);
    return page;
  }

  async close() {
    try { await this.send('Browser.close', {}, undefined, 2000); } catch {}
    this.socket?.close();
    try {
      if (process.platform === 'win32') execFileSync('taskkill', ['/PID', String(this.process.pid), '/T', '/F'], { windowsHide: true, stdio: 'ignore' });
      else this.process.kill();
    } catch {}
    await delay(200);
    const target = resolve(this.profile);
    if (target.startsWith(this.root + (process.platform === 'win32' ? '\\' : '/'))) {
      try { rmSync(target, { recursive: true, force: true, maxRetries: 3, retryDelay: 200 }); } catch {}
    }
  }
}

class Page {
  constructor(browser, session) {
    this.browser = browser; this.session = session; this.errors = [];
    browser.on(session, 'Runtime.exceptionThrown', params => this.errors.push(params.exceptionDetails?.exception?.description || params.exceptionDetails?.text));
  }
  send(method, params = {}) { return this.browser.send(method, params, this.session); }
  async viewport(width, height) { await this.send('Emulation.setDeviceMetricsOverride', { width, height, deviceScaleFactor: 1, mobile: width < 600 }); }
  async evaluate(callback, argument) {
    const expression = typeof callback === 'function' ? `(${callback.toString()})(${argument === undefined ? '' : JSON.stringify(argument)})` : callback;
    const response = await this.send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true });
    if (response.exceptionDetails) throw new Error(response.exceptionDetails.exception?.description || response.exceptionDetails.text);
    return response.result.value;
  }
  async waitFor(expression, timeout = 12000) {
    const start = Date.now();
    while (Date.now() - start < timeout) { if (await this.evaluate(expression)) return; await delay(150); }
    throw new Error(`UI did not reach the expected state: ${expression.toString().slice(0, 140)}`);
  }
  async goto(url) { await this.send('Page.navigate', { url }); await this.waitFor(() => document.readyState === 'complete'); await delay(400); }
  async clickPoint(point) {
    await this.send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: point.x, y: point.y });
    await this.send('Input.dispatchMouseEvent', { type: 'mousePressed', x: point.x, y: point.y, button: 'left', clickCount: 1 });
    await this.send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: point.x, y: point.y, button: 'left', clickCount: 1 });
    await delay(100);
  }
  async click(selector) {
    const point = await this.evaluate(selector => {
      const element = document.querySelector(selector);
      if (!element) throw new Error('Missing control: ' + selector);
      element.scrollIntoView({ block: 'center', inline: 'nearest' });
      const rect = element.getBoundingClientRect();
      if (!rect.width || !rect.height) throw new Error('Hidden control: ' + selector);
      return { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 };
    }, selector);
    await this.clickPoint(point);
  }
  async clickText(text) {
    const point = await this.evaluate(text => {
      const element = [...document.querySelectorAll('button')].find(button => button.textContent.trim() === text && button.getClientRects().length);
      if (!element) throw new Error('Missing button: ' + text);
      element.scrollIntoView({ block: 'center', inline: 'nearest' });
      const rect = element.getBoundingClientRect();
      return { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 };
    }, text);
    await this.clickPoint(point);
  }
  async fill(selector, value) {
    await this.evaluate(({ selector, value }) => {
      const element = document.querySelector(selector);
      if (!element) throw new Error(`Missing field: ${selector}`);
      const prototype = element instanceof HTMLSelectElement ? HTMLSelectElement.prototype : element instanceof HTMLTextAreaElement ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
      Object.getOwnPropertyDescriptor(prototype, 'value').set.call(element, value);
      element.dispatchEvent(new Event('input', { bubbles: true }));
      element.dispatchEvent(new Event('change', { bubbles: true }));
    }, { selector, value });
  }
  async screenshot(path, fullPage = false) {
    await this.evaluate(() => window.scrollTo(0, 0));
    const params = { format: 'png', captureBeyondViewport: fullPage };
    if (fullPage) { const layout = await this.send('Page.getLayoutMetrics'); const size = layout.cssContentSize || layout.contentSize; params.clip = { x: 0, y: 0, width: Math.ceil(size.width), height: Math.min(12000, Math.ceil(size.height)), scale: 1 }; }
    const { data } = await this.send('Page.captureScreenshot', params);
    writeFileSync(path, Buffer.from(data, 'base64'));
  }
}
