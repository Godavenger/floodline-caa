import { useEffect, useState } from 'react';
import { ArrowLeft, ArrowUpRight, ImagePlus, LocateFixed, Pencil, Send, Trash2 } from 'lucide-react';
import { api, dateTime, localInputTime, post, severityWord, time } from './api';
import type { Dashboard, Report, Session } from './types';
import MapView from './MapView';
import { EmptyState, ErrorMessage, LoadingRows, Note, ReportTag } from './ui';

export default function ReportsScreen({ data, session, refresh, notify }: { data: Dashboard; session: Session; refresh: () => Promise<void>; notify: (value: string) => void }) {
  const [tab, setTab] = useState<'mine' | 'community'>('mine');
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [formOpen, setFormOpen] = useState(true);
  const [version, setVersion] = useState(0);
  const [description, setDescription] = useState('');
  const [severity, setSeverity] = useState('water_on_road');
  const [observed, setObserved] = useState(localInputTime(data.clock));
  const [pin, setPin] = useState({ longitude: 88.341, latitude: 22.571 });
  const [landmark, setLandmark] = useState('n2-1');
  const [image, setImage] = useState<File | null>(null);
  const [imageIssue, setImageIssue] = useState('');
  const [locationError, setLocationError] = useState('');
  const [formError, setFormError] = useState('');
  const [saving, setSaving] = useState(false);
  const [edit, setEdit] = useState<string | null>(null);
  const [editText, setEditText] = useState('');
  const [withdraw, setWithdraw] = useState<string | null>(null);
  const [busy, setBusy] = useState('');
  useEffect(() => {
    let active = true;
    setLoading(true);
    api<{ items: Report[] }>(tab === 'mine' ? '/reports?mine=true' : '/reports?status=verified').then(result => {
      if (active) { setReports(result.items); setError(''); }
    }).catch(error => { if (active) setError(error.message); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [tab, version, session.role]);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setSaving(true); setFormError(''); setLocationError('');
    try {
      const [southwest, northeast] = data.pilot.bounds;
      if (!Number.isFinite(pin.longitude) || !Number.isFinite(pin.latitude)
        || pin.latitude < southwest[0] || pin.latitude > northeast[0]
        || pin.longitude < southwest[1] || pin.longitude > northeast[1]) {
        setLocationError('Choose a landmark or map pin inside the synthetic study area.');
        return;
      }
      const at = new Date(observed);
      if (!Number.isFinite(at.getTime())) throw new Error('Choose a valid observation date and time.');
      const report = await post<Report>('/reports', { description, severity, observed_at: at.toISOString(), ...pin });
      let message = 'Report saved as pending. It will not restrict a road before moderator review.';
      if (image) {
        const payload = new FormData(); payload.append('image', image);
        try { await api(`/reports/${report.id}/image`, { method: 'POST', body: payload }); }
        catch (error) { message = `Your text report is saved. The image could not be attached: ${(error as Error).message}`; }
      }
      setDescription(''); setImage(null); setImageIssue(''); setFormOpen(false); setTab('mine'); setVersion(value => value + 1);
      notify(message); await refresh();
    } catch (error) { setFormError((error as Error).message); }
    finally { setSaving(false); }
  }

  async function update(reportId: string, deleting = false) {
    setBusy(reportId); setError('');
    try {
      await api(`/reports/${reportId}`, { method: deleting ? 'DELETE' : 'PATCH', body: deleting ? undefined : JSON.stringify({ description: editText }) });
      setEdit(null); setWithdraw(null); setVersion(value => value + 1); await refresh();
      notify(deleting ? 'Report evidence withdrawn. Reviewed restrictions retain their own expiry.' : 'Your pending report has been corrected.');
    } catch (error) { setError((error as Error).message); } finally { setBusy(''); }
  }

  function chooseLocation(longitude: number, latitude: number, selectedLandmark = 'custom') {
    setPin({ longitude, latitude }); setLandmark(selectedLandmark); setLocationError('');
  }

  function shareLocation() {
    if (!navigator.geolocation) { setLocationError('Location sharing is unavailable. Choose a demo landmark or map pin.'); return; }
    navigator.geolocation.getCurrentPosition(position => {
      const { longitude, latitude } = position.coords;
      const [southwest, northeast] = data.pilot.bounds;
      if (latitude < southwest[0] || latitude > northeast[0] || longitude < southwest[1] || longitude > northeast[1]) {
        setLocationError('Your device location is outside the synthetic study area. Choose a demo landmark instead.');
      } else { chooseLocation(longitude, latitude); }
    }, () => setLocationError('Location sharing failed. You can still choose a demo landmark or map pin.'), { enableHighAccuracy: false, timeout: 10000 });
  }

  const form = <section className="panel report-form-panel"><div className="panel-header"><h2>Submit an observation</h2><button className="text-button" onClick={() => setFormOpen(false)}>Close form</button></div>
    <form onSubmit={submit}>
      <div className="field"><label htmlFor="report-description">What did you observe?</label><textarea id="report-description" minLength={10} maxLength={800} required rows={4} value={description}
        placeholder="Describe the waterlogging, its location and how passage is affected." onChange={event => setDescription(event.target.value)} /><span className="field-help">Report existing evidence. Do not enter water to measure it.</span></div>
      <div className="form-two-columns"><div className="field"><label htmlFor="report-severity">Passage conditions</label><select id="report-severity" value={severity} onChange={event => setSeverity(event.target.value)}>{['water_on_road', 'slow_passage', 'impassable', 'unknown'].map(value => <option key={value} value={value}>{severityWord(value)}</option>)}</select></div>
        <div className="field"><label htmlFor="report-observed">Observed at</label><input type="datetime-local" id="report-observed" required value={observed} onChange={event => setObserved(event.target.value)} /><span className="field-help">Device-local input; demo clock {time(data.clock)}.</span></div></div>
      <div className="field"><label htmlFor="report-landmark">Observation location</label><select id="report-landmark" value={landmark} onChange={event => {
        const node = data.network.nodes.find(node => node.id === event.target.value); if (node) chooseLocation(node.longitude, node.latitude, node.id);
      }}><option value="custom">Custom map pin</option>{data.network.nodes.filter(node => node.landmark && node.id !== 'island').map(node => <option key={node.id} value={node.id}>{node.name}</option>)}</select></div>
      <div className="coordinate-row"><div className="field"><label htmlFor="report-latitude">Latitude</label><input id="report-latitude" type="number" step="any" required value={pin.latitude} onChange={event => chooseLocation(pin.longitude, Number(event.target.value))} /></div>
        <div className="field"><label htmlFor="report-longitude">Longitude</label><input id="report-longitude" type="number" step="any" required value={pin.longitude} onChange={event => chooseLocation(Number(event.target.value), pin.latitude)} /></div>
        <button type="button" className="icon-button location-button" title="Use device location" aria-label="Use device location" onClick={shareLocation}><LocateFixed size={18} /></button></div>
      {locationError && <ErrorMessage>{locationError}</ErrorMessage>}
      <div className="field image-field"><label htmlFor="report-image"><ImagePlus size={16} />Image evidence <span className="meta">optional</span></label><input id="report-image" type="file" accept="image/jpeg,image/png,image/webp" onChange={event => {
        const file = event.target.files?.[0] ?? null;
        if (file && file.size > 5 * 1024 * 1024) { setImage(null); setImageIssue('That file exceeds 5 MB. Choose a smaller image or save a text-only report.'); event.target.value = ''; }
        else { setImage(file); setImageIssue(''); }
      }} /><span className="field-help">JPEG, PNG or WebP · up to 5 MB. Images stay private until a moderator reviews privacy.</span>{imageIssue && <p className="field-help warning-text">{imageIssue}</p>}</div>
      {formError && <ErrorMessage>{formError}</ErrorMessage>}
      <div className="form-actions"><button className="button primary" type="submit" disabled={saving}>{saving ? 'Saving report…' : 'Submit for review'}<Send size={15} /></button><span className="meta">Will be saved as pending. Text-only reporting is available.</span></div>
    </form>
  </section>;

  return <><div className="title-row"><div><h1>Waterlogging reports</h1><p>Share an observation, track its review and distinguish verified conditions from unreviewed evidence.</p></div>
    {!formOpen && <button className="button primary" onClick={() => { setFormOpen(true); setObserved(localInputTime(data.clock)); }}>New report<ArrowUpRight size={16} /></button>}</div>
    {formOpen ? <div className="report-compose-grid">{form}<section className="panel report-location-panel"><div className="panel-header"><h2>Pin the observation</h2><span className="meta">Synthetic study area</span></div>
      <MapView data={data} selected="B2" pin={pin} onPick={chooseLocation} />
      <Note>Choose a landmark, enter coordinates or click the map. The pin must remain inside the demo catchment.</Note><p className="privacy-copy">Your identity stays private. Pending submissions do not appear in the public report layer or close roads automatically.</p>
    </section></div> : <>
      <div className="tabs"><button onClick={() => setTab('mine')} className={tab === 'mine' ? 'active' : ''}>Your reports</button><button onClick={() => setTab('community')} className={tab === 'community' ? 'active' : ''}>Verified community reports</button></div>
      <section className="panel report-list-panel"><div className="panel-header"><h2>{tab === 'mine' ? 'Your observations' : 'Current verified observations'}</h2><button className="text-button" onClick={() => setVersion(value => value + 1)}>Refresh</button></div>
        {error && <ErrorMessage retry={() => setVersion(value => value + 1)}>{error}</ErrorMessage>}
        {loading ? <LoadingRows /> : reports.length === 0 ? <EmptyState action={<button className="text-button" onClick={() => setFormOpen(true)}>Submit an observation<ArrowUpRight size={14} /></button>}>{tab === 'mine' ? 'You have not submitted any observations in this resident session.' : 'No current verified reports. Unreported hazards may still exist.'}</EmptyState> : reports.map(report => <article key={report.id} className="report-list-row">
          <div className="report-row-heading"><strong>{data.areas.features.find(area => area.properties.id === report.area_id)?.properties.name}</strong><ReportTag status={report.status} /></div>
          {edit === report.id ? <div className="inline-edit"><label className="sr-only" htmlFor={`edit-${report.id}`}>Correct report description</label><textarea id={`edit-${report.id}`} value={editText} minLength={10} maxLength={800} onChange={event => setEditText(event.target.value)} /><div className="form-actions"><button className="button" disabled={busy === report.id || editText.trim().length < 10} onClick={() => update(report.id)}>Save correction</button><button className="text-button" onClick={() => setEdit(null)}>Cancel</button></div></div> : <p>{report.description}</p>}
          <div className="report-meta"><span>{severityWord(report.severity)}</span><span>Observed {dateTime(report.observed_at)}</span><span>{report.has_image ? 'Image attached' : 'Text-only evidence'}</span></div>
          {report.image_available && report.image_url && <a className="text-link" href={report.image_url} target="_blank" rel="noreferrer">View image evidence<ArrowUpRight size={13} /></a>}
          {report.review_reason && <p className="review-note">Review: {report.review_reason}</p>}
          {tab === 'mine' && <div className="row-actions">{report.status === 'pending' && <button className="text-button" onClick={() => { setEdit(report.id); setEditText(report.description); }}><Pencil size={13} />Correct</button>}<button className="text-button" onClick={() => setWithdraw(report.id)}><Trash2 size={13} />Withdraw evidence</button></div>}
          {withdraw === report.id && <div className="withdraw-confirm"><p>Remove your text and image evidence? A separately reviewed road restriction retains its own validity.</p><button className="button" disabled={busy === report.id} onClick={() => update(report.id, true)}>Withdraw report</button><button className="text-button" onClick={() => setWithdraw(null)}>Keep report</button></div>}
        </article>)}
      </section><button className="text-button back-link" onClick={() => setFormOpen(true)}><ArrowLeft size={14} />Submit another observation</button>
    </>}
  </>;
}
