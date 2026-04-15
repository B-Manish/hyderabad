# Hyderabad Road Reporting & Accountability Platform
## Detailed Product + Engineering Specification for Cursor

Version: 1.0  
Prepared for: MVP build of a public road issue reporting platform for Hyderabad  
Primary goal: Let citizens report bad roads, view issue hotspots on a public map, and see which authority is responsible for fixing each road segment.

---

## 1. Product Summary

Build a Hyderabad-focused public platform where riders and citizens can:

- report potholes and other road defects with photo/video and GPS location
- see nearby reports on a map
- avoid duplicate reporting by clustering repeated complaints
- view who is responsible for the road
- track issue age, severity, and status
- escalate unresolved issues
- optionally export or forward complaints into official channels later

This is **not** just a complaints app.

The core differentiator is:

> A citizen should be able to take one photo, share one location, and immediately see:
> - which road stretch is affected
> - which administrative area it belongs to
> - which authority is likely responsible
> - which official chain is accountable

---

## 2. Product Vision

### 2.1 Problem
Road users in Hyderabad face:
- potholes
- broken surfaces
- waterlogging
- dangerous patches after rains
- poor resurfacing
- open manholes
- unmarked speed breakers
- missing lane markings
- unsafe debris or construction spillover

Current complaint systems are fragmented. A citizen often does not know:
- whether the road belongs to GHMC, HMDA, R&B, NHAI, or another authority
- which ward/circle/zone they are in
- who to contact
- whether the complaint is already reported
- whether the issue is genuinely being tracked

### 2.2 Core user value
This platform should answer:

- What is wrong here?
- How many people have reported it?
- How serious is it?
- How long has it existed?
- Who is responsible?
- Has it been fixed?
- If not fixed, who should be escalated?

### 2.3 Target users
Primary:
- bikers
- daily commuters
- car users
- residents
- delivery riders

Secondary:
- journalists
- civic volunteers
- RWAs
- local activists
- ward-level political representatives
- municipal staff

---

## 3. Scope

### 3.1 In scope for MVP
- report road-related issues
- upload image(s), optionally short video later
- auto-capture GPS
- public issue map
- issue detail page
- duplicate detection
- clustering of nearby reports
- ward/authority lookup
- accountability chain display
- basic status workflow
- admin moderation
- analytics dashboard
- mobile-friendly UI

### 3.2 Out of scope for MVP
- all civic complaints across every category
- guaranteed official integration on day one
- direct ticket submission into government systems
- multilingual OCR from signboards
- advanced AI-based road damage classification
- native Android/iOS apps
- citizen identity verification via Aadhaar or government ID
- legal-grade evidence pipeline

---

## 4. Product Positioning

Use this framing in UI and copy:

**A public road safety map for Hyderabad that shows dangerous road issues and who is responsible for fixing them.**

Do not position it as:
- generic complaint portal
- government replacement
- legal grievance platform

Position it as:
- public visibility
- accountability
- rider safety
- crowd-verified road issue map

---

## 5. User Stories

### 5.1 Reporter
As a biker, I want to report a pothole with one photo and my location so that others and the responsible authority can see it.

### 5.2 Nearby viewer
As a commuter, I want to open the map and see dangerous stretches near me before traveling.

### 5.3 Accountability seeker
As a citizen, I want to know which authority is responsible for a damaged road so I know whom to hold accountable.

### 5.4 Duplicate avoidance
As a user, I want to see if the same issue is already reported nearby so that reports are consolidated.

### 5.5 Admin
As a moderator, I want to review suspicious or abusive reports before they affect public trust.

### 5.6 Analyst
As an operator, I want to see which areas have the highest unresolved road risk and oldest pending problems.

---

## 6. Functional Requirements

## 6.1 Issue reporting
The user should be able to:
- upload 1 to 5 images
- optionally add short text
- optionally select issue type
- allow GPS capture
- manually adjust map pin
- set severity
- mention whether issue is dangerous for bikes
- mention whether issue is worse at night or in rain

