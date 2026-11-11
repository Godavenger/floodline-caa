import { useEffect, useMemo, useRef, useState } from 'react';
import type { Observation } from './types';
import { time } from './api';

export function RainChart({ observations, now }: { observations: Observation[]; now: string }) {
  const svg = useRef<SVGSVGElement>(null);
  const [width, setWidth] = useState(620);
  useEffect(() => {
    const element = svg.current?.parentElement;
    if (!element) return;
    const observer = new ResizeObserver(() => setWidth(Math.max(250, element.clientWidth - 40)));
    observer.observe(element);
    return () => observer.disconnect();
  }, []);
  const bins = useMemo(() => {
    const finish = new Date(now).getTime();
    const begin = finish - 6 * 3600000;
    const latest = new Map<string, Observation>();
    observations.filter(row => row.variable === 'rainfall' && row.quality === 'good' && new Date(row.observed_at).getTime() > begin)
      .sort((a, b) => a.received_at.localeCompare(b.received_at)).forEach(row => latest.set(row.source_id + row.observed_at, row));
    return Array.from({ length: 6 }, (_, index) => {
      const start = begin + index * 3600000;
      const end = start + 3600000;
      const rows = [...latest.values()].filter(row => new Date(row.observed_at).getTime() > start && new Date(row.observed_at).getTime() <= end);
      return { end, value: rows.length ? rows.reduce((sum, row) => sum + (row.value ?? 0), 0) : null, count: rows.length };
    });
  }, [observations, now]);
  const max = Math.max(20, Math.ceil(Math.max(...bins.map(bin => bin.value ?? 0)) / 20) * 20 + 20);
  const height = 164, left = 32, top = 16, bottom = 130, plotWidth = width - left - 10;
  return <svg ref={svg} className="rain-chart" viewBox={`0 0 ${width} ${height}`} role="img" aria-label={`Synthetic hourly rainfall for the past six hours. ${bins.map(bin => `${time(new Date(bin.end).toISOString())}: ${bin.value == null ? 'no observation' : bin.value.toFixed(1) + ' mm'}`).join('; ')}`}>
    {[0, 1, 2].map(index => {
      const value = max * index / 2;
      const y = bottom - (bottom - top) * value / max;
      return <g key={index}><line x1={left} y1={y} x2={width - 16} y2={y} stroke="var(--rule)" /><text x={left - 8} y={y + 4} textAnchor="end">{value}</text></g>;
    })}
    <text x={6} y={10}>mm</text>
    {bins.map((bin, index) => {
      const pitch = plotWidth / 6, x = left + index * pitch + pitch * 0.18;
      const barHeight = (bin.value ?? 0) / max * (bottom - top);
      return <g key={index}>
        {bin.value != null && <rect x={x} y={bottom - barHeight} width={pitch * 0.52} height={barHeight} rx={1} fill="var(--accent)" opacity={bin.count < 4 ? 0.45 : 0.9}><title>{bin.value.toFixed(1)} mm; {bin.count}/4 intervals observed</title></rect>}
        <text x={x + pitch * 0.26} y={152} textAnchor="middle">{time(new Date(bin.end).toISOString()).replace(' IST', '')}</text>
      </g>;
    })}
  </svg>;
}

export function Gauge({ level, stale }: { level: number | null; stale: boolean }) {
  const ratio = level == null ? 0 : Math.min(1, Math.max(0, level / 8));
  return <div className={`gauge ${stale ? 'gauge-stale' : ''}`} aria-hidden="true">
    <div className="gauge-column"><div className="gauge-water" style={{ height: `${ratio * 100}%` }} /></div>
    <div className="gauge-marks">{[8, 6, 4, 2, 0].map(value => <span key={value}>{value}</span>)}</div>
  </div>;
}
