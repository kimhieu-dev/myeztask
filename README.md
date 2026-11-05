# MyEzTask

A local task pool with no priorities and no deadlines. Drop tasks in, and when you have time, pick one and do it.

Stack: Python + Flask, HTMX 2.0.11 (bundled in `static/vendor`, no internet needed), MariaDB.

## Setup

1. Install MariaDB from https://mariadb.org/download/ and remember the root password.

2. Create the database and user. Run this in a MariaDB shell (`mysql -u root -p`) or in HeidiSQL:

   ```sql
   CREATE DATABASE IF NOT EXISTS myeztask CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   CREATE USER IF NOT EXISTS 'myeztask'@'localhost' IDENTIFIED BY 'myeztask';
   CREATE USER IF NOT EXISTS 'myeztask'@'127.0.0.1' IDENTIFIED BY 'myeztask';
   GRANT ALL PRIVILEGES ON myeztask.* TO 'myeztask'@'localhost';
   GRANT ALL PRIVILEGES ON myeztask.* TO 'myeztask'@'127.0.0.1';
   FLUSH PRIVILEGES;
   ```

   The password above is only the default. Change it if you like, and then set `MYEZTASK_DB_PASSWORD` (see step 4).

3. Install the Python packages from the project folder:

   ```powershell
   python -m venv .venv
   .venv\Scripts\python -m pip install -r requirements.txt
   ```

4. Optional: point the app at a different database or user with environment variables:

   | Variable | Default |
   | --- | --- |
   | `MYEZTASK_DB_HOST` | `127.0.0.1` |
   | `MYEZTASK_DB_PORT` | `3306` |
   | `MYEZTASK_DB_USER` | `myeztask` |
   | `MYEZTASK_DB_PASSWORD` | `myeztask` |
   | `MYEZTASK_DB_NAME` | `myeztask` |

5. Start the app:

   ```powershell
   .venv\Scripts\python app.py
   ```

   Then open http://127.0.0.1:5000. The `tasks` table is created automatically on first start.

## Using it

- **Home**: the pool, oldest first, 10 per page. Click a task to select it, then use Edit, Mark done, or Delete. Double-click a task to edit it.
- **Done**: finished tasks, struck through. Delete one task, or use Delete all. Both ask for confirmation.
- **Keyboard**: Arrow keys move the selection, Enter edits the selected task, Esc closes a dialog or clears the selection.
- **Theme**: the Dark / Light button is at the top right. Your choice is remembered in this browser.

## Layout

```
app.py              Flask routes
db.py               MariaDB queries (plain SQL via PyMySQL)
config.py           Database settings and page size
templates/          Jinja2 + HTMX fragments
static/css/         Styles (light and dark tokens)
static/js/app.js    Selection, toolbar state, keyboard, dialogs
static/vendor/      Vendored htmx 2.0.11 and its license
```