Required input:
- latitude
- longitude
- at least one image
- issue type
- severity

Optional input:
- description
- landmark
- road name if known
- direction of travel
- occurred during rain/night
- anonymous vs public display name

### 6.2 Supported issue categories
For MVP, support:
- pothole
- road surface broken
- repeated patchwork / uneven resurfacing
- waterlogging
- open manhole / drain cover issue
- dangerous speed breaker
- loose gravel / debris
- construction spill / mud on road
- missing lane markings
- road shoulder collapse
- road cave-in / severe hazard
- other road safety issue

### 6.3 Severity levels
- low
- medium
- high
- critical

Severity factors:
- depth/size
- road speed
- traffic volume
- bike risk
- visibility
- rain impact
- crash potential

### 6.4 Status workflow
Suggested public statuses:
- reported
- under review
- verified
- assigned
- in progress
- resolved
- rejected
- duplicate

Suggested internal moderation statuses:
- pending moderation
- approved
- rejected abuse
- low quality evidence
- duplicate merged

### 6.5 Public map
Map should support:
- point markers
- clusters
- severity-based marker emphasis
- heatmap or hotspot layer later
- boundaries overlay
- ward polygons
- filter by:
  - issue type
  - severity
  - status
  - date range
  - authority
  - ward
  - zone
  - verified only

### 6.6 Issue detail page
Display:
- title
- issue type
- severity
- status
- image gallery
- location map
- nearby duplicate count
- number of supporting reports
- first reported date
- latest activity
- likely responsible authority
- geographic metadata
- accountability chain
- comments or updates later
- shareable public URL

### 6.7 Duplicate detection
When a user reports near an existing issue:
- show a prompt saying nearby reports already exist
- allow the user to support an existing issue
- or create a distinct issue if clearly different

Initial duplicate logic:
- within X meters radius
- same issue type or compatible type
- similar recency window
- same road segment
- optionally image similarity later

### 6.8 Accountability engine
Given a location, the backend should resolve:
- road ownership candidate
- ward
- circle
- zone
- constituency metadata if available
- elected representative mapping
- engineering chain / authority chain

Output example:
- likely authority: GHMC
- ward: 42
- circle: X
- zone: Y
- corporator: Name
- engineer/division: Name if known
- alternate possible authority: HMDA

### 6.9 Confidence model
Authority resolution should support confidence:
- high confidence
- medium confidence
- low confidence

Also store a numeric score:
- 0.00 to 1.00

Example:
- likely authority: GHMC
- confidence: 0.82
- alternatives: HMDA, R&B

### 6.10 Search
Allow search by:
- locality
- road name
- ward
- pin code
- issue ID
- nearby location

### 6.11 Admin panel
Admin should be able to:
- view all reports
- moderate images/text
- merge duplicates
- edit metadata
- mark status changes
- manage authorities
- manage jurisdiction layers
- manage users
- export CSV
- inspect analytics

---

## 7. Non-Functional Requirements

- mobile-first responsive UI
- fast map performance
- secure media upload flow
- observability and audit logs
- role-based admin access
- API rate limiting
- anti-spam protection
- scalable geospatial querying
- support thousands of reports without poor performance
- proper caching for public map reads
- low-latency tile/layer loading

Performance targets:
- issue report submit API under 2 seconds excluding upload time
- public map query under 800 ms for cached views
- authority lookup under 500 ms for common cases
- image upload with signed URLs

---

## 8. Suggested Tech Stack

This stack aligns well with modern spatial apps and your background.

### Backend
Choose one:
- FastAPI + SQLAlchemy + Alembic
- or NestJS + Prisma/TypeORM

Recommended for this project:
- FastAPI

### Database
- PostgreSQL
- PostGIS extension for geospatial support

### Cache / queue
- Redis

### Background jobs
- Celery / RQ / Dramatiq if Python
- BullMQ if Node

