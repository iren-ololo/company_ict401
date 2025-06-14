import json
import pytest
from click.testing import CliRunner
from unittest.mock import patch
import datetime as dt

from company.cli import cli
from company.utils import Context, Session
from company.models import (
    User, Role, Permission, PermissionCode, Company, 
    Inventory, Category, Boat, Motor
)
from company.data import AppData


@pytest.fixture
def runner():
    """Create a CLI runner for testing commands."""
    return CliRunner()


@pytest.fixture(autouse=True)
def patch_context_load(monkeypatch, mock_context):
    """
    Automatically patch Context.load for all tests.
    This fixture runs for every test without needing to be explicitly included.
    """
    with patch('company.cli.Context.load', return_value=mock_context):
        yield


@pytest.fixture
def mock_context(monkeypatch):
    """Create a mock application context for testing."""
    # Create basic test data
    perm_view = Permission(PermissionCode.VIEW)
    perm_company_view = Permission(PermissionCode.COMPANY_VIEW)
    perm_company_edit = Permission(PermissionCode.COMPANY_EDIT)
    perm_create_user = Permission(PermissionCode.CREATE_USER)
    perm_view_roles = Permission(PermissionCode.VIEW_LIST_ROLES)
    perm_view_users = Permission(PermissionCode.VIEW_LIST_USERS)
    
    # Roles
    user_role = Role("user", [perm_view])
    manager_role = Role(
        "company_manager", [perm_view, perm_company_view, perm_company_edit]
    )
    admin_role = Role(
        "admin", [perm_view, perm_company_view, perm_company_edit, 
                 perm_create_user, perm_view_roles, perm_view_users]
    )
    
    # Users
    test_user = User("test_user", "password", [user_role])
    test_manager = User("test_manager", "manager_pwd", [manager_role])
    test_admin = User("admin", "admin_pwd", [admin_role])
    
    # Categories
    cat_vehicle = Category(1, "Vehicle", "All vehicles")
    cat_boat = Category(101, "Boat", "All boats", parent=cat_vehicle)
    
    # Products
    product1 = Boat(
        uuid="TEST001",
        name="Test Boat",
        description="Test boat description",
        price=10000.0,
        produced_date=dt.datetime(2023, 1, 1),
        is_new=True,
        category=cat_boat,
        length_m=5.0,
        beam_m=2.0,
        material="Fiberglass",
        engine_type="Outboard",
        power_hp=90
    )
    product2 = Motor(
        uuid="TEST002",
        name="Test Motor",
        description="Test motor description",
        price=2000.0,
        produced_date=dt.datetime(2023, 2, 1),
        is_new=True,
        category=cat_boat,
        power_hp=75,
        fuel_type="Petrol",
        weight_kg=45.0
    )
    
    # Inventory and Company
    test_inventory = Inventory("Test Inventory", [product1, product2])
    test_company = Company(
        name="Test Company",
        owner="Test Owner",
        location="Test Location",
        inventory=test_inventory
    )
    
    # Add test user to the company
    test_company.add_member(
        user=test_user,
        role=user_role,
        joined_date=dt.datetime.now().date()
    )
    
    # Add test manager to the company with manager role
    test_company.add_member(
        user=test_manager,
        role=manager_role,
        joined_date=dt.datetime.now().date()
    )
    
    # Add test admin to the company with admin role
    test_company.add_member(
        user=test_admin,
        role=admin_role,
        joined_date=dt.datetime.now().date()
    )
    
    # Create AppData
    app_data = AppData(
        users=[test_user, test_manager, test_admin],
        roles=[user_role, manager_role, admin_role],
        companies=[test_company],
        categories=[cat_vehicle, cat_boat]
    )
    
    # Create session
    session = Session()
    
    # Create context
    context = Context(data=app_data, _session=session)
    
    # Patch save method to do nothing during tests
    def mock_save(*args, **kwargs):
        pass
    
    monkeypatch.setattr(context, 'save', mock_save)
    
    return context


# Auth command tests
def test_login_success(runner, mock_context):
    """Test successful login with correct credentials."""
    result = runner.invoke(cli, ['auth', 'login', 'test_user', 'password'], obj=mock_context)
    assert result.exit_code == 0
    assert "Logged in as test_user" in result.output
    assert mock_context.current_user is not None
    assert mock_context.current_user.username == "test_user"


def test_login_with_company(runner, mock_context):
    """Test login with company selection."""
    result = runner.invoke(
        cli, ['auth', 'login', 'test_user', 'password', '-c', 'Test Company'],
        obj=mock_context
    )
    assert result.exit_code == 0
    assert "Logged in as test_user" in result.output
    # We've set up the membership now, so this should pass
    assert "Logged in company Test Company" in result.output


def test_login_invalid_credentials(runner, mock_context):
    """Test login with invalid credentials."""
    result = runner.invoke(
        cli, ['auth', 'login', 'test_user', 'wrong_password'],
        obj=mock_context
    )
    assert result.exit_code == 0
    assert "Invalid credentials" in result.output
    assert mock_context.current_user is None


def test_logout(runner, mock_context):
    """Test logout functionality."""
    # First login
    mock_context.set_user(mock_context.data.users[0])
    
    result = runner.invoke(cli, ['auth', 'logout'], obj=mock_context)
    assert result.exit_code == 0
    assert "Logged out" in result.output
    assert mock_context.current_user is None


