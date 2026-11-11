import { useCallback, useEffect, useRef, useState, type KeyboardEvent as ReactKeyboardEvent, type ReactNode } from 'react';
import { Bell, ChevronRight, Database, FlaskConical, Map, Menu, MessageSquare, Moon, Route, ShieldCheck, Sun, X, LogOut, RefreshCw } from 'lucide-react';
import { api, post, time } from './api';
import type { Dashboard, Screen, Session } from './types';
import Overview from './Overview';
import ReportsScreen from './ReportsScreen';
import RoutesScreen from './RoutesScreen';
import AlertsScreen from './AlertsScreen';
import DataScreen from './DataScreen';
import ReviewScreen from './ReviewScreen';
import { ErrorMessage } from './ui';
import { useTheme, type ThemePreference } from './theme';

const screens = [{ id: 'map', label: 'Flood map', icon: Map }, { id: 'reports', label: 'Reports', icon: MessageSquare },
  { id: 'routes', label: 'Route suggestions', icon: Route }, { id: 'alerts', label: 'Your alerts', icon: Bell },
  { id: 'data', label: 'Data & model', icon: Database }, { id: 'review', label: 'Evidence review', icon: ShieldCheck }] as const;
let residentBootstrap: Promise<Session> | null = null;
const ensureSession = () => residentBootstrap ??= api<Session>('/auth/session').then(session => session.authenticated ? session : post<Session>('/auth/guest')).catch(error => { residentBootstrap = null; throw error; });
const initialScreen = (): Screen => screens.some(screen => screen.id === location.hash.slice(1)) ? location.hash.slice(1) as Screen : 'map';

function Mark() { return <svg className="product-mark" width="28" height="28" viewBox="0 0 32 32" aria-hidden="true"><path d="M5 8h22M5 16h15M5 24h22M24 12v9" fill="none" stroke="currentColor" strokeWidth="2.8" strokeLinecap="round" /></svg>; }

function keepDialogFocus(event: ReactKeyboardEvent<HTMLDialogElement>) {
  if (event.key !== 'Tab') return;
  const controls = [...event.currentTarget.querySelectorAll<HTMLElement>('a[href], button:not(:disabled), input:not(:disabled), select:not(:disabled), textarea:not(:disabled), [tabindex="0"]')].filter(element => element.getClientRects().length > 0);
  const first = controls[0], last = controls.at(-1);
  if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
  else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
}

function MobileNavigation({ close, children }: { close: () => void; children: ReactNode }) {
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const element = dialog.current;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    element?.showModal();
    const desktop = window.matchMedia('(min-width: 1051px)');
    const changed = () => { if (desktop.matches) close(); };
    desktop.addEventListener('change', changed);
    return () => { desktop.removeEventListener('change', changed); document.body.style.overflow = previousOverflow; element?.close(); };
  }, [close]);
  return <dialog ref={dialog} className="mobile-nav-overlay" aria-label="Navigation" onClose={close} onKeyDown={keepDialogFocus}>
    <button className="icon-button mobile-nav-close" onClick={close} aria-label="Close navigation" autoFocus><X size={21} /></button>{children}
  </dialog>;
}

function LoginDialog({ close, onLogin }: { close: () => void; onLogin: (session: Session) => void }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [username, setUsername] = useState('moderator');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    const element = dialog.current;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    element?.showModal();
    return () => { document.body.style.overflow = previousOverflow; element?.close(); };
  }, []);
  return <dialog ref={dialog} className="login-dialog" onClose={close} onKeyDown={keepDialogFocus} aria-labelledby="login-title"><div className="dialog-heading"><h2 id="login-title">Moderator sign in</h2><button className="icon-button" onClick={close} aria-label="Close moderator sign in"><X size={18} /></button></div><p>Review community evidence and inspect the synthetic pipeline.</p>
    <form onSubmit={async event => { event.preventDefault(); setBusy(true); setError(''); try { const session = await post<Session>('/auth/login', { username, password }); onLogin(session); close(); } catch (error) { setError((error as Error).message); } finally { setBusy(false); } }}>
      <div className="field"><label htmlFor="login-username">Username</label><input id="login-username" autoComplete="username" value={username} onChange={event => setUsername(event.target.value)} required autoFocus /></div><div className="field"><label htmlFor="login-password">Password</label><input id="login-password" type="password" autoComplete="current-password" value={password} onChange={event => setPassword(event.target.value)} required /></div>
      {error && <ErrorMessage>{error}</ErrorMessage>}<button className="button primary full-width" type="submit" disabled={busy}>{busy ? 'Signing in…' : 'Sign in'}</button><p className="field-help">Default local demo: moderator / floodline-demo. A configured password replaces this default.</p>
    </form></dialog>;
}