### Object storage
- MinIO for local/dev
- S3-compatible storage for prod

### Frontend
- React
- Vite
- TypeScript
- Tailwind CSS
- React Query / TanStack Query
- Leaflet or Mapbox GL JS

Recommended for MVP:
- Leaflet with OpenStreetMap tiles or MapLibre if vector layers are needed

### Auth
- email OTP or magic link for light auth
- anonymous reporting allowed with limits
- Google login optional later

### Infra
- Docker Compose for dev
- reverse proxy via Traefik or Caddy
- CDN later for images and static assets

### Monitoring
- structured logs
- request tracing
- Sentry optional
- Prometheus/Grafana optional later

---

## 9. High-Level Architecture

## 9.1 Main components
1. Web frontend
2. API backend
3. Postgres + PostGIS
4. Redis
5. Object storage
6. Background worker
7. Admin dashboard
8. Jurisdiction data pipeline

## 9.2 Main flows
### Report creation
Frontend -> signed upload request -> object storage upload -> create issue API -> geospatial authority resolution -> duplicate detection -> moderation queue -> public issue published

### Public map query
Frontend -> map bounds API -> cached geospatial query -> cluster results -> render markers

### Accountability resolution
Frontend/API -> point coordinates -> spatial lookup across ward/authority polygons -> scoring engine -> accountability response

### Status update
Admin -> update issue -> write audit log -> notify watchers later -> update public map cache

---

## 10. Core Domain Model

Major entities:
- User
- Report
- Issue
- IssueEvidence
- IssueSupport
- IssueStatusHistory
- Authority
- JurisdictionLayer
- JurisdictionPolygon
- ResponsibilityMapping
- Ward
- Zone
- Circle
- RoadSegment
- AccountabilityChainNode
- ModerationAction
- AuditLog

Important distinction:
- A **Report** is one citizen submission.
- An **Issue** is the deduplicated public problem entity.
- Multiple reports can map to one issue.

This distinction is very important.

---

## 11. Database Design

Below is a strong MVP schema direction.

## 11.1 users
```sql
users
- id (uuid, pk)
- name
- email
- phone
- auth_provider
- is_anonymous_allowed
- role (citizen, moderator, admin)
- created_at
- updated_at
```

## 11.2 reports
```sql
reports
- id (uuid, pk)
- user_id (nullable if anonymous)
- issue_id (nullable until dedupe complete)
- latitude
- longitude
- geom geography(Point, 4326)
- issue_type
- severity
- description
- landmark
- road_name_input
- direction_of_travel
- dangerous_for_bikes boolean
- worse_in_rain boolean
- worse_at_night boolean
- moderation_status
- source (web, mobile-web, admin)
- submitted_at
- created_at
- updated_at
```

## 11.3 report_media
```sql
report_media
- id (uuid, pk)
- report_id (fk)
- storage_key
- media_type (image, video)
- mime_type
- width
- height
- size_bytes
- sort_order
- created_at
```

## 11.4 issues
```sql
issues
- id (uuid, pk)
- primary_report_id
- title
- canonical_issue_type
- canonical_severity
- status
- latitude
- longitude
- geom geography(Point, 4326)
- road_segment_id (nullable)
- first_reported_at
- latest_reported_at
- resolved_at (nullable)
- support_count
- report_count
- verification_score
- is_verified
- public_visibility
- created_at
- updated_at
```

## 11.5 issue_reports
```sql
issue_reports
- issue_id
- report_id
- linked_at
- link_reason
```

## 11.6 issue_status_history
```sql
issue_status_history
- id
- issue_id
- old_status
- new_status
- changed_by_user_id
- change_reason
- created_at
```

## 11.7 authorities
```sql
authorities
- id
- name
- authority_type (municipal, planning, highway, state, ward-level, contractor, other)
- parent_authority_id (nullable)
- description
- website_url
- grievance_url
- contact_phone
- contact_email
- is_active
- created_at
- updated_at
```

