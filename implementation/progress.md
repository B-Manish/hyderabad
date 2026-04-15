# Hyderabad Road Reporting Platform — Implementation Progress

> **Last Updated:** 2026-04-15  
> **Current Phase:** Phase 4  
> **Overall Status:** Phase 3 Complete

---

## Overview

| Phase | Name | Status | Progress | Key Deliverable |
|-------|------|--------|----------|-----------------|
| 1 | [Core Foundation](phases/phase-1-core-foundation.md) | � Complete | 100% | Users can submit reports with image + location |
| 2 | [Map + Issue Model](phases/phase-2-map-issue-model.md) | � Complete | 100% | Public map with deduplicated issues |
| 3 | [Jurisdiction & Authority](phases/phase-3-jurisdiction-authority.md) | � Complete | 100% | Authority resolution with confidence scoring |
| 4 | [Admin & Moderation](phases/phase-4-admin-moderation.md) | 🔴 Not Started | 0% | Operational moderation + analytics |
| 5 | [Trust & Growth](phases/phase-5-trust-growth.md) | 🔴 Not Started | 0% | Community trust signals + engagement loops |

**Status Legend:** 🔴 Not Started | 🟡 In Progress | 🟢 Complete | ⏸️ Blocked

---

## Phase 1: Core Foundation

### Backend Setup
| Task | Status | Notes |
|------|--------|-------|
| FastAPI project scaffolding | � | `backend/app/main.py` |
| Project folder structure | 🟢 | api/core/db/models/schemas/services/repositories/geo/workers/tasks/auth/admin |
| Environment & settings module | 🟢 | `backend/app/core/config.py` |
| CORS & middleware setup | 🟢 | Configured in `main.py` |
| Structured logging | 🟢 | `backend/app/core/logging.py` with structlog JSON |
| Request tracing | 🟢 | `RequestTracingMiddleware` with X-Request-ID |

### Frontend Setup
| Task | Status | Notes |
|------|--------|-------|
| React + Vite + TypeScript init | � | `frontend/` with Vite + React 18 + TS |
| Tailwind CSS setup | 🟢 | `tailwind.config.js` with custom colors |
| TanStack Query setup | 🟢 | QueryClientProvider in `App.tsx` |
| Routing (React Router) | 🟢 | 4 routes: /, /issues, /issues/:id, /report |
| API client / service layer | 🟢 | `frontend/src/services/api.ts` |
| Mobile-first layout shell | 🟢 | Responsive Navbar + Layout + footer |

### Infrastructure
| Task | Status | Notes |
|------|--------|-------|
| Docker Compose (Postgres+PostGIS, Redis, MinIO) | � | `docker-compose.yml` with all services |
| Backend Dockerfile | 🟢 | `backend/Dockerfile` Python 3.12-slim |
| Frontend Dockerfile | 🟢 | `frontend/Dockerfile` Node 20-alpine |
| Reverse proxy config | 🟢 | Caddy reverse proxy (`Caddyfile`) |
| Seed/fixture scripts | 🟢 | `backend/seed.py` with 5 sample reports |

### Database
| Task | Status | Notes |
|------|--------|-------|
| Alembic + SQLAlchemy + GeoAlchemy2 setup | � | `alembic/env.py` + models |
| PostGIS extension enabled | 🟢 | `CREATE EXTENSION IF NOT EXISTS postgis` in migration |
| `users` table migration | 🟢 | UUID PK, role enum, email |
| `reports` table migration | 🟢 | geography(Point,4326), all enums |
| `report_media` table migration | 🟢 | storage_key, media_type |
| `issues` table migration | 🟢 | Separate from reports, with status |
| `issue_reports` table migration | 🟢 | Composite PK, link_reason |
| `issue_status_history` table migration | 🟢 | Full audit trail |
| GiST spatial indexes | 🟢 | idx_reports_geom, idx_issues_geom |

### Media Upload
| Task | Status | Notes |
|------|--------|-------|
| Signed URL upload endpoint (`POST /api/v1/uploads/sign`) | � | `api/uploads.py` |
| MinIO/S3 integration | 🟢 | `services/storage.py` with boto3 |
| File validation (type, size, resolution) | 🟢 | Content-type + size validation |
| Frontend image upload component | 🟢 | `ImageUpload.tsx` with preview + drag |

### Report Submission
| Task | Status | Notes |
|------|--------|-------|
| Report creation API (`POST /api/v1/reports`) | � | Creates report + issue + media records |
| PostGIS geometry creation | 🟢 | ST_SetSRID(ST_MakePoint) |
| Input validation | 🟢 | Pydantic schemas with field validators |
| Rate limiting on submission endpoint | 🟢 | slowapi 10/hour per IP |
| Report detail API (`GET /api/v1/reports/{id}`) | 🟢 | Includes media URLs |

