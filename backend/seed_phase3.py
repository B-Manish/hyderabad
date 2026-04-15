"""Phase 3 seed data: Hyderabad authorities, ward/zone/circle polygons, road segments, accountability chains."""
import uuid
import asyncio
from sqlalchemy import text
from app.db.session import async_session

# --- Authority Records ---
# Well-known Hyderabad road authorities
AUTHORITIES = [
    {
        "id": "a0000001-0000-0000-0000-000000000001",
        "name": "GHMC",
        "authority_type": "municipal",
        "description": "Greater Hyderabad Municipal Corporation — responsible for municipal roads, wards, and local infrastructure",
        "website_url": "https://www.ghmc.gov.in",
        "grievance_url": "https://www.ghmc.gov.in/Grievance.aspx",
        "contact_phone": "040-21111111",
        "contact_email": "commissioner@ghmc.gov.in",
    },
    {
        "id": "a0000001-0000-0000-0000-000000000002",
        "name": "HMDA",
        "authority_type": "planning",
        "description": "Hyderabad Metropolitan Development Authority — responsible for metropolitan planning and ORR",
        "website_url": "https://www.hmda.gov.in",
        "grievance_url": "https://www.hmda.gov.in/complaints",
        "contact_phone": "040-23262626",
        "contact_email": "commissioner@hmda.gov.in",
    },
    {
        "id": "a0000001-0000-0000-0000-000000000003",
        "name": "R&B",
        "authority_type": "state",
        "description": "Roads & Buildings Department, Telangana — responsible for state highways and major roads",
        "website_url": "https://roadsandbuildings.telangana.gov.in",
        "grievance_url": "https://roadsandbuildings.telangana.gov.in/grievances",
        "contact_phone": "040-23456789",
        "contact_email": "se-rb@telangana.gov.in",
    },
    {
        "id": "a0000001-0000-0000-0000-000000000004",
        "name": "NHAI",
        "authority_type": "highway",
        "description": "National Highways Authority of India — responsible for national highways",
        "website_url": "https://www.nhai.gov.in",
        "grievance_url": "https://grievances.nhai.gov.in",
        "contact_phone": "1033",
        "contact_email": "complaints@nhai.org",
    },
    {
        "id": "a0000001-0000-0000-0000-000000000005",
        "name": "HGCL",
        "authority_type": "municipal",
        "description": "Hyderabad Growth Corridor Limited — ORR and strategic corridor maintenance",
        "website_url": "https://www.hgcl.gov.in",
        "grievance_url": "https://www.hgcl.gov.in/complaints",
        "contact_phone": "040-23001234",
        "contact_email": "info@hgcl.gov.in",
    },
]

# --- Simplified Hyderabad Zone Polygons ---
# These are simplified bounding polygons for the 6 GHMC zones
# Real data would come from GeoJSON imports but we seed approximations
ZONES = [
    {
        "name": "Charminar Zone",
        "code": "CHZ",
        "polygon_wkt": "MULTIPOLYGON(((78.44 17.34, 78.50 17.34, 78.50 17.38, 78.44 17.38, 78.44 17.34)))",
    },
    {
        "name": "Khairatabad Zone",
        "code": "KHZ",
        "polygon_wkt": "MULTIPOLYGON(((78.42 17.38, 78.48 17.38, 78.48 17.44, 78.42 17.44, 78.42 17.38)))",
    },
    {
        "name": "Serilingampally Zone",
        "code": "SRZ",
        "polygon_wkt": "MULTIPOLYGON(((78.30 17.40, 78.42 17.40, 78.42 17.48, 78.30 17.48, 78.30 17.40)))",
    },
    {
        "name": "Kukatpally Zone",
        "code": "KKZ",
        "polygon_wkt": "MULTIPOLYGON(((78.38 17.44, 78.50 17.44, 78.50 17.52, 78.38 17.52, 78.38 17.44)))",
    },
    {
        "name": "Secunderabad Zone",
        "code": "SCZ",
        "polygon_wkt": "MULTIPOLYGON(((78.46 17.42, 78.54 17.42, 78.54 17.48, 78.46 17.48, 78.46 17.42)))",
    },
    {
        "name": "LB Nagar Zone",
        "code": "LBZ",
        "polygon_wkt": "MULTIPOLYGON(((78.46 17.34, 78.56 17.34, 78.56 17.42, 78.46 17.42, 78.46 17.34)))",
    },
]

