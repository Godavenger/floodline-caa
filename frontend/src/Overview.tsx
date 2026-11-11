import { useEffect, useState } from 'react';
import { ArrowUpRight, CheckCircle2, Layers2, RefreshCw } from 'lucide-react';
import type { Dashboard, Observation, Screen } from './types';
import { api, number, severityWord, time } from './api';
import { Gauge, RainChart } from './Charts';
import MapView from './MapView';
import { ErrorMessage, Note, RiskTag } from './ui';

type Props = { data: Dashboard; selected: string; setSelected: (id: string) => void; navigate: (screen: Screen) => void; refresh: () => void; refreshing: boolean };

export default function Overview({ data, selected, setSelected, navigate, refresh, refreshing }: Props) {
  const [basemap, setBasemap] = useState(false);
  const [riskLayer, setRiskLayer] = useState(true);
  const [observations, setObservations] = useState<Observation[]>([]);
  const [historyError, setHistoryError] = useState('');
  const [retry, setRetry] = useState(0);
  const risk = data.risk.find(row => row.area_id === selected) ?? data.risk[0];
  const property = data.areas.features.find(area => area.properties.id === risk.area_id)!.properties;
  const levelTime = risk.features.level_observed_at;
  const gaugeStale = !levelTime || (new Date(data.clock).getTime() - new Date(levelTime).getTime()) / 60000 > 60;
  const evaluatedCells = data.summary.cells - data.summary.unknown;
  const warningSummary = evaluatedCells === 0
    ? `All ${data.summary.cells} cells have unknown conditions because rainfall evidence is missing or stale. Current warnings cannot be estimated.`
    : `${data.summary.warnings} of ${evaluatedCells} cells with current evidence meet the demo warning rule.${data.summary.unknown ? ` ${data.summary.unknown} ${data.summary.unknown === 1 ? 'cell is' : 'cells are'} unknown.` : ''} Inspect the evidence before acting.`;
  useEffect(() => {
    let active = true;
    api<{ items: Observation[] }>(`/observations?area_id=${encodeURIComponent(risk.area_id)}`).then(result => {
      if (active) { setObservations(result.items); setHistoryError(''); }
    }).catch(error => { if (active) { setObservations([]); setHistoryError(error.message); } });
    return () => { active = false; };
  }, [risk.area_id, risk.id, retry]);

  return <>
    <div className="title-row"><div><h1>Community flood map</h1><p>{warningSummary}</p></div>
      <button className="button primary" onClick={() => navigate('reports')}>Report waterlogging<ArrowUpRight size={16} /></button></div>
    <div className="metrics-strip">
      <div><span>Cells under warning</span><strong className="num">{evaluatedCells ? <>{data.summary.warnings}<small> / {evaluatedCells}</small></> : <span className="missing-value">Unavailable</span>}</strong></div>
      <div><span>Verified road hazards</span><strong className="num">{data.summary.active_hazards}<small> active</small></strong></div>
      <div><span>Unknown cells</span><strong className="num">{data.summary.unknown}<small> need data</small></strong></div>
      <div><span>Demo time</span><strong className="num metric-time">{time(data.clock).replace(' IST', '')}<small> IST</small></strong></div>
    </div>
    <div className="map-evidence-grid">
      <section className="panel map-panel" aria-labelledby="study-heading">
        <div className="panel-header"><h2 id="study-heading">Study area</h2><div className="map-options">
          <label><input type="checkbox" checked={riskLayer} onChange={event => setRiskLayer(event.target.checked)} /><Layers2 size={14} />Risk cells</label>
          <label><input type="checkbox" checked={basemap} onChange={event => setBasemap(event.target.checked)} />OSM map<span className="sr-only">: loads online map tiles</span></label>
          <button className="icon-button" onClick={refresh} disabled={refreshing} aria-label="Refresh map data"><RefreshCw size={15} /></button>
        </div></div>
        <MapView data={data} selected={selected} onSelect={setSelected} basemap={basemap} riskLayer={riskLayer} />
        <div className="map-legend" aria-label="Risk legend">{(['low', 'elevated', 'high', 'unknown'] as const).map(level => <RiskTag key={level} level={level} />)}<span className="legend-hazard"><span />Verified road hazard</span></div>
      </section>
      <section className="panel evidence-panel" aria-labelledby="evidence-heading">
        <div className="panel-header"><h2 id="evidence-heading">Area evidence</h2><span className="meta">{risk.area_id}</span></div>
        <label className="sr-only" htmlFor="selected-area">Choose an analysis area</label>
        <select id="selected-area" className="area-select" value={risk.area_id} onChange={event => setSelected(event.target.value)}>
          {data.areas.features.map(area => <option key={area.properties.id} value={area.properties.id}>{area.properties.name}</option>)}
        </select>
        <div className="evidence-score"><RiskTag level={risk.risk_level} /><span className="index-value num">{risk.index == null ? <span className="missing-value">Not estimable</span> : <>{risk.index}<small> / 100</small></>}</span></div>
        <p className="evidence-explanation">{risk.stale ? 'The retained update is stale. Current conditions cannot be estimated reliably.' : risk.risk_level === 'unknown' ? 'Rainfall coverage is insufficient. Current conditions cannot be estimated reliably.' : risk.risk_level === 'high' ? 'Heavy recent rainfall meets the high demo threshold. This index is not a validated forecast.' : risk.risk_level === 'elevated' ? 'Rainfall and synthetic drainage conditions meet the elevated demo threshold.' : 'The demo warning threshold is not met. Unreported waterlogging may still exist.'}</p>
        <dl className="evidence-facts">
          <div><dt>Rainfall · past 3 h</dt><dd className="num">{number(risk.features.rainfall_3h_mm)}<small> mm known</small></dd></div>
          <div><dt>Data support</dt><dd className={`support-${risk.data_support}`}>{risk.data_support.charAt(0).toUpperCase() + risk.data_support.slice(1)}</dd></div>
          <div><dt>Rainfall observed</dt><dd className="num">{time(risk.features.rainfall_observed_at)}</dd></div>
          <div><dt>Intervals available</dt><dd className="num">{number(risk.features.coverage_3h * 100, 0)}<small>% of 3 h</small></dd></div>
        </dl>
        <div className="gauge-row"><Gauge level={risk.features.water_level_m} stale={gaugeStale} /><div><span className="field-label">Local demo gauge</span><strong className="num">{number(risk.features.water_level_m)}<small> m{gaugeStale ? ' · stale' : ''}</small></strong><p>Observed {time(levelTime)}.<br />Synthetic datum; not road-water depth.</p></div></div>
        <div className="validity-row"><span>Issued {time(risk.issued_at)}</span><span>{risk.expired ? 'Expired' : `Valid to ${time(risk.valid_until)}`}</span></div>
        <details className="reason-details"><summary>Rule and source details</summary><p>{risk.rule_version} · {property.source_resolution_m / 1000} km source resolution.</p><ul>{risk.reasons.map(reason => <li key={reason}>{reason}</li>)}</ul></details>
        <span className="index-caption">Relative demo index · No validated flood probability</span>
      </section>
    </div>
    <div className="history-reports-grid">
      <section className="panel history-panel"><div className="panel-header"><h2>Rainfall history</h2><span className="meta">{property.ward_name} · 6 demo hours</span></div>
        {historyError ? <ErrorMessage retry={() => setRetry(value => value + 1)}>{historyError}</ErrorMessage> : <RainChart observations={observations} now={data.clock} />}
        <p className="chart-caption">Hourly totals from 15-minute observations. Pale bars have missing intervals; absent observations remain blank.</p>
      </section>
      <section className="panel recent-panel"><div className="panel-header"><h2>Observed waterlogging</h2><button className="text-button" onClick={() => navigate('reports')}>View reports<ArrowUpRight size={13} /></button></div>
        {data.reports.length ? data.reports.slice(0, 2).map(report => <div className="recent-report" key={report.id}><CheckCircle2 size={17} /><div><strong>{data.areas.features.find(area => area.properties.id === report.area_id)?.properties.ward_name}</strong><p>{severityWord(report.severity)} · {time(report.observed_at)}</p><span className="meta">Verified · expires {time(report.expires_at)}</span></div></div>) : <p className="empty-copy">No current verified reports. A missing report does not establish clear roads.</p>}
        <Note>Observed reports describe conditions at a place and time. They are separate from the risk index.</Note>
      </section>
    </div>
  </>;
}
