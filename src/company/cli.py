import datetime as dt
import json
from collections import defaultdict
from typing import Optional

import click
from company.utils import (
    Context,
    with_app_context,
    require_login,
    require_permissions,
)

from company.models import User, PermissionCode


@click.group(help="Company management CLI tool", context_settings={"help_option_names": ["-h", "--help"]})
@click.pass_context
def cli(ctx):
    """
    Main entry point for the Company Management CLI.
    """
    pass


@cli.group(help="Authentication commands")
def auth():
    """
    Authentication related commands.
    """
    pass


@cli.group(help="User management commands")
def user():
    """
    User management commands.
    """
    pass


@cli.group(help="Inventory and product management")
def inventory():
    """
    Inventory and product management commands.
    """
    pass


@auth.command("login", help="Log in to the system with username and password")
@click.argument("username")
@click.argument("password")
@click.option("--company-name", "-c", help="Company name to log into")
@with_app_context
def login(
    ctx: Context, username: str, password: str,
    company_name: Optional[str] = None
):
    """
    Authenticate a user and optionally log into a specific company.
    The session is reset before login to ensure a clean state.
    """
    # Reset any existing session
    ctx.reset_session()
    
    # Find the user by case-insensitive username match
    _user = next(
        (u for u in ctx.data.users if u.username.lower() == username.lower()),
        None
    )
    
    # Validate credentials
    if not (_user and _user.authenticate(password)):
        click.secho("Invalid credentials", fg="red", bold=True)
        return
        
    # Set the authenticated user in the session
    ctx.set_user(_user)
    click.secho(f"Logged in as {username}", fg="green")

    # If company name is provided, attempt to log into that company
    if company_name:
        # Find the company by name
        company = next(
            (c for c in ctx.data.companies if c.name == company_name), None
        )
        
        # Check if company exists
        if not company:
            click.secho(f"Company {company_name} not found", fg="yellow")
            return
            
        # Check if user is a member of the company
        if not company.is_member(_user):
            click.secho(
                f"User {username} is not a member of company {company_name}",
                fg="red"
            )
            return
            
        # Set the company in the session
        ctx.set_company(company)
        click.secho(f"Logged in company {company.name}", fg="green")
        return


@auth.command("logout", help="Log out from the current session")
@with_app_context
def logout(ctx: Context):
    """
    Log out from the current session.
    """
    # Reset the session (clear user and company)
    ctx.reset_session()
    click.secho("Logged out", fg="blue")


@user.command("show-me", help="Display current logged in user information")
@require_login
def get_me(ctx: Context):
    """Display information about the currently logged in user."""
    if ctx.current_company:
        membership = ctx.current_company.find_membership(ctx.current_user)
        click.secho(f"You logged in as {ctx.current_user.username} in company {ctx.current_company.name}." , fg="blue",bold=True)
        if membership:
            click.secho(f"  Your current role is {membership.role.name}" , fg="blue",bold=True)
    else:
        click.secho(f"You logged in as {ctx.current_user.username}", fg="blue", bold=True)
        click.secho(f"  Your roles:", fg="blue", bold=True)
        for role in ctx.current_user.roles:
            click.secho(f"    -{role.name}", fg="blue", bold=True)


@inventory.command("view", help="Display company inventory with all products")
@require_permissions([PermissionCode.VIEW])
def get_inventory_list(ctx: Context):
    """Display all products in the current company inventory or all inventories."""
    company = ctx.current_company
    for _inventory in ctx.data.get_inventories(company):
        click.secho(f"Inventory: {_inventory.description}", fg="blue", bold=True)
        for p in _inventory.products:
            click.secho(f"- {p.uuid}: {p.name} ({p.category.name}) — ${p.price}", fg="cyan")


@inventory.command("search", help="Search for products by SKU or category")
@click.option("--sku", "-s", help="Product SKU to search for")
@click.option("--category-id", "-c", help="Category ID to filter products")
@require_permissions([PermissionCode.VIEW])
def search_inventory(
    ctx: Context, sku: Optional[str] = None, category_id: Optional[str] = None
):
    """Search for products by exact SKU match or by category ID."""
    if not (sku or category_id):
        click.secho("Search filters were not provided", fg="yellow")
        return

    company = ctx.current_company
    # Track which inventories have matching products and what those products are
    inventories = []
    products = defaultdict(list)
    
    for _inventory in ctx.data.get_inventories(company):
        # Search either by SKU (exact match) or by category
        if sku:
            prod = _inventory.get_product(sku)
            if prod:
                inventories.append(_inventory)
                products[_inventory].append(prod)

        elif category_id:
            category = ctx.data.find_category(int(category_id))
            click.secho(f"{category}", fg="blue")
            if category:
                prods = _inventory.get_products_by_category(category)
                if prods:
                    inventories.append(_inventory)
                    products[_inventory] = prods

    if not inventories:
        click.secho("Product not found", fg="yellow")
        return

    # Display results grouped by inventory
    for _inventory in inventories:
        click.secho(f"Inventory: {_inventory.description}", fg="blue", bold=True)
        for p in products[_inventory]:
            click.secho(f"- {p.name} ({p.uuid}) - {p.description} - ${p.price}", fg="cyan")


