"""Settings for MyEzTask. Every database value can be overridden with an environment variable."""
import os

DB_CONFIG = {
    "host": os.environ.get("MYEZTASK_DB_HOST", "127.0.0.1"),
    "port": int(os.environ.get("MYEZTASK_DB_PORT", "3307")),
    "user": os.environ.get("MYEZTASK_DB_USER", "myeztask"),
    "password": os.environ.get("MYEZTASK_DB_PASSWORD", "myeztask"),
    "database": os.environ.get("MYEZTASK_DB_NAME", "myeztask"),
    "charset": "utf8mb4",
}

# Tasks per page on both Home and Done.
PAGE_SIZE = 10
