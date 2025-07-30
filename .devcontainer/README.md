# Instagram Flask App - DevContainer Setup

This devcontainer configuration provides a complete development environment for the Instagram Flask application.

## Features

- **Python 3.11** with Poetry dependency management
- **Flask development server** with hot reload
- **MySQL database** for data persistence
- **Redis** for caching and session management
- **Debugging support** with debugpy on port 5678
- **Code formatting** with Black
- **Linting** with Flake8 and Pylint
- **VS Code extensions** pre-installed for Python development

## Getting Started

1. **Prerequisites**: Make sure you have Docker and VS Code with the Remote - Containers extension installed.

2. **Environment Variables**: Create a `.env` file in the root directory with the following variables:
   ```env
   MYSQL_USER=instagram_user
   MYSQL_DATABASE=instagram_db
   MYSQL_ROOT_PASSWORD=root_password
   MYSQL_PASSWORD=instagram_password
   MYSQL_HOST=mysql
   ```

3. **Open in DevContainer**:
   - Open the project in VS Code
   - Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
   - Select "Dev Containers: Reopen in Container"
   - Wait for the container to build and start

## Ports

- **8000**: Flask application
- **5678**: Python debugger
- **3306**: MySQL database
- **6379**: Redis

## Development Workflow

1. **Start the application**:
   ```bash
   poetry run python -m flask run --host=0.0.0.0 --port=8000
   ```

2. **Run with debugging**:
   ```bash
   poetry run python -m debugpy --listen 0.0.0.0:5678 --wait-for-client -m flask run --host=0.0.0.0 --port=8000
   ```

3. **Database migrations**:
   ```bash
   poetry run flask db upgrade
   ```

4. **Run tests**:
   ```bash
   poetry run python -m pytest
   ```

## VS Code Integration

The devcontainer comes with pre-configured VS Code settings:
- Python interpreter automatically set to the virtual environment
- Black formatting on save
- Flake8 linting
- Debugging configuration ready to use

## Troubleshooting

- If the container fails to build, check that all required files are present
- Ensure Docker has enough resources allocated
- Check the Docker logs for any service startup issues
- Make sure the `.env` file exists and contains valid database credentials

## Services

- **app**: Main Flask application container
- **mysql**: MySQL database server
- **redis**: Redis cache server

All services are networked together and can communicate using their service names. 