export default function App() {
  const { theme, preference, selectTheme } = useTheme();
  const [screen, setScreen] = useState<Screen>(initialScreen);
  const [data, setData] = useState<Dashboard | null>(null);
  const [session, setSession] = useState<Session>({ authenticated: false, role: 'visitor', username: null });
  const [selected, setSelected] = useState('C2');
  const [error, setError] = useState('');
  const [refreshing, setRefreshing] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [loginOpen, setLoginOpen] = useState(false);
  const [notice, setNotice] = useState('');
  const closeMenu = useCallback(() => setMenuOpen(false), []);
  const latestRefresh = useRef(0);
  const refresh = useCallback(async () => {
    const request = ++latestRefresh.current;
    setRefreshing(true);
    try { const next = await api<Dashboard>('/dashboard'); if (request === latestRefresh.current) { setData(next); setError(''); } }
    catch (error) { if (request === latestRefresh.current) setError((error as Error).message); }
    finally { if (request === latestRefresh.current) setRefreshing(false); }
  }, []);
  useEffect(() => {
    let active = true;
    ensureSession().then(session => { if (active) setSession(session); }).catch(error => { if (active) setError(error.message); });
    void refresh();
    const timer = setInterval(() => { if (!document.hidden) void refresh(); }, 30000);
    const hash = () => { setScreen(initialScreen()); setMenuOpen(false); setNotice(''); };
    window.addEventListener('hashchange', hash);
    return () => { active = false; clearInterval(timer); window.removeEventListener('hashchange', hash); };
  }, [refresh]);
  function navigate(next: Screen) { location.hash = next; setScreen(next); setMenuOpen(false); setNotice(''); window.scrollTo({ top: 0 }); }
  async function signOut() {
    try { await post('/auth/logout'); residentBootstrap = null; setSession(await ensureSession()); setNotice('Moderator access ended. Your resident session is retained.'); }
    catch (error) { setError((error as Error).message); }
  }
  const nav = <><div className="brand"><Mark /><span>Floodline<span className="brand-subtitle">Community flood platform</span></span></div><div className="workspace-label"><span className="workspace-dot" />Riverside demo catchment</div>
    <nav aria-label="Main navigation">{screens.map(({ id, label, icon: Icon }) => <a key={id} href={`#${id}`} className={`nav-link ${screen === id ? 'active' : ''}`} aria-current={screen === id ? 'page' : undefined} onClick={() => navigate(id)}><Icon size={18} strokeWidth={1.7} /><span>{label}</span>{screen === id && <ChevronRight size={14} />}</a>)}</nav>
    <div className="sidebar-bottom"><div className="prototype-note"><FlaskConical size={16} /><p>Synthetic pilot<span>Demo conditions. No live forecast.</span></p></div><div className="account-row"><span>{session.role === 'moderator' ? `Moderator · ${session.username}` : 'Resident session'}</span>{session.role === 'moderator' ? <button className="icon-button" title="Return to resident" aria-label="Return to resident" onClick={() => void signOut()}><LogOut size={16} /></button> : <button className="text-button" onClick={() => { setLoginOpen(true); setMenuOpen(false); }}>Moderator sign in</button>}</div><label className="appearance-row"><span>Appearance</span><select aria-label="Appearance" value={preference} onChange={event => selectTheme(event.target.value as ThemePreference)}><option value="system">System</option><option value="light">Light</option><option value="dark">Dark</option></select></label><span className="course-note">CAA project · Six-person pipeline</span></div></>;
  return <div className="app-shell"><a className="skip-link" href="#main-content">Skip to content</a><aside className="sidebar">{nav}</aside>
    <div className="app-workspace"><header className="topbar"><div className="mobile-brand"><Mark /><span>Floodline</span></div><div className="scope-breadcrumb"><span>Riverside pilot</span><ChevronRight size={13} /><strong>{screens.find(item => item.id === screen)?.label}</strong></div><div className="topbar-actions"><div className="mode-label"><FlaskConical size={14} /><span>Synthetic data</span><span className="mode-time">{data ? time(data.clock) : 'Connecting…'}</span></div><button className="icon-button theme-toggle" aria-label="Dark mode" aria-pressed={theme === 'dark'} title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`} onClick={() => selectTheme(theme === 'dark' ? 'light' : 'dark')}>{theme === 'dark' ? <Sun size={18} aria-hidden="true" /> : <Moon size={18} aria-hidden="true" />}</button><button className="icon-button mobile-menu" onClick={() => setMenuOpen(true)} aria-label="Open navigation" aria-haspopup="dialog" aria-expanded={menuOpen}><Menu size={20} /></button></div></header>
      <main id="main-content" className="canvas" tabIndex={-1}>
        {notice && <div className="notice" role="status"><p>{notice}</p><button className="icon-button" aria-label="Dismiss update" onClick={() => setNotice('')}><X size={16} /></button></div>}
        {error && <ErrorMessage retry={() => void refresh()}>{data ? `Could not refresh. The retained map is from demo time ${time(data.clock)}. ` : ''}{error}</ErrorMessage>}
        {data ? screen === 'map' ? <Overview data={data} selected={selected} setSelected={setSelected} navigate={navigate} refresh={() => void refresh()} refreshing={refreshing} />
          : screen === 'reports' ? <ReportsScreen data={data} session={session} refresh={refresh} notify={setNotice} />
          : screen === 'routes' ? <RoutesScreen data={data} />
          : screen === 'alerts' ? <AlertsScreen data={data} session={session} notify={setNotice} />
          : screen === 'data' ? <DataScreen data={data} />
          : <ReviewScreen data={data} session={session} signIn={() => setLoginOpen(true)} refresh={refresh} notify={setNotice} />
          : <div className="first-load"><h1>Community flood map</h1><p>Loading the synthetic catchment and its evidence.</p><div className="loading-map" role="status" aria-label="Loading map"><RefreshCw size={24} /></div></div>}
        <footer className="app-footer"><span>Smart City Flood Prediction and Community Alert Platform</span><span>Prototype · Predictions require real historical validation</span></footer>
      </main>
    </div>
    {menuOpen && <MobileNavigation close={closeMenu}>{nav}</MobileNavigation>}
    {loginOpen && <LoginDialog close={() => setLoginOpen(false)} onLogin={next => { setSession(next); residentBootstrap = null; setNotice('Moderator access enabled. Review decisions are recorded in the audit trail.'); }} />}
  </div>;
}
