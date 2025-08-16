#!/usr/bin/env python3
"""
Complete setup script - creates users, projects, and WIP data
"""
import sys
import os
from decimal import Decimal
from datetime import date

# Add the parent directory to the path so we can import our app
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.user import User
from app.models.project import Project
from app.models.wip_snapshot import WIPSnapshot
from app.core.security import get_password_hash
from app.services.wip_service import WIPService
from app.schemas.wip import WIPSnapshotCreate


def setup_all_data():
    """Complete setup: users, projects, and WIP data"""

    db = SessionLocal()
    try:
        print("🚀 Starting complete WIP system setup...")

        # 1. CREATE USERS
        print("\n1️⃣ Creating users...")
        users_data = [
            {
                "username": "kulike@muehlhan.com",
                "email": "kulike@muehlhan.com",
                "role": "viewer",
            },
            {
                "username": "mueler-arends@muehlhan.com",
                "email": "mueler-arends@muehlhan.com",
                "role": "viewer",
            },
            {
                "username": "brockman@muehlhan.com",
                "email": "brockman@muehlhan.com",
                "role": "viewer",
            },
            {
                "username": "paulb@gototsi.com",
                "email": "paulb@gototsi.com",
                "role": "viewer",
            },
            {
                "username": "evans@muehlhan.com",
                "email": "evans@muehlhan.com",
                "role": "viewer",
            },
            {
                "username": "walz@muehlhan.com",
                "email": "walz@muehlhan.com",
                "role": "viewer",
            },
            {
                "username": "zaczeniuk@muehlhan.com",
                "email": "zaczeniuk@muehlhan.com",
                "role": "viewer",
            },
            {
                "username": "nedal@muehlhan.com",
                "email": "nedal@muehlhan.com",
                "role": "viewer",
            },
            {
                "username": "hell@muehlhan.com",
                "email": "hell@muehlhan.com",
                "role": "viewer",
            },
            {
                "username": "dahern@gototsi.com",
                "email": "dahern@gototsi.com",
                "role": "admin",
            },
        ]

        password = "123456"
        hashed_password = get_password_hash(password)

        admin_user = None
        for user_data in users_data:
            existing_user = (
                db.query(User).filter(User.username == user_data["username"]).first()
            )
            if existing_user:
                if user_data["role"] == "admin":
                    admin_user = existing_user
                continue

            db_user = User(
                username=user_data["username"],
                email=user_data["email"],
                role=user_data["role"],
                password_hash=hashed_password,
                is_active=True,
            )
            db.add(db_user)
            if user_data["role"] == "admin":
                admin_user = db_user
            print(f"   Created user: {user_data['username']} ({user_data['role']})")

        db.commit()

        if not admin_user:
            print("❌ No admin user found after creation!")
            return

        # 2. CREATE PROJECTS
        print("\n2️⃣ Creating projects...")
        projects_data = [
            {"job_number": "2215", "name": "PNSY DD2 Caisson-KUNJ-ME"},
            {"job_number": "2217", "name": "D6 Sched and Emer Repairs-SPS-MA"},
            {"job_number": "2218", "name": "Lettsworth Army Bulkhead- Kone Crane - LA"},
            {
                "job_number": "2305-3",
                "name": "Queechee Gorge - Removal & Containment - VT",
            },
            {"job_number": "2305-2", "name": "Queechee Gorge - Field Painting - VT"},
            {"job_number": "2305-1", "name": "Queechee Gorge - Platform - VT"},
            {"job_number": "2306", "name": "PNSY Blast Condensate Tanks - ESC - ME"},
            {"job_number": "2307-1", "name": "BIW Portal Cranes - Crane 18 - ME"},
            {"job_number": "2307-2", "name": "BIW Portal Cranes - Crane 16 - ME"},
            {"job_number": "2307-3", "name": "BIW Portal Cranes - Crane 17 - ME"},
            {"job_number": "2310", "name": "Downtown Crossing - SPS - MA"},
            {"job_number": "2313", "name": "T&M Offshore Wind Project - B&V - MA"},
            {"job_number": "2315", "name": "395 Bridges- Blast All - CT"},
            {"job_number": "2317", "name": "T&M NAVFAC - RI"},
            {"job_number": "2318", "name": "PSNY Bridge 2 - Cianbro - ME"},
            {"job_number": "2319", "name": "Groton Shoreline Receptacles - CCI - CT"},
            {"job_number": "2401", "name": "Rte 8 Bridge - Blast All - CT"},
            {"job_number": "2402", "name": "BIW Crane 16& 17 Counterweights - ME"},
            {"job_number": "2405", "name": "Dutch Point - CT"},
            {"job_number": "2407", "name": "Jump Towers - Semper Tek - GA"},
            {
                "job_number": "2501",
                "name": "Cummington Bridges - Northern Construction -MA",
            },
            {"job_number": "2502", "name": "Spencer Bridge (Rt 9) - JH Lynch - MA"},
            {"job_number": "2503", "name": "Cutler Ice Shields - CCI- ME"},
            {"job_number": "2504", "name": "Power Mill Bridge MAS"},
            {"job_number": "2505", "name": "Braga Bridge-Coviello Electric - MA"},
            {"job_number": "2506", "name": "Washinton Street Bridge Replacement* - MA"},
            {"job_number": "2507", "name": "PNSY Stairs A & B"},
            {"job_number": "2509", "name": "Dutch Point T & M"},
        ]

        project_lookup = {}
        for project_data in projects_data:
            existing_project = (
                db.query(Project)
                .filter(Project.job_number == project_data["job_number"])
                .first()
            )
            if existing_project:
                project_lookup[project_data["job_number"]] = existing_project
                continue

            db_project = Project(
                job_number=project_data["job_number"],
                name=project_data["name"],
                is_active=True,
            )
            db.add(db_project)
            project_lookup[project_data["job_number"]] = db_project
            print(
                f"   Created project: {project_data['job_number']} - {project_data['name']}"
            )

        db.commit()

        # 3. CREATE WIP DATA
        print("\n3️⃣ Creating WIP snapshots...")
        wip_data = [
            {
                "job_number": "2215",
                "original_contract": Decimal("1571138.7"),
                "change_orders": Decimal("114750.98"),
            },
            {
                "job_number": "2217",
                "original_contract": Decimal("120124"),
                "change_orders": Decimal("280027.53"),
            },
            {
                "job_number": "2218",
                "original_contract": Decimal("187654"),
                "change_orders": Decimal("477275.8"),
            },
            {
                "job_number": "2305-3",
                "original_contract": Decimal("2315187"),
                "change_orders": Decimal("0"),
            },
            {
                "job_number": "2305-2",
                "original_contract": Decimal("2021008"),
                "change_orders": Decimal("0"),
            },
            {
                "job_number": "2305-1",
                "original_contract": Decimal("1543458"),
                "change_orders": Decimal("0"),
            },
            {
                "job_number": "2306",
                "original_contract": Decimal("394900"),
                "change_orders": Decimal("329378"),
            },
            {
                "job_number": "2307-1",
                "original_contract": Decimal("1837185"),
                "change_orders": Decimal("154271.02"),
            },
            {
                "job_number": "2307-2",
                "original_contract": Decimal("1240000"),
                "change_orders": Decimal("0"),
            },
            {
                "job_number": "2307-3",
                "original_contract": Decimal("1800000"),
                "change_orders": Decimal("0"),
            },
            {
                "job_number": "2310",
                "original_contract": Decimal("256632"),
                "change_orders": Decimal("0"),
            },
            {
                "job_number": "2313",
                "original_contract": Decimal("15000"),
                "change_orders": Decimal("2084980.98"),
            },
            {
                "job_number": "2315",
                "original_contract": Decimal("1582389"),
                "change_orders": Decimal("4697371.23"),
            },
            {
                "job_number": "2317",
                "original_contract": Decimal("166524.57"),
                "change_orders": Decimal("0"),
            },
            {
                "job_number": "2318",
                "original_contract": Decimal("1341023"),
                "change_orders": Decimal("216635.41"),
            },
            {
                "job_number": "2319",
                "original_contract": Decimal("1343649.06"),
                "change_orders": Decimal("3000"),
            },
            {
                "job_number": "2401",
                "original_contract": Decimal("6435082.5"),
                "change_orders": Decimal("0"),
            },
            {
                "job_number": "2402",
                "original_contract": Decimal("334270"),
                "change_orders": Decimal("20258"),
            },
            {
                "job_number": "2405",
                "original_contract": Decimal("4531360"),
                "change_orders": Decimal("0"),
            },
            {
                "job_number": "2407",
                "original_contract": Decimal("688798"),
                "change_orders": Decimal("1390234"),
            },
            {
                "job_number": "2501",
                "original_contract": Decimal("2068892"),
                "change_orders": Decimal("0"),
            },
            {
                "job_number": "2502",
                "original_contract": Decimal("166864"),
                "change_orders": Decimal("0"),
            },
            {
                "job_number": "2503",
                "original_contract": Decimal("70507"),
                "change_orders": Decimal("0"),
            },
            {
                "job_number": "2504",
                "original_contract": Decimal("153120"),
                "change_orders": Decimal("0"),
            },
            {
                "job_number": "2505",
                "original_contract": Decimal("365035"),
                "change_orders": Decimal("0"),
            },
            {
                "job_number": "2506",
                "original_contract": Decimal("797754"),
                "change_orders": Decimal("0"),
            },
        ]

        report_date = date(2025, 7, 31)
        wip_service = WIPService(db)

        total_contract_value = Decimal("0")
        for data in wip_data:
            project = project_lookup.get(data["job_number"])
            if not project:
                print(f"   ❌ Project {data['job_number']} not found")
                continue

            # Check if WIP already exists
            existing_wip = (
                db.query(WIPSnapshot)
                .filter(
                    WIPSnapshot.project_id == project.id,
                    WIPSnapshot.report_date == report_date,
                )
                .first()
            )

            if existing_wip:
                continue

            # Create WIP snapshot
            wip_create = WIPSnapshotCreate(
                project_id=project.id,
                job_number=data["job_number"],
                report_date=report_date,
                current_month_original_contract_amount=data["original_contract"],
                current_month_change_order_amount=data["change_orders"],
            )

            wip_snapshot = wip_service.create_wip_snapshot(wip_create, admin_user.id)
            total = wip_snapshot.current_month_total_contract_amount
            total_contract_value += total

            print(
                f"   ✅ {data['job_number']}: ${data['original_contract']:,.0f} + ${data['change_orders']:,.0f} = ${total:,.0f}"
            )

        print(f"\n🎉 Setup Complete!")
        print(f"   👥 Users: {len(users_data)} (1 admin, {len(users_data)-1} viewers)")
        print(f"   📋 Projects: {len(projects_data)}")
        print(f"   📊 WIP Snapshots: {len(wip_data)} for {report_date}")
        print(f"   💰 Total Contract Value: ${total_contract_value:,.0f}")
        print(f"   🔑 Password for all users: {password}")

    except Exception as e:
        print(f"❌ Error during setup: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    setup_all_data()
