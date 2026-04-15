# Phase 4: Admin & Moderation

**Goal:** Build the admin dashboard, moderation queue, duplicate merge tools, status management, audit logging, and analytics dashboard so that operators can maintain platform quality and trust.

**Deliverable:** Operators can review reports, moderate content, merge duplicates, update statuses, and view analytics.

**Depends on:** Phase 3 (Jurisdiction & Authority Mapping) completed.

---

## 4.1 Admin Dashboard

### Dashboard Home
Display at-a-glance metrics:
- Total reports (all time)
- Total deduplicated issues
- Unresolved issues count
- Issues pending moderation
- New reports today / this week
- Average issue age (unresolved)
- Top 5 hotspot wards (by unresolved count)
- Critical issues with high support count

### Layout
- Sidebar navigation for all admin sections
- Role-based visibility (moderator vs admin)
- Responsive but desktop-optimized (admin is primarily desktop)

### Admin Sections
1. Dashboard (home / summary)
2. Moderation Queue
3. Issue Management
4. Authority Management
5. Jurisdiction Import / Status
6. Analytics
7. User Management (admin only)
8. Audit Log (admin only)

---

## 4.2 Moderation Queue

### Purpose
All new reports enter `moderation_status = pending_moderation`. Moderators review before they become publicly visible.

### Queue View
- Table/card list of pending reports
- Sortable by: submitted date, severity, issue type
- Filterable by: issue type, severity, source
- Each item shows:
  - Thumbnail of first image
  - Issue type, severity
  - Location (ward + road name if available)
  - Submitted at
  - Reporter info (name or "anonymous")
  - Quick action buttons

### Moderation Actions
| Action | Result |
|--------|--------|
| **Approve** | `moderation_status = approved`, report becomes public, linked issue updated |
| **Reject (abuse)** | `moderation_status = rejected_abuse`, hidden from public |
| **Reject (low quality)** | `moderation_status = low_quality_evidence`, hidden, user notified |
| **Mark duplicate** | `moderation_status = duplicate_merged`, link to existing issue |
| **Edit metadata** | Fix issue type, severity, location before approval |

### APIs

#### `GET /api/v1/admin/reports`
Paginated list with filters:
- `moderation_status`: pending_moderation, approved, rejected_abuse, etc.
- `issue_type`, `severity`, `date_from`, `date_to`
- `sort_by`: submitted_at, severity

#### `POST /api/v1/admin/reports/{reportId}/approve`
```json
{
  "notes": "Verified pothole image, location correct"
}
```
- Sets `moderation_status = approved`
- Creates/links issue if not yet done
- Logs action to `moderation_actions` and `audit_logs`

#### `POST /api/v1/admin/reports/{reportId}/reject`
```json
{
  "reason": "rejected_abuse",
  "notes": "Offensive content in image"
}
```
- Sets `moderation_status` to specified reason
- Logs action

---

## 4.3 Duplicate Merge Tools

### Admin Merge Flow
1. Admin views an issue and sees potentially related issues nearby
2. System suggests merge candidates (same logic as Phase 2 dedupe, but broader radius for admin)
3. Admin selects issues to merge
4. Admin picks the "surviving" canonical issue
5. All reports from merged issues are re-linked to the surviving issue
6. Merged issues get `status = duplicate`
7. Counts (report_count, support_count) aggregated on surviving issue
8. All actions logged

### API: `POST /api/v1/admin/issues/{issueId}/merge`
```json
{
  "merge_issue_ids": ["uuid-1", "uuid-2"],
  "surviving_issue_id": "uuid-target",
  "notes": "Same pothole reported from different angles"
}
```

### Merge Logic
1. Validate all issues exist and are not already resolved/rejected
2. For each merged issue:
   - Update all `issue_reports` entries to point to surviving issue
   - Transfer `issue_supports` to surviving issue
   - Set merged issue `status = duplicate`
   - Log `issue_status_history` entry
3. Recalculate surviving issue:
   - `report_count` = sum of all linked reports
   - `support_count` = sum of all supports
   - `canonical_severity` = highest among all
   - `first_reported_at` = earliest
   - `latest_reported_at` = latest
   - Recalculate `verification_score`
4. Log `moderation_actions` and `audit_logs`

---

## 4.4 Issue Management

### Issue List View
- Paginated table of all issues
- Columns: ID, title, type, severity, status, ward, authority, report count, support count, first reported, last activity
- Filterable by: status, type, severity, ward, authority, date range, verified/unverified
- Sortable by all columns
- Bulk actions: update status, assign authority

### Issue Detail (Admin View)
Everything from the public view, plus:
- All linked reports (with moderation status)
- Edit metadata inline (title, type, severity, location)
- Status change controls
- Authority override controls
- Merge tool access
- Moderation history
- Audit trail for this issue

