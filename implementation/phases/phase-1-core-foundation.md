# Phase 1: Core Foundation

**Goal:** Build the foundational backend, frontend, database, media upload, and basic report submission so that users can submit road issue reports with image and location.

**Deliverable:** Users can submit road issue reports with image and location. Reports appear in a public issue list and detail page.

---

## 1.1 Project Scaffolding

### Backend (FastAPI + Python)
- Initialize Python project with FastAPI
- Set up project structure:
  ```
  backend/
    app/
      api/
      core/
      db/
      models/
      schemas/
      services/
      repositories/
      geo/
      workers/
      tasks/
      auth/
      admin/
    alembic/
  ```
- Configure environment variables and settings module
- Set up dependency injection patterns
- Add structured logging (JSON logs with request IDs)
- Add CORS middleware for frontend communication
- Add request tracing middleware

### Frontend (React + Vite + TypeScript)
- Initialize React project with Vite and TypeScript
- Set up project structure:
  ```
  frontend/
    src/
      components/
      pages/
      hooks/
      services/
      utils/
      types/
      assets/
  ```
- Install and configure Tailwind CSS
- Install and configure TanStack Query (React Query)
- Set up API client/service layer
- Set up routing (React Router)
- Mobile-first responsive layout shell

### Infrastructure
- Create `docker-compose.yml` with:
  - PostgreSQL + PostGIS
  - Redis
  - MinIO (S3-compatible object storage)
  - Backend API service
  - Frontend dev server
- Create Dockerfiles for backend and frontend
- Set up reverse proxy (Caddy or Traefik) configuration
- Add seed/fixture loading scripts

---

## 1.2 Database Setup (PostgreSQL + PostGIS)

### Core Requirements
- PostgreSQL with PostGIS extension enabled
- Alembic for migration management
- SQLAlchemy models with GeoAlchemy2 for spatial types

### Initial Migrations

#### `users` table
| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| name | VARCHAR | |
| email | VARCHAR | nullable |
| phone | VARCHAR | nullable |
| auth_provider | VARCHAR | |
| is_anonymous_allowed | BOOLEAN | |
| role | ENUM(citizen, moderator, admin) | |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

#### `reports` table
| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| user_id | UUID (FK, nullable) | nullable if anonymous |
| issue_id | UUID (FK, nullable) | nullable until dedupe |
| latitude | DECIMAL | |
| longitude | DECIMAL | |
| geom | geography(Point, 4326) | PostGIS spatial column |
| issue_type | ENUM | See supported categories |
| severity | ENUM(low, medium, high, critical) | |
| description | TEXT | optional |
| landmark | VARCHAR | optional |
| road_name_input | VARCHAR | optional |
| direction_of_travel | VARCHAR | optional |
| dangerous_for_bikes | BOOLEAN | |
| worse_in_rain | BOOLEAN | |
| worse_at_night | BOOLEAN | |
| moderation_status | ENUM(pending_moderation, approved, rejected_abuse, low_quality_evidence, duplicate_merged) | |
| source | ENUM(web, mobile-web, admin) | |
| submitted_at | TIMESTAMPTZ | |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

#### `report_media` table
| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| report_id | UUID (FK) | |
| storage_key | VARCHAR | path in object storage |
| media_type | ENUM(image, video) | |
| mime_type | VARCHAR | |
| width | INTEGER | |
| height | INTEGER | |
| size_bytes | BIGINT | |
| sort_order | INTEGER | |
| created_at | TIMESTAMPTZ | |

#### `issues` table
| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| primary_report_id | UUID (FK) | |
| title | VARCHAR | |
| canonical_issue_type | ENUM | |
| canonical_severity | ENUM | |
| status | ENUM(reported, under_review, verified, assigned, in_progress, resolved, rejected, duplicate) | |
| latitude | DECIMAL | |
| longitude | DECIMAL | |
| geom | geography(Point, 4326) | |
| road_segment_id | UUID (FK, nullable) | |
| first_reported_at | TIMESTAMPTZ | |
| latest_reported_at | TIMESTAMPTZ | |
| resolved_at | TIMESTAMPTZ (nullable) | |
| support_count | INTEGER | |
| report_count | INTEGER | |
| verification_score | DECIMAL | |
| is_verified | BOOLEAN | |
| public_visibility | BOOLEAN | |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

#### `issue_reports` table
| Column | Type | Notes |
|--------|------|-------|
| issue_id | UUID (FK) | |
| report_id | UUID (FK) | |
| linked_at | TIMESTAMPTZ | |
| link_reason | VARCHAR | |

#### `issue_status_history` table
| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| issue_id | UUID (FK) | |
| old_status | VARCHAR | |
| new_status | VARCHAR | |
| changed_by_user_id | UUID (FK) | |
| change_reason | TEXT | |
| created_at | TIMESTAMPTZ | |

### Spatial Indexes
Create GiST indexes on:
- `reports.geom`
- `issues.geom`

### Supported Issue Types (ENUM)
- pothole
- road_surface_broken
- uneven_resurfacing
- waterlogging
- open_manhole
- dangerous_speed_breaker
- loose_gravel_debris
- construction_spill
- missing_lane_markings
- road_shoulder_collapse
- road_cave_in
- other_road_safety

---

## 1.3 Media Upload Flow

### Signed URL Upload Pattern
1. Frontend requests a signed upload URL from backend: `POST /api/v1/uploads/sign`
2. Backend generates a pre-signed PUT URL for MinIO/S3
3. Frontend uploads directly to object storage using the signed URL
4. Frontend sends the resulting `storage_key` with the report submission
5. Backend validates storage key existence on report creation