## 11.8 jurisdiction_polygons
```sql
jurisdiction_polygons
- id
- authority_id (nullable)
- layer_type (ward, circle, zone, municipality, constituency, special_road_zone, other)
- name
- code
- geom geometry(MultiPolygon, 4326)
- source_name
- source_version
- is_active
- created_at
- updated_at
```

## 11.9 responsibility_mappings
```sql
responsibility_mappings
- id
- polygon_id (nullable)
- road_segment_id (nullable)
- primary_authority_id
- secondary_authority_id (nullable)
- ownership_confidence numeric(5,4)
- notes
- created_at
- updated_at
```

## 11.10 accountability_chain_nodes
```sql
accountability_chain_nodes
- id
- authority_id
- jurisdiction_polygon_id (nullable)
- node_type (field_officer, engineer, circle_office, zonal_office, elected_rep, escalation, grievance_channel)
- display_name
- title
- phone
- email
- display_order
- is_public
- created_at
- updated_at
```

## 11.11 road_segments
```sql
road_segments
- id
- name
- alt_names
- road_class
- osm_way_id (nullable)
- geom geometry(MultiLineString, 4326)
- source_name
- source_version
- created_at
- updated_at
```

## 11.12 issue_supports
```sql
issue_supports
- id
- issue_id
- user_id (nullable)
- support_type (same_issue, dangerous, fixed_confirmed, still_exists)
- created_at
```

## 11.13 moderation_actions
```sql
moderation_actions
- id
- report_id (nullable)
- issue_id (nullable)
- moderator_user_id
- action_type
- notes
- created_at
```

## 11.14 audit_logs
```sql
audit_logs
- id
- actor_user_id
- entity_type
- entity_id
- action
- metadata_json
- created_at
```

---

## 12. Geospatial Design

This is one of the most important sections.

### 12.1 Use PostGIS
You need:
- point-in-polygon lookups
- distance queries
- clustering support
- road-segment proximity checks
- area aggregations
- map bounds filtering

### 12.2 Required spatial indexes
Add GiST indexes on:
- reports.geom
- issues.geom
- jurisdiction_polygons.geom
- road_segments.geom

### 12.3 Core spatial operations
1. Find polygons containing a point
2. Find nearest road segment
3. Find nearby reports within N meters
4. Aggregate issues within current viewport
5. Compute issue hotspots by grid/geohash later

### 12.4 Example geospatial use cases
- user taps map point -> determine ward
- issue created -> snap to nearest road segment
- map open -> fetch issues within viewport
- admin dashboard -> count unresolved issues by ward

---

## 13. Authority Resolution Engine

This is your moat.

## 13.1 Inputs
- lat/lng
- nearest road segment
- intersecting polygons
- optional road metadata
- manual admin overrides

## 13.2 Resolution logic
Run a scoring pipeline:
1. Check if point lies in special road ownership polygon
2. Check road segment explicit mapping
3. Check municipal ward/circle/zone
4. Check if road class implies external authority
5. Apply overrides if known
6. Return best authority with confidence score

## 13.3 Output example
```json
{
  "primary_authority": {
    "id": "uuid",
    "name": "GHMC",
    "confidence": 0.82
  },
  "alternate_authorities": [
    { "name": "HMDA", "confidence": 0.12 },
    { "name": "R&B", "confidence": 0.06 }
  ],
  "ward": {
    "name": "Ward 42",
    "code": "42"
  },
  "zone": {
    "name": "Serilingampally Zone"
  },
  "accountability_chain": [
    { "type": "field_officer", "title": "AEE", "display_name": "Name" },
    { "type": "circle_office", "title": "Deputy Commissioner", "display_name": "Name" },
    { "type": "elected_rep", "title": "Corporator", "display_name": "Name" }
  ]
}
```

## 13.4 Admin override support
Admins must be able to:
- manually correct authority
- manually set ownership confidence
- override bad automatic matches
- mark “ownership disputed”

That is essential for early versions.

---