# --- Simplified Ward Polygons (sample of ~15 wards) ---
WARDS = [
    {"name": "Ward 1 - Patancheru", "code": "1", "polygon_wkt": "MULTIPOLYGON(((78.26 17.52, 78.30 17.52, 78.30 17.56, 78.26 17.56, 78.26 17.52)))"},
    {"name": "Ward 2 - Chandanagar", "code": "2", "polygon_wkt": "MULTIPOLYGON(((78.30 17.48, 78.34 17.48, 78.34 17.52, 78.30 17.52, 78.30 17.48)))"},
    {"name": "Ward 10 - Gachibowli", "code": "10", "polygon_wkt": "MULTIPOLYGON(((78.32 17.42, 78.36 17.42, 78.36 17.46, 78.32 17.46, 78.32 17.42)))"},
    {"name": "Ward 15 - HITEC City", "code": "15", "polygon_wkt": "MULTIPOLYGON(((78.34 17.43, 78.38 17.43, 78.38 17.46, 78.34 17.46, 78.34 17.43)))"},
    {"name": "Ward 25 - Jubilee Hills", "code": "25", "polygon_wkt": "MULTIPOLYGON(((78.40 17.42, 78.44 17.42, 78.44 17.45, 78.40 17.45, 78.40 17.42)))"},
    {"name": "Ward 30 - Banjara Hills", "code": "30", "polygon_wkt": "MULTIPOLYGON(((78.44 17.41, 78.47 17.41, 78.47 17.44, 78.44 17.44, 78.44 17.41)))"},
    {"name": "Ward 42 - Ameerpet", "code": "42", "polygon_wkt": "MULTIPOLYGON(((78.44 17.44, 78.48 17.44, 78.48 17.47, 78.44 17.47, 78.44 17.44)))"},
    {"name": "Ward 50 - Begumpet", "code": "50", "polygon_wkt": "MULTIPOLYGON(((78.46 17.44, 78.49 17.44, 78.49 17.46, 78.46 17.46, 78.46 17.44)))"},
    {"name": "Ward 60 - Secunderabad", "code": "60", "polygon_wkt": "MULTIPOLYGON(((78.48 17.43, 78.51 17.43, 78.51 17.46, 78.48 17.46, 78.48 17.43)))"},
    {"name": "Ward 75 - Charminar", "code": "75", "polygon_wkt": "MULTIPOLYGON(((78.46 17.36, 78.50 17.36, 78.50 17.38, 78.46 17.38, 78.46 17.36)))"},
    {"name": "Ward 80 - Malakpet", "code": "80", "polygon_wkt": "MULTIPOLYGON(((78.49 17.36, 78.52 17.36, 78.52 17.39, 78.49 17.39, 78.49 17.36)))"},
    {"name": "Ward 90 - Dilsukhnagar", "code": "90", "polygon_wkt": "MULTIPOLYGON(((78.51 17.36, 78.54 17.36, 78.54 17.39, 78.51 17.39, 78.51 17.36)))"},
    {"name": "Ward 100 - LB Nagar", "code": "100", "polygon_wkt": "MULTIPOLYGON(((78.48 17.34, 78.52 17.34, 78.52 17.37, 78.48 17.37, 78.48 17.34)))"},
    {"name": "Ward 110 - Kukatpally", "code": "110", "polygon_wkt": "MULTIPOLYGON(((78.40 17.48, 78.44 17.48, 78.44 17.51, 78.40 17.51, 78.40 17.48)))"},
    {"name": "Ward 120 - Miyapur", "code": "120", "polygon_wkt": "MULTIPOLYGON(((78.34 17.48, 78.38 17.48, 78.38 17.51, 78.34 17.51, 78.34 17.48)))"},
]