@inventory.command("product-details", help="Show detailed information about a specific product")
@click.argument("sku")
@require_permissions([PermissionCode.COMPANY_VIEW])
def get_product_details(ctx: Context, sku: str):
    """Display detailed JSON information for a product identified by SKU."""
    company = ctx.current_company
    for _inventory in ctx.data.get_inventories(company):
        prod = _inventory.get_product(sku)
        if prod:
            click.secho(f"{prod.to_json()}", fg="blue")
            return
    click.secho("Product not found", fg="yellow")


@inventory.command("update", help="Update product information")
@click.option("--sku", "-s", help="SKU of the product to update")
@click.option("--product", "-p", help="JSON string with product data to update")
@require_permissions([PermissionCode.COMPANY_EDIT])
def update_inventory(ctx: Context, sku: str, product: str):
    """Update product attributes using JSON data for the specified SKU."""
    try:
        product_dict = json.loads(product)
    except json.JSONDecodeError:
        click.secho("Invalid JSON format for product data", fg="red")
        return
        
    company = ctx.current_company
    for _inventory in ctx.data.get_inventories(company):
        prod = _inventory.get_product(sku)
        if prod:
            if click.confirm(f"Are you sure you want to update product {prod.name}?"):
                prod.update(**product_dict)
                click.secho("Product updated successfully", fg="green")
            else:
                click.secho("Update cancelled", fg="yellow")
            return
    click.secho("Product not found", fg="red")


@cli.command("employees", help="List all employees in the current company or all companies")
@require_permissions([PermissionCode.COMPANY_VIEW])
def get_employees(ctx: Context):
    """List all employees in the current company or in all companies."""
    if ctx.current_company:
        companies = [ctx.current_company]
    else:
        companies = ctx.data.companies

    for _company in companies:
        _employees = _company.get_employees()
        click.secho(f"Company {_company.name}:", fg="blue", bold=True)
        for u in _employees:
            click.secho(f"- {u.username}", fg="cyan")


@cli.command("list", help="List all available companies")
@require_permissions([PermissionCode.VIEW])
def get_companies(ctx: Context):
    """List all companies registered in the system."""
    click.secho("Available companies:", fg="blue", bold=True)
    for _company in ctx.data.companies:
        click.secho(f"{_company}", fg="cyan")


@user.command("list", help="List all users in the system")
@require_permissions([PermissionCode.VIEW_LIST_USERS])
def get_all_users(ctx: Context):
    """List all users registered in the system."""
    click.secho("System users:", fg="blue", bold=True)
    for _user in ctx.data.users:
        click.secho(f"- {_user.username}", fg="cyan")


@inventory.command("categories", help="List all product categories")
@require_permissions([PermissionCode.VIEW])
def get_inventory_categories(ctx: Context):
    """List all product categories with their IDs and names."""
    click.secho("Product categories:", fg="blue", bold=True)
    for cat in ctx.data.categories:
        click.secho(f"{cat}", fg="cyan")


@user.command("roles", help="List all available user roles")
@require_permissions([PermissionCode.VIEW_LIST_ROLES])
def get_roles(ctx: Context):
    """List all available roles and their permissions."""
    click.secho("Available user roles:", fg="blue", bold=True)
    for role in ctx.data.roles:
        click.secho(f"- {role}", fg="cyan")


@user.command("add", help="Add a new user to the system")
@click.option(
    "--username", "-u", required=True, help="Username for the new user"
)
@click.option("--password", "-p", required=True, help="User password")
@click.option(
    "--role", "-r", default="user",
    help="User role (default: user)"
)
@click.option("--company", "-c", help="Company name to assign the user to")
@require_permissions([PermissionCode.CREATE_USER])
def create_user(
    ctx: Context, username: str, password: str, role: str = "user",
    company: Optional[str] = None
):
    """Create a new user with specified role and optional company assignment."""
    # Check if user with this username already exists
    existing_user = next(
        (u for u in ctx.data.users if u.username.lower() == username.lower()),
        None
    )
    
    if existing_user:
        click.secho(f"User with username '{username}' already exists", fg="red")
        return
        
    if not click.confirm(f"Are you sure you want to create user '{username}'?"):
        click.secho("User creation cancelled", fg="yellow")
        return
        
    default_role = ctx.data.find_role("user")
    role = ctx.data.find_role(role)
    _roles = [role] if role else []

    if company:
        company_obj = ctx.data.find_company(company)
        if not company_obj:
            click.secho(f"Company {company} not found", fg="red")
            return
        _user = User(username, password, [default_role])
        company_obj.add_member(
            user=_user,
            role=role,
            joined_date=dt.datetime.now(tz=dt.timezone.utc),
        )
        click.secho(f"User {username} added to company {company}", fg="green")
    else:
        _user = User(username, password, _roles)
        click.secho(f"User {username} added to system", fg="green")
    ctx.data.users.append(_user)


@cli.command("exit", help="Exit the application")
@with_app_context
def exit_company(ctx: Context):
    """
    Exit the application gracefully.
    """
    if click.confirm("Are you sure you want to exit?"):
        click.secho("Bye!", fg="blue")
        # Save any pending changes and reset the session
        ctx.reset_session()
        raise SystemExit
    click.secho("Exit cancelled", fg="yellow")


def main():
    """
    Main entry point for the CLI application.
    """
    cli(obj=Context.load())


if __name__ == "__main__":
    main()