## 14. Deduplication Strategy

### 14.1 Why it matters
Without dedupe:
- map gets noisy
- trust drops
- the same pothole appears 20 times
- analytics become misleading

### 14.2 MVP logic
When a report comes in:
1. find issues within configurable radius, e.g. 20 to 50 meters
2. compare issue type compatibility
3. compare nearest road segment
4. compare recency
5. if strong match, suggest merge/support
6. if no match, create new issue

### 14.3 Future improvements
- image similarity embeddings
- road direction awareness
- temporal merge confidence
- user-confirmed duplicate resolution

---

## 15. Moderation & Trust

You need trust controls from day one.

### 15.1 Threats
- fake reports
- abusive images/text
- spam
- repeated low-quality reports
- wrong locations
- political misuse
- mass false campaigns

### 15.2 MVP controls
- rate limit per IP/user
- captcha for anonymous reporting
- moderation queue
- image/type mismatch checks later
- minimum image resolution
- profanity filter in text
- duplicate suppression
- admin ability to hide reports

### 15.3 Trust signals
Show publicly:
- verified issue badge
- report count
- first seen date
- last confirmed date
- community confirmations
- confidence of authority mapping

This helps users trust the platform.

---

## 16. Roles and Permissions

### Citizen
- create report
- view map
- support existing issue
- share issue

### Moderator
- review reports
- reject/approve
- merge duplicates
- edit metadata
- manage status

### Admin
- all moderator permissions
- manage jurisdiction data
- manage authority mappings
- manage accountability chains
- manage users
- export analytics
- configure thresholds

---

## 17. API Design

Below is a suggested REST-first API set.

## 17.1 Public/reporting APIs
```http
POST   /api/v1/uploads/sign
POST   /api/v1/reports
GET    /api/v1/reports/{reportId}
GET    /api/v1/issues
GET    /api/v1/issues/{issueId}
POST   /api/v1/issues/{issueId}/support
GET    /api/v1/map/issues
GET    /api/v1/lookup/authority
GET    /api/v1/lookup/reverse-geocode
GET    /api/v1/search
```

## 17.2 Admin APIs
```http
GET    /api/v1/admin/reports
POST   /api/v1/admin/reports/{reportId}/approve
POST   /api/v1/admin/reports/{reportId}/reject
POST   /api/v1/admin/issues/{issueId}/merge
PATCH  /api/v1/admin/issues/{issueId}
POST   /api/v1/admin/issues/{issueId}/status
GET    /api/v1/admin/analytics/summary
POST   /api/v1/admin/jurisdictions/import
POST   /api/v1/admin/authorities
PATCH  /api/v1/admin/authorities/{authorityId}
POST   /api/v1/admin/accountability-chain
```

## 17.3 API payload examples

