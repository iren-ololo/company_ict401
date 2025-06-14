import datetime as dt
import dataclasses
import functools
import os
import pickle
from typing import Optional

import click

from company.data import AppData
from company.models import User, Company


def save_data(data, filename):
    """
    Save data to a file using pickle serialization.
    
    Args:
        data: The data object to save
        filename: Path to the file where data will be saved
    """
    with open(filename, "wb") as _file:
        pickle.dump(data, _file)


def load_data(filename):
    """
    Load data from a pickle file.
    
    Args:
        filename: Path to the file to load data from
        
    Returns:
        The loaded data object or None if the file doesn't exist
    """
    if os.path.exists(filename):
        with open(filename, "rb") as _file:
            return pickle.load(_file)
    return None


# File paths for storing session and application data
SESSION_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), ".session.pkl"
)
DATA_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), ".data.pkl"
)


@dataclasses.dataclass
class Session:
    """Represents a user session with authenticated user and selected company."""
    _current_user: Optional[User] = None
    company: Optional[Company] = None
    last_visited_date: dt.datetime = dt.datetime.now()

    @property
    def current_user(self):
        """Get the currently authenticated user, if any."""
        if self._current_user:
            self.last_visited_date = dt.datetime.now()
        return self._current_user

    @current_user.setter
    def current_user(self, user: User):
        """Set the currently authenticated user."""
        self._current_user = user
        self.last_visited_date = dt.datetime.now()


@dataclasses.dataclass
class Context:
    """
    Application context containing both data and session information.
    
    This class provides methods for managing the user session and
    accessing application data. It also handles saving and loading
    the application state.
    """
    data: AppData
    _session: Session

    @property
    def current_user(self) -> Optional[User]:
        """Get the currently authenticated user, if any."""
        return self._session.current_user

    @property
    def user_logged_in(self) -> bool:
        """Check if a user is logged in."""
        if self._session.last_visited_date < dt.datetime.now() - dt.timedelta(minutes=10):
            self.reset_session()
        return self._session.current_user is not None

    @property
    def current_company(self) -> Optional[Company]:
        """Get the currently selected company, if any."""
        return self._session.company

    def set_user(self, user: User):
        """Set the authenticated user in the session."""
        self._session.current_user = user

    def set_company(self, company: Company):
        """Set the selected company in the session."""
        self._session.company = company

    def reset_session(self):
        """Reset the session, clearing the current user and company."""
        self._session = Session()

    def save(self):
        """Save both application data and session to files."""
        save_data(self.data, DATA_FILE)
        save_data(self._session, SESSION_FILE)

    @classmethod
    def load(cls):
        """
        Load or initialize the application context.
        """
        # Load existing data or None if no data file exists
        data = load_data(DATA_FILE)
        
        # Load existing session or create a new one
        session = load_data(SESSION_FILE) or Session()
        
        if not data:
            # Initialize with default data if no data file exists
            ctx = Context(
                data=AppData.init_default(),
                _session=session,
            )
        else:
            # Use loaded data
            ctx = Context(
                data=data,
                _session=session,
            )
        return ctx


def with_app_context(func):
    """
    Decorator that provides the application context to a command function.
    
    This decorator:
    1. Extracts the Context object from Click's context
    2. Passes it to the decorated function
    3. Automatically saves the context after the function executes
    """
    @functools.wraps(func)
    @click.pass_context
    def wrapper(click_ctx, *args, **kwargs):
        ctx: Context = click_ctx.obj
        result = func(ctx, *args, **kwargs)
        ctx.save()
        return result

    return wrapper


def require_login(func):
    """
    Decorator that ensures a user is logged in before executing a command.
    """
    @functools.wraps(func)
    @with_app_context
    def wrapper(ctx: Context, *args, **kwargs):
        # Check if a user is logged in
        if not ctx.user_logged_in:
            click.secho("Login required", fg="red", bold=True)
            return None
        # User is logged in, proceed with the command
        return func(ctx, *args, **kwargs)

    return wrapper


def require_permissions(permissions: list[str] = None, ):
    """
    Decorator factory that ensures a user has required permissions.
    
    This decorator:
    1. Checks if the user has all the specified permissions
    2. Handles both global user permissions and company-specific permissions
    3. Only proceeds if all permissions are granted
    """
    def decorator(func):
        @functools.wraps(func)
        @require_login  # First ensure user is logged in
        def wrapper(ctx: Context, *args, **kwargs):
            # Check permissions based on context
            if not ctx.current_company:
                # Check global user permissions when no company is selected
                for permission in permissions:
                    if not ctx.current_user.has_permission(permission):
                        click.secho("Not Authorized to perform this action.", fg="red", bold=True)
                        return None
            else:
                # Check company-specific permissions when a company is selected
                for permission in permissions:
                    if not ctx.current_company.has_permission(
                        user=ctx.current_user,
                        code=permission
                    ):
                        click.secho("Not Authorized to perform this action.", fg="red", bold=True)
                        return None
            
            # All permission checks passed, proceed with the command
            return func(ctx, *args, **kwargs)

        return wrapper

    return decorator
