import { useEffect, useState } from 'react';
import { Database, FileCheck2, ArrowUpRight } from 'lucide-react';
import { api, dateTime } from './api';
import type { Dashboard, Source } from './types';
import { ErrorMessage, LoadingRows, Note } from './ui';

type Evaluation = { historical_accuracy_established: boolean; reason?: string; rule_version: string; mode: string;
  independent_events?: number; usable_rows?: number; split?: { train: { event_count: number; row_count: number }; validation: { event_count: number; row_count: number }; test: { event_count: number; row_count: number } };
  candidate_promoted?: boolean; status?: string };

export default function DataScreen({ data }: { data: Dashboard }) {
  const [sources, setSources] = useState<Source[]>([]);
  const [evaluation, setEvaluation] = useState<Evaluation | null>(null);
  const [error, setError] = useState('');
  const [version, setVersion] = useState(0);
  useEffect(() => {
    let active = true;
    Promise.all([api<{ items: Source[] }>('/sources'), api<Evaluation>('/evaluation')]).then(([sources, evaluation]) => { if (active) { setSources(sources.items); setEvaluation(evaluation); setError(''); } }).catch(error => { if (active) setError(error.message); });
    return () => { active = false; };
  }, [version, data.scenario]);
  return <><div className="title-row"><div><h1>Data and model evidence</h1><p>Trace the inputs, understand the active fallback and identify what still needs real-world validation.</p></div><button className="button" onClick={() => setVersion(value => value + 1)}>Refresh sources</button></div>
    {error && <ErrorMessage retry={() => setVersion(value => value + 1)}>{error}</ErrorMessage>}
    <div className="data-evidence-layout"><section className="panel sources-panel"><div className="panel-header"><h2>Environmental sources</h2><Database size={17} /></div>
      {sources.length ? sources.map(source => <article key={source.id} className="source-row"><div className="report-row-heading"><strong>{source.name}</strong><span className="status neutral-status">Synthetic</span></div><dl className="source-facts"><div><dt>Observation interval</dt><dd className="num">{source.interval_minutes} min</dd></div><div><dt>Available records</dt><dd className="num">{source.available_records.toLocaleString('en-IN')}</dd></div><div><dt>Last observation</dt><dd>{source.latest_observed_at ? dateTime(source.latest_observed_at) : 'Unavailable'}</dd></div><div><dt>Units</dt><dd>{source.unit}</dd></div></dl><p className="field-help">{source.licence}{source.datum ? `. ${source.datum}.` : '.'}</p></article>) : <LoadingRows count={2} />}
      <Note>Original fixture files and SHA-256 checksums are included in the source bundle. Delayed receipts are excluded from earlier issue-time features.</Note>
    </section><section className="panel model-panel"><div className="panel-header"><h2>Active approach</h2><FileCheck2 size={17} /></div>
      <span className="status neutral-status">Sparse-data fallback</span><h3>Susceptibility + rainfall thresholds</h3><p>The map uses an interpretable relative index built from synthetic rainfall, terrain and drainage. It does not display a flood probability.</p>
      <dl className="source-facts"><div><dt>Rule version</dt><dd>{data.rule_version}</dd></div><div><dt>Historical accuracy</dt><dd>Not established</dd></div><div><dt>Spatial support</dt><dd>Approximately 1 km demo cells</dd></div><div><dt>Candidate promotion</dt><dd>Not promoted</dd></div></dl>
      <p className="field-help">{evaluation?.reason ?? 'No independent historical event labels are present. Real labels, credible negative observations and a frozen event/temporal split are needed before a forecast can be evaluated.'}</p>
      <details><summary>Demo evaluation and promotion gate</summary>{evaluation?.split ? <><p>The software evaluation uses {evaluation.independent_events} independent synthetic scenarios. Its results do not validate real flood prediction.</p><div className="split-summary">{(['train', 'validation', 'test'] as const).map(key => <div key={key}><span>{key.charAt(0).toUpperCase() + key.slice(1)}</span><strong className="num">{evaluation.split![key].event_count}<small> events</small></strong><p>{evaluation.split![key].row_count} rows</p></div>)}</div></> : <p>Run the documented evaluation command to create the synthetic software experiment. Real-world model promotion remains blocked by missing historical evidence.</p>}</details>
    </section></div>
    <section className="panel data-contracts-panel"><div className="panel-header"><h2>Interpretation rules</h2><a className="text-link" href="/docs" target="_blank" rel="noreferrer">API reference<ArrowUpRight size={14} /></a></div>
      <div className="interpretation-rules"><div><h3>Risk is relative</h3><p>A hand-weighted index describes warning conditions; it cannot supply a calibrated probability.</p></div><div><h3>Reports are observations</h3><p>Only current reviewed road evidence changes exclusions. A coarse risk cell alone does not close a street.</p></div><div><h3>Unknown stays unknown</h3><p>Missing or stale rainfall prevents a reliable current estimate. A past update keeps its original issue time.</p></div></div>
      <p className="field-help">Pilot: {data.pilot.name} · geometry {data.pilot.version} · WGS84 display, UTM zone 45N distance calculations. Names and road locations are invented.</p>
    </section>
  </>;
}
