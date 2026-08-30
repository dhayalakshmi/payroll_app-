import io
from flask import Flask, render_template, request, redirect, url_for, send_file, session

app = Flask(__name__)
app.secret_key = "dev-secret-key-change-in-production"

# ---------------------------------------------------------------- sample / mock data
SAMPLE_EMPLOYEES = [
    {"id": "EMP001", "name": "John Mathew",   "dept": "Engineering",      "desig": "Software Engineer", "basic": 35000, "hra": 10000, "allow": 5000},
    {"id": "EMP002", "name": "Priya Sharma",  "dept": "Finance",          "desig": "Accountant",        "basic": 32000, "hra": 9000,  "allow": 4000},
    {"id": "EMP003", "name": "Arjun Mehta",   "dept": "Sales",            "desig": "Sales Executive",   "basic": 28000, "hra": 8000,  "allow": 3500},
    {"id": "EMP004", "name": "Divya Nair",    "dept": "Human Resources",  "desig": "HR Executive",      "basic": 30000, "hra": 8500,  "allow": 4000},
    {"id": "EMP005", "name": "Karthik Iyer",  "dept": "Operations",       "desig": "Operations Lead",   "basic": 40000, "hra": 12000, "allow": 6000},
]

SAMPLE_ATTENDANCE = [
    {"emp": "John Mathew",  "date": "2026-07-28", "status": "Present"},
    {"emp": "Priya Sharma", "date": "2026-07-28", "status": "Present"},
    {"emp": "Arjun Mehta",  "date": "2026-07-28", "status": "On Leave"},
    {"emp": "Divya Nair",   "date": "2026-07-28", "status": "Absent"},
    {"emp": "Karthik Iyer", "date": "2026-07-28", "status": "Present"},
]

SAMPLE_LEAVE = [
    {"emp": "Arjun Mehta",  "type": "Casual Leave", "from": "2026-07-28", "to": "2026-07-29", "status": "Approved"},
    {"emp": "Divya Nair",   "type": "Sick Leave",   "from": "2026-07-30", "to": "2026-07-30", "status": "Pending"},
    {"emp": "Priya Sharma", "type": "Earned Leave", "from": "2026-08-10", "to": "2026-08-12", "status": "Pending"},
]

# in-memory-only state (no database) — mirrors the original Tkinter app's design
STATE = {"payroll_period": None, "payroll_results": []}


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


def compute_payroll(emp):
    gross = emp["basic"] + emp["hra"] + emp["allow"]
    pf = emp["basic"] * 0.12
    prof_tax = 200 if gross > 15000 else 0
    taxable = gross - pf
    if taxable > 50000:
        income_tax = taxable * 0.10
    elif taxable > 25000:
        income_tax = taxable * 0.05
    else:
        income_tax = 0
    net = gross - pf - prof_tax - income_tax
    return {
        "id": emp["id"], "name": emp["name"], "gross": gross, "pf": pf,
        "prof_tax": prof_tax, "income_tax": income_tax, "net": net,
    }


def find_employee(name=None, emp_id=None):
    for e in SAMPLE_EMPLOYEES:
        if (name and e["name"] == name) or (emp_id and e["id"] == emp_id):
            return e
    return None


# ---------------------------------------------------------------- tiny pure-python PDF writer
def _pdf_escape(s):
    return s.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


def build_pdf_bytes(title, lines):
    y = 760
    leading = 20
    content = [f"BT /F1 16 Tf 50 {y} Td ({_pdf_escape(title)}) Tj ET"]
    y -= int(leading * 1.6)
    for line in lines:
        content.append(f"BT /F1 11 Tf 50 {y} Td ({_pdf_escape(line)}) Tj ET")
        y -= leading
    stream = "\n".join(content).encode("latin-1", "replace")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 4 0 R >> >> "
        b"/MediaBox [0 0 612 792] /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        (f"<< /Length {len(stream)} >>\nstream\n".encode("latin-1") + stream + b"\nendstream"),
    ]

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf += f"{i} 0 obj\n".encode("latin-1")
        pdf += obj
        pdf += b"\nendobj\n"
    xref_offset = len(pdf)
    pdf += f"xref\n0 {len(objects) + 1}\n".encode("latin-1")
    pdf += b"0000000000 65535 f \n"
    for off in offsets:
        pdf += f"{off:010d} 00000 n \n".encode("latin-1")
    pdf += b"trailer\n"
    pdf += f"<< /Size {len(objects) + 1} /Root 1 0 R >>\n".encode("latin-1")
    pdf += b"startxref\n"
    pdf += f"{xref_offset}\n".encode("latin-1")
    pdf += b"%%EOF"
    return bytes(pdf)