### Create report
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
  "media_keys": [
    "reports/2026/04/abc123.jpg"
  ]
}
```

### Map query
```http
GET /api/v1/map/issues?minLat=...&minLng=...&maxLat=...&maxLng=...&status=verified&severity=high,critical
```

---

## 18. Frontend Pages

## 18.1 Public pages
- landing page
- map page
- issue detail page
- report flow page
- locality page
- authority page
- about/how it works page

## 18.2 Admin pages
- dashboard
- moderation queue
- issue management
- authority management
- jurisdiction import/status
- analytics
- audit log

---

## 19. Frontend UX Details

## 19.1 Landing page
Should immediately answer:
- what the platform does
- why it matters
- report now CTA
- open map CTA
- recent hotspots
- stats such as:
  - issues reported
  - unresolved count
  - wards covered

## 19.2 Report flow
Step 1: capture/upload image  
Step 2: confirm location  
Step 3: select issue type  
Step 4: select severity  
Step 5: add optional details  
Step 6: show possible duplicate  
Step 7: submit

### Important UX rules
- keep reporting flow under 60 seconds
- mobile-first
- map interaction must not be painful on phone
- duplicate suggestion should not block reporting aggressively

## 19.3 Map page
Must support:
- current location
- filters
- issue cards on marker click
- list/map toggle on mobile
- "report here" CTA
- warning badges for critical issues

## 19.4 Issue page
Must clearly show:
- what is wrong
- how dangerous it is
- since when
- how many people confirm it
- who is responsible
- what the current status is

---

## 20. Analytics & Dashboards

Track:
- total reports
- total deduped issues
- unresolved issues
- avg issue age
- top hotspot areas
- worst wards by unresolved count
- worst wards by critical issue count
- new issues per day/week
- resolved issues per week
- duplicate merge rate
- authority confidence distribution

Useful admin views:
- unresolved issues older than 30 days
- critical issues with high support count
- issues with disputed authority
- wards with rapid increase in reports after rain

---

## 21. Data Acquisition Plan

This is crucial. Cursor should not skip this.

### 21.1 Required datasets
You will need:
- Hyderabad ward polygons
- zone/circle boundaries
- municipality boundaries
- road network data
- optional constituency data
- known authority ownership overlays if available
- named roads and road classes
- official public contact hierarchy where possible

### 21.2 Possible data sources
- OpenStreetMap for roads
- publicly available ward boundary files
- manually curated civic datasets
- government PDFs/manual imports
- admin-entered overrides

### 21.3 Reality check
Authority ownership will not be perfectly available as one clean dataset.

So build for:
- partial coverage
- confidence scoring
- manual corrections
- data versioning

### 21.4 Data pipeline requirements
Create import jobs for:
- GeoJSON
- Shapefile
- CSV with WKT/GeoJSON
- manual admin uploads

---

## 22. Suggested Folder Structure

If using a monorepo:

```text
apps/
  web/
  api/
  worker/
packages/
  db/
  ui/
  shared/
  geo/
infrastructure/
  docker/
  seeds/
  scripts/
data/
  geo/
  imports/
  fixtures/
