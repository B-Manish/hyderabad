# Phase 5: Trust & Growth

**Goal:** Build features that drive user retention, community trust, and platform growth — support confirmations, shareable URLs, hotspot rankings, locality pages, search, and foundation for future alerts/subscriptions.

**Deliverable:** Users return because the map is genuinely useful. The platform gains trust signals, discoverability, and community engagement loops.

**Depends on:** Phase 4 (Admin & Moderation) completed.

---

## 5.1 Issue Support / Confirmation System

### Purpose
Allow users to confirm or interact with existing issues — building community-verified trust signals.

### `issue_supports` table (from schema)
| Column | Type | Notes |
|--------|------|-------|
| id | UUID (PK) | |
| issue_id | UUID (FK) | |
| user_id | UUID (FK, nullable) | nullable for anonymous |
| support_type | ENUM | same_issue, dangerous, fixed_confirmed, still_exists |
| created_at | TIMESTAMPTZ | |

### Support Types
| Type | Meaning | Effect |
|------|---------|--------|
| `same_issue` | "I've seen this too" | Increments support_count, boosts verification_score |
| `dangerous` | "This is dangerous" | Adds weight to severity, flags for attention |
| `fixed_confirmed` | "This has been fixed" | If enough confirmations, suggest status → resolved |
| `still_exists` | "This is still here" | Resets age tracking, keeps issue active |

### API: `POST /api/v1/issues/{issueId}/support`
```json
{
  "support_type": "same_issue"
}
```
**Response:**
```json
{
  "issue_id": "uuid",
  "support_count": 13,
  "support_type": "same_issue",
  "created_at": "2026-04-15T10:00:00Z"
}
```

### Rules
- Rate limit: 1 support per user per issue per type per 24 hours
- Anonymous supports allowed but with stricter rate limiting (per IP)
- `support_count` on `issues` table updated on each new support
- `verification_score` recalculated
- If `fixed_confirmed` count exceeds threshold (configurable, default: 3), trigger admin review for resolution

### Frontend UX
- Issue detail page shows support buttons:
  - "I've seen this too" (👁️ with count)
  - "This is dangerous" (⚠️)
  - "Still exists" (🔄)
  - "Fixed" (✅)
- Show total support count prominently
- Show "X riders confirmed this issue" social proof text

---

## 5.2 Shareable URLs & Social Sharing

### Shareable Issue URLs
- Every issue has a clean public URL: `/issues/{issueId}`
- URL slug alternative (future): `/issues/{issueId}/{slugified-title}`
- Open Graph (OG) meta tags for social media preview:
  - `og:title`: Issue title
  - `og:description`: "Pothole reported 12 days ago near Gachibowli. 8 riders confirmed. Likely authority: GHMC."
  - `og:image`: First report image (thumbnail)
  - `og:url`: Canonical issue URL
- Twitter Card meta tags

### Shareable Map URLs
- Map state encoded in URL query parameters:
  - Center lat/lng, zoom level
  - Active filters
  - Example: `/map?lat=17.44&lng=78.38&zoom=15&severity=high,critical`
- Users can copy/share the current map view

### Share Actions
- Share button on issue detail page
- Options: Copy link, WhatsApp, Twitter/X, generic share (Web Share API on mobile)
- Track share events for analytics (optional)

---

## 5.3 Hotspot Rankings

### What Are Hotspots
Areas with concentrated unresolved road issues, ranked by severity and density.

### Hotspot Computation
Periodically compute (background job, e.g., daily):
- Aggregate issues by ward
- Score each ward:
  ```
  hotspot_score = (critical_count * 4) + (high_count * 3) + (medium_count * 2) + (low_count * 1)
                  + (avg_age_days * 0.1) + (total_support * 0.05)
  ```
- Rank wards by hotspot_score
- Store results in a cache table or Redis

### Public Hotspot Display
- **Landing page**: "Top 5 Worst Road Areas This Week"
- **Dedicated hotspot page**: Full ranked list of wards
- Each entry shows: ward name, issue count, critical count, avg age, hotspot score
- Link to map filtered by that ward

