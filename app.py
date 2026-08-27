from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = "dev-secret-key-change-in-production"

# ----------------------------------------------------------------
# In-memory data store. This mirrors the Tkinter app's behavior:
# no database, no file — data lives only as long as the process runs.
# ----------------------------------------------------------------
data = {
    "employees": [],
    "attendance_log": [],
    "leave_requests": [],
    "emp_seq": 0,
    "leave_seq": 0,
}


def format_inr(n):
    """Indian digit grouping, e.g. 1234567 -> ₹12,34,567."""
    n = int(round(float(n)))
    sign = "-" if n < 0 else ""
    s = str(abs(n))
    if len(s) <= 3:
        grouped = s
    else:
        last3, rest = s[-3:], s[:-3]
        parts = []
        while len(rest) > 2:
            parts.insert(0, rest[-2:])
            rest = rest[:-2]
        if rest:
            parts.insert(0, rest)
        grouped = ",".join(parts) + "," + last3
    return f"{sign}\u20B9{grouped}"


app.jinja_env.filters["inr"] = format_inr


def get_stats():
    pending = len([r for r in data["leave_requests"] if r["status"] == "Pending"])
    return {
        "headcount": len(data["employees"]),
        "attendance": len(data["attendance_log"]),
        "pending": pending,
    }


def employee_names():
    return [f'{e["id"]} \u2014 {e["name"]}' for e in data["employees"]]


# ---------------------------------------------------------------- routes
@app.route("/")
def index():
    return redirect(url_for("employees"))


@app.route("/employees", methods=["GET"])
def employees():
    return render_template(
        "employees.html",
        active="employees",
        employees=data["employees"],
        stats=get_stats(),
    )


@app.route("/employees/add", methods=["POST"])
def add_employee():
    name = request.form.get("name", "").strip()
    dept = request.form.get("dept", "").strip()
    desig = request.form.get("desig", "").strip()
    basic = request.form.get("basic", "").strip()
    hra = request.form.get("hra", "").strip() or "0"
    allow = request.form.get("allow", "").strip() or "0"

    if not name or not dept or not desig or basic == "":
        flash("Please fill in name, department, designation, and basic salary.", "error")
        return redirect(url_for("employees"))
    try:
        basic_v, hra_v, allow_v = float(basic), float(hra), float(allow)
    except ValueError:
        flash("Salary fields must be non-negative numbers.", "error")
        return redirect(url_for("employees"))
    if basic_v < 0 or hra_v < 0 or allow_v < 0:
        flash("Salary fields must be non-negative numbers.", "error")
        return redirect(url_for("employees"))

    data["emp_seq"] += 1
    emp_id = f'EMP{data["emp_seq"]:03d}'
    data["employees"].append({
        "id": emp_id, "name": name, "dept": dept, "desig": desig,
        "basic": basic_v, "hra": hra_v, "allow": allow_v,
    })
    flash(f"{emp_id} \u2014 {name} added to the roster.", "success")
    return redirect(url_for("employees"))


@app.route("/employees/remove/<emp_id>", methods=["POST"])
def remove_employee(emp_id):
    before = len(data["employees"])
    data["employees"] = [e for e in data["employees"] if e["id"] != emp_id]
    if len(data["employees"]) < before:
        flash(f"{emp_id} removed from the roster.", "success")
    return redirect(url_for("employees"))


@app.route("/attendance", methods=["GET"])
def attendance():
    return render_template(
        "attendance.html",
        active="attendance",
        log=data["attendance_log"],
        emp_names=employee_names(),
        stats=get_stats(),
    )


@app.route("/attendance/add", methods=["POST"])
def add_attendance():
    emp = request.form.get("emp", "").strip()
    date = request.form.get("date", "").strip()
    status = request.form.get("status", "Present").strip()
    if not emp or not date:
        flash("Please select an employee and a date.", "error")
        return redirect(url_for("attendance"))
    data["attendance_log"].insert(0, {"emp": emp, "date": date, "status": status})
    flash(f"Attendance recorded for {emp}.", "success")
    return redirect(url_for("attendance"))


@app.route("/leave", methods=["GET"])
def leave():
    return render_template(
        "leave.html",
        active="leave",
        requests=data["leave_requests"],
        emp_names=employee_names(),
        stats=get_stats(),
    )


@app.route("/leave/add", methods=["POST"])
def add_leave():
    emp = request.form.get("emp", "").strip()
    ltype = request.form.get("type", "Casual Leave").strip()
    date_from = request.form.get("from", "").strip()
    date_to = request.form.get("to", "").strip()
    if not emp or not date_from or not date_to:
        flash("Please select an employee and both dates.", "error")
        return redirect(url_for("leave"))
    data["leave_seq"] += 1
    data["leave_requests"].insert(0, {
        "id": data["leave_seq"], "emp": emp, "type": ltype,
        "from": date_from, "to": date_to, "status": "Pending",
    })
    flash(f"Leave request submitted for {emp}.", "success")
    return redirect(url_for("leave"))


@app.route("/leave/decide/<int:req_id>/<decision>", methods=["POST"])
def decide_leave(req_id, decision):
    if decision not in ("Approved", "Rejected"):
        return redirect(url_for("leave"))
    for r in data["leave_requests"]:
        if r["id"] == req_id and r["status"] == "Pending":
            r["status"] = decision
            break
    return redirect(url_for("leave"))


# ---------------------------------------------------------------- entrypoint
if __name__ == "__main__":
    # host 0.0.0.0 so it's reachable from outside the container/CI agent.
    # debug=False on purpose — this is meant to run unattended (e.g. Jenkins).
    app.run(host="0.0.0.0", port=5000, debug=False)
