# Phase 2: Map + Issue Model

**Goal:** Build the public map experience with deduplicated issues, clustering, viewport-based querying, and mobile-friendly map UI. Separate the Issue entity from Report entity with proper deduplication logic.

**Deliverable:** Public interactive map with deduplicated, clustered issues. Users can view, filter, and explore road issues on the map.

**Depends on:** Phase 1 (Core Foundation) completed.

---

## 2.1 Issue Entity Separation

### Domain Model Clarification
- A **Report** is one citizen submission (raw input).
- An **Issue** is the deduplicated public problem entity (canonical).
- Multiple Reports map to one Issue via the `issue_reports` junction table.

### Issue Creation Logic
When a new report is submitted:
1. Run duplicate detection (see 2.3)
2. If a matching issue exists → link report to existing issue, increment `report_count`
3. If no match → create a new Issue from the report:
   - Set `primary_report_id` to the new report
   - Copy `issue_type` → `canonical_issue_type`
   - Copy `severity` → `canonical_severity`
   - Copy lat/lng/geom
   - Set `status = reported`
   - Set `first_reported_at` and `latest_reported_at`
   - Set `report_count = 1`, `support_count = 0`
   - Set `public_visibility = true` (after moderation)
4. Link report to issue via `issue_reports` table with `link_reason`

### Issue Title Generation
Auto-generate title from:
- Issue type (human-readable)
- Road name or landmark if provided
- Example: "Pothole — Gachibowli Main Road" or "Waterlogging — Near XYZ Junction"

---

## 2.2 Issue Aggregation & Canonical Fields

When multiple reports link to one issue:
- `canonical_severity` = highest severity among linked reports
- `canonical_issue_type` = most common type, or the primary report's type
- `latest_reported_at` = timestamp of most recent linked report
- `report_count` = count of linked reports
- `verification_score` = function of report count, unique users, recency
- `is_verified` = true when verification_score exceeds threshold (configurable)

### Verification Score Formula (MVP)
```
score = min(1.0, (report_count * 0.3) + (unique_users * 0.2) + recency_factor)
```
- `recency_factor` = 0.5 if reported within last 7 days, decays over time
- Threshold for `is_verified`: configurable, default 0.6

---

## 2.3 Duplicate Detection

### When to Run
- On every new report submission
- Before creating a new Issue

### MVP Logic
1. Find existing Issues within configurable radius (default: 30 meters, range: 20–50m)
2. Filter by compatible issue types:
   - Exact match on `canonical_issue_type`
   - Or compatible types (e.g., `pothole` ↔ `road_surface_broken`)
3. Filter by recency (issue not resolved, or reported within last 90 days)
4. Filter by same road segment if available
5. Score candidates and return best match if confidence > threshold

### Duplicate Detection Query (PostGIS)
```sql
SELECT i.id, i.canonical_issue_type, i.status,
       ST_Distance(i.geom, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)) AS distance
FROM issues i
WHERE ST_DWithin(i.geom, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography, :radius_meters)
  AND i.status NOT IN ('resolved', 'rejected', 'duplicate')
  AND i.canonical_issue_type IN (:compatible_types)
ORDER BY distance ASC
LIMIT 5;
```

### User Flow for Duplicates
When a potential duplicate is detected:
1. Show the user a prompt: "Similar issue already reported nearby"
2. Display the existing issue card(s)
3. Offer options:
   - **"Same issue — add my report"** → link report to existing issue
   - **"Different issue — create new"** → create new issue
4. Do NOT block the user from reporting — the prompt is a suggestion, not a gate

### Issue Type Compatibility Matrix
| Type | Compatible With |
|------|----------------|
| pothole | road_surface_broken, road_cave_in |
| road_surface_broken | pothole, uneven_resurfacing |
| uneven_resurfacing | road_surface_broken |
| open_manhole | (unique) |
| waterlogging | (unique) |
| dangerous_speed_breaker | (unique) |
| loose_gravel_debris | construction_spill |
| construction_spill | loose_gravel_debris |
| missing_lane_markings | (unique) |
| road_shoulder_collapse | road_cave_in |
| road_cave_in | pothole, road_shoulder_collapse |

---

## 2.4 Map Viewport API

### API: `GET /api/v1/map/issues`
**Query Parameters:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| minLat | float | yes | South bound |
| minLng | float | yes | West bound |
| maxLat | float | yes | North bound |
| maxLng | float | yes | East bound |
| status | string | no | Comma-separated statuses |
| severity | string | no | Comma-separated severities |
| issue_type | string | no | Comma-separated types |
| verified_only | bool | no | Only verified issues |
| date_from | date | no | Earliest first_reported_at |
| date_to | date | no | Latest first_reported_at |

**Response:**
```json
{
  "issues": [
    {
      "id": "uuid",
      "latitude": 17.4432,
      "longitude": 78.3771,
      "canonical_issue_type": "pothole",
      "canonical_severity": "high",
      "status": "verified",
      "report_count": 5,
      "support_count": 12,
      "is_verified": true,
      "first_reported_at": "2026-03-15T10:00:00Z",
      "title": "Pothole — Gachibowli Main Road"
    }
  ],
  "total_count": 142,
  "viewport_bounds": { "minLat": ..., "maxLat": ..., "minLng": ..., "maxLng": ... }
}
```