### Public Pages
| Task | Status | Notes |
|------|--------|-------|
| Issue list API (`GET /api/v1/issues`) | � | Paginated, filterable, sortable |
| Issue detail API (`GET /api/v1/issues/{id}`) | 🟢 | Full issue with linked report media |
| Landing page (frontend) | 🟢 | Hero + stats + how-it-works + CTA |
| Issue list page (frontend) | 🟢 | Card grid with filters + pagination |
| Issue detail page (frontend) | 🟢 | Gallery, metadata, location, share |
| Report submission flow (frontend) | 🟢 | 5-step flow: upload→location→type→severity→details |

### Auth
| Task | Status | Notes |
|------|--------|-------|
| Anonymous reporting (with limits) | � | `POST /api/v1/auth/anonymous` |
| Email OTP / magic link | 🟢 | Simplified email register for Phase 1 |
| JWT / session auth | 🟢 | python-jose JWT with HS256 |
| Role-based middleware | 🟢 | `require_role()` dependency with hierarchy |

---

## Phase 2: Map + Issue Model

### Issue Entity Separation
| Task | Status | Notes |
|------|--------|-------|
| Issue creation from report logic | � | `services/issues.py` create_issue_from_report() |
| Issue-report linking service | 🟢 | `services/issues.py` link_report_to_existing_issue() |
| Auto-title generation | 🟢 | generate_issue_title() from type+landmark/road |
| Canonical field aggregation | 🟢 | recalculate_issue_aggregates() — severity/type/count |
| Verification score calculation | 🟢 | compute_verification_score() — report_count+unique_users+recency |

### Duplicate Detection
| Task | Status | Notes |
|------|--------|-------|
| Spatial duplicate query (ST_DWithin) | � | find_nearby_duplicates() with 30m default radius |
| Issue type compatibility matrix | 🟢 | COMPATIBLE_TYPES dict in services/issues.py |
| Duplicate suggestion API | 🟢 | `GET /api/v1/map/duplicates` with lat/lng/type/radius |
| Frontend duplicate prompt UX | 🟢 | Step 6 in report wizard with nearby issue cards |
| Link report to existing issue flow | 🟢 | existing_issue_id in ReportCreateRequest → link_report_to_existing_issue() |

### Map Viewport API
| Task | Status | Notes |
|------|--------|-------|
| `GET /api/v1/map/issues` endpoint | � | `api/map.py` with viewport bounds params |
| PostGIS viewport query (ST_Intersects + envelope) | 🟢 | ST_Intersects + ST_MakeEnvelope in get_map_issues() |
| Filter support (type, severity, status, date) | 🟢 | issue_type, severity, status, date_from, date_to, verified |
| Redis caching for viewport queries | 🟢 | `services/cache.py` with 60s TTL, key from bounds+filters |
| Cache invalidation on issue updates | 🟢 | invalidate_map_cache() SCAN+DELETE all map:* keys |

### Frontend Map
| Task | Status | Notes |
|------|--------|-------|
| Leaflet + OSM tile integration | � | MapPage.tsx with OSM tiles, center Hyderabad |
| Severity-based marker colors | 🟢 | Green/yellow/orange/red custom markers |
| Marker clustering (Leaflet.markercluster) | 🟢 | MarkerClusterGroup with worst-severity coloring |
| Marker click → issue summary popup | 🟢 | Bottom sheet with issue summary + "View Details" |
| "Locate me" button | 🟢 | LocateButton component with geolocation API |
| Filter panel (type, severity, status, date) | 🟢 | Collapsible panel with type/severity/status/date/verified |
| Map / list toggle (mobile) | 🟢 | Toggle between map view and card list view |
| "Report here" CTA | 🟢 | Floating button → /report with coordinates |
| Shareable URL with filter state | 🟢 | searchParams sync for all filters |

### Report Flow Enhancement
| Task | Status | Notes |
|------|--------|-------|
| Multi-step report wizard (7 steps) | � | Upload→Location→Type→Severity→Details→DupCheck→Submit |
| Draggable map pin for location | 🟢 | Leaflet map with draggable marker + click-to-set |
| Issue type visual selector | 🟢 | Visual grid with emoji icons, 8 issue types |
| Duplicate check step integration | 🟢 | Step 6 calls checkDuplicates API, shows nearby issues |
| Progress indicator | 🟢 | Step labels + progress bar at top of wizard |

---

## Phase 3: Jurisdiction & Authority Mapping

