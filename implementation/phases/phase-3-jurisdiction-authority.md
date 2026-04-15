# Phase 3: Jurisdiction & Authority Mapping

**Goal:** Build the authority resolution engine — the platform's core differentiator. Given a GPS location, resolve which authority is responsible, which ward/circle/zone the point belongs to, and display the full accountability chain.

**Deliverable:** Issue detail page shows the likely responsible authority and area hierarchy with confidence scoring. Polygon import pipeline is operational.

**Depends on:** Phase 2 (Map + Issue Model) completed.

---

## 3.1 Additional Database Tables

### `authorities` table
| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| name | VARCHAR | e.g., GHMC, HMDA, R&B, NHAI |
| authority_type | ENUM(municipal, planning, highway, state, ward_level, contractor, other) | |
| parent_authority_id | UUID (FK, nullable) | hierarchical relationship |
| description | TEXT | |
| website_url | VARCHAR | |
| grievance_url | VARCHAR | |
| contact_phone | VARCHAR | |
| contact_email | VARCHAR | |
| is_active | BOOLEAN | |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

### `jurisdiction_polygons` table
| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| authority_id | UUID (FK, nullable) | |
| layer_type | ENUM(ward, circle, zone, municipality, constituency, special_road_zone, other) | |
| name | VARCHAR | e.g., "Ward 42", "Serilingampally Zone" |
| code | VARCHAR | e.g., "42" |
| geom | geometry(MultiPolygon, 4326) | PostGIS spatial column |
| source_name | VARCHAR | e.g., "OSM", "GHMC Official" |
| source_version | VARCHAR | for data versioning |
| is_active | BOOLEAN | |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

### `responsibility_mappings` table
| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| polygon_id | UUID (FK, nullable) | |
| road_segment_id | UUID (FK, nullable) | |
| primary_authority_id | UUID (FK) | |
| secondary_authority_id | UUID (FK, nullable) | |
| ownership_confidence | NUMERIC(5,4) | 0.0000 to 1.0000 |
| notes | TEXT | |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

### `accountability_chain_nodes` table
| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| authority_id | UUID (FK) | |
| jurisdiction_polygon_id | UUID (FK, nullable) | |
| node_type | ENUM(field_officer, engineer, circle_office, zonal_office, elected_rep, escalation, grievance_channel) | |
| display_name | VARCHAR | |
| title | VARCHAR | e.g., AEE, Deputy Commissioner, Corporator |
| phone | VARCHAR | |
| email | VARCHAR | |
| display_order | INTEGER | ordering in the chain |
| is_public | BOOLEAN | controls public visibility |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

### `road_segments` table
| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| name | VARCHAR | |
| alt_names | TEXT[] | array of alternate names |
| road_class | VARCHAR | e.g., national_highway, state_highway, municipal, local |
| osm_way_id | BIGINT (nullable) | OpenStreetMap reference |
| geom | geometry(MultiLineString, 4326) | |
| source_name | VARCHAR | |
| source_version | VARCHAR | |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

### Spatial Indexes
Add GiST indexes on:
- `jurisdiction_polygons.geom`
- `road_segments.geom`

---

## 3.2 Polygon Import Pipeline

### Supported Import Formats
1. **GeoJSON** — primary format
2. **Shapefile** (.shp + .shx + .dbf + .prj) — via Fiona/GDAL
3. **CSV with WKT or GeoJSON column** — for tabular data with geometry
4. **Manual admin upload** — single polygon via admin UI

### Import Job Design
Background task (Celery/RQ) that:
1. Accepts uploaded file and layer metadata
2. Validates geometry (valid polygons, correct CRS/SRID)
3. Transforms to EPSG:4326 if needed
4. Parses features and maps properties to schema fields
5. Upserts into `jurisdiction_polygons` table
6. Logs import results (success count, error count, skipped)
7. Triggers spatial index rebuild if needed

### API: `POST /api/v1/admin/jurisdictions/import`
**Request (multipart):**
- `file`: GeoJSON/Shapefile/CSV
- `layer_type`: ward | circle | zone | municipality | constituency | special_road_zone
- `source_name`: string
- `source_version`: string
- `authority_id`: optional UUID

**Response:**
```json
{
  "job_id": "uuid",
  "status": "processing",
  "features_found": 150
}
```

### Data Versioning
- Each import stores `source_name` and `source_version`
- Old polygons can be deactivated (`is_active = false`) when new data arrives
- Never hard-delete polygon data — keep for audit trail

