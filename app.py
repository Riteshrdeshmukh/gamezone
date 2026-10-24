import os
import re
from datetime import date, datetime, timedelta
from functools import wraps

import click
from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from db import fetch, run

OPEN_HOUR, CLOSE_HOUR = 10, 23

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-only-change-me")
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")


def admin_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if "admin" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapper


# ---------- Public pages ----------

@app.route("/")
def index():
    games = fetch("SELECT * FROM games ORDER BY id LIMIT 6")
    plans = fetch("SELECT * FROM pricing ORDER BY id")
    return render_template("index.html", games=games, plans=plans)


@app.route("/games")
def games():
    games = fetch("SELECT * FROM games ORDER BY platform, title")
    platforms = fetch("SELECT platform FROM pricing ORDER BY id")
    return render_template("games.html", games=games, platforms=platforms)


@app.route("/pricing")
def pricing():
    return render_template("pricing.html", plans=fetch("SELECT * FROM pricing ORDER BY id"))


@app.route("/booking", methods=["GET", "POST"])
def booking():
    plans = fetch("SELECT * FROM pricing ORDER BY id")
    if request.method == "POST":
        error = save_booking(plans, request.form)
        if error:
            flash(error, "error")
        else:
            flash("Booking received. We will confirm it by phone shortly.", "success")
            return redirect(url_for("booking"))
    return render_template(
        "booking.html", plans=plans, form=request.values,
        today=date.today().isoformat(), open_hour=OPEN_HOUR, close_hour=CLOSE_HOUR,
    )


def save_booking(plans, f):
    """Validate the form and store the booking. Returns an error message or None."""
    name = f.get("name", "").strip()
    phone = f.get("phone", "").strip()
    email = f.get("email", "").strip()
    try:
        plan = next(p for p in plans if p["id"] == int(f.get("pricing_id", 0)))
        play_date = date.fromisoformat(f.get("play_date", ""))
        start = datetime.strptime(f.get("start_time", ""), "%H:%M")
        hours = int(f.get("hours", 0))
        stations = int(f.get("stations", 0))
    except (StopIteration, ValueError):
        return "Please fill in every field with valid values."

    if not name or not re.fullmatch(r"\d{10}", phone):
        return "Enter your name and a 10-digit phone number."
    if email and "@" not in email:
        return "Enter a valid email address or leave it empty."
    if not 1 <= hours <= 6 or not 1 <= stations <= 4:
        return "Choose 1 to 6 hours and 1 to 4 stations."

    start_time = start.time()
    start_min = start.hour * 60 + start.minute
    if play_date < date.today() or (play_date == date.today() and start_time <= datetime.now().time()):
        return "Pick a start time that has not passed yet."
    if start_min < OPEN_HOUR * 60 or start_min + hours * 60 > CLOSE_HOUR * 60:
        return f"We are open {OPEN_HOUR}:00 to {CLOSE_HOUR}:00. Your session must finish by closing time."

    end_time = (start + timedelta(hours=hours)).time()
    used = fetch(
        """SELECT COALESCE(SUM(stations), 0) AS used FROM bookings
           WHERE pricing_id = %s AND play_date = %s AND status <> 'cancelled'
             AND start_time < %s AND start_time + hours * INTERVAL '1 hour' > %s""",
        (plan["id"], play_date, end_time, start_time), one=True,
    )["used"]
    if used + stations > plan["stations"]:
        free = plan["stations"] - used
        return f"Only {free} {plan['platform']} station(s) are free at that time. Try another slot."

    run(
        """INSERT INTO bookings (customer_name, phone, email, pricing_id, play_date,
                                 start_time, hours, stations, total_price)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        (name, phone, email or None, plan["id"], play_date, start_time, hours, stations,
         plan["price_per_hour"] * hours * stations),
    )
    return None


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name, email, message = (request.form.get(k, "").strip() for k in ("name", "email", "message"))
        if not name or "@" not in email or len(message) < 10:
            flash("Enter your name, a valid email and a message of at least 10 characters.", "error")
        else:
            run("INSERT INTO messages (name, email, message) VALUES (%s, %s, %s)", (name, email, message))
            flash("Message sent. We reply within a day.", "success")
            return redirect(url_for("contact"))
    return render_template("contact.html", form=request.form)


# ---------- Admin ----------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        admin = fetch("SELECT * FROM admins WHERE username = %s",
                      (request.form.get("username", "").strip(),), one=True)
        if admin and check_password_hash(admin["password_hash"], request.form.get("password", "")):
            session.clear()
            session["admin"] = admin["username"]
            return redirect(url_for("admin_dashboard"))
        flash("Wrong username or password.", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/admin")
@admin_required
def admin_dashboard():
    bookings = fetch(
        """SELECT b.*, p.platform FROM bookings b JOIN pricing p ON p.id = b.pricing_id
           ORDER BY b.play_date DESC, b.start_time DESC LIMIT 50"""
    )
    stats = fetch(
        """SELECT COUNT(*) FILTER (WHERE status = 'pending') AS pending,
                  COUNT(*) FILTER (WHERE play_date = CURRENT_DATE AND status <> 'cancelled') AS today,
                  COALESCE(SUM(total_price) FILTER (WHERE status = 'confirmed'), 0) AS revenue
           FROM bookings""", one=True,
    )
    return render_template(
        "admin_dashboard.html", bookings=bookings, stats=stats,
        messages=fetch("SELECT * FROM messages ORDER BY created_at DESC LIMIT 20"),
        games=fetch("SELECT * FROM games ORDER BY platform, title"),
        platforms=fetch("SELECT platform FROM pricing ORDER BY id"),
    )


@app.post("/admin/bookings/<int:booking_id>/<status>")
@admin_required
def booking_status(booking_id, status):
    if status in ("confirmed", "cancelled"):
        run("UPDATE bookings SET status = %s WHERE id = %s", (status, booking_id))
        flash(f"Booking #{booking_id} {status}.", "success")
    return redirect(url_for("admin_dashboard"))


@app.post("/admin/games")
@admin_required
def add_game():
    title, genre, description = (request.form.get(k, "").strip() for k in ("title", "genre", "description"))
    platform = request.form.get("platform", "")
    if title and genre and description and fetch("SELECT 1 FROM pricing WHERE platform = %s", (platform,)):
        run("INSERT INTO games (title, platform, genre, description) VALUES (%s, %s, %s, %s)",
            (title, platform, genre, description))
        flash(f"Added {title}.", "success")
    else:
        flash("Fill in every game field.", "error")
    return redirect(url_for("admin_dashboard"))


@app.post("/admin/games/<int:game_id>/delete")
@admin_required
def delete_game(game_id):
    run("DELETE FROM games WHERE id = %s", (game_id,))
    flash("Game removed.", "success")
    return redirect(url_for("admin_dashboard"))


@app.cli.command("create-admin")
@click.argument("username")
@click.password_option()
def create_admin(username, password):
    """Create an admin account, or reset its password."""
    run(
        """INSERT INTO admins (username, password_hash) VALUES (%s, %s)
           ON CONFLICT (username) DO UPDATE SET password_hash = EXCLUDED.password_hash""",
        (username, generate_password_hash(password)),
    )
    click.echo(f"Admin '{username}' saved.")


if __name__ == "__main__":
    app.run(debug=True)