### API: `POST /api/v1/uploads/sign`
**Request:**
```json
{
  "filename": "pothole.jpg",
  "content_type": "image/jpeg",
  "file_size": 2048576
}
```
**Response:**
```json
{
  "upload_url": "https://storage.../signed-put-url",
  "storage_key": "reports/2026/04/abc123.jpg",
  "expires_in": 300
}
```

### Constraints
- Accept image formats: JPEG, PNG, WebP
- Max file size: 10 MB per image
- 1 to 5 images per report
- Minimum resolution check (e.g., 640×480)
- Video support deferred to post-MVP

---

## 1.4 Report Submission Backend

### API: `POST /api/v1/reports`
**Request:**
```json
{
  "latitude": 17.4432,
  "longitude": 78.3771,
  "issue_type": "pothole",
  "severity": "high",
  "description": "Deep pothole near the left lane after the signal",
  "landmark": "Near XYZ junction",
  "road_name_input": "Gachibowli Main Road",
  "dangerous_for_bikes": true,
  "worse_in_rain": true,
  "worse_at_night": true,
  "media_keys": ["reports/2026/04/abc123.jpg"]
}
```

### Backend Logic
1. Validate input (required: lat, lng, at least one media_key, issue_type, severity)
2. Validate media keys exist in object storage
3. Create `geom` point from lat/lng using PostGIS: `ST_SetSRID(ST_MakePoint(lng, lat), 4326)`
4. Create `report` record with `moderation_status = pending_moderation`
5. Create `report_media` records for each media key
6. Return report ID and status

### API: `GET /api/v1/reports/{reportId}`
- Return report details including media URLs, location, metadata
- Respect moderation status (only show approved reports publicly)

### Security & Validation
- Rate limiting: max 10 reports per IP per hour (configurable)
- Captcha for anonymous reporting
- Input sanitization on all text fields
- Profanity filter on description text
- Anti-spam protection

---

## 1.5 Public Issue List & Detail Page

### API: `GET /api/v1/issues`
- Paginated list of public, approved issues
- Sortable by: date, severity, support count
- Filterable by: issue_type, severity, status

### API: `GET /api/v1/issues/{issueId}`
- Full issue details including:
  - Title, issue type, severity, status
  - Image gallery (from linked reports)
  - Location map (static or embedded)
  - Nearby duplicate count
  - Number of supporting reports
  - First reported date, latest activity
  - Shareable public URL

### Frontend Pages

#### Issue List Page
- Card-based list of recent issues
- Each card shows: thumbnail, issue type, severity badge, location, date, support count
- Mobile-responsive grid/list layout

#### Issue Detail Page
- Hero image gallery
- Issue metadata section
- Location mini-map
- Status badge
- Report count / support count
- Shareable URL
- "Support this issue" CTA (functional in later phase)

---

## 1.6 Basic Auth

### MVP Auth Strategy
- Anonymous reporting allowed (with rate limits and captcha)
- Email OTP / magic link for registered users
- Session-based or JWT token auth
- Role field on user: citizen, moderator, admin
- Google login deferred to post-Phase 1

---

## 1.7 Landing Page (Frontend)

### Content
- Hero section: "Report dangerous roads in Hyderabad. See who is responsible."
- Subtext: "Upload a photo, mark the location, and help build a public accountability map for potholes and unsafe roads."
- CTA buttons: "Report a road issue" | "View live map"
- Stats section: issues reported, unresolved count, wards covered (placeholder data for Phase 1)
- Recent hotspots section (placeholder for Phase 1)

---

## Acceptance Criteria for Phase 1

- [ ] Docker Compose brings up all services (Postgres+PostGIS, Redis, MinIO, backend, frontend)
- [ ] Database migrations run cleanly with all Phase 1 tables
- [ ] Spatial indexes created on geom columns
- [ ] Signed URL upload flow works for images
- [ ] Report submission API validates and stores reports with PostGIS geometry
- [ ] Report media records created and linked
- [ ] Public issue list API returns paginated results
- [ ] Public issue detail API returns full issue data
- [ ] Frontend landing page renders with CTAs
- [ ] Frontend report submission flow works (upload → location → type → severity → submit)
- [ ] Frontend issue list page displays issues
- [ ] Frontend issue detail page displays full issue info
- [ ] Rate limiting active on report submission endpoint
- [ ] Structured logging on all API requests
- [ ] Mobile-responsive UI across all pages

---

## Key Engineering Constraints (from Spec)

1. **Reports ≠ Issues**: They are separate entities. A single Issue supports multiple Reports.
2. **PostGIS from day one**: Use `geography(Point, 4326)` for all location columns. No plain decimal-only fields.
3. **Media storage decoupled**: Use signed URLs and storage keys, never DB blobs.
4. **Moderation vs Public status**: `moderation_status` on reports is separate from `status` on issues.
5. **Performance target**: Report submit API under 2 seconds (excluding upload time).

---

## Related Spec Sections
- Section 6.1: Issue reporting
- Section 6.2: Supported issue categories
- Section 6.3: Severity levels
- Section 6.4: Status workflow
- Section 6.6: Issue detail page
- Section 8: Tech stack
- Section 9: Architecture
- Section 10: Domain model
- Section 11: Database design (11.1–11.6)
- Section 17.1: Public/reporting APIs
- Section 18: Frontend pages
- Section 19.1–19.2: UX details
- Section 22: Folder structure
- Section 25: Engineering notes