### API
```http
GET /api/v1/hotspots?limit=10&period=week
```
**Response:**
```json
{
  "period": "2026-W16",
  "hotspots": [
    {
      "ward": "Ward 42",
      "zone": "Serilingampally",
      "issue_count": 34,
      "critical_count": 8,
      "avg_age_days": 22,
      "hotspot_score": 156,
      "map_url": "/map?ward=42&severity=high,critical"
    }
  ]
}
```

---

## 5.4 Locality Pages

### Purpose
SEO-friendly, human-readable pages for each locality/ward/area showing road conditions.

### URL Structure
- `/areas/{ward-slug}` — e.g., `/areas/ward-42-gachibowli`
- `/areas/{zone-slug}` — e.g., `/areas/serilingampally-zone`

### Content
- Area name and hierarchy (Ward → Circle → Zone)
- Total issues in area
- Unresolved count
- Severity breakdown (bar chart)
- Top issues list (sorted by severity + support)
- Mini-map showing issues in this area
- Responsible authority info
- Accountability chain for this area
- Hotspot rank for this ward

### API
```http
GET /api/v1/areas/{wardCode}
GET /api/v1/areas/{wardCode}/issues?page=1&per_page=20
```

### SEO
- Server-side rendering (SSR) or static generation for locality pages
- Structured data (JSON-LD) for location and civic information
- Canonical URLs
- Sitemap generation for all active ward/locality pages

---

## 5.5 Search

### Search Capabilities
| Query Type | Input | Behavior |
|-----------|-------|----------|
| Locality name | "Gachibowli" | Match ward/zone names, road names |
| Road name | "Outer Ring Road" | Match road_segments.name, reports.road_name_input |
| Ward number/name | "Ward 42" | Match jurisdiction_polygons |
| Pin code | "500032" | Geocode to area, then spatial search |
| Issue ID | "abc123" | Direct lookup |
| Nearby location | GPS coords or "near me" | Spatial search around point |

### API: `GET /api/v1/search`
**Query Parameters:**
- `q`: search query text
- `type`: locality | road | ward | issue | nearby (optional filter)
- `lat`, `lng`: for nearby search
- `page`, `per_page`: pagination

**Response:**
```json
{
  "results": [
    {
      "type": "ward",
      "id": "uuid",
      "name": "Ward 42 — Gachibowli",
      "issue_count": 34,
      "url": "/areas/ward-42-gachibowli"
    },
    {
      "type": "issue",
      "id": "uuid",
      "title": "Pothole — Gachibowli Main Road",
      "severity": "high",
      "url": "/issues/uuid"
    }
  ],
  "total": 15
}
```

### Search Implementation
- Full-text search on PostgreSQL using `tsvector` / `tsquery` for names
- Spatial search using PostGIS for nearby queries
- Combine results across entity types with relevance scoring
- Add search bar to header/map page

---

## 5.6 Trust Signals & Public Confidence

### Display on Issues
- **Verified badge**: shown when `is_verified = true` (verification_score > threshold)
- **Report count**: "8 riders reported this"
- **First seen date**: "First reported 12 days ago"
- **Last confirmed**: "Last confirmed 2 days ago" (from `still_exists` supports)
- **Community confirmations**: "12 people confirmed this issue"
- **Authority confidence**: "High confidence" / "Medium confidence" badge
- Disclaimer language: always "likely authority", never absolute claims

### Public Statistics (Landing Page)
Update landing page stats from placeholders to real data:
- Total issues reported
- Total unresolved issues
- Wards covered
- Community confirmations
- Issues resolved

---

## 5.7 About / How It Works Page

### Content
- What the platform does
- How to report an issue (step by step with illustrations)
- How authority resolution works (simplified explanation)
- What "confidence" means
- How duplicates are handled
- How to support/confirm existing issues
- Privacy and data handling
- Disclaimer about authority mapping accuracy
- Contact / feedback information

---

## 5.8 Authority Public Page

