import { useEffect, useState } from 'react';
import { Check, ShieldCheck, AlertTriangle, Play, RefreshCw } from 'lucide-react';
import { api, dateTime, post, severityWord, time } from './api';
import type { Dashboard, Operations, Report, Session } from './types';
import { EmptyState, ErrorMessage, LoadingRows, Note, ReportTag } from './ui';

export default function ReviewScreen({ data, session, signIn, refresh, notify }: { data: Dashboard; session: Session; signIn: () => void; refresh: () => Promise<void>; notify: (value: string) => void }) {
  const [reports, setReports] = useState<Report[]>([]);
  const [operations, setOperations] = useState<Operations | null>(null);
  const [selected, setSelected] = useState('');
  const [queue, setQueue] = useState<'pending' | 'verified'>('pending');
  const [status, setStatus] = useState('verified');
  const [reason, setReason] = useState('');
  const [road, setRoad] = useState('');
  const [restrict, setRestrict] = useState(false);
  const [privacy, setPrivacy] = useState(false);
  const [publish, setPublish] = useState(false);
  const [duplicate, setDuplicate] = useState('');
  const [busy, setBusy] = useState('');
  const [error, setError] = useState('');
  const [version, setVersion] = useState(0);
  useEffect(() => {
    if (session.role !== 'moderator') return;
    let active = true;
    Promise.all([api<{ items: Report[] }>('/reports'), api<Operations>('/admin/operations')]).then(([reports, operations]) => {
      if (active) { setReports(reports.items); setOperations(operations); setError(''); }
    }).catch(error => { if (active) setError(error.message); });
    return () => { active = false; };
  }, [session.role, version, data.scenario]);
  const candidates = reports.filter(report => report.status === queue);
  const report = candidates.find(report => report.id === selected) ?? candidates[0];
  useEffect(() => {
    setReason(''); setRestrict(false); setPrivacy(false); setPublish(false); setRoad('');
    setStatus(report?.status === 'verified' ? 'resolved' : 'verified');
  }, [report?.id, report?.status]);
  async function action(path: string, body?: unknown) {
    setBusy(path); setError('');
    try {
      const result = await post<{ new_alerts?: number; new_risk_records?: number }>(path, body);
      setVersion(value => value + 1); await refresh();
      notify(path.includes('scenarios') ? 'Synthetic scenario applied. Risk, expiry and route exclusions have been recomputed.' : path.includes('moderate') ? 'Review recorded. Map evidence and road restrictions are updated.' : path.includes('cycle') ? `Cycle complete: ${result.new_risk_records ?? 0} new risk records, ${result.new_alerts ?? 0} new alerts.` : 'The next simulated delivery will fail once, then use bounded retries.');
    } catch (error) { setError((error as Error).message); } finally { setBusy(''); }
  }
  if (session.role !== 'moderator') return <><div className="title-row"><div><h1>Report review</h1><p>Moderator authentication is required to review evidence, manage road restrictions and inspect operations.</p></div></div><section className="panel moderator-gate"><ShieldCheck size={28} /><h2>Sign in to review evidence</h2><p>Resident sessions can submit and manage their own reports. Review decisions are restricted to moderators and recorded in the audit trail.</p><button className="button primary" onClick={signIn}>Moderator sign in</button></section></>;
  const roads = data.network.features.slice().sort((a, b) => {
    if (!report) return 0;
    const distance = (points: number[][]) => Math.min(...points.map(point => Math.hypot((point[0] - report.longitude) * 102000, (point[1] - report.latitude) * 111000)));
    return distance(a.geometry.coordinates) - distance(b.geometry.coordinates);
  });
  return <><div className="title-row"><div><h1>Evidence review</h1><p>Verify time and location before publishing observations or restricting a mapped road segment.</p></div><button className="button" onClick={() => setVersion(value => value + 1)} disabled={!!busy}><RefreshCw size={15} />Refresh queue</button></div>
    {error && <ErrorMessage retry={() => setVersion(value => value + 1)}>{error}</ErrorMessage>}
    <div className="review-layout"><section className="panel review-queue"><div className="panel-header"><h2>Review queue</h2><span className="meta">{candidates.length} {queue}</span></div><div className="tabs compact-tabs"><button className={queue === 'pending' ? 'active' : ''} onClick={() => setQueue('pending')}>Pending</button><button className={queue === 'verified' ? 'active' : ''} onClick={() => setQueue('verified')}>Verified</button></div>
      {reports.length === 0 && !operations ? <LoadingRows /> : candidates.length ? candidates.map(item => <button className={`queue-row ${report?.id === item.id ? 'selected' : ''}`} key={item.id} onClick={() => setSelected(item.id)}><strong>{data.areas.features.find(area => area.properties.id === item.area_id)?.properties.name}</strong><span>{item.description}</span><small>Observed {time(item.observed_at)} · {item.has_image ? 'Image attached' : 'Text only'}</small></button>) : <EmptyState>No {queue} reports in this queue.</EmptyState>}
    </section><section className="panel review-detail"><div className="panel-header"><h2>Review observation</h2>{report && <ReportTag status={report.status} />}</div>
      {report ? <><p className="review-description">{report.description}</p><div className="report-meta"><span>{severityWord(report.severity)}</span><span>{dateTime(report.observed_at)}</span><span>{report.latitude.toFixed(5)}, {report.longitude.toFixed(5)}</span></div>
        {report.image_url && report.image_available ? <a className="review-image-link" href={report.image_url} target="_blank" rel="noreferrer"><img src={report.image_url} alt="Private waterlogging evidence awaiting privacy review" /><span>Open full evidence image</span></a> : <Note>This report has no image evidence. Record what corroborates its time, location and impact.</Note>}
        <form onSubmit={event => { event.preventDefault(); void action(`/reports/${report.id}/moderate`, { status, reason, road_edge_ids: status === 'verified' && restrict && road ? [road] : [], ttl_minutes: 120, privacy_reviewed: privacy, publish_image: publish, duplicate_of: status === 'duplicate' ? duplicate : null }); }}>
          <div className="field"><label htmlFor="review-decision">Decision</label><select id="review-decision" value={status} onChange={event => setStatus(event.target.value)}>{report.status === 'verified' ? <option value="resolved">Resolve verified hazard</option> : <><option value="verified">Verify observation</option><option value="rejected">Reject evidence</option><option value="duplicate">Mark as duplicate</option></>}</select></div>
          <div className="field"><label htmlFor="review-reason">Review reason</label><textarea id="review-reason" rows={3} minLength={10} maxLength={500} required value={reason} onChange={event => setReason(event.target.value)} placeholder="Record the corroborating evidence and why this decision is justified." /></div>
          {status === 'verified' && <><label className="check-row"><input type="checkbox" checked={restrict} onChange={event => setRestrict(event.target.checked)} /><span>Create a 2-hour road restriction from this reviewed observation.</span></label>{restrict && <div className="field"><label htmlFor="review-road">Affected mapped segment</label><select id="review-road" value={road} required onChange={event => setRoad(event.target.value)}><option value="">Select a nearby road segment</option>{roads.map(edge => <option key={edge.properties.id} value={edge.properties.id}>{edge.properties.name} · {edge.properties.segment_id}</option>)}</select><span className="field-help">The backend checks a 150 m match and excludes both mapped directions of the segment.</span></div>}
            {report.has_image && <><label className="check-row"><input type="checkbox" checked={privacy} onChange={event => { setPrivacy(event.target.checked); if (!event.target.checked) setPublish(false); }} /><span>I reviewed this image for identifying people, plates and sensitive details.</span></label><label className="check-row"><input type="checkbox" checked={publish} disabled={!privacy} onChange={event => setPublish(event.target.checked)} /><span>Publish the privacy-reviewed image with the verified report.</span></label></>}
          </>}
          {status === 'duplicate' && <div className="field"><label htmlFor="review-duplicate">Existing observation</label><select id="review-duplicate" required value={duplicate} onChange={event => setDuplicate(event.target.value)}><option value="">Choose the original report</option>{reports.filter(item => item.id !== report.id && ['pending', 'verified'].includes(item.status)).map(item => <option key={item.id} value={item.id}>{item.area_id} · {item.description.slice(0, 60)}</option>)}</select></div>}
          <button className="button primary" disabled={!!busy} type="submit"><Check size={15} />{busy.includes('moderate') ? 'Recording review…' : status === 'verified' ? 'Verify report' : status === 'resolved' ? 'Record resolution' : status === 'duplicate' ? 'Record duplicate' : 'Reject report'}</button>
        </form></> : <EmptyState>Select a report from the queue to inspect its evidence.</EmptyState>}
    </section></div>
    <section className="panel demo-controls"><div className="panel-header"><h2>Synthetic replay controls</h2><span className="meta">Scenario: {data.scenario}</span></div><p>Feed scenarios preserve submitted reports and subscriptions. An outage advances demo time by 105 minutes; other scenarios advance it by 15 minutes.</p><div className="demo-button-row">{['normal', 'storm', 'outage', 'recovery'].map(name => <button key={name} className="button" disabled={!!busy} onClick={() => void action(`/admin/scenarios/${name}`)}><Play size={13} />{({ normal: 'Light rain', storm: 'Heavy rain', outage: 'Feed outage', recovery: 'Recover feed' })[name]}</button>)}<button className="button" disabled={!!busy} onClick={() => void action('/admin/cycle')}><RefreshCw size={13} />Process again</button><button className="button" disabled={!!busy} onClick={() => void action('/admin/delivery-fault', { fail_next: 1 })}><AlertTriangle size={13} />Fail next delivery</button></div></section>
    {operations && <div className="operations-grid"><section className="panel operations-panel"><div className="panel-header"><h2>Pipeline health</h2><span className="meta">Local demo</span></div><dl className="operation-counts"><div><dt>Accepted observations</dt><dd className="num">{operations.counts.observations.toLocaleString('en-IN')}</dd></div><div><dt>Quarantined records</dt><dd className="num">{operations.counts.quarantine}</dd></div><div><dt>Initial duplicates ignored</dt><dd className="num">{operations.initial_ingestion.duplicates}</dd></div><div><dt>Failed deliveries</dt><dd className="num">{operations.failed_deliveries.length}</dd></div></dl>
      {operations.jobs.slice(0, 4).map(job => <div className="job-row" key={job.id}><span>{job.kind.replaceAll('-', ' ')}</span><span className="meta num">{time(job.started_at)}</span><span className="status neutral-status">{job.status}</span></div>)}
    </section><section className="panel audit-panel"><div className="panel-header"><h2>Recent audit trail</h2><span className="meta">Moderator actions and delivery decisions</span></div>{operations.audit.slice(0, 5).map((entry, index) => <div className="audit-row" key={`${entry.at}-${index}`}><span>{entry.action.replaceAll('_', ' ')}</span><span className="meta num">{time(entry.at)}</span></div>)}{operations.audit.length === 0 && <p className="empty-copy">No audit actions yet.</p>}</section></div>}
  </>;
}
