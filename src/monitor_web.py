"""Flask web UI for managing monitored sites and viewing alert history."""
from __future__ import annotations

import os

from flask import Flask, flash, jsonify, redirect, render_template, request, url_for

from . import monitor_db as db
from .monitor_runner import run_checks

app = Flask(
    __name__,
    template_folder="../templates",
    static_folder="../static",
)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-change-me")


# ── Pages ──────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    db.ensure_db()
    sites = db.list_sites()
    alerts = db.list_alerts(limit=20)
    interval = int(os.getenv("CHECK_INTERVAL_MINUTES", "30"))
    return render_template("monitor.html", sites=sites, alerts=alerts, interval=interval)


# ── Site CRUD ──────────────────────────────────────────────────────────────

@app.route("/sites/add", methods=["POST"])
def add_site():
    name = request.form.get("name", "").strip()
    url = request.form.get("url", "").strip()
    site_type = request.form.get("type", "html")
    css_selector = request.form.get("css_selector", "").strip() or None

    if not name or not url:
        flash("Name and URL are required.", "danger")
        return redirect(url_for("index"))

    db.add_site(name, url, site_type, css_selector)
    flash(f"'{name}' added successfully.", "success")
    return redirect(url_for("index"))


@app.route("/sites/<int:site_id>/edit", methods=["POST"])
def edit_site(site_id: int):
    name = request.form.get("name", "").strip()
    url = request.form.get("url", "").strip()
    site_type = request.form.get("type", "html")
    css_selector = request.form.get("css_selector", "").strip() or None

    if not name or not url:
        flash("Name and URL are required.", "danger")
        return redirect(url_for("index"))

    db.update_site(site_id, name, url, site_type, css_selector)
    flash(f"'{name}' updated.", "success")
    return redirect(url_for("index"))


@app.route("/sites/<int:site_id>/toggle", methods=["POST"])
def toggle_site(site_id: int):
    site = db.get_site(site_id)
    if not site:
        return jsonify({"error": "not found"}), 404
    new_state = not bool(site["enabled"])
    db.toggle_site(site_id, new_state)
    return jsonify({"enabled": new_state})


@app.route("/sites/<int:site_id>/delete", methods=["POST"])
def delete_site(site_id: int):
    site = db.get_site(site_id)
    if site:
        db.delete_site(site_id)
        flash(f"'{site['name']}' removed.", "info")
    return redirect(url_for("index"))


# ── Manual check ───────────────────────────────────────────────────────────

@app.route("/check", methods=["POST"])
def check_all():
    result = run_checks()
    flash(
        f"Check complete — {result['alerts_sent']} alert(s) sent across {result['checked']} site(s).",
        "success" if not result["errors"] else "warning",
    )
    return redirect(url_for("index"))


@app.route("/check/<int:site_id>", methods=["POST"])
def check_one(site_id: int):
    result = run_checks(site_id=site_id)
    flash(
        f"Check complete — {result['alerts_sent']} alert(s) sent.",
        "success" if not result["errors"] else "warning",
    )
    return redirect(url_for("index"))


# ── API (JSON) ─────────────────────────────────────────────────────────────

@app.route("/api/sites")
def api_sites():
    return jsonify(db.list_sites())


@app.route("/api/alerts")
def api_alerts():
    limit = int(request.args.get("limit", 50))
    return jsonify(db.list_alerts(limit=limit))


@app.route("/api/check", methods=["POST"])
def api_check():
    result = run_checks()
    return jsonify(result)