### Spatial Query (PostGIS)
```sql
SELECT id, latitude, longitude, canonical_issue_type, canonical_severity, status,
       report_count, support_count, is_verified, first_reported_at, title
FROM issues
WHERE ST_Intersects(
    geom,
    ST_MakeEnvelope(:minLng, :minLat, :maxLng, :maxLat, 4326)::geography
)
  AND public_visibility = true
  AND status NOT IN ('rejected', 'duplicate')
ORDER BY canonical_severity DESC, first_reported_at DESC;
```

### Performance Requirements
- Map query response under 800ms for cached views
- Use Redis caching for frequently queried viewports
- Add cache invalidation when issues are created/updated in a viewport
- Limit response to reasonable count per viewport (e.g., 500 issues max, cluster the rest)

---

## 2.5 Issue Clustering

### Why Clustering
- At low zoom levels, individual markers overlap and become unusable
- Clusters provide a cleaner UX and better performance

### Client-Side Clustering (MVP)
Use Leaflet.markercluster or equivalent:
- Cluster markers when zoom level is below threshold
- Show cluster count
- Color-code clusters by worst severity in group
- Expand cluster on click or zoom

### Server-Side Clustering (Future Enhancement)
For scale, implement server-side clustering using:
- Geohash-based aggregation
- Grid-based aggregation with configurable cell size
- Return cluster centroids with aggregate counts

---

## 2.6 Frontend Map Page

### Technology
- Leaflet with OpenStreetMap tiles (MVP)
- MapLibre for vector tiles (future upgrade)

### Map Features
- **Default view**: Centered on Hyderabad (17.385, 78.4867), zoom level ~12
- **Current location**: "Locate me" button using browser geolocation
- **Markers**: Color-coded by severity
  - Low: yellow/green
  - Medium: orange
  - High: red
  - Critical: dark red / pulsing
- **Marker click**: Show issue summary card/popup
- **Clustering**: At lower zoom levels
- **"Report here" CTA**: Floating button or map long-press

### Filter Panel
- Issue type (multi-select dropdown)
- Severity (multi-select)
- Status (multi-select)
- Date range picker
- Verified only toggle
- Apply/Clear filters

### Mobile UX
- Filters in collapsible drawer/sheet
- Bottom sheet for issue details
- Map/list toggle button
- Touch-friendly controls
- Full-screen map mode

### List View (Mobile Alternative)
- Toggle between map and card list
- List sorted by distance from user or by recency
- Each card: thumbnail, type, severity, distance, date, support count

---

## 2.7 Issue Filters

### Available Filters (all optional, combinable)
| Filter | Values |
|--------|--------|
| Issue Type | All 12 supported types |
| Severity | low, medium, high, critical |
| Status | reported, under_review, verified, assigned, in_progress, resolved |
| Date Range | from/to date |
| Authority | GHMC, HMDA, R&B, NHAI, etc. (available after Phase 3) |
| Ward | Ward number/name (available after Phase 3) |
| Zone | Zone name (available after Phase 3) |
| Verified Only | boolean toggle |

### Filter Behavior
- Filters apply to both map markers and list view
- URL query parameters reflect active filters (shareable filtered views)
- Filter counts shown where feasible (e.g., "High severity (42)")

---

## 2.8 Report Flow Enhancement

### Multi-Step Report Flow (Mobile-First)
1. **Capture/Upload**: Camera capture or file picker, 1–5 images
2. **Confirm Location**: Map with draggable pin, current location auto-fill, address preview
3. **Select Issue Type**: Visual grid of issue type cards
4. **Select Severity**: Severity selector with description hints
5. **Optional Details**: Description, landmark, road name, bike danger, rain/night flags
6. **Duplicate Check**: Show nearby existing issues if found
7. **Submit**: Confirmation with report summary

### UX Rules
- Total flow target: under 60 seconds
- Progress indicator (step X of 7)
- Back navigation between steps
- Map pin adjustment must not be painful on phone
- Duplicate suggestion is non-blocking
- Success screen with option to "View on map" or "Report another"

---

## Acceptance Criteria for Phase 2

- [ ] Issue entity is separate from Report entity in both schema and logic
- [ ] New reports trigger duplicate detection before issue creation
- [ ] Duplicate detection uses PostGIS spatial queries within configurable radius
- [ ] User sees "similar issue nearby" prompt when duplicates found
- [ ] User can link report to existing issue or create new one
- [ ] Map viewport API returns issues within bounds with filters
- [ ] Map viewport API responds under 800ms with caching
- [ ] Redis caching layer for map queries is active
- [ ] Frontend map page renders with Leaflet + OSM tiles
- [ ] Map markers color-coded by severity
- [ ] Marker clustering works at lower zoom levels
- [ ] Filter panel works for issue type, severity, status, date range
- [ ] Map/list toggle works on mobile
- [ ] Report flow is multi-step and completes under 60 seconds on mobile
- [ ] Issue detail page shows linked report count and verification status
- [ ] Shareable URLs with filter state work correctly

---

## Related Spec Sections
- Section 6.5: Public map
- Section 6.6: Issue detail page
- Section 6.7: Duplicate detection
- Section 10: Core domain model (Report vs Issue)
- Section 12: Geospatial design
- Section 14: Deduplication strategy
- Section 17.1: Map query API
- Section 19.2: Report flow UX
- Section 19.3: Map page UX
- Section 25.1: Reports ≠ Issues
