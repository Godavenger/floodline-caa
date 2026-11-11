import { useEffect, useState } from 'react';
import { Bell, Check, Plus, X } from 'lucide-react';
import { api, dateTime, post, time } from './api';
import type { Alert, Dashboard, Session, Subscription } from './types';
import { EmptyState, ErrorMessage, LoadingRows, Note } from './ui';

export default function AlertsScreen({ data, session, notify }: { data: Dashboard; session: Session; notify: (value: string) => void }) {
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [ward, setWard] = useState('C');
  const [consented, setConsented] = useState(false);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [version, setVersion] = useState(0);
  useEffect(() => {
    let active = true;
    Promise.all([api<{ items: Subscription[] }>('/subscriptions'), api<{ items: Alert[] }>('/alerts')]).then(([subscriptions, alerts]) => {
      if (active) { setSubscriptions(subscriptions.items); setAlerts(alerts.items); setError(''); }
    }).catch(error => { if (active) setError(error.message); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [version, session.role, data.clock]);
  async function subscribe(event: React.FormEvent) {
    event.preventDefault(); setBusy(true); setError('');
    try { await post('/subscriptions', { ward_id: ward, channel: 'in_app', consented }); setConsented(false); setVersion(value => value + 1); notify('Area subscription saved. Eligible demo warnings now appear in your in-app history.'); }
    catch (error) { setError((error as Error).message); } finally { setBusy(false); }
  }
  async function unsubscribe(id: string) {
    setBusy(true); setError('');
    try { await api(`/subscriptions/${id}`, { method: 'DELETE' }); setVersion(value => value + 1); notify('Subscription withdrawn. Queued deliveries for it are cancelled.'); }
    catch (error) { setError((error as Error).message); } finally { setBusy(false); }
  }
  return <><div className="title-row"><div><h1>Your area alerts</h1><p>Opt in to demo warnings, inspect their evidence and withdraw a subscription at any time.</p></div><button className="button" onClick={() => setVersion(value => value + 1)}>Refresh history</button></div>
    {error && <ErrorMessage retry={() => setVersion(value => value + 1)}>{error}</ErrorMessage>}
    <div className="alerts-layout"><section className="panel subscriptions-panel"><div className="panel-header"><h2>Area subscriptions</h2><Bell size={17} /></div>
      <form onSubmit={subscribe}><div className="field"><label htmlFor="alert-ward">Choose a ward</label><select id="alert-ward" value={ward} onChange={event => setWard(event.target.value)}>{data.wards.map(ward => <option key={ward.id} value={ward.id}>{ward.name}</option>)}</select></div>
        <label className="check-row"><input type="checkbox" checked={consented} onChange={event => setConsented(event.target.checked)} /><span>I agree to receive in-app alerts for this ward in this resident session.</span></label>
        <button className="button primary" type="submit" disabled={busy || !consented}>Subscribe<Plus size={15} /></button></form>
      <div className="subscription-list">{loading ? <LoadingRows count={2} /> : subscriptions.length ? subscriptions.map(subscription => <div className="subscription-row" key={subscription.id}><div><strong>{data.wards.find(ward => ward.id === subscription.ward_id)?.name}</strong><span><Check size={12} /> In-app · opted in</span></div><button className="icon-button" disabled={busy} onClick={() => void unsubscribe(subscription.id)} aria-label={`Unsubscribe from ${data.wards.find(ward => ward.id === subscription.ward_id)?.name}`}><X size={16} /></button></div>) : <p className="empty-copy">You have no active subscriptions.</p>}</div>
      <Note>The delivery adapter is simulated. No email or SMS is sent. Provider acceptance would not establish that a person read a message.</Note>
    </section><section className="panel alert-history-panel"><div className="panel-header"><h2>Delivery history</h2><span className="meta">{alerts.length} in this session</span></div>
      {loading ? <LoadingRows /> : alerts.length ? alerts.map(alert => <article key={alert.id} className="alert-row"><div className="report-row-heading"><strong>{data.wards.find(ward => ward.id === alert.ward_id)?.name}</strong><span className={`status delivery-${alert.state}`}>{alert.state.charAt(0).toUpperCase() + alert.state.slice(1)}</span></div>
        <span className="alert-kind">{alert.kind === 'observed_hazard' ? 'Observed, reviewed road hazard' : 'Environmental threshold warning'}</span><p>{alert.message}</p><div className="report-meta"><span>Issued {dateTime(alert.issued_at)}</span><span>Valid to {time(alert.expires_at)}</span><span>{alert.attempts} delivery {alert.attempts === 1 ? 'attempt' : 'attempts'}</span></div>
        {alert.next_attempt_at && <p className="field-help">Next simulated retry: {time(alert.next_attempt_at)}. Expired warnings will not be sent.</p>}
        {!alert.evidence_current && <p className="field-help">This alert's evidence is no longer current. Its delivery record is retained; check the map for the latest data support.</p>}
      </article>) : <EmptyState>No alerts yet. Subscribe to a ward to receive eligible demo warnings or reviewed road-hazard updates.</EmptyState>}
    </section></div>
  </>;
}
