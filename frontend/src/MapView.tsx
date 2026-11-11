import { useEffect, useId, useMemo } from 'react';
import { MapContainer, GeoJSON, TileLayer, CircleMarker, Polyline, Tooltip, useMap, useMapEvents } from 'react-leaflet';
import type { PathOptions } from 'leaflet';
import type { Dashboard, Report, Route, RiskLevel } from './types';

const riskColors: Record<RiskLevel, string> = { low: 'var(--map-low)', elevated: 'var(--map-elevated)', high: 'var(--map-high)', unknown: 'var(--map-unknown)' };

function ResizeMap({ bounds }: { bounds: Dashboard['pilot']['bounds'] }) {
  const map = useMap();
  useEffect(() => {
    const observer = new ResizeObserver(() => { map.invalidateSize(); map.fitBounds(bounds, { padding: [16, 16], animate: false }); });
    observer.observe(map.getContainer());
    return () => observer.disconnect();
  }, [map, bounds]);
  return null;
}

function PickPoint({ onPick }: { onPick?: (longitude: number, latitude: number) => void }) {
  useMapEvents({ click(event) { onPick?.(event.latlng.lng, event.latlng.lat); } });
  return null;
}

type Props = { data: Dashboard; selected: string; onSelect?: (id: string) => void; reports?: Report[]; route?: Route | null;
  basemap?: boolean; onPick?: (longitude: number, latitude: number) => void; pin?: { longitude: number; latitude: number } | null; small?: boolean; riskLayer?: boolean };

export default function MapView({ data, selected, onSelect, reports = data.reports, route, basemap = false, onPick, pin, small = false, riskLayer = true }: Props) {
  const unknownPattern = `unknown-${useId().replace(/[^a-zA-Z0-9_-]/g, '')}`;
  const risks = useMemo(() => new Map(data.risk.map(risk => [risk.area_id, risk])), [data.risk]);
  const excluded = new Set(data.hazards.flatMap(hazard => hazard.edge_ids));
  return <div className={`map-wrap ${small ? 'map-small' : ''}`}>
    <svg width="0" height="0" className="map-pattern-defs" aria-hidden="true"><defs><pattern id={unknownPattern} patternUnits="userSpaceOnUse" width="7" height="7">
      <rect width="7" height="7" fill="var(--map-unknown)" /><path d="M-1 1L1-1M0 7L7 0M6 8L8 6" stroke="var(--unknown-hatch)" strokeWidth="1" />
    </pattern></defs></svg>
    <MapContainer zoomSnap={0.25} bounds={data.pilot.bounds} boundsOptions={{ padding: [16, 16] }}
      minZoom={12} maxZoom={18} scrollWheelZoom={false} attributionControl={true} className="map-canvas">
      <ResizeMap bounds={data.pilot.bounds} /><PickPoint onPick={onPick} />
      {basemap && <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' />}
      <GeoJSON key={`cells-${data.risk.map(risk => `${risk.id}:${risk.risk_level}`).join('-')}-${selected}-${riskLayer}`} data={data.areas}
        style={feature => {
          const id = feature?.properties?.id as string;
          const risk = risks.get(id);
          return { fillColor: riskLayer ? risk?.risk_level === 'unknown' ? `url(#${unknownPattern})` : riskColors[risk?.risk_level ?? 'unknown'] : 'var(--map-area)', fillOpacity: basemap ? 0.5 : 0.85,
            color: id === selected ? 'var(--selected-map)' : 'var(--map-edge)', weight: id === selected ? 2.4 : 1.5,
            dashArray: risk?.risk_level === 'unknown' ? '4 4' : undefined } as PathOptions;
        }} onEachFeature={(feature, layer) => {
          const id = feature.properties.id as string;
          // Plain text DOM avoids HTML injection in Leaflet's string tooltip API.
          const label = document.createElement('span');
          label.textContent = `${feature.properties.name}: ${risks.get(id)?.risk_level ?? 'unknown'}`;
          layer.bindTooltip(label, { sticky: true });
          layer.on('click', () => onSelect?.(id));
        }} />
      {!basemap && data.pilot.cartography.parks.map((park, index) => <GeoJSON key={`park-${index}`} data={park} style={{ fillColor: 'var(--map-park)', fillOpacity: 0.8, stroke: false }} />)}
      {!basemap && <GeoJSON data={data.pilot.cartography.river} style={{ color: 'var(--map-river)', weight: 17, opacity: 0.85 }} />}
      <GeoJSON data={data.network} style={{ color: 'var(--map-road-casing)', weight: 7, opacity: 0.96 }} interactive={false} />
      <GeoJSON key={`roads-${data.hazards.map(hazard => hazard.id).join('-')}`} data={data.network}
        style={feature => ({ color: feature?.properties.edge_ids.some((id: string) => excluded.has(id)) ? 'var(--negative)' : 'var(--map-road)',
          weight: feature?.properties.edge_ids.some((id: string) => excluded.has(id)) ? 4.5 : 1.5,
          opacity: 0.9, dashArray: feature?.properties.edge_ids.some((id: string) => excluded.has(id)) ? '7 5' : undefined })} interactive={false} />
      {data.wards.map(ward => {
        const area = data.areas.features.find(feature => feature.properties.ward_id === ward.id && feature.properties.id.endsWith('2'))!;
        const points = area.geometry.coordinates[0];
        const longitude = (points[0][0] + points[1][0]) / 2;
        const latitude = points[2][1] - 0.0015;
        return <CircleMarker key={ward.id} center={[latitude, longitude]} radius={0} interactive={false}><Tooltip permanent direction="center" className="ward-label">{ward.name}</Tooltip></CircleMarker>;
      })}
      {data.network.nodes.filter(node => node.landmark && node.id !== 'island').map(node => <CircleMarker key={node.id} center={[node.latitude, node.longitude]} radius={3}
        pathOptions={{ fillColor: 'var(--map-landmark)', color: 'var(--map-marker-edge)', weight: 1.5, fillOpacity: 1 }}><Tooltip direction="top" className="landmark-label">{node.name}</Tooltip></CircleMarker>)}
      {reports.filter(report => report.status === 'verified' || report.status === 'pending').map(report => <CircleMarker key={report.id} center={[report.latitude, report.longitude]} radius={7}
        pathOptions={{ color: 'var(--map-marker-edge)', weight: 2, fillColor: report.status === 'verified' ? 'var(--negative)' : 'var(--map-pending)', fillOpacity: 1 }}>
        <Tooltip>{report.status === 'verified' ? 'Verified waterlogging' : 'Your pending report'}</Tooltip>
      </CircleMarker>)}
      {route?.geometry && <Polyline positions={route.geometry.coordinates.map(point => [point[1], point[0]])} pathOptions={{ color: 'var(--accent)', weight: 5, opacity: 1 }} />}
      {pin && <CircleMarker center={[pin.latitude, pin.longitude]} radius={9} pathOptions={{ color: 'var(--selected-map)', weight: 3, fillColor: 'var(--map-pin-fill)', fillOpacity: 1 }}><Tooltip>Selected report location</Tooltip></CircleMarker>}
    </MapContainer>
    <div className="map-source">Synthetic geography · WGS84 · approximately 1 km analysis cells</div>
    <span className="sr-only">Use the area selector and evidence list for a text alternative to the map. The geography and reports are synthetic.</span>
  </div>;
}
