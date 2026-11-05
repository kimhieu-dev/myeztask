/* MyEzTask UI glue: theme switch, row selection, toolbar state, modal dismissal.
   Data work happens on the server through the HTMX attributes in the templates. */
(function () {
  "use strict";

  var THEME_KEY = "myeztask-theme";
  var selectedId = null;
  var selectedView = null;

  // ---- Theme ------------------------------------------------------------

  function currentTheme() {
    return document.documentElement.getAttribute("data-theme") === "dark" ? "dark" : "light";
  }

  function setTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    try {
      localStorage.setItem(THEME_KEY, theme);
    } catch (e) {
      /* Storage blocked: the choice simply lasts for this page view. */
    }
    syncThemeButton();
  }

  function syncThemeButton() {
    var btn = document.getElementById("theme-toggle");
    if (btn) btn.textContent = currentTheme() === "dark" ? "Light mode" : "Dark mode";
  }

  // ---- List and selection -------------------------------------------------

  function taskList() {
    return document.getElementById("task-list");
  }

  function rowById(id) {
    var list = taskList();
    return list ? list.querySelector('.row[data-id="' + id + '"]') : null;
  }

  function selectRow(row) {
    selectedId = row.dataset.id;
    selectedView = taskList().dataset.view;
    markSelected();
    updateToolbar();
  }

  function clearSelection() {
    selectedId = null;
    selectedView = null;
    markSelected();
    updateToolbar();
  }

  function markSelected() {
    document.querySelectorAll(".row.is-selected").forEach(function (row) {
      row.classList.remove("is-selected");
    });
    var row = selectedId ? rowById(selectedId) : null;
    if (row) row.classList.add("is-selected");
  }

  // After any swap, drop the selection if its row is gone or the view changed.
  function reconcileSelection() {
    var list = taskList();
    if (selectedId && (!list || list.dataset.view !== selectedView || !rowById(selectedId))) {
      selectedId = null;
      selectedView = null;
    }
  }

  function updateToolbar() {
    var hasSelection = selectedId !== null;
    document.querySelectorAll("[data-requires-selection]").forEach(function (btn) {
      btn.disabled = !hasSelection;
    });
    var list = taskList();
    var clearAll = document.querySelector('[data-action="clear-done"]');
    if (clearAll) clearAll.disabled = !list || Number(list.dataset.total) === 0;
  }

  // ---- Actions ------------------------------------------------------------

  function runAction(action) {
    var list = taskList();
    if (!list) return;
    var q = "view=" + list.dataset.view + "&page=" + list.dataset.page;

    if (action === "add") {
      return htmx.ajax("GET", "/tasks/new?" + q, { target: "#modal-slot", swap: "innerHTML" });
    }
    if (action === "clear-done") {
      return htmx.ajax("GET", "/tasks/done/confirm?" + q, { target: "#modal-slot", swap: "innerHTML" });
    }
    if (!selectedId) return;

    if (action === "edit") {
      return htmx.ajax("GET", "/tasks/" + selectedId + "/edit?" + q, { target: "#modal-slot", swap: "innerHTML" });
    }
    if (action === "delete") {
      return htmx.ajax("GET", "/tasks/" + selectedId + "/confirm?" + q, { target: "#modal-slot", swap: "innerHTML" });
    }
    if (action === "complete") {
      return htmx.ajax("POST", "/tasks/" + selectedId + "/complete?" + q, { target: "#task-list", swap: "outerHTML" });
    }
  }

  function modalOpen() {
    return !!document.querySelector("#modal-slot .backdrop");
  }

  function closeModal() {
    var slot = document.getElementById("modal-slot");
    if (slot) slot.innerHTML = "";
  }

  // ---- Events -------------------------------------------------------------

  document.addEventListener("click", function (e) {
    var el = e.target;

    var action = el.closest("[data-action]");
    if (action) {
      if (!action.disabled) runAction(action.dataset.action);
      return;
    }

    var backdrop = document.querySelector("#modal-slot .backdrop");
    if (el.closest("[data-close]") || (backdrop && el === backdrop)) {
      closeModal();
      return;
    }

    var row = el.closest(".row");
    if (row && taskList() && taskList().contains(row)) selectRow(row);
  });

  document.addEventListener("dblclick", function (e) {
    var row = e.target.closest(".row");
    if (row && row.dataset.id === selectedId) runAction("edit");
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
      if (modalOpen()) closeModal();
      else if (selectedId) clearSelection();
      return;
    }
    if (modalOpen() || /^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName)) return;

    var list = taskList();
    if (!list) return;

    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      var rows = Array.prototype.slice.call(list.querySelectorAll(".row"));
      if (!rows.length) return;
      e.preventDefault();
      var index = rows.findIndex(function (r) { return r.dataset.id === selectedId; });
      var next = index === -1 ? 0 : index + (e.key === "ArrowDown" ? 1 : -1);
      next = Math.max(0, Math.min(rows.length - 1, next));
      selectRow(rows[next]);
      rows[next].focus();
    } else if (e.key === "Enter" && e.target.classList.contains("row") && selectedId) {
      runAction("edit");
    }
  });

  document.body.addEventListener("htmx:afterSettle", function () {
    reconcileSelection();
    markSelected();
    updateToolbar();
    var firstField = document.querySelector("#modal-slot [autofocus]");
    if (firstField) firstField.focus();
  });

  document.body.addEventListener("htmx:responseError", function () {
    window.alert("Something went wrong. Check the terminal that is running app.py.");
  });

  document.body.addEventListener("htmx:sendError", function () {
    window.alert("Cannot reach the local server. Is app.py still running?");
  });

  document.getElementById("theme-toggle").addEventListener("click", function () {
    setTheme(currentTheme() === "dark" ? "light" : "dark");
  });

  syncThemeButton();
  updateToolbar();
})();