# --- Circle Boundaries (simplified - 3 sample circles in Serilingampally) ---
CIRCLES = [
    {"name": "Serilingampally Circle", "code": "SRC", "polygon_wkt": "MULTIPOLYGON(((78.30 17.40, 78.38 17.40, 78.38 17.48, 78.30 17.48, 78.30 17.40)))"},
    {"name": "Kukatpally Circle", "code": "KKC", "polygon_wkt": "MULTIPOLYGON(((78.38 17.44, 78.46 17.44, 78.46 17.52, 78.38 17.52, 78.38 17.44)))"},
    {"name": "Secunderabad Circle", "code": "SCC", "polygon_wkt": "MULTIPOLYGON(((78.46 17.42, 78.54 17.42, 78.54 17.48, 78.46 17.48, 78.46 17.42)))"},
]

# --- Road Segments (sample major roads) ---
ROAD_SEGMENTS = [
    {
        "name": "Cyber Towers Road",
        "road_class": "municipal",
        "line_wkt": "MULTILINESTRING((78.3450 17.4420, 78.3500 17.4400, 78.3560 17.4380))",
    },
    {
        "name": "Gachibowli Main Road",
        "road_class": "municipal",
        "line_wkt": "MULTILINESTRING((78.3300 17.4280, 78.3380 17.4260, 78.3450 17.4240))",
    },
    {
        "name": "ORR (Outer Ring Road) - Gachibowli Stretch",
        "road_class": "national_highway",
        "line_wkt": "MULTILINESTRING((78.3200 17.4400, 78.3400 17.4350, 78.3600 17.4300))",
    },
    {
        "name": "NH 65 (Hyderabad - Vijayawada Highway)",
        "road_class": "national_highway",
        "line_wkt": "MULTILINESTRING((78.4800 17.3850, 78.5000 17.3800, 78.5200 17.3750))",
    },
    {
        "name": "Ameerpet Main Road",
        "road_class": "municipal",
        "line_wkt": "MULTILINESTRING((78.4450 17.4480, 78.4500 17.4490, 78.4550 17.4500))",
    },
    {
        "name": "MG Road (Secunderabad)",
        "road_class": "state_highway",
        "line_wkt": "MULTILINESTRING((78.4900 17.4380, 78.4950 17.4400, 78.5000 17.4420))",
    },
    {
        "name": "LB Nagar - Hayathnagar Road",
        "road_class": "state_highway",
        "line_wkt": "MULTILINESTRING((78.4870 17.3850, 78.4950 17.3830, 78.5050 17.3810))",
    },
    {
        "name": "Miyapur Main Road",
        "road_class": "municipal",
        "line_wkt": "MULTILINESTRING((78.3550 17.4950, 78.3600 17.4960, 78.3650 17.4970))",
    },
    {
        "name": "Kukatpally Housing Board Road",
        "road_class": "municipal",
        "line_wkt": "MULTILINESTRING((78.4150 17.4950, 78.4200 17.4960, 78.4250 17.4970))",
    },
    {
        "name": "Tank Bund Road",
        "road_class": "state_highway",
        "line_wkt": "MULTILINESTRING((78.4750 17.4250, 78.4760 17.4300, 78.4770 17.4350))",
    },
]

