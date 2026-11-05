"""MariaDB access layer: plain SQL through PyMySQL, one short-lived connection per call."""
from contextlib import contextmanager

import pymysql

from config import DB_CONFIG

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id           INT UNSIGNED NOT NULL AUTO_INCREMENT,
    title        VARCHAR(255) NOT NULL,
    is_done      TINYINT(1)   NOT NULL DEFAULT 0,
    created_at   DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    completed_at DATETIME(6)  NULL DEFAULT NULL,
    PRIMARY KEY (id),
    KEY idx_tasks_home (is_done, created_at, id),
    KEY idx_tasks_done (is_done, completed_at, id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
"""

# Keyed by is_done (0 = Home, 1 = Done). Home drains oldest first; Done shows the latest finished on top.
ORDER_BY = {
    0: "created_at ASC, id ASC",
    1: "completed_at DESC, id DESC",
}


@contextmanager
def connection():
    conn = pymysql.connect(cursorclass=pymysql.cursors.DictCursor, autocommit=True, **DB_CONFIG)
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    with connection() as conn, conn.cursor() as cur:
        cur.execute(SCHEMA)


def count_tasks(is_done):
    with connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) AS n FROM tasks WHERE is_done = %s", (int(is_done),))
        return cur.fetchone()["n"]


def list_tasks(is_done, limit, offset):
    sql = (
        "SELECT id, title FROM tasks WHERE is_done = %s "
        f"ORDER BY {ORDER_BY[int(is_done)]} LIMIT %s OFFSET %s"
    )
    with connection() as conn, conn.cursor() as cur:
        cur.execute(sql, (int(is_done), limit, offset))
        return cur.fetchall()


def get_task(task_id):
    with connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT id, title, is_done FROM tasks WHERE id = %s", (task_id,))
        return cur.fetchone()


def create_task(title):
    with connection() as conn, conn.cursor() as cur:
        cur.execute("INSERT INTO tasks (title) VALUES (%s)", (title,))


def update_task(task_id, title):
    with connection() as conn, conn.cursor() as cur:
        cur.execute("UPDATE tasks SET title = %s WHERE id = %s", (title, task_id))


def complete_task(task_id):
    with connection() as conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE tasks SET is_done = 1, completed_at = NOW(6) WHERE id = %s AND is_done = 0",
            (task_id,),
        )


def delete_task(task_id):
    with connection() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM tasks WHERE id = %s", (task_id,))


def delete_all_done():
    with connection() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM tasks WHERE is_done = 1")