### Required Datasets for Hyderabad
| Dataset | Layer Type | Priority | Source |
|---------|-----------|----------|--------|
| Ward boundaries | ward | P0 | GHMC / public civic data |
| Zone boundaries | zone | P0 | GHMC / public data |
| Circle boundaries | circle | P1 | GHMC / public data |
| Municipality boundaries | municipality | P1 | Revenue / public data |
| Road network | road_segments | P0 | OpenStreetMap |
| Constituency boundaries | constituency | P2 | ECI / public data |
| Special road zones (NH, SH) | special_road_zone | P1 | NHAI / R&B / manual |

### Seed Data Strategy
- Seed Hyderabad ward polygons from available open datasets
- Import OSM road network for Hyderabad metro area
- Create placeholder authority records (GHMC, HMDA, R&B, NHAI, HGCL)
- Create sample accountability chain nodes with placeholder contacts
- Mark all seeded data with low confidence until verified

---

## 3.3 Authority Resolution Engine

### This is the platform's moat.

### Inputs
- `latitude`, `longitude` (required)
- Nearest road segment (computed)
- Intersecting jurisdiction polygons (computed)
- Road metadata (class, name, OSM tags)
- Admin overrides (if any)

### Resolution Pipeline
Execute steps in order, accumulating scores:

#### Step 1: Check Special Road Zones
```sql
SELECT jp.id, jp.authority_id, rm.ownership_confidence
FROM jurisdiction_polygons jp
JOIN responsibility_mappings rm ON rm.polygon_id = jp.id
WHERE jp.layer_type = 'special_road_zone'
  AND jp.is_active = true
  AND ST_Contains(jp.geom, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326));
```
If match found with high confidence → return immediately.

#### Step 2: Check Road Segment Explicit Mapping
```sql
SELECT rs.id, rs.road_class, rm.primary_authority_id, rm.ownership_confidence
FROM road_segments rs
JOIN responsibility_mappings rm ON rm.road_segment_id = rs.id
WHERE ST_DWithin(rs.geom, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography, 50)
ORDER BY ST_Distance(rs.geom, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography)
LIMIT 1;
```
If explicit road authority mapping exists → high weight.

#### Step 3: Check Municipal Ward / Circle / Zone
```sql
SELECT jp.id, jp.layer_type, jp.name, jp.code, jp.authority_id
FROM jurisdiction_polygons jp
WHERE jp.is_active = true
  AND jp.layer_type IN ('ward', 'circle', 'zone')
  AND ST_Contains(jp.geom, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326))
ORDER BY jp.layer_type;
```
Returns ward, circle, and zone containment.

#### Step 4: Road Class Inference
If road segment found, use `road_class` to infer authority:
| Road Class | Likely Authority | Base Confidence |
|-----------|-----------------|-----------------|
| national_highway | NHAI | 0.85 |
| state_highway | R&B | 0.75 |
| municipal | GHMC | 0.70 |
| local | GHMC | 0.65 |
| unknown | GHMC (default) | 0.40 |

#### Step 5: Apply Admin Overrides
Check `responsibility_mappings` for manual admin entries that override automatic resolution.

#### Step 6: Compute Final Score
Combine scores from all steps using weighted aggregation:
- Special zone match: weight 1.0
- Explicit road mapping: weight 0.9
- Ward containment + municipal default: weight 0.7
- Road class inference: weight 0.6
- Normalize to 0.00–1.00

### API: `GET /api/v1/lookup/authority`
**Query Parameters:**
| Param | Type | Required |
|-------|------|----------|
| lat | float | yes |
| lng | float | yes |

**Response:**
```json
{
  "primary_authority": {
    "id": "uuid",
    "name": "GHMC",
    "authority_type": "municipal",
    "confidence": 0.82
  },
  "alternate_authorities": [
    { "id": "uuid", "name": "HMDA", "confidence": 0.12 },
    { "id": "uuid", "name": "R&B", "confidence": 0.06 }
  ],
  "ward": {
    "id": "uuid",
    "name": "Ward 42",
    "code": "42"
  },
  "circle": {
    "id": "uuid",
    "name": "Serilingampally Circle"
  },
  "zone": {
    "id": "uuid",
    "name": "Serilingampally Zone"
  },
  "nearest_road": {
    "id": "uuid",
    "name": "Gachibowli Main Road",
    "road_class": "municipal",
    "distance_meters": 12.5
  },
  "accountability_chain": [
    {
      "type": "field_officer",
      "title": "AEE",
      "display_name": "Name",
      "is_public": true
    },
    {
      "type": "circle_office",
      "title": "Deputy Commissioner",
      "display_name": "Name",
      "is_public": true
    },
    {
      "type": "elected_rep",
      "title": "Corporator",
      "display_name": "Name",
      "is_public": true
    }
  ],
  "confidence_level": "high",
  "resolution_metadata": {
    "steps_matched": ["ward_containment", "road_class_inference"],
    "data_version": "2026-04"
  }
}
```

