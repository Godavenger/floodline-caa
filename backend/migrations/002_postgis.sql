CREATE EXTENSION IF NOT EXISTS postgis;
ALTER TABLE areas ADD COLUMN IF NOT EXISTS geom geometry(Geometry, 4326);
ALTER TABLE road_edges ADD COLUMN IF NOT EXISTS geom geometry(LineString, 4326);
ALTER TABLE reports ADD COLUMN IF NOT EXISTS geom geometry(Point, 4326)
    GENERATED ALWAYS AS (ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)) STORED;
CREATE OR REPLACE FUNCTION floodline_sync_geometry() RETURNS trigger AS $$
BEGIN
    NEW.geom := ST_SetSRID(ST_GeomFromGeoJSON(NEW.geometry_json), 4326);
    IF NOT ST_IsValid(NEW.geom) THEN
        RAISE EXCEPTION 'Invalid geometry for %', NEW.id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
DROP TRIGGER IF EXISTS areas_geometry_sync ON areas;
CREATE TRIGGER areas_geometry_sync BEFORE INSERT OR UPDATE OF geometry_json ON areas
    FOR EACH ROW EXECUTE FUNCTION floodline_sync_geometry();
DROP TRIGGER IF EXISTS roads_geometry_sync ON road_edges;
CREATE TRIGGER roads_geometry_sync BEFORE INSERT OR UPDATE OF geometry_json ON road_edges
    FOR EACH ROW EXECUTE FUNCTION floodline_sync_geometry();
UPDATE areas SET geom = ST_SetSRID(ST_GeomFromGeoJSON(geometry_json), 4326);
UPDATE road_edges SET geom = ST_SetSRID(ST_GeomFromGeoJSON(geometry_json), 4326);
CREATE INDEX IF NOT EXISTS area_spatial_index ON areas USING GIST(geom);
CREATE INDEX IF NOT EXISTS road_spatial_index ON road_edges USING GIST(geom);
CREATE INDEX IF NOT EXISTS report_spatial_index ON reports USING GIST(geom);
