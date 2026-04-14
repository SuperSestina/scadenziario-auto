from flask import Flask, render_template, request, redirect, session
import database
from werkzeug.security import check_password_hash
from datetime import datetime
import pdfkit
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from flask import make_response
import io


config = pdfkit.configuration(
    wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
)

app = Flask(__name__)
app.secret_key = "supersecretkey"

database.init_db()

@app.route("/")
def home():
    if "user_id" not in session:
        return redirect("/login")

    vehicles = database.get_vehicles_by_user(session["user_id"])
    deadlines = database.get_all_deadlines_by_user(session["user_id"])

    today = datetime.today()
    alerts = []

    for d in deadlines:
        if not d["due_date"]:
            continue

        due_date = datetime.strptime(d["due_date"], "%Y-%m-%d")
        days_left = (due_date - today).days

        if days_left <= 30:
            if days_left <= 10:
                status = "red"
            else:
                status = "yellow"

            alerts.append({
                "vehicle": d["vehicle_name"],
                "description": d["description"],
                "due_date": d["due_date"],
                "days_left": days_left,
                "status": status
            })

    return render_template(
        "home.html",
        name=session.get("name", "Utente"),
        vehicles=vehicles,
        alerts=alerts
    )

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        database.create_user(name, email, password)
        return redirect("/login")

    return """
    <h2>Registrazione</h2>

    <form method="post">
        <input name="name" placeholder="Nome utente">
        <input name="email" placeholder="Email">
        <input name="password" type="password" placeholder="Password">
        <button>Registrati</button>
    </form>

    <hr>

    <p>Hai già un account?</p>
    <a href="/login">Vai al Login</a>
    """

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = database.get_user_by_email(email)

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["name"] = user["name"]
            session["email"] = user["email"]
            return redirect("/")
        else:
            return "Login errato"

    return """
    <h2>Login</h2>

    <form method="post">
        <input name="email" placeholder="Email">
        <input name="password" type="password" placeholder="Password">
        <button>Login</button>
    </form>

    <hr>

    <p>Non hai un account?</p>
    <a href="/register">Registrati</a>
    """

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")



@app.route("/add_vehicle", methods=["POST"])
def add_vehicle():
    if "user_id" not in session:
        return redirect("/login")

    name = request.form["name"]
    plate = request.form["plate"]

    database.add_vehicle(session["user_id"], name, plate)

    return redirect("/")

@app.route("/vehicle/<int:vehicle_id>")
def vehicle(vehicle_id):
    if "user_id" not in session:
        return redirect("/login")

    vehicle = database.get_vehicle_by_id(vehicle_id, session["user_id"])

    if not vehicle:
        return "Veicolo non trovato"

    deadlines = database.get_deadlines_by_vehicle(vehicle_id)

    # 🔥 calcolo alert
    today = datetime.today()
    maintenances = database.get_maintenances_by_vehicle(vehicle_id)
    notes = database.get_notes_by_vehicle(vehicle_id)

    deadlines_with_status = []

    for d in deadlines:
        if not d["due_date"]:
            continue  # salta se vuota

        due_date = datetime.strptime(d["due_date"], "%Y-%m-%d")
        days_left = (due_date - today).days

        if days_left <= 10:
            status = "red"
        elif days_left <= 30:
            status = "yellow"
        else:
            status = "normal"

        deadlines_with_status.append({
            "id": d["id"],
            "description": d["description"],
            "due_date": d["due_date"],
            "days_left": days_left,
            "status": status
        })

    return render_template(
        "vehicle.html",
        vehicle=vehicle,
        deadlines=deadlines_with_status,
        notes=notes,
        maintenances=maintenances
    )


@app.route("/add_deadline/<int:vehicle_id>", methods=["POST"])
def add_deadline(vehicle_id):
    if "user_id" not in session:
        return redirect("/login")

    description = request.form["description"]
    due_date = request.form["due_date"]

    # 🔴 BLOCCO DATI VUOTI
    if not due_date:
        return "Inserisci una data valida"

    database.add_deadline(vehicle_id, description, due_date)

    return redirect(f"/vehicle/{vehicle_id}")

@app.route("/add_note/<int:vehicle_id>", methods=["POST"])
def add_note(vehicle_id):
    if "user_id" not in session:
        return redirect("/login")

    content = request.form["content"]

    if not content:
        return "Inserisci una nota"

    database.add_note(vehicle_id, content)

    return redirect(f"/vehicle/{vehicle_id}")

@app.route("/delete_note/<int:note_id>/<int:vehicle_id>")
def delete_note(note_id, vehicle_id):
    if "user_id" not in session:
        return redirect("/login")

    database.delete_note(note_id)

    return redirect(f"/vehicle/{vehicle_id}")

@app.route("/delete_deadline/<int:deadline_id>/<int:vehicle_id>")
def delete_deadline(deadline_id, vehicle_id):
    if "user_id" not in session:
        return redirect("/login")

    database.delete_deadline(deadline_id)

    return redirect(f"/vehicle/{vehicle_id}")

@app.route("/add_maintenance/<int:vehicle_id>", methods=["POST"])
def add_maintenance(vehicle_id):
    if "user_id" not in session:
        return redirect("/login")

    description = request.form["description"]
    cost = request.form["cost"]
    workshop = request.form["workshop"]
    date = request.form["date"]

    database.add_maintenance(vehicle_id, description, cost, workshop, date)

    return redirect(f"/vehicle/{vehicle_id}")