# Inventory command tests
def test_inventory_view_unauthorized(runner, mock_context):
    """Test inventory view without login."""
    result = runner.invoke(cli, ['inventory', 'view'], obj=mock_context)
    assert result.exit_code == 0
    assert "Login required" in result.output


def test_inventory_view_authorized(runner, mock_context):
    """Test inventory view with proper login."""
    # Login as user with view permission
    mock_context.set_user(mock_context.data.users[0])  # test_user
    mock_context.set_company(mock_context.data.companies[0])
    
    result = runner.invoke(cli, ['inventory', 'view'], obj=mock_context)
    assert result.exit_code == 0
    assert "Test Boat" in result.output
    assert "Test Motor" in result.output


def test_inventory_search_by_sku(runner, mock_context):
    """Test inventory search by SKU."""
    # Login as user with view permission
    mock_context.set_user(mock_context.data.users[0])  # test_user
    mock_context.set_company(mock_context.data.companies[0])
    
    # Test the --sku option
    result = runner.invoke(
        cli, ['inventory', 'search', '--sku', 'TEST001'],
        obj=mock_context
    )
    assert result.exit_code == 0
    assert "Test Boat" in result.output
    assert "TEST001" in result.output
    assert "Test Motor" not in result.output


def test_inventory_search_by_category(runner, mock_context):
    """Test inventory search by category ID."""
    # Login as user with view permission
    mock_context.set_user(mock_context.data.users[0])  # test_user
    mock_context.set_company(mock_context.data.companies[0])
    
    result = runner.invoke(
        cli, ['inventory', 'search', '-c', '101'],  # Boat category
        obj=mock_context
    )
    assert result.exit_code == 0
    assert "Test Boat" in result.output
    assert "Test Motor" in result.output  # Both are in the boat category


def test_inventory_product_details(runner, mock_context):
    """Test product details command."""
    # Login as manager with company_view permission
    mock_context.set_user(mock_context.data.users[1])  # test_manager
    mock_context.set_company(mock_context.data.companies[0])
    
    result = runner.invoke(
        cli, ['inventory', 'product-details', 'TEST001'],
        obj=mock_context
    )
    assert result.exit_code == 0
    assert "Test Boat" in result.output


def test_inventory_update(runner, mock_context):
    """Test updating product information."""
    # Login as manager with company_edit permission
    mock_context.set_user(mock_context.data.users[1])  # test_manager
    mock_context.set_company(mock_context.data.companies[0])
    
    # Define updated product data
    updated_data = {
        "name": "Updated Test Boat",
        "price": 12000.0
    }
    
    # Test with auto-confirmation
    result = runner.invoke(
        cli,
        ['inventory', 'update', '-s', 'TEST001', '-p', json.dumps(updated_data)],
        input='y\n',  # Confirm the update
        obj=mock_context
    )
    assert result.exit_code == 0
    assert "Product updated successfully" in result.output


# User command tests
def test_user_show_me(runner, mock_context):
    """Test showing current user information."""
    # Login as a user
    mock_context.set_user(mock_context.data.users[0])  # test_user
    
    result = runner.invoke(cli, ['user', 'show-me'], obj=mock_context)
    assert result.exit_code == 0
    assert "You logged in as test_user" in result.output


def test_user_list_all(runner, mock_context):
    """Test listing all users."""
    # Login as admin with view_list_users permission
    mock_context.set_user(mock_context.data.users[2])  # admin
    
    result = runner.invoke(cli, ['user', 'list'], obj=mock_context)
    assert result.exit_code == 0
    assert "test_user" in result.output
    assert "test_manager" in result.output
    assert "admin" in result.output


def test_user_add(runner, mock_context):
    """Test adding a new user."""
    # Login as admin with create_user permission
    mock_context.set_user(mock_context.data.users[2])  # admin
    
    result = runner.invoke(
        cli,
        ['user', 'add', '-u', 'new_user', '-p', 'new_password'],
        input='y\n',  # Confirm the creation
        obj=mock_context
    )
    assert result.exit_code == 0
    assert "User new_user added to system" in result.output


def test_user_roles(runner, mock_context):
    """Test listing available roles."""
    # Login as admin with view_list_roles permission
    mock_context.set_user(mock_context.data.users[2])  # admin
    
    result = runner.invoke(cli, ['user', 'roles'], obj=mock_context)
    assert result.exit_code == 0
    assert "user" in result.output
    assert "company_manager" in result.output
    assert "admin" in result.output


# Company command tests
def test_list_all_companies(runner, mock_context):
    """Test listing all companies."""
    # Login as a regular user
    mock_context.set_user(mock_context.data.users[0])  # test_user
    
    result = runner.invoke(cli, ['list'], obj=mock_context)
    assert result.exit_code == 0
    assert "Test Company" in result.output
    assert "Test Location" in result.output


def test_list_employees(runner, mock_context):
    """Test listing company employees."""
    # Login as manager with company_view permission
    mock_context.set_user(mock_context.data.users[1])  # test_manager
    mock_context.set_company(mock_context.data.companies[0])
    
    result = runner.invoke(cli, ['employees'], obj=mock_context)
    assert result.exit_code == 0
    assert "Company Test Company" in result.output
    assert "test_user" in result.output