### Confidence Levels
| Score Range | Level | Display |
|------------|-------|---------|
| 0.80–1.00 | high | "High confidence" |
| 0.50–0.79 | medium | "Medium confidence" |
| 0.20–0.49 | low | "Low confidence — may need verification" |
| 0.00–0.19 | very_low | "Unable to determine with certainty" |

### Performance Target
- Authority lookup under 500ms for common cases
- Cache authority results per geohash cell (Redis)
- Invalidate cache on polygon/mapping updates

---

## 3.4 Issue-Authority Integration

### On Issue Creation / Report Submission
1. Run authority resolution for the issue location
2. Store resolved authority data on the issue (or linked table)
3. Display on issue detail page

### Issue Detail Page — Accountability Section
Display:
- **"Who is responsible?"** header
- Primary authority name and type
- Confidence badge (high / medium / low)
- Ward, circle, zone hierarchy
- Nearest road name
- Accountability chain (ordered list of officials)
- Disclaimer: "This location **likely** falls under [Authority], [Ward]. The authority mapping has [confidence level] confidence."

### Important UX Copy
- Always use "likely authority" — never state authority as absolute fact
- Show confidence level prominently
- Link to "Is this wrong? Help us correct it" for community feedback (future)

---

## 3.5 Reverse Geocode Endpoint

### API: `GET /api/v1/lookup/reverse-geocode`
**Query Parameters:** `lat`, `lng`

**Response:**
```json
{
  "ward": { "name": "Ward 42", "code": "42" },
  "zone": { "name": "Serilingampally Zone" },
  "circle": { "name": "Serilingampally Circle" },
  "nearest_road": { "name": "Gachibowli Main Road", "distance_meters": 15 },
  "locality_hint": "Gachibowli"
}
```

Used in the report flow to show the user where their pin lands before submission.

---

## 3.6 Admin Override Support

### Why Overrides Are Essential
Automatic resolution will be wrong sometimes. Admins must be able to correct:
- Wrong authority assignment
- Wrong ward containment (bad polygon data)
- Shared/disputed road ownership
- Roads that changed authority recently

### Admin Override Actions
- **Manually set primary authority** for an issue or road segment
- **Set ownership confidence** manually
- **Mark "ownership disputed"** flag
- **Add notes** explaining the override
- **All overrides logged** in `audit_logs`

### API: Override responsibility mapping
```http
POST /api/v1/admin/responsibility-mappings
PATCH /api/v1/admin/responsibility-mappings/{id}
```

---

## 3.7 Map Overlays

### Ward Boundary Overlay
- Add optional ward polygon overlay on the public map
- Toggle-able layer in map controls
- Semi-transparent fill with ward label
- Helps users understand administrative boundaries

### Future Overlays
- Zone boundaries
- Authority jurisdiction shading
- Hotspot heatmap layer (Phase 5)

---

## Acceptance Criteria for Phase 3

- [ ] All Phase 3 database tables created with migrations
- [ ] GiST spatial indexes on `jurisdiction_polygons.geom` and `road_segments.geom`
- [ ] GeoJSON import pipeline works for ward/zone/circle polygons
- [ ] Shapefile import pipeline works
- [ ] Road segment import from OSM data works
- [ ] Authority resolution engine runs the full scoring pipeline
- [ ] Authority lookup API returns primary + alternates with confidence
- [ ] Authority lookup API responds under 500ms
- [ ] Accountability chain resolves and displays for locations within coverage
- [ ] Confidence levels displayed correctly (high/medium/low/very_low)
- [ ] Issue detail page shows accountability section with authority + chain
- [ ] Reverse geocode endpoint returns ward/zone/road for a point
- [ ] Admin can manually override authority for an issue/road segment
- [ ] Admin overrides logged in audit_logs
- [ ] Ward boundary overlay available on public map
- [ ] Seed data loaded: Hyderabad wards, zones, authorities, sample road segments
- [ ] All confidence values use "likely" language — never absolute claims

---

## Related Spec Sections
- Section 6.8: Accountability engine
- Section 6.9: Confidence model
- Section 11.7–11.11: Authority/jurisdiction/road schema
- Section 12: Geospatial design
- Section 13: Authority resolution engine (13.1–13.4)
- Section 21: Data acquisition plan
- Section 25.3: Design for partial authority certainty
- Section 25.8: Build admin data correction tools early