### Database
| Task | Status | Notes |
|------|--------|-------|
| `authorities` table migration | � | `alembic/versions/002_phase3_jurisdiction.py` |
| `jurisdiction_polygons` table migration | 🟢 | geometry(MultiPolygon,4326) + GiST index |
| `responsibility_mappings` table migration | 🟢 | issue_type + polygon FK |
| `accountability_chain_nodes` table migration | 🟢 | role hierarchy per authority |
| `road_segments` table migration | 🟢 | geometry(LineString,4326) + GiST index |
| GiST indexes on polygon + road geom | 🟢 | idx_jurisdiction_polygons_geom, idx_road_segments_geom |

### Polygon Import Pipeline
| Task | Status | Notes |
|------|--------|-------|
| GeoJSON import job | � | `services/geo_import.py` import_geojson_polygons() |
| Shapefile import job | 🟢 | import_shapefile_polygons() via fiona |
| CSV with WKT import job | 🟢 | import_csv_wkt_polygons() |
| Geometry validation + CRS transform | 🟢 | validate_and_transform_geometry() with pyproj |
| Import API (`POST /api/v1/admin/jurisdictions/import`) | 🟢 | `api/admin_jurisdictions.py` |
| Data versioning support | 🟢 | data_version field + replaced_by FK on polygons |

### Authority Resolution Engine
| Task | Status | Notes |
|------|--------|-------|
| Special road zone check (step 1) | � | `services/authority.py` resolve_authority() |
| Road segment explicit mapping (step 2) | 🟢 | ST_DWithin road segment query |
| Municipal ward/circle/zone containment (step 3) | 🟢 | ST_Contains polygon containment |
| Road class inference (step 4) | 🟢 | road_class → authority mapping table |
| Admin override application (step 5) | 🟢 | authority_override_notes on Issue |
| Weighted score aggregation (step 6) | 🟢 | confidence_score 0.0–1.0 float |
| Authority lookup API (`GET /api/v1/lookup/authority`) | 🟢 | `api/lookup.py` with lat/lng params |
| Confidence level classification | 🟢 | HIGH/MEDIUM/LOW/NONE enum |
| Redis caching for lookups | 🟢 | 5-min TTL cache keyed by lat/lng/type |

### Integration
| Task | Status | Notes |
|------|--------|-------|
| Issue creation triggers authority resolution | � | create_issue_from_report() calls resolve_authority() |
| Issue detail page accountability section | 🟢 | `IssueDetailPage.tsx` AccountabilitySection component |
| Reverse geocode API | 🟢 | `GET /api/v1/lookup/reverse-geocode` |
| Ward boundary map overlay | 🟢 | `MapPage.tsx` WardBoundaryOverlay toggle |

### Seed Data
| Task | Status | Notes |
|------|--------|-------|
| Hyderabad ward polygons imported | � | `seed_phase3.py` — 5 ward polygons |
| Zone/circle boundaries imported | 🟢 | 2 zone polygons (Central, West) |
| Authority records seeded (GHMC, HMDA, R&B, NHAI) | 🟢 | 5 authorities with contact details |
| Sample road segments from OSM | 🟢 | 3 road segments (NH65, IR, ORR) |
| Sample accountability chain nodes | 🟢 | Commissioner → ZC → AE hierarchy |

### Admin Overrides
| Task | Status | Notes |
|------|--------|-------|
| Manual authority correction API | � | `POST /api/v1/admin/issues/{id}/authority-override` |
| Ownership confidence override | 🟢 | override sets confidence_level = HIGH |
| "Ownership disputed" flag | 🔴 | Deferred to Phase 4 |
| Override audit logging | 🟢 | authority_override_notes + changed_by recorded |

---

## Phase 4: Admin & Moderation

### Admin Dashboard
| Task | Status | Notes |
|------|--------|-------|
| Dashboard layout + sidebar nav | 🔴 | |
| Summary metrics display | 🔴 | |
| Role-based section visibility | 🔴 | |

### Moderation Queue
| Task | Status | Notes |
|------|--------|-------|
| Pending reports list (`GET /api/v1/admin/reports`) | 🔴 | |
| Approve action + API | 🔴 | |
| Reject action + API | 🔴 | |
| Edit metadata before approval | 🔴 | |
| Moderation queue frontend | 🔴 | |

### Duplicate Merge
| Task | Status | Notes |
|------|--------|-------|
| Merge API (`POST /api/v1/admin/issues/{id}/merge`) | 🔴 | |
| Report re-linking logic | 🔴 | |
| Surviving issue recalculation | 🔴 | |
| Merge UI in admin | 🔴 | |

### Issue Management
| Task | Status | Notes |
|------|--------|-------|
| Admin issue list with filters | 🔴 | |
| Status change API with transition validation | 🔴 | |
| Status history tracking | 🔴 | |
| Inline metadata editing | 🔴 | |

