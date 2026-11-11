import { useEffect, useRef, useState } from 'react';
import { ArrowDownUp, Route as RouteIcon, ArrowUpRight } from 'lucide-react';
import { number, post, time } from './api';
import type { Dashboard, Route } from './types';
import MapView from './MapView';
import { ErrorMessage, Note } from './ui';

export default function RoutesScreen({ data }: { data: Dashboard }) {
  const [start, setStart] = useState('n0-1');
  const [end, setEnd] = useState('n4-1');
  const [route, setRoute] = useState<Route | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const sequence = useRef(0);
  const startNode = data.network.nodes.find(node => node.id === start)!;
  const endNode = data.network.nodes.find(node => node.id === end)!;
  const hazardVersion = data.hazards.map(hazard => `${hazard.id}:${hazard.expires_at}`).join('|');
  async function calculate() {
    const request = ++sequence.current;
    setLoading(true); setError(''); setSubmitted(true);
    try {
      const result = await post<Route>('/routes', { start: { longitude: startNode.longitude, latitude: startNode.latitude }, end: { longitude: endNode.longitude, latitude: endNode.latitude } });
      if (request === sequence.current) setRoute(result);
    } catch (error) { if (request === sequence.current) { setError((error as Error).message); setRoute(null); } }
    finally { if (request === sequence.current) setLoading(false); }
  }
  useEffect(() => {
    if (submitted) void calculate();
    return () => { sequence.current++; };
    // Recompute a requested route when its known exclusions change.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hazardVersion]);
  function changePoint(value: string, which: 'start' | 'end') {
    sequence.current++; setRoute(null); setSubmitted(false); setLoading(false);
    if (which === 'start') setStart(value); else setEnd(value);
  }
  return <><div className="title-row"><div><h1>Route around known hazards</h1><p>Find a demonstration route that excludes current verified flooded road segments.</p></div></div>
    <div className="route-layout"><section className="panel route-controls"><div className="panel-header"><h2>Choose your journey</h2><RouteIcon size={18} /></div>
      <form onSubmit={event => { event.preventDefault(); void calculate(); }}>
        <div className="field"><label htmlFor="route-start">From</label><select id="route-start" value={start} onChange={event => changePoint(event.target.value, 'start')}>{data.network.nodes.filter(node => node.landmark).map(node => <option key={node.id} value={node.id}>{node.name}</option>)}</select></div>
        <button type="button" className="text-button swap-button" onClick={() => { const old = start; changePoint(end, 'start'); changePoint(old, 'end'); }}><ArrowDownUp size={14} />Swap direction</button>
        <div className="field"><label htmlFor="route-end">To</label><select id="route-end" value={end} onChange={event => changePoint(event.target.value, 'end')}>{data.network.nodes.filter(node => node.landmark).map(node => <option key={node.id} value={node.id}>{node.name}</option>)}</select></div>
        <button className="button primary full-width" type="submit" disabled={loading}>{loading ? 'Finding a route…' : 'Find route'}<ArrowUpRight size={15} /></button>
      </form>
      {error && <ErrorMessage retry={() => void calculate()}>{error}</ErrorMessage>}
      {route && <div className={`route-result ${route.status !== 'available' ? 'route-unavailable' : ''}`} role="status"><h3>{route.status === 'available' ? 'Route found' : 'Route unavailable'}</h3>
        {route.distance_m != null && <strong className="route-distance num">{number(route.distance_m / 1000, 2)}<small> km on mapped roads</small></strong>}
        <p>{route.message}</p><div className="route-detail"><span>{route.excluded_edge_ids?.length ?? 0} directed edges excluded</span><span>Calculated {time(route.calculated_at)}</span></div>
        {route.edge_ids && <details><summary>Inspect route segments</summary><ol>{route.edge_ids.map(edge => <li key={edge}>{data.network.features.find(road => road.properties.edge_ids.includes(edge))?.properties.name ?? edge}</li>)}</ol></details>}
      </div>}
      <Note>Distance is the route cost. The road graph is synthetic and includes a one-way segment and a disconnected destination.</Note>
    </section><section className="panel route-map-panel"><div className="panel-header"><h2>Verified exclusions</h2><span className="meta">{data.summary.active_hazards} active hazards</span></div>
      <MapView data={data} selected="B2" route={route} riskLayer={false} />
      <div className="route-key"><span><i className="route-key-line" />Suggested route</span><span><i className="hazard-key-line" />Verified restriction</span></div>
      <p className="chart-caption">The route geometry follows snapped graph nodes. The app does not establish that the connector from your original point is safe.</p>
    </section></div>
  </>;
}
