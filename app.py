"""MyEzTask: a local task pool. Flask renders the HTML, HTMX swaps the fragments."""
import math

import pymysql
from flask import Flask, abort, make_response, redirect, render_template, request

import db
from config import PAGE_SIZE

TITLE_MAX = 255
VIEWS = ("home", "done")

app = Flask(__name__)


def is_htmx():
    # Back-button restores need the full page, so they are not treated as fragment requests.
    return (
        request.headers.get("HX-Request") == "true"
        and request.headers.get("HX-History-Restore-Request") != "true"
    )


def parse_view(value):
    return value if value in VIEWS else "home"


def parse_page(value):
    try:
        return max(1, int(value))
    except (TypeError, ValueError):
        return 1


def query_view_page():
    return parse_view(request.args.get("view")), parse_page(request.args.get("page"))


def build_context(view, page):
    """Everything a view needs. page=None means the last page, used right after adding."""
    counts = {"home": db.count_tasks(False), "done": db.count_tasks(True)}
    total = counts[view]
    pages = max(1, math.ceil(total / PAGE_SIZE))
    page = pages if page is None else min(page, pages)
    tasks = db.list_tasks(view == "done", PAGE_SIZE, (page - 1) * PAGE_SIZE)
    return {
        "view": view,
        "page": page,
        "pages": pages,
        "total": total,
        "tasks": tasks,
        "counts": counts,
        "qs": f"view={view}&page={page}",
    }


def title_error(title):
    if not title:
        return "Write a short title first."
    if len(title) > TITLE_MAX:
        return f"Keep it under {TITLE_MAX} characters."
    return None


def list_response(view, page):
    ctx = build_context(view, page)
    resp = make_response(render_template("partials/list_swap.html", **ctx))
    resp.headers["HX-Push-Url"] = f"/{view}?page={ctx['page']}"
    return resp


def form_response(view, page, task_id, title, error=None, retarget=False):
    html = render_template(
        "partials/form_modal.html",
        task_id=task_id,
        title=title,
        error=error,
        qs=f"view={view}&page={page}",
    )
    resp = make_response(html)
    if retarget:
        # Validation errors stay inside the open modal and leave the list alone.
        resp.headers["HX-Retarget"] = "#modal-slot"
        resp.headers["HX-Reswap"] = "innerHTML"
    return resp


def show_view(view):
    ctx = build_context(view, parse_page(request.args.get("page")))
    template = "partials/view_swap.html" if is_htmx() else "index.html"
    return render_template(template, **ctx)


@app.get("/")
def index():
    return redirect("/home")


@app.get("/home")
def home_page():
    return show_view("home")


@app.get("/done")
def done_page():
    return show_view("done")


@app.get("/tasks/new")
def new_task_form():
    view, page = query_view_page()
    return form_response(view, page, task_id=None, title="")


@app.get("/tasks/<int:task_id>/edit")
def edit_task_form(task_id):
    task = db.get_task(task_id)
    if task is None:
        abort(404)
    view, page = query_view_page()
    return form_response(view, page, task_id=task_id, title=task["title"])


@app.post("/tasks")
def create_task():
    view, page = query_view_page()
    raw = request.form.get("title", "")
    title = raw.strip()
    error = title_error(title)
    if error:
        return form_response(view, page, task_id=None, title=raw, error=error, retarget=True)
    db.create_task(title)
    # New tasks join the end of Home, so jump to the last page where they appear.
    return list_response("home", None)


@app.put("/tasks/<int:task_id>")
def update_task(task_id):
    view, page = query_view_page()
    raw = request.form.get("title", "")
    title = raw.strip()
    error = title_error(title)
    if error:
        return form_response(view, page, task_id=task_id, title=raw, error=error, retarget=True)
    db.update_task(task_id, title)
    return list_response(view, page)


@app.post("/tasks/<int:task_id>/complete")
def complete_task(task_id):
    view, page = query_view_page()
    db.complete_task(task_id)
    return list_response(view, page)


@app.get("/tasks/<int:task_id>/confirm")
def confirm_delete_task(task_id):
    task = db.get_task(task_id)
    if task is None:
        abort(404)
    view, page = query_view_page()
    return render_template(
        "partials/confirm_modal.html",
        scope="task",
        task_id=task_id,
        title=task["title"],
        qs=f"view={view}&page={page}",
    )


@app.delete("/tasks/<int:task_id>")
def delete_task(task_id):
    view, page = query_view_page()
    db.delete_task(task_id)
    return list_response(view, page)


@app.get("/tasks/done/confirm")
def confirm_delete_done():
    view, page = query_view_page()
    return render_template(
        "partials/confirm_modal.html",
        scope="done",
        count=db.count_tasks(True),
        qs=f"view={view}&page={page}",
    )


@app.delete("/tasks/done")
def delete_all_done():
    db.delete_all_done()
    return list_response("done", 1)


if __name__ == "__main__":
    try:
        db.init_db()
    except pymysql.MySQLError as exc:
        raise SystemExit(
            f"Could not connect to MariaDB: {exc}\n"
            "Check the MYEZTASK_DB_* values in config.py and the setup steps in README.md."
        )
    app.run(host="127.0.0.1", port=5000, debug=False)