### URL: `/authorities/{authority-slug}`
Display:
- Authority name and type
- Number of issues attributed to this authority
- Severity breakdown
- Unresolved count
- Average resolution time (if enough data)
- Covered wards/zones
- Public accountability chain (where `is_public = true`)
- Grievance URL / contact info (if available)

### Purpose
Public accountability — citizens can see which authority has the most unresolved issues.

---

## 5.9 Subscriptions & Alerts Foundation

### MVP Scope (Foundation Only)
- "Watch this issue" button → stores user-issue subscription
- "Watch this area" → stores user-ward subscription
- No email/push delivery in Phase 5 — just the data model and UI
- Delivery mechanism (email, push, WhatsApp) planned for post-MVP

### Data Model
```sql
subscriptions
- id (UUID, PK)
- user_id (UUID, FK)
- entity_type (issue, ward, zone, authority)
- entity_id (UUID)
- created_at
```

---

## 5.10 Anti-Spam & Rate Limiting Hardening

### Tighten Controls
- Review and tune rate limits based on Phase 1–4 usage patterns
- IP-based throttling for anonymous actions
- User-based throttling for authenticated actions
- Progressive challenge: captcha after N reports per day
- Detect and flag bulk similar reports from same IP range
- Moderator alerts for suspicious patterns

### Configurable Thresholds (Admin-Managed)
| Setting | Default | Description |
|---------|---------|-------------|
| `max_reports_per_ip_per_hour` | 10 | Anonymous report limit |
| `max_reports_per_user_per_day` | 30 | Authenticated user limit |
| `max_supports_per_user_per_day` | 50 | Support action limit |
| `duplicate_radius_meters` | 30 | Duplicate detection radius |
| `verification_threshold` | 0.6 | Score to mark verified |
| `fixed_confirm_threshold` | 3 | Confirmations to suggest resolved |

---

## 5.11 Performance & Caching Optimization

### Caching Strategy
- Redis cache for:
  - Map viewport queries (TTL: 5 min, invalidated on issue changes)
  - Authority lookups by geohash (TTL: 1 hour)
  - Hotspot rankings (TTL: 1 hour)
  - Landing page stats (TTL: 15 min)
  - Locality page data (TTL: 30 min)
- HTTP cache headers for static assets and images
- CDN consideration for media files

### Query Optimization
- Review and optimize slow queries from Phases 1–4
- Add missing indexes based on query patterns
- Connection pooling tuning
- Monitor query performance in production

---

## Acceptance Criteria for Phase 5

- [ ] Issue support / confirmation system works (same_issue, dangerous, still_exists, fixed_confirmed)
- [ ] Support counts update on issues and influence verification score
- [ ] Rate limiting active on support actions
- [ ] Shareable URLs work with Open Graph meta tags for social preview
- [ ] Map state encoded in URL and shareable
- [ ] Share button on issue detail page (copy link, WhatsApp, Twitter)
- [ ] Hotspot rankings computed and displayed on landing page
- [ ] Hotspot API returns ranked wards with scores
- [ ] Locality pages render for each ward with issue data and mini-map
- [ ] Locality pages have proper SEO (SSR/meta tags/structured data)
- [ ] Search works for locality, road, ward, issue ID, and nearby location
- [ ] Trust signals displayed on issues (verified badge, report count, age, confirmations)
- [ ] Landing page shows real statistics
- [ ] About / How It Works page present
- [ ] Authority public page displays accountability data
- [ ] Subscription data model exists (watch issue, watch area)
- [ ] Rate limiting and anti-spam tuned and configurable by admin
- [ ] Caching layer covers all high-traffic queries
- [ ] All performance targets met (map < 800ms, authority < 500ms, submit < 2s)

---

## Related Spec Sections
- Section 5.2–5.4: User stories (viewer, accountability, duplicate)
- Section 6.5: Public map filters
- Section 6.10: Search
- Section 7: Non-functional requirements / performance
- Section 15.3: Trust signals
- Section 18.1: Public pages (locality, authority, about)
- Section 19.1: Landing page
- Section 19.4: Issue page
- Section 20: Analytics
- Section 28: Launch strategy
- Section 29: Sample copy