# --- Accountability Chain Nodes ---
CHAIN_NODES = [
    # GHMC chain
    {
        "authority_name": "GHMC",
        "node_type": "field_officer",
        "display_name": "Area AEE (Assistant Executive Engineer)",
        "title": "AEE",
        "display_order": 1,
    },
    {
        "authority_name": "GHMC",
        "node_type": "engineer",
        "display_name": "Divisional Engineer",
        "title": "Divisional EE",
        "display_order": 2,
    },
    {
        "authority_name": "GHMC",
        "node_type": "circle_office",
        "display_name": "Deputy Commissioner (Circle)",
        "title": "Deputy Commissioner",
        "display_order": 3,
    },
    {
        "authority_name": "GHMC",
        "node_type": "zonal_office",
        "display_name": "Zonal Commissioner",
        "title": "Zonal Commissioner",
        "display_order": 4,
    },
    {
        "authority_name": "GHMC",
        "node_type": "elected_rep",
        "display_name": "Ward Corporator",
        "title": "Corporator",
        "display_order": 5,
    },
    {
        "authority_name": "GHMC",
        "node_type": "grievance_channel",
        "display_name": "GHMC Grievance Portal",
        "title": "Online Grievance",
        "display_order": 6,
    },
    # NHAI chain
    {
        "authority_name": "NHAI",
        "node_type": "field_officer",
        "display_name": "Highway Patrol Officer",
        "title": "Patrol Officer",
        "display_order": 1,
    },
    {
        "authority_name": "NHAI",
        "node_type": "engineer",
        "display_name": "Project Director",
        "title": "Project Director",
        "display_order": 2,
    },
    {
        "authority_name": "NHAI",
        "node_type": "grievance_channel",
        "display_name": "NHAI Helpline (1033)",
        "title": "Helpline",
        "display_order": 3,
    },
    # R&B chain
    {
        "authority_name": "R&B",
        "node_type": "field_officer",
        "display_name": "Assistant Engineer",
        "title": "AE",
        "display_order": 1,
    },
    {
        "authority_name": "R&B",
        "node_type": "engineer",
        "display_name": "Executive Engineer",
        "title": "EE",
        "display_order": 2,
    },
    {
        "authority_name": "R&B",
        "node_type": "escalation",
        "display_name": "Superintending Engineer",
        "title": "SE",
        "display_order": 3,
    },
]


