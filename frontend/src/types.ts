import type { FeatureCollection, LineString, Polygon } from 'geojson';

export type RiskLevel = 'unknown' | 'low' | 'elevated' | 'high';
export type Screen = 'map' | 'reports' | 'routes' | 'alerts' | 'data' | 'review';
export type Session = { authenticated: boolean; role: 'visitor' | 'resident' | 'moderator'; username: string | null };
export type AreaProperties = { id: string; name: string; ward_id: string; ward_name: string; source_resolution_m: number; geometry_version: string; relative_elevation_m: number; drainage_constraint: number; impervious_fraction: number; distance_to_water_m: number };
export type Features = {
  rainfall_1h_mm: number | null; rainfall_3h_mm: number | null; rainfall_6h_mm: number | null; rainfall_24h_mm: number | null;
  coverage_1h: number; coverage_3h: number; missing_fraction: number;
  rainfall_observed_at: string | null; level_observed_at: string | null; water_level_m: number | null;
  datum: string; level_age_minutes: number | null;
};
export type Risk = { id: string; area_id: string; ward_id: string; area_name: string; risk_level: RiskLevel; index: number | null; susceptibility_index: number;
  data_support: 'adequate' | 'limited' | 'insufficient'; issued_at: string; valid_until: string; features: Features; rainfall_age_minutes: number | null;
  rule_version: string; source_resolution_m: number; reasons: string[]; stale: boolean; expired: boolean; previous_index?: number | null };
export type Report = { id: string; area_id: string; description: string; severity: string; longitude: number; latitude: number; observed_at: string; submitted_at: string;
  expires_at: string; status: 'pending' | 'verified' | 'rejected' | 'duplicate' | 'resolved' | 'expired'; has_image: boolean; image_available: boolean; image_url: string | null; review_reason?: string | null };
export type RoadProperties = { id: string; name: string; segment_id: string; edge_ids: string[] };
export type Node = { id: string; name: string; longitude: number; latitude: number; landmark: boolean };
export type Network = FeatureCollection<LineString, RoadProperties> & { nodes: Node[]; snap_tolerance_m: number };
export type Dashboard = {
  pilot: { name: string; description: string; bounds: [[number, number], [number, number]]; version: string; cartography: { river: LineString; parks: Polygon[] } };
  clock: string; mode: 'synthetic'; scenario: string; areas: FeatureCollection<Polygon, AreaProperties>; risk: Risk[];
  wards: { id: string; name: string; risk_level: RiskLevel; cell_ids: string[]; unknown_cells: number }[];
  network: Network; reports: Report[]; hazards: { id: string; edge_ids: string[]; report_id: string; expires_at: string }[];
  summary: { cells: number; warnings: number; unknown: number; active_hazards: number }; rule_version: string; forecast_validated: false;
};
export type Observation = { source_id: string; observed_at: string; received_at: string; variable: string; value: number | null; unit: string; quality: string; interval_minutes: number };
export type Subscription = { id: string; ward_id: string; channel: string; active: boolean };
export type Alert = { id: string; ward_id: string; kind: string; severity: string; state: string; attempts: number; issued_at: string; expires_at: string; message: string; support: string; next_attempt_at: string | null; evidence_current: boolean };
export type Route = { status: string; message: string; geometry?: LineString; distance_m?: number; edge_ids?: string[]; excluded_edge_ids?: string[]; hazard_ids?: string[]; calculated_at: string; snap_distance_m?: number[] };
export type Source = { id: string; name: string; kind: string; unit: string; interval_minutes: number; licence: string; latest_observed_at: string | null; available_records: number; datum?: string };
export type Operations = { counts: Record<string, number>; initial_ingestion: { accepted: number; duplicates: number; quarantined: number; reasons: string[] };
  jobs: { id: string; kind: string; status: string; started_at: string; details: { new_risk_records?: number; new_alerts?: number } }[];
  audit: { action: string; at: string; subject_id: string; details: Record<string, unknown> }[];
  failed_deliveries: { id: string; attempts: number; next_attempt_at: string | null; ward_id: string }[] };