### Status Management
#### API: `POST /api/v1/admin/issues/{issueId}/status`
```json
{
  "new_status": "verified",
  "reason": "Confirmed via field inspection"
}
```
- Validates status transition
- Creates `issue_status_history` entry
- Logs to `audit_logs`
- If `new_status = resolved`, sets `resolved_at`

#### Valid Status Transitions
| From | Allowed To |
|------|-----------|
| reported | under_review, verified, rejected, duplicate |
| under_review | verified, rejected, duplicate |
| verified | assigned, in_progress, resolved, rejected |
| assigned | in_progress, resolved, rejected |
| in_progress | resolved, verified (revert) |
| resolved | verified (re-opened) |
| rejected | reported (re-opened) |
| duplicate | reported (un-merged) |

### Metadata Edit
#### API: `PATCH /api/v1/admin/issues/{issueId}`
```json
{
  "title": "Updated Title",
  "canonical_issue_type": "road_surface_broken",
  "canonical_severity": "critical",
  "latitude": 17.4432,
  "longitude": 78.3771
}
```
- All changes logged in `audit_logs`

---

## 4.5 Authority Management

### Authority CRUD
- List all authorities
- Add new authority
- Edit authority details (name, type, contacts, URLs)
- Deactivate authority
- View responsibility mappings for an authority

### APIs
```http
GET    /api/v1/admin/authorities
POST   /api/v1/admin/authorities
PATCH  /api/v1/admin/authorities/{authorityId}
```

### Accountability Chain Management
- View/edit accountability chain nodes for an authority + jurisdiction
- Add/remove chain nodes
- Reorder display_order
- Toggle `is_public` visibility

### API: `POST /api/v1/admin/accountability-chain`
```json
{
  "authority_id": "uuid",
  "jurisdiction_polygon_id": "uuid",
  "node_type": "field_officer",
  "display_name": "Name",
  "title": "AEE",
  "phone": "+91...",
  "email": "...",
  "display_order": 1,
  "is_public": true
}
```

---

## 4.6 Jurisdiction Import & Status

### Admin UI for Data Import
- Upload GeoJSON / Shapefile / CSV
- Select layer type and metadata
- Preview features on map before import
- Trigger import job
- View import job status and results

### Jurisdiction Data Status Page
- Table of all jurisdiction layers with:
  - Layer type
  - Feature count
  - Source name and version
  - Import date
  - Active/inactive status
- Coverage visualization: show which areas have data vs gaps
- Quick actions: activate/deactivate layer, re-import

---

## 4.7 Audit Logging

### What Gets Logged
Every admin/moderator action:
| Entity | Actions Logged |
|--------|---------------|
| Report | approve, reject, edit metadata |
| Issue | status change, merge, metadata edit, authority override |
| Authority | create, update, deactivate |
| Jurisdiction | import, activate, deactivate |
| Accountability chain | add node, edit node, remove node |
| User | role change, deactivation |
| Responsibility mapping | create, update, override |

### `audit_logs` table (from Phase 1 schema)
| Column | Type |
|--------|------|
| id | UUID (PK) |
| actor_user_id | UUID (FK) |
| entity_type | VARCHAR (report, issue, authority, etc.) |
| entity_id | UUID |
| action | VARCHAR (approve, reject, status_change, merge, etc.) |
| metadata_json | JSONB (old values, new values, notes) |
| created_at | TIMESTAMPTZ |

### `moderation_actions` table
| Column | Type |
|--------|------|
| id | UUID (PK) |
| report_id | UUID (FK, nullable) |
| issue_id | UUID (FK, nullable) |
| moderator_user_id | UUID (FK) |
| action_type | VARCHAR |
| notes | TEXT |
| created_at | TIMESTAMPTZ |

### Audit Log Viewer (Admin Only)
- Paginated table of all audit entries
- Filterable by: entity_type, action, actor, date range
- Each entry shows: timestamp, actor, action, entity link, metadata diff
- Export to CSV

---

## 4.8 Analytics Dashboard

### Summary Metrics
| Metric | Description |
|--------|-------------|
| Total reports | All-time report count |
| Total deduped issues | Canonical issue count |
| Unresolved issues | Issues not resolved/rejected |
| Avg issue age | Mean days since first_reported_at for unresolved issues |
| New issues per day/week | Trend line |
| Resolved issues per week | Trend line |
| Duplicate merge rate | % of reports merged into existing issues |

### Geographic Analytics
- Top hotspot areas (by issue count)
- Worst wards by unresolved count
- Worst wards by critical issue count
- Ward-level breakdown table
- Authority confidence distribution (% high/medium/low)