def payslip_lines(emp, r, period, total_deduct):
    # Helvetica's built-in encoding can't render ₹, so the exported PDF uses "Rs."
    def rs(n):
        return format_inr(n).replace("\u20B9", "Rs. ")

    return [
        f"Employee Name: {emp['name']}",
        f"Employee ID: {emp['id']}",
        f"Department: {emp['dept']}   Designation: {emp['desig']}",
        f"Pay Period: {period}",
        "",
        f"Basic Salary: {rs(emp['basic'])}",
        f"HRA: {rs(emp['hra'])}",
        f"Other Allowances: {rs(emp['allow'])}",
        f"Gross Earnings: {rs(r['gross'])}",
        "",
        f"Provident Fund (12%): - {rs(r['pf'])}",
        f"Professional Tax: - {rs(r['prof_tax'])}",
        f"Income Tax: - {rs(r['income_tax'])}",
        f"Total Deductions: - {rs(total_deduct)}",
        "",
        f"NET PAY: {rs(r['net'])}",
    ]


# ---------------------------------------------------------------- routes
@app.route("/")
def index():
    return redirect(url_for("payroll"))


@app.route("/payroll", methods=["GET", "POST"])
def payroll():
    message = None
    if request.method == "POST":
        period = request.form.get("period", "").strip()
        if not period:
            message = ("error", "Please select a pay-period ending date.")
        else:
            STATE["payroll_period"] = period
            STATE["payroll_results"] = [compute_payroll(e) for e in SAMPLE_EMPLOYEES]
            message = ("success", f"Payroll run complete for {len(SAMPLE_EMPLOYEES)} employee(s).")

    results = STATE["payroll_results"]
    total_net = sum(r["net"] for r in results) if results else 0
    return render_template(
        "payroll.html",
        active="payroll",
        message=message,
        results=results,
        total_net=format_inr(total_net) if results else None,
        format_inr=format_inr,
        period=STATE["payroll_period"] or "",
    )


@app.route("/payslip", methods=["GET", "POST"])
def payslip():
    message = None
    current = None

    if request.method == "POST":
        name = request.form.get("employee", "").strip()
        period = request.form.get("period", "").strip()
        if not name or not period:
            message = ("error", "Please select an employee and enter a pay period.")
        else:
            emp = find_employee(name=name)
            if not emp:
                message = ("error", "Employee not found.")
            else:
                r = compute_payroll(emp)
                total_deduct = r["pf"] + r["prof_tax"] + r["income_tax"]
                current = {"emp": emp, "period": period, "r": r, "total_deduct": total_deduct}
                # keep the last lookup around so the PDF-download route can rebuild it
                session["last_payslip"] = {"name": name, "period": period}

    return render_template(
        "payslip.html",
        active="payslip",
        message=message,
        current=current,
        employees=[e["name"] for e in SAMPLE_EMPLOYEES],
        format_inr=format_inr,
    )


@app.route("/payslip/pdf")
def payslip_pdf():
    name = request.args.get("employee", "")
    period = request.args.get("period", "")
    emp = find_employee(name=name)
    if not emp or not period:
        return redirect(url_for("payslip"))

    r = compute_payroll(emp)
    total_deduct = r["pf"] + r["prof_tax"] + r["income_tax"]
    pdf_bytes = build_pdf_bytes(f"Payslip \u2014 {emp['name']}", payslip_lines(emp, r, period, total_deduct))
    filename = f"Payslip_{emp['id']}_{period}.pdf".replace(" ", "_")
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename,
    )


@app.route("/reports", methods=["GET", "POST"])
def reports():
    message = None
    report = None

    depts = ["All Departments"] + sorted({e["dept"] for e in SAMPLE_EMPLOYEES})

    if request.method == "POST":
        report_type = request.form.get("report_type", "Payroll Summary")
        dept_filter = request.form.get("department", "All Departments")
        period = request.form.get("period", "").strip()

        if not period:
            message = ("error", "Please enter a pay period.")
        else:
            message = ("success", "Report generated.")
            employees = [e for e in SAMPLE_EMPLOYEES if dept_filter == "All Departments" or e["dept"] == dept_filter]
            emp_names = {e["name"] for e in employees}

            results = [compute_payroll(e) for e in employees]
            total_gross = sum(r["gross"] for r in results)
            total_deduct = sum(r["pf"] + r["prof_tax"] + r["income_tax"] for r in results)
            total_net = sum(r["net"] for r in results)

            dept_counts = {}
            for e in employees:
                dept_counts[e["dept"]] = dept_counts.get(e["dept"], 0) + 1

            relevant_leave = [l for l in SAMPLE_LEAVE if l["emp"] in emp_names]
            leave_summary = {
                "Approved": len([l for l in relevant_leave if l["status"] == "Approved"]),
                "Pending": len([l for l in relevant_leave if l["status"] == "Pending"]),
                "Rejected": len([l for l in relevant_leave if l["status"] == "Rejected"]),
                "Total requests": len(relevant_leave),
            }

            relevant_att = [a for a in SAMPLE_ATTENDANCE if a["emp"] in emp_names]

            report = {
                "report_type": report_type,
                "dept_filter": dept_filter,
                "period": period,
                "total_gross": format_inr(total_gross),
                "total_deduct": format_inr(total_deduct),
                "total_net": format_inr(total_net),
                "dept_counts": dept_counts,
                "leave_summary": leave_summary,
                "attendance": relevant_att,
            }

    return render_template(
        "reports.html",
        active="reports",
        message=message,
        depts=depts,
        report=report,
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=False)