async def seed_phase3():
    async with async_session() as session:
        # Check if already seeded
        result = await session.execute(text("SELECT count(*) FROM authorities"))
        count = result.scalar()
        if count and count > 0:
            print("Phase 3 data already seeded. Skipping.")
            return

        ghmc_id = AUTHORITIES[0]["id"]

        # 1. Seed authorities
        for auth in AUTHORITIES:
            await session.execute(
                text("""
                    INSERT INTO authorities (id, name, authority_type, description, website_url, grievance_url, contact_phone, contact_email)
                    VALUES (:id, :name, :authority_type, :description, :website_url, :grievance_url, :contact_phone, :contact_email)
                """),
                auth,
            )
        print(f"  Seeded {len(AUTHORITIES)} authorities.")

        # 2. Seed zone polygons
        zone_ids = {}
        for zone in ZONES:
            zone_id = str(uuid.uuid4())
            zone_ids[zone["code"]] = zone_id
            await session.execute(
                text("""
                    INSERT INTO jurisdiction_polygons (id, authority_id, layer_type, name, code, geom, source_name, source_version)
                    VALUES (:id, :authority_id, 'zone', :name, :code,
                            ST_GeomFromText(:wkt, 4326), 'seed', 'v1')
                """),
                {"id": zone_id, "authority_id": ghmc_id, "name": zone["name"], "code": zone["code"], "wkt": zone["polygon_wkt"]},
            )
        print(f"  Seeded {len(ZONES)} zone polygons.")

        # 3. Seed ward polygons
        ward_ids = {}
        for ward in WARDS:
            ward_id = str(uuid.uuid4())
            ward_ids[ward["code"]] = ward_id
            await session.execute(
                text("""
                    INSERT INTO jurisdiction_polygons (id, authority_id, layer_type, name, code, geom, source_name, source_version)
                    VALUES (:id, :authority_id, 'ward', :name, :code,
                            ST_GeomFromText(:wkt, 4326), 'seed', 'v1')
                """),
                {"id": ward_id, "authority_id": ghmc_id, "name": ward["name"], "code": ward["code"], "wkt": ward["polygon_wkt"]},
            )
        print(f"  Seeded {len(WARDS)} ward polygons.")

        # 4. Seed circle polygons
        for circle in CIRCLES:
            circle_id = str(uuid.uuid4())
            await session.execute(
                text("""
                    INSERT INTO jurisdiction_polygons (id, authority_id, layer_type, name, code, geom, source_name, source_version)
                    VALUES (:id, :authority_id, 'circle', :name, :code,
                            ST_GeomFromText(:wkt, 4326), 'seed', 'v1')
                """),
                {"id": circle_id, "authority_id": ghmc_id, "name": circle["name"], "code": circle["code"], "wkt": circle["polygon_wkt"]},
            )
        print(f"  Seeded {len(CIRCLES)} circle polygons.")

        # 5. Seed road segments
        road_ids = {}
        nhai_id = AUTHORITIES[3]["id"]  # NHAI
        rb_id = AUTHORITIES[2]["id"]  # R&B
        for road in ROAD_SEGMENTS:
            road_id = str(uuid.uuid4())
            road_ids[road["name"]] = road_id
            await session.execute(
                text("""
                    INSERT INTO road_segments (id, name, road_class, geom, source_name, source_version)
                    VALUES (:id, :name, :road_class,
                            ST_GeomFromText(:wkt, 4326), 'seed', 'v1')
                """),
                {"id": road_id, "name": road["name"], "road_class": road["road_class"], "wkt": road["line_wkt"]},
            )
        print(f"  Seeded {len(ROAD_SEGMENTS)} road segments.")

        # 6. Seed responsibility mappings for key roads
        # ORR → NHAI
        orr_id = road_ids.get("ORR (Outer Ring Road) - Gachibowli Stretch")
        if orr_id:
            await session.execute(
                text("""
                    INSERT INTO responsibility_mappings (id, road_segment_id, primary_authority_id, ownership_confidence, notes)
                    VALUES (:id, :road_segment_id, :primary_authority_id, 0.9000, 'National highway - NHAI maintained')
                """),
                {"id": str(uuid.uuid4()), "road_segment_id": orr_id, "primary_authority_id": nhai_id},
            )
        # NH 65 → NHAI
        nh65_id = road_ids.get("NH 65 (Hyderabad - Vijayawada Highway)")
        if nh65_id:
            await session.execute(
                text("""
                    INSERT INTO responsibility_mappings (id, road_segment_id, primary_authority_id, ownership_confidence, notes)
                    VALUES (:id, :road_segment_id, :primary_authority_id, 0.9500, 'National highway')
                """),
                {"id": str(uuid.uuid4()), "road_segment_id": nh65_id, "primary_authority_id": nhai_id},
            )
        # MG Road → R&B
        mg_id = road_ids.get("MG Road (Secunderabad)")
        if mg_id:
            await session.execute(
                text("""
                    INSERT INTO responsibility_mappings (id, road_segment_id, primary_authority_id, ownership_confidence, notes)
                    VALUES (:id, :road_segment_id, :primary_authority_id, 0.7500, 'State highway')
                """),
                {"id": str(uuid.uuid4()), "road_segment_id": mg_id, "primary_authority_id": rb_id},
            )
        print("  Seeded responsibility mappings for 3 key roads.")

        # 7. Seed accountability chain nodes
        # Map authority names to IDs
        auth_name_to_id = {a["name"]: a["id"] for a in AUTHORITIES}
        for node in CHAIN_NODES:
            authority_id = auth_name_to_id[node["authority_name"]]
            await session.execute(
                text("""
                    INSERT INTO accountability_chain_nodes (id, authority_id, node_type, display_name, title, display_order, is_public)
                    VALUES (:id, :authority_id, :node_type, :display_name, :title, :display_order, true)
                """),
                {
                    "id": str(uuid.uuid4()),
                    "authority_id": authority_id,
                    "node_type": node["node_type"],
                    "display_name": node["display_name"],
                    "title": node["title"],
                    "display_order": node["display_order"],
                },
            )
        print(f"  Seeded {len(CHAIN_NODES)} accountability chain nodes.")

        await session.commit()
        print("Phase 3 seed complete!")


if __name__ == "__main__":
    asyncio.run(seed_phase3())