### Operational Views
| View | Description |
|------|-------------|
| Unresolved > 30 days | Issues older than 30 days still open |
| Critical + high support | Critical issues with high community confirmation |
| Disputed authority | Issues where authority mapping is low confidence |
| Post-rain surge | Wards with rapid increase after rain (requires date correlation) |

### Charts & Visualizations
- Bar chart: issues by ward
- Line chart: reports over time
- Pie chart: issue type distribution
- Severity distribution
- Status distribution
- Heatmap visualization of issue density (optional)

### API: `GET /api/v1/admin/analytics/summary`
**Response:**
```json
{
  "total_reports": 1234,
  "total_issues": 890,
  "unresolved_issues": 456,
  "avg_issue_age_days": 18.5,
  "reports_this_week": 67,
  "resolved_this_week": 23,
  "duplicate_merge_rate": 0.28,
  "top_wards": [
    { "ward": "Ward 42", "unresolved_count": 34 },
    { "ward": "Ward 15", "unresolved_count": 28 }
  ],
  "severity_distribution": {
    "low": 120,
    "medium": 340,
    "high": 310,
    "critical": 120
  },
  "status_distribution": {
    "reported": 200,
    "under_review": 50,
    "verified": 150,
    "assigned": 30,
    "in_progress": 26,
    "resolved": 400,
    "rejected": 24,
    "duplicate": 10
  }
}
```

### Export
- CSV export for all analytics data
- CSV export for filtered issue lists
- Date range selection for all exports

### API: Export
```http
GET /api/v1/admin/analytics/export?format=csv&date_from=...&date_to=...
GET /api/v1/admin/issues/export?format=csv&status=...&ward=...
```

---

## 4.9 User Management (Admin Only)

### User List
- Paginated table of all users
- Columns: name, email, role, reports submitted, joined date, status
- Search by name/email
- Filter by role

### User Actions
- Change role (citizen ↔ moderator ↔ admin)
- Deactivate user
- View user's reports
- All changes logged in audit_logs

---

## 4.10 Roles & Permissions Enforcement

### Permission Matrix
| Action | Citizen | Moderator | Admin |
|--------|---------|-----------|-------|
| Create report | ✅ | ✅ | ✅ |
| View public map | ✅ | ✅ | ✅ |
| Support issue | ✅ | ✅ | ✅ |
| Share issue | ✅ | ✅ | ✅ |
| Review reports | ❌ | ✅ | ✅ |
| Approve/reject | ❌ | ✅ | ✅ |
| Merge duplicates | ❌ | ✅ | ✅ |
| Edit issue metadata | ❌ | ✅ | ✅ |
| Manage status | ❌ | ✅ | ✅ |
| Manage authorities | ❌ | ❌ | ✅ |
| Manage jurisdictions | ❌ | ❌ | ✅ |
| Manage accountability chains | ❌ | ❌ | ✅ |
| Manage users | ❌ | ❌ | ✅ |
| View audit logs | ❌ | ❌ | ✅ |
| Export analytics | ❌ | ❌ | ✅ |
| Configure thresholds | ❌ | ❌ | ✅ |

### Implementation
- Role stored on `users.role`
- Backend middleware/dependency checks role on every admin endpoint
- Frontend hides UI elements based on role
- All permission denials return 403 with clear message

---

## Acceptance Criteria for Phase 4

- [ ] Admin dashboard displays summary metrics
- [ ] Moderation queue shows pending reports with quick actions
- [ ] Moderators can approve, reject, and edit reports
- [ ] Duplicate merge tool works (select issues → merge → surviving issue updated)
- [ ] Issue status changes validated against transition rules
- [ ] Status history tracked in `issue_status_history`
- [ ] Authority management CRUD works
- [ ] Accountability chain CRUD works
- [ ] Jurisdiction import UI allows upload and monitoring
- [ ] All admin actions logged in `audit_logs`
- [ ] All moderation actions logged in `moderation_actions`
- [ ] Audit log viewer shows filterable history
- [ ] Analytics dashboard shows all summary metrics
- [ ] Analytics shows geographic breakdown by ward
- [ ] CSV export works for analytics and issue lists
- [ ] User management works (role change, deactivation)
- [ ] Role-based permissions enforced on all admin endpoints
- [ ] Admin UI is responsive but desktop-optimized

---

## Related Spec Sections
- Section 6.4: Status workflow
- Section 6.11: Admin panel
- Section 11.13: moderation_actions
- Section 11.14: audit_logs
- Section 13.4: Admin override support
- Section 15: Moderation & trust
- Section 16: Roles and permissions
- Section 17.2: Admin APIs
- Section 18.2: Admin pages
- Section 20: Analytics & dashboards
- Section 25.6: Audit logs for admin actions
