import dataclasses
import datetime as dt
from typing import Optional

from company.models import (
    Permission, Role, User, Membership, Category,
    Inventory, Company, Yacht, Boat, Motor, PermissionCode, Product,
)


@dataclasses.dataclass
class AppData:
    """
    Application data container class that stores all system entities.
    """
    users: list[User]
    companies: list[Company]
    categories: list[Category]
    roles: list[Role] = dataclasses.field(default_factory=list)

    def find_role(self, role_name: str) -> Optional[Role]:
        """Find a role by its name (case-sensitive)."""
        for role in self.roles:
            if role.name == role_name:
                return role
        return None

    def find_company(self, company_name: str) -> Optional[Company]:
        """Find a company by its name (case-insensitive)."""
        for company in self.companies:
            if company.name.lower() == company_name.lower():
                return company
        return None

    def find_category(self, category_id: int) -> Optional[Category]:
        """Find a category by its ID."""
        for cat in self.categories:
            if cat.cat_id == category_id:
                return cat
        return None

    @property
    def inventories(self) -> list[Inventory]:
        """Get all inventories from all companies."""
        return [company.inventory for company in self.companies]

    def get_inventories(self, company: Optional[Company] = None) -> list[
        Inventory]:
        """Get inventories for a specific company or all companies."""
        if company:
            return [company.inventory]
        else:
            return self.inventories

    @classmethod
    def init_default(cls) -> "AppData":
        """Initialize a default dataset with sample users, companies, and products."""
        # Permissions
        perm_view = Permission(PermissionCode.VIEW)
        perm_company_view = Permission(PermissionCode.COMPANY_VIEW)
        perm_company_edit = Permission(PermissionCode.COMPANY_EDIT)
        # Roles
        user_role = Role("user", [perm_view])
        manager_role = Role(
            "company_manager", [perm_view, perm_company_view, perm_company_edit]
        )
        worker_role = Role("company_worker", [perm_view, perm_company_view])
        superuser_role = Role(
            "superuser", [Permission(code) for code in PermissionCode]
        )
        # Users
        superuser = User("superuser", "superuser", [superuser_role])
        alice = User("Alice", "alice", [user_role])
        bob = User("Bob", "bob", [user_role])
        user = User("user", "user", [user_role])

        # Memberships
        c1_manager = Membership(
            alice, manager_role, dt.datetime(2020, 1, 1), True
        )
        c2_manager = Membership(
            bob, manager_role, dt.datetime(2021, 5, 12), True
        )

        # Categories
        vehicle = Category(1, "Vehicle", "All kind of vehicles")
        water_vehicle = Category(
            100, "Water Vehicle", "Boats, yachts, etc", parent=vehicle
        )
        parts = Category(2, "Parts", "Parts for vehicles")
        yacht_cat = Category(
            1000, "Yacht", "Luxury yachts", parent=water_vehicle
        )
        boat_cat = Category(
            1001, "Boat", "Boats for all purposes", parent=water_vehicle
        )
        motor_cat = Category(10000, "Motors", "Motors", parent=parts)

        sail_cat = Category(
            1002, "Sailboats", "Boats powered by sails", parent=water_vehicle
        )
        electronics_cat = Category(
            3, "Electronics", "Electronic equipment for boats"
        )

        # Products for Boat Store
        yacht1 = Yacht(
            uuid="SKU001",
            name="Yacht X",
            description="Luxury yacht",
            price=700000,
            produced_date=dt.datetime(2022, 6, 1), is_new=True,
            category=yacht_cat,
            loa_m=14.5,
            beam_m=4.8,
            draft_m=2.0,
            berths_int=8,
            engine_type="Diesel",
            power_hp=800
        )
        boat1 = Boat(
            uuid="SKU002",
            name="Boat A",
            description="Affordable boat",
            price=35000,
            produced_date=dt.datetime(2023, 1, 15), is_new=True,
            category=boat_cat,
            length_m=6.0,
            beam_m=2.2,
            material="Fiberglass",
            engine_type="Petrol",
            power_hp=120
        )
        motor1 = Motor(
            uuid="SKU003",
            name="Motor B",
            description="Outboard motor",
            price=5000,
            produced_date=dt.datetime(2022, 11, 20), is_new=True,
            category=motor_cat,
            power_hp=90,
            fuel_type="Petrol",
            weight_kg=55
        )
        boat2 = Boat(
            uuid="SKU004",
            name="Fisherman Pro",
            description="Professional fishing boat",
            price=48000,
            produced_date=dt.datetime(2023, 3, 10), is_new=True,
            category=boat_cat,
            length_m=7.2,
            beam_m=2.5,
            material="Aluminum",
            engine_type="Diesel",
            power_hp=150
        )
        sailboat1 = Boat(
            uuid="SKU005",
            name="WindRider 220",
            description="Elegant sailboat for weekend adventures",
            price=28500,
            produced_date=dt.datetime(2022, 8, 15), is_new=True,
            category=sail_cat,
            length_m=6.8,
            beam_m=2.3,
            material="Fiberglass",
            engine_type="Auxiliary Electric",
            power_hp=15
        )

        # Products for Yacht Inc inventory
        yacht2 = Yacht(
            uuid="SKU006",
            name="Ocean Master 48",
            description="Premium ocean-going yacht",
            price=1200000,
            produced_date=dt.datetime(2023, 4, 20), is_new=True,
            category=yacht_cat,
            loa_m=16.8,
            beam_m=5.2,
            draft_m=2.4,
            berths_int=10,
            engine_type="Twin Diesel",
            power_hp=1200
        )
        yacht3 = Yacht(
            uuid="SKU007",
            name="Coastal Explorer 38",
            description="Comfortable coastal cruiser",
            price=520000,
            produced_date=dt.datetime(2022, 10, 5), is_new=True,
            category=yacht_cat,
            loa_m=11.6,
            beam_m=4.1,
            draft_m=1.8,
            berths_int=6,
            engine_type="Diesel",
            power_hp=450
        )
        motor2 = Motor(
            uuid="SKU008",
            name="PowerMax 150",
            description="High-performance outboard motor",
            price=12000,
            produced_date=dt.datetime(2023, 2, 8), is_new=True,
            category=motor_cat,
            power_hp=150,
            fuel_type="Petrol",
            weight_kg=95
        )
        sailboat2 = Boat(
            uuid="SKU009",
            name="BlueWater 32",
            description="Ocean-capable sailing yacht",
            price=125000,
            produced_date=dt.datetime(2022, 7, 25), is_new=True,
            category=sail_cat,
            length_m=9.8,
            beam_m=3.4,
            material="Fiberglass/Carbon",
            engine_type="Diesel Auxiliary",
            power_hp=40
        )

        navigation_system = Product(
            uuid="SKU010",
            name="NavPro 5000",
            description="Advanced marine navigation system",
            price=3500,
            produced_date=dt.datetime(2023, 1, 10),
            is_new=True,
            category=electronics_cat
        )

        # Inventories
        boat_store_inventory = Inventory(
            "Boat Store Main Warehouse",
            [yacht1, boat1, motor1, boat2, sailboat1]
        )

        yacht_inc_inventory = Inventory(
            "Yacht Inc Premium Showroom",
            [yacht2, yacht3, motor2, sailboat2, navigation_system]
        )

        # Companies
        company_1 = Company(
            "Boat Store", "Trump", "Sydney", boat_store_inventory, [c1_manager]
        )
        company_2 = Company(
            "Yachts Inc", "Ilon Mask", "Melbourne", yacht_inc_inventory,
            [c2_manager]
        )

        return AppData(
            users=[alice, bob, user, superuser],
            roles=[user_role, manager_role, worker_role],
            companies=[company_1, company_2],
            categories=[yacht_cat, boat_cat, motor_cat, vehicle, water_vehicle,
                        parts, sail_cat, electronics_cat],
        )