@app.route("/delete_maintenance/<int:maintenance_id>/<int:vehicle_id>")
def delete_maintenance(maintenance_id, vehicle_id):
    if "user_id" not in session:
        return redirect("/login")

    database.delete_maintenance(maintenance_id)

    return redirect(f"/vehicle/{vehicle_id}")

@app.route("/edit_deadline/<int:deadline_id>/<int:vehicle_id>")
def edit_deadline_page(deadline_id, vehicle_id):
    if "user_id" not in session:
        return redirect("/login")

    conn = database.get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM deadlines WHERE id = ?", (deadline_id,))
    deadline = cursor.fetchone()

    conn.close()

    return render_template(
        "edit_deadline.html",
        deadline=deadline,
        vehicle_id=vehicle_id
    )

@app.route("/update_deadline/<int:deadline_id>/<int:vehicle_id>", methods=["POST"])
def update_deadline(deadline_id, vehicle_id):
    if "user_id" not in session:
        return redirect("/login")

    description = request.form["description"]
    due_date = request.form["due_date"]

    conn = database.get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE deadlines
        SET description = ?, due_date = ?
        WHERE id = ?
    """, (description, due_date, deadline_id))

    conn.commit()
    conn.close()

    return redirect(f"/vehicle/{vehicle_id}")


@app.route("/delete_vehicle/<int:vehicle_id>")
def delete_vehicle(vehicle_id):
    if "user_id" not in session:
        return redirect("/login")

    database.delete_vehicle(vehicle_id)

    return redirect("/")

@app.route("/edit_maintenance/<int:maintenance_id>/<int:vehicle_id>")
def edit_maintenance_page(maintenance_id, vehicle_id):
    if "user_id" not in session:
        return redirect("/login")

    conn = database.get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM maintenances WHERE id = ?", (maintenance_id,))
    maintenance = cursor.fetchone()

    conn.close()

    return render_template(
        "edit_maintenance.html",
        maintenance=maintenance,
        vehicle_id=vehicle_id
    )

@app.route("/update_maintenance/<int:maintenance_id>/<int:vehicle_id>", methods=["POST"])
def update_maintenance(maintenance_id, vehicle_id):
    if "user_id" not in session:
        return redirect("/login")

    description = request.form["description"]
    cost = request.form["cost"]
    workshop = request.form["workshop"]
    date = request.form["date"]

    conn = database.get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE maintenances
        SET description = ?, cost = ?, workshop = ?, date = ?
        WHERE id = ?
    """, (description, cost, workshop, date, maintenance_id))

    conn.commit()
    conn.close()

    return redirect(f"/vehicle/{vehicle_id}")

@app.route("/edit_note/<int:note_id>/<int:vehicle_id>")
def edit_note_page(note_id, vehicle_id):
    if "user_id" not in session:
        return redirect("/login")

    conn = database.get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
    note = cursor.fetchone()

    conn.close()

    return render_template(
        "edit_note.html",
        note=note,
        vehicle_id=vehicle_id
    )

@app.route("/update_note/<int:note_id>/<int:vehicle_id>", methods=["POST"])
def update_note(note_id, vehicle_id):
    if "user_id" not in session:
        return redirect("/login")

    content = request.form["content"]

    conn = database.get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE notes
        SET content = ?
        WHERE id = ?
    """, (content, note_id))

    conn.commit()
    conn.close()

    return redirect(f"/vehicle/{vehicle_id}")

@app.route("/vehicle_pdf/<int:vehicle_id>")
def vehicle_pdf(vehicle_id):
    if "user_id" not in session:
        return redirect("/login")

    vehicle = database.get_vehicle(vehicle_id)
    deadlines = database.get_deadlines(vehicle_id)
    maintenances = database.get_maintenances(vehicle_id)
    notes = database.get_notes(vehicle_id)

    # ✅ buffer in memoria
    buffer = io.BytesIO()

    c = canvas.Canvas(buffer, pagesize=A4)

    y = 800

    # Titolo
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, f"Veicolo: {vehicle['name']}")
    y -= 20
    c.setFont("Helvetica", 12)
    c.drawString(50, y, f"Targa: {vehicle['plate']}")

    y -= 30

    # Scadenze
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Scadenze:")
    y -= 20

    c.setFont("Helvetica", 10)
    for d in deadlines:
        if d["due_date"]:
            text = f"- {d['description']} ({d['due_date']})"
        else:
            text = f"{d['description']}"

        c.drawString(60, y, text)
        y -= 15

    y -= 20

    # Manutenzioni
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Manutenzioni:")
    y -= 20

    c.setFont("Helvetica", 10)
    for m in maintenances:
        c.drawString(60, y, f"- {m['description']} - {m['cost']}€ ({m['date']})")
        y -= 15

    y -= 20

    # Note
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Note:")
    y -= 20

    c.setFont("Helvetica", 10)
    for n in notes:
        c.drawString(60, y, f"- {n['content']}")
        y -= 15

    c.save()

    # ✅ torna all'inizio del buffer
    buffer.seek(0)

    # ✅ crea response corretta
    response = make_response(buffer.read())
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = "inline; filename=scheda_veicolo.pdf"

    return response




if __name__ == "__main__":
    app.run(debug=True)