docs/
```

If using Python backend + React frontend:

```text
frontend/
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
data/
docs/
docker/
```

---

## 23. Recommended Build Plan

## Phase 1: Core foundation
Build:
- backend skeleton
- frontend skeleton
- Postgres + PostGIS
- media upload
- basic report submission
- public issue list
- public issue detail page

Deliverable:
- users can submit road issue reports with image and location

## Phase 2: Map + issue model
Build:
- issue entity separate from report
- dedupe logic
- issue clustering
- map viewport APIs
- issue filters
- mobile map UI

Deliverable:
- public map with deduplicated issues

## Phase 3: Jurisdiction & authority mapping
Build:
- polygon import pipeline
- point-in-polygon services
- accountability metadata
- authority resolution scoring
- confidence display

Deliverable:
- issue detail page shows likely responsible authority and area hierarchy

## Phase 4: Admin & moderation
Build:
- moderation queue
- duplicate merge admin tools
- status updates
- audit logs
- analytics dashboard

Deliverable:
- operators can maintain platform quality

## Phase 5: Trust & growth
Build:
- support confirmations
- shareable URLs
- hotspot rankings
- locality pages
- subscriptions/alerts later

Deliverable:
- users return because the map becomes useful

---

## 24. MVP Acceptance Criteria

MVP is successful if:
- a user can submit a report from mobile in under 1 minute
- uploaded report appears on public map after moderation
- nearby duplicate reports can be merged
- issue detail page shows severity, age, image, and status
- system resolves at least ward and a likely authority for many locations
- admin can review and moderate reports
- map performs smoothly with hundreds to thousands of issues

---

## 25. Critical Engineering Notes for Cursor

These instructions are important.

### 25.1 Do not model reports and issues as the same table
A single issue must support multiple reports.

### 25.2 Use PostGIS from the beginning
Do not fake geospatial features with plain decimal fields only.

### 25.3 Design for partial authority certainty
Never hardcode false certainty when ownership is ambiguous.

### 25.4 Separate public and internal status
Moderation state and public issue resolution are different concepts.

### 25.5 Keep media storage decoupled
Use signed uploads and storage keys, not DB blobs.

### 25.6 Add audit logs for admin actions
This platform needs trust and traceability.

### 25.7 Keep issue types road-focused
Do not expand to general civic issues in MVP.

### 25.8 Build admin data correction tools early
Geo and authority data will be imperfect.

---

## 26. Nice-to-Have Features After MVP

- rain overlay and weather correlation
- AI-assisted severity estimation from image
- automatic road risk scoring
- SMS/WhatsApp sharing
- weekly locality digest
- issue subscription alerts
- multilingual UI
- route risk planner for bikers
- “safe today / risky today” road insights
- official complaint export packet PDF
- ward scorecards
- journalist/public data portal

---

## 27. Risks

### Product risks
- insufficient user adoption
- bad-quality reports
- duplicate-heavy map
- unclear ownership data
- legal sensitivity if naming officials incorrectly

### Technical risks
- poor map performance
- bad polygon data quality
- weak dedupe logic
- low authority resolution accuracy
- expensive media bandwidth at scale

### Operational risks
- moderation burden
- abuse/spam campaigns
- outdated official contact data
- political misuse

Mitigations:
- moderation tooling
- confidence-based resolution
- manual override workflows
- careful wording: “likely authority”
- versioned data imports
- rate limiting + abuse controls

---

## 28. Suggested Initial Launch Strategy

Start narrow:
- Hyderabad only
- road issues only
- mobile web only
- selected localities first if needed

Ideal initial launch areas:
- high commuter traffic zones
- biker-heavy corridors
- areas with frequent pothole complaints
- places where map density becomes visible quickly

Early traction channels:
- biker communities
- local X/Twitter pages
- Reddit Hyderabad
- local Instagram pages
- community groups
- RWAs

---

## 29. Sample Copy for UI

### Hero
**Report dangerous roads in Hyderabad. See who is responsible.**

### Subtext
Upload a photo, mark the location, and help build a public accountability map for potholes and unsafe roads.

### CTA buttons
- Report a road issue
- View live map

### Issue card copy
- First reported 12 days ago
- 8 riders confirmed this issue
- Likely authority: GHMC
- Status: Unresolved

### Accountability section
**Who is responsible?**  
This location likely falls under GHMC, Ward 42. The authority mapping has medium confidence.

---

## 30. What Cursor Should Build First

Tell Cursor to implement in this exact order:

1. project scaffolding
2. Postgres + PostGIS setup
3. report submission backend
4. object storage upload flow
5. issue/report schema separation
6. public map API with viewport query
7. frontend map page
8. issue detail page
9. duplicate matching
10. polygon import system
11. authority lookup endpoint
12. admin moderation UI
13. analytics dashboard

Do not start with advanced AI features.

Do not start with native mobile apps.

Do not start with full government integration.

---

## 31. Direct Build Instructions for Cursor

Use the following implementation intent:

- Build a production-oriented MVP, not a hackathon demo.
- Use clear domain modeling for reports vs issues.
- Use PostGIS for all location-aware features.
- Build a mobile-friendly reporting flow.
- Prioritize public map performance.
- Keep the UI clean, minimal, and action-driven.
- Add admin tools for data correction and moderation.
- Make authority mapping confidence-aware and overrideable.
- Write clean migrations, seeders, and sample fixtures.
- Add structured logging and audit logs.
- Add rate limiting and abuse protection on public report APIs.
- Seed sample Hyderabad data placeholders where real datasets are not yet available.
- Keep all constants configurable.

---

## 32. Final Note

The product will succeed only if these three things are done well:

1. reporting must be extremely easy  
2. the public map must feel alive and useful  
3. authority resolution must be better than what people can figure out on their own

That third part is the moat.

If the system only lets people upload pothole photos, it becomes forgettable.

If it tells people where the issue is, how bad it is, how many others saw it, and who is responsible, it becomes valuable.
