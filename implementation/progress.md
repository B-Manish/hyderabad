# Hyderabad Road Reporting Platform — Implementation Progress

> **Last Updated:** 2026-04-15  
> **Current Phase:** Phase 2  
> **Overall Status:** Phase 1 Complete

---

## Overview

| Phase | Name | Status | Progress | Key Deliverable |
|-------|------|--------|----------|-----------------|
| 1 | [Core Foundation](phases/phase-1-core-foundation.md) | � Complete | 100% | Users can submit reports with image + location |
| 2 | [Map + Issue Model](phases/phase-2-map-issue-model.md) | 🔴 Not Started | 0% | Public map with deduplicated issues |
| 3 | [Jurisdiction & Authority](phases/phase-3-jurisdiction-authority.md) | 🔴 Not Started | 0% | Authority resolution with confidence scoring |
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
| Issue creation from report logic | 🔴 | |
| Issue-report linking service | 🔴 | |
| Auto-title generation | 🔴 | |
| Canonical field aggregation | 🔴 | |
| Verification score calculation | 🔴 | |

### Duplicate Detection
| Task | Status | Notes |
|------|--------|-------|
| Spatial duplicate query (ST_DWithin) | 🔴 | |
| Issue type compatibility matrix | 🔴 | |
| Duplicate suggestion API | 🔴 | |
| Frontend duplicate prompt UX | 🔴 | |
| Link report to existing issue flow | 🔴 | |

### Map Viewport API
| Task | Status | Notes |
|------|--------|-------|
| `GET /api/v1/map/issues` endpoint | 🔴 | |
| PostGIS viewport query (ST_Intersects + envelope) | 🔴 | |
| Filter support (type, severity, status, date) | 🔴 | |
| Redis caching for viewport queries | 🔴 | |
| Cache invalidation on issue updates | 🔴 | |

### Frontend Map
| Task | Status | Notes |
|------|--------|-------|
| Leaflet + OSM tile integration | 🔴 | |
| Severity-based marker colors | 🔴 | |
| Marker clustering (Leaflet.markercluster) | 🔴 | |
| Marker click → issue summary popup | 🔴 | |
| "Locate me" button | 🔴 | |
| Filter panel (type, severity, status, date) | 🔴 | |
| Map / list toggle (mobile) | 🔴 | |
| "Report here" CTA | 🔴 | |
| Shareable URL with filter state | 🔴 | |

### Report Flow Enhancement
| Task | Status | Notes |
|------|--------|-------|
| Multi-step report wizard (7 steps) | 🔴 | |
| Draggable map pin for location | 🔴 | |
| Issue type visual selector | 🔴 | |
| Duplicate check step integration | 🔴 | |
| Progress indicator | 🔴 | |

---

## Phase 3: Jurisdiction & Authority Mapping

### Database
| Task | Status | Notes |
|------|--------|-------|
| `authorities` table migration | 🔴 | |
| `jurisdiction_polygons` table migration | 🔴 | |
| `responsibility_mappings` table migration | 🔴 | |
| `accountability_chain_nodes` table migration | 🔴 | |
| `road_segments` table migration | 🔴 | |
| GiST indexes on polygon + road geom | 🔴 | |

### Polygon Import Pipeline
| Task | Status | Notes |
|------|--------|-------|
| GeoJSON import job | 🔴 | |
| Shapefile import job | 🔴 | |
| CSV with WKT import job | 🔴 | |
| Geometry validation + CRS transform | 🔴 | |
| Import API (`POST /api/v1/admin/jurisdictions/import`) | 🔴 | |
| Data versioning support | 🔴 | |

### Authority Resolution Engine
| Task | Status | Notes |
|------|--------|-------|
| Special road zone check (step 1) | 🔴 | |
| Road segment explicit mapping (step 2) | 🔴 | |
| Municipal ward/circle/zone containment (step 3) | 🔴 | |
| Road class inference (step 4) | 🔴 | |
| Admin override application (step 5) | 🔴 | |
| Weighted score aggregation (step 6) | 🔴 | |
| Authority lookup API (`GET /api/v1/lookup/authority`) | 🔴 | |
| Confidence level classification | 🔴 | |
| Redis caching for lookups | 🔴 | |

### Integration
| Task | Status | Notes |
|------|--------|-------|
| Issue creation triggers authority resolution | 🔴 | |
| Issue detail page accountability section | 🔴 | |
| Reverse geocode API | 🔴 | |
| Ward boundary map overlay | 🔴 | |

### Seed Data
| Task | Status | Notes |
|------|--------|-------|
| Hyderabad ward polygons imported | 🔴 | |
| Zone/circle boundaries imported | 🔴 | |
| Authority records seeded (GHMC, HMDA, R&B, NHAI) | 🔴 | |
| Sample road segments from OSM | 🔴 | |
| Sample accountability chain nodes | 🔴 | |

### Admin Overrides
| Task | Status | Notes |
|------|--------|-------|
| Manual authority correction API | 🔴 | |
| Ownership confidence override | 🔴 | |
| "Ownership disputed" flag | 🔴 | |
| Override audit logging | 🔴 | |

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
