import abc
import dataclasses
import json
from dataclasses import dataclass, field
from enum import StrEnum
from typing import List, Optional, Protocol, TypeVar
import datetime

# ____ Interfaces ____

class CategoryWithIdProtocol(Protocol):
    """
    Protocol defining entities that can serve as a category with a unique identifier.
    """
    cat_id: int

    @abc.abstractmethod
    def get_products(self, all_products: List["_CategorisedType"]) -> List["_CategorisedType"]:
        """
        Filter and return products that belong to this category.
        """
        ...


class CategorisedProtocol(Protocol):
    """
    Protocol defining entities that can be assigned to categories.
    """
    @abc.abstractmethod
    def has_category(self, category: CategoryWithIdProtocol) -> bool:
        """
        Check if this entity belongs to the specified category.
        """
        ...


# ____ Types ____

# Type variable representing any type that implements the CategorisedProtocol.
_CategorisedType = TypeVar('_CategorisedType', bound=CategorisedProtocol)


# ---- Users ----

class PermissionCode(StrEnum):
    VIEW = "view"
    EDIT = "edit"
    DELETE = "delete"
    CREATE = "create"
    MANAGE = "manage"
    ADMIN = "admin"

    # Company-specific permissions
    COMPANY_VIEW = "company_view"
    COMPANY_EDIT = "company_edit"
    COMPANY_DELETE = "company_delete"
    COMPANY_CREATE = "company_create"
    COMPANY_MANAGE = "company_manage"
    COMPANY_ADMIN = "company_admin"

    # Special permissions
    VIEW_LIST_ROLES = "view_list_permissions"
    VIEW_LIST_USERS = "view_list_users"
    CREATE_USER = "create_user"


@dataclass
class Permission:
    """A single permission with a code and optional description."""
    perm_code: str
    perm_description: Optional[str] = ""

    def __str__(self) -> str:
        return f"{self.perm_code}"


@dataclass
class Role:
    """
    A role that can be assigned to users, containing multiple permissions.
    """
    name: str
    permissions: List[Permission] = field(default_factory=list)

    def __str__(self) -> str:
        """String representation showing role name and all permissions."""
        permissions = " :: ".join(map(str, self.permissions))
        return f"{self.name} -> {permissions}"


@dataclass
class User:
    """
    User entity with authentication and permission checking capabilities.
    """
    username: str
    password_hash: str  # In a real system, this would be a hashed password
    roles: List[Role] = field(default_factory=list)

    def authenticate(self, pw: str) -> bool:
        """Verify if the provided password matches the stored password."""
        return self.password_hash == pw

    def has_permission(self, code: str) -> bool:
        """Check if the user has a specific permission through any of their roles."""
        return any(
            code == perm.perm_code
            for role in self.roles
            for perm in role.permissions
        )


@dataclass
class Membership:
    """
    Represents a user's membership in a company with a specific role.
    """
    user: User
    role: Role
    joined_date: datetime.date
    active: bool = True

    def has_permission(self, code: str) -> bool:
        """Check if this membership grants a specific permission."""
        return any(
            code == perm.perm_code
            for perm in self.role.permissions
        )


# ---- Companies ----

@dataclass
class Company:
    """
    Company entity with employees, inventory, and permission management.
    """
    name: str
    owner: str
    location: str
    inventory: 'Inventory'
    employees: List[Membership] = field(default_factory=list)

    def get_employees(self, role: Optional[List[str]] = None) -> List[User]:
        """Get active employees, optionally filtered by role names."""
        if not role:
            return [m.user for m in self.employees if m.active]
        return [
            m.user for m in self.employees
            if m.active and m.role.name in role
        ]

    def add_member(self, user: User, role: Role, joined_date: datetime.date):
        """Add a new member to the company with a specific role."""
        self.employees.append(Membership(user, role, joined_date))

    def find_membership(self, user: User) -> Optional[Membership]:
        """Find a user's membership record in this company."""
        for membership in self.employees:
            if membership.user == user:
                return membership
        return None

    def is_member(self, user: User):
        """Check if a user is a member of this company."""
        return self.find_membership(user) is not None

    def has_permission(self, user: User, code: str) -> bool:
        """Check if a user has a specific permission in this company."""
        membership = self.find_membership(user)
        if not membership:
            return False
        return membership.has_permission(code)

    def __str__(self):
        """String representation showing company name and location."""
        return f"{self.name} ({self.location})"


@dataclass
class Inventory:
    """
    Inventory containing products with search capabilities.
    """
    description: str
    products: List['Product'] = field(default_factory=list)

    def __hash__(self):
        """Hash based on inventory description for dictionary usage."""
        return hash(self.description)

    def get_products_by_category(self, category: CategoryWithIdProtocol) -> List['Product']:
        """Get all products belonging to a specific category."""
        return category.get_products(self.products)

    def get_product(self, sku: str) -> Optional['Product']:
        """Find a product by its SKU (exact match)."""
        for p in self.products:
            if p.uuid == sku:
                return p
        return None


# ---- Products ----

@dataclass
class Category(CategoryWithIdProtocol):
    """
    Product category with hierarchical structure (supports parent categories).
    """
    cat_id: int
    name: str
    description: str
    parent: Optional['Category'] = None

    def get_products(self, all_products: List[_CategorisedType]) -> List[_CategorisedType]:
        """Filter products that belong to this category."""
        return [p for p in all_products if p.has_category(self)]

    def __str__(self):
        return f"[ID: {self.cat_id}] - {self.name}"


@dataclass
class Product(CategorisedProtocol):
    """
    Base product class with common properties for all product types.
    """
    uuid: str  # SKU (Stock Keeping Unit)
    name: str
    description: str
    price: float
    produced_date: datetime.date
    is_new: bool
    category: Optional[Category] = None

    def __post_init__(self):
        """
        Initialize category hierarchy for efficient category lookup.
        
        Builds a set of all category IDs in the hierarchy (including parent categories)
        to enable fast category membership checking.
        """
        categories = set()
        category = self.category
        # Traverse up the category hierarchy
        while category is not None:
            # Prevent infinite loops in case of circular references
            if category.cat_id in categories:
                category = None
                continue
            categories.add(category.cat_id)
            category = category.parent

        self._categories_ids: set[int] = categories

    def has_category(self, category: CategoryWithIdProtocol) -> bool:
        """Check if the product belongs to a specific category."""
        return category.cat_id in self._categories_ids

    def to_json(self):
        product_dict = dataclasses.asdict(self)
        return json.dumps(
            {k: v for k, v in product_dict.items() if
             isinstance(v, (str, int, float, bool))}
        )

    def update(self, **kwargs):
        """Update product attributes from a dictionary."""
        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)


@dataclass
class Yacht(Product):
    loa_m: float = 0.0
    beam_m: float = 0.0
    draft_m: float = 0.0
    berths_int: int = 0
    engine_type: str = ""
    power_hp: int = 0


@dataclass
class Boat(Product):
    length_m: float = 0.0
    beam_m: float = 0.0
    material: str = ""
    engine_type: str = ""
    power_hp: int = 0


@dataclass
class Motor(Product):
    power_hp: int = 0
    fuel_type: str = ""
    weight_kg: float = 0.0