### Authority & Jurisdiction Management
| Task | Status | Notes |
|------|--------|-------|
| Authority CRUD APIs | 🔴 | |
| Authority management UI | 🔴 | |
| Accountability chain CRUD | 🔴 | |
| Jurisdiction import UI | 🔴 | |
| Jurisdiction status page | 🔴 | |

### Audit & Logging
| Task | Status | Notes |
|------|--------|-------|
| `audit_logs` writes on all admin actions | 🔴 | |
| `moderation_actions` writes | 🔴 | |
| Audit log viewer UI (filterable) | 🔴 | |
| CSV export for audit logs | 🔴 | |

### Analytics Dashboard
| Task | Status | Notes |
|------|--------|-------|
| Summary analytics API | 🔴 | |
| Geographic breakdown by ward | 🔴 | |
| Time-series charts (reports/resolutions) | 🔴 | |
| Severity/status distribution charts | 🔴 | |
| Operational views (stale, critical, disputed) | 🔴 | |
| CSV export for analytics | 🔴 | |

### User Management
| Task | Status | Notes |
|------|--------|-------|
| User list with search/filter | 🔴 | |
| Role change functionality | 🔴 | |
| User deactivation | 🔴 | |

### Permissions
| Task | Status | Notes |
|------|--------|-------|
| Role-based backend middleware enforced | 🔴 | |
| Frontend role-based UI visibility | 🔴 | |

---

## Phase 5: Trust & Growth

### Issue Support System
| Task | Status | Notes |
|------|--------|-------|
| Support API (`POST /api/v1/issues/{id}/support`) | 🔴 | |
| Support types (same_issue, dangerous, still_exists, fixed_confirmed) | 🔴 | |
| Support count + verification score updates | 🔴 | |
| Rate limiting on supports | 🔴 | |
| Frontend support buttons on issue detail | 🔴 | |

### Shareable URLs & Sharing
| Task | Status | Notes |
|------|--------|-------|
| Open Graph meta tags on issue pages | 🔴 | |
| Twitter Card meta tags | 🔴 | |
| Map state in URL (shareable filtered views) | 🔴 | |
| Share button (copy, WhatsApp, Twitter) | 🔴 | |

### Hotspot Rankings
| Task | Status | Notes |
|------|--------|-------|
| Hotspot computation background job | 🔴 | |
| Hotspot API (`GET /api/v1/hotspots`) | 🔴 | |
| Landing page hotspot display | 🔴 | |
| Hotspot rankings page | 🔴 | |

### Locality Pages
| Task | Status | Notes |
|------|--------|-------|
| Ward/area page API | 🔴 | |
| Locality page frontend (SSR/SEO) | 🔴 | |
| Mini-map per locality | 🔴 | |
| SEO (structured data, sitemap) | 🔴 | |

### Search
| Task | Status | Notes |
|------|--------|-------|
| Search API (`GET /api/v1/search`) | 🔴 | |
| Full-text search (tsvector) | 🔴 | |
| Spatial nearby search | 🔴 | |
| Search UI in header/map | 🔴 | |

### Trust Signals
| Task | Status | Notes |
|------|--------|-------|
| Verified badge on issues | 🔴 | |
| Report/support counts displayed | 🔴 | |
| Real stats on landing page | 🔴 | |

### Additional Pages
| Task | Status | Notes |
|------|--------|-------|
| About / How It Works page | 🔴 | |
| Authority public page | 🔴 | |

### Subscriptions Foundation
| Task | Status | Notes |
|------|--------|-------|
| Subscriptions data model | 🔴 | |
| Watch issue / Watch area UI | 🔴 | |

### Performance & Hardening
| Task | Status | Notes |
|------|--------|-------|
| Caching review + optimization | 🔴 | |
| Rate limiting tuning | 🔴 | |
| Query performance audit | 🔴 | |
| Anti-spam hardening | 🔴 | |
| Configurable admin thresholds | 🔴 | |

---

## Blockers & Risks

| ID | Phase | Description | Status | Resolution |
|----|-------|-------------|--------|------------|
| — | — | No blockers yet | — | — |

---

## Key Decisions Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-04-15 | Implementation plan created with 5 phases | Based on spec v1.0 recommended build plan |
| | | |

---

## Notes

- Each phase file in `phases/` contains detailed requirements, APIs, acceptance criteria, and related spec sections.
- Update this file as tasks progress. Replace 🔴 with 🟡 (in progress) or 🟢 (complete).
- Add blockers to the Blockers table immediately when encountered.
- Log key architectural and product decisions in the Decisions Log.
