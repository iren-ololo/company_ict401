# Company Management CLI Tool

A command-line interface tool for managing companies, inventories, and users.

## Features

- User authentication and permission management
- Company and employee management
- Inventory and product tracking
- Role-based access control

## Setup

### Prerequisites

- Python 3.12 or higher

### Installation

#### Option 1: Using `uv` (Recommended)

1. Clone the repository:
   ```bash
   git clone https://github.com/iren-ololo/company_ict401.git
   cd company
   ```

2. Install `uv` if you don't have it already:
   ```bash
   pip install uv
   ```

3. Install the package and dependencies using `uv`:
   ```bash
   uv sync
   ```

4. Run the command-line tool using entry point command:
   ```bash
   uv run company -h
   ```

#### Option 2: Using `requirements.txt`

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use: venv\Scripts\activate
   ```

3. Install dependencies from requirements.txt:
   ```bash
   pip install -r requirements.txt
   ```

4. Install the package in development mode:
   ```bash
   pip install -e .
   ```

Run the command-line tool using entry point command:
   ```bash
   company -h
   ```

# Company CLI Command Structure

```md
company
├── auth                       # Authentication commands
│   ├── login                  # Login to the system
│   └── logout                 # Logout from the system
│
├── user                       # User management commands
│   ├── show-me                # View your profile
│   ├── list                   # List all users (admin only)
│   ├── add                    # Add new user (admin only)
│   └── roles                  # View available roles
│
├── companies                  # List all companies
├── employees                  # List employees in the current company
│
├── inventory                  # Inventory management commands
│   ├── view                   # Display company inventory with all products
│   ├── search                 # Search for products by various criteria
│   ├── product-details        # Show detailed information about a specific product
│   └── update                 # Update product information
│
└── exit                       # Exit the application
```

# Usage

## CLI
   ```sh
   uv run company -h
   ```

## Tests
   ```sh
   uv run pytest -v
   ```