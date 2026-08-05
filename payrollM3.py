import os
import platform
import subprocess
import tempfile
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# ---------------------------------------------------------------- palette
ACCENT      = "#0F9488"
ACCENT_DIM  = "#DCF2ED"
ACCENT_DEEP = "#0B6E64"
BG          = "#F1FAF7"
CARD        = "#FFFFFF"
INK         = "#1B1D28"
MUTED       = "#828A85"
LINE        = "#DDEBE2"
GREEN       = "#2E9D6B"
GREEN_SOFT  = "#E1F4EA"
RED         = "#DA4A4A"
RED_SOFT    = "#FCEAEA"
AMBER       = "#C9891E"
AMBER_SOFT  = "#FBF1DF"

FONT       = ("Segoe UI", 10)
FONT_BOLD  = ("Segoe UI", 10, "bold")
FONT_H1    = ("Segoe UI", 16, "bold")
FONT_H3    = ("Segoe UI", 11, "bold")
FONT_SMALL = ("Segoe UI", 9)
FONT_STAT  = ("Segoe UI", 18, "bold")

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


def format_inr(n):
    """Mimics JS's Number.toLocaleString('en-IN') Indian digit grouping."""
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
    """Same PF / Professional Tax / Income Tax formulas as the web version."""
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
# No external libraries (reportlab / fpdf etc.) — this hand-writes a minimal,
# valid single-page PDF so "Save as PDF" works with nothing but the standard library.
def _pdf_escape(s):
    return s.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


def save_lines_as_pdf(filepath, title, lines):
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

    with open(filepath, "wb") as f:
        f.write(pdf)


def open_with_default_app(path):
    system = platform.system()
    try:
        if system == "Windows":
            os.startfile(path)  # noqa
        elif system == "Darwin":
            subprocess.call(["open", path])
        else:
            subprocess.call(["xdg-open", path])
        return True
    except Exception:
        return False


# ---------------------------------------------------------------- reusable widgets
class Card(tk.Frame):
    def __init__(self, parent, title=None, **kw):
        super().__init__(parent, bg=CARD, highlightbackground=LINE,
                          highlightthickness=1, bd=0, **kw)
        self.body = tk.Frame(self, bg=CARD)
        self.body.pack(fill="both", expand=True, padx=20, pady=18)
        if title:
            tk.Label(self.body, text=title, bg=CARD, fg=INK, font=FONT_H3).pack(anchor="w", pady=(0, 12))


class InlineMessage(tk.Label):
    def __init__(self, parent):
        super().__init__(parent, text="", bg=BG, fg=BG, font=FONT_SMALL, anchor="w", padx=10, pady=6)
        self._job = None

    def show(self, text, kind):
        bg, fg = (GREEN_SOFT, GREEN) if kind == "success" else (RED_SOFT, RED)
        self.configure(text=text, bg=bg, fg=fg)
        self.pack(fill="x", pady=(0, 10))
        if self._job:
            self.after_cancel(self._job)
        self._job = self.after(3500, self.hide)

    def hide(self):
        self.configure(text="", bg=BG, fg=BG)
        self.pack_forget()


class LabeledEntry(tk.Frame):
    def __init__(self, parent, label, **entry_kw):
        super().__init__(parent, bg=CARD)
        tk.Label(self, text=label, bg=CARD, fg=MUTED, font=FONT_SMALL).pack(anchor="w")
        self.var = tk.StringVar()
        self.entry = tk.Entry(self, textvariable=self.var, font=FONT, bg=BG, fg=INK,
                               relief="flat", highlightbackground=LINE, highlightthickness=1, **entry_kw)
        self.entry.pack(fill="x", ipady=5, pady=(5, 0))

    def get(self):
        return self.var.get().strip()

    def clear(self):
        self.var.set("")


class LabeledCombo(tk.Frame):
    def __init__(self, parent, label, values, default=None):
        super().__init__(parent, bg=CARD)
        tk.Label(self, text=label, bg=CARD, fg=MUTED, font=FONT_SMALL).pack(anchor="w")
        self.var = tk.StringVar()
        self.combo = ttk.Combobox(self, textvariable=self.var, values=values, state="readonly", font=FONT)
        self.combo.pack(fill="x", ipady=3, pady=(5, 0))
        if default:
            self.var.set(default)

    def get(self):
        return self.var.get().strip()


class StatCard(tk.Frame):
    def __init__(self, parent, label, value="\u20B90", accent=False):
        super().__init__(parent, bg=CARD, highlightbackground=LINE, highlightthickness=1)
        inner = tk.Frame(self, bg=CARD)
        inner.pack(fill="both", expand=True, padx=18, pady=14)
        tk.Label(inner, text=label, bg=CARD, fg=MUTED, font=FONT_BOLD).pack(anchor="w")
        self.value_lbl = tk.Label(inner, text=value, bg=CARD,
                                   fg=ACCENT_DEEP if accent else INK, font=FONT_STAT)
        self.value_lbl.pack(anchor="w", pady=(4, 0))

    def set(self, value):
        self.value_lbl.configure(text=value)


def primary_button(parent, text, command):
    return tk.Button(parent, text=text, bg=ACCENT, fg="white", font=FONT_BOLD, relief="flat",
                      padx=16, pady=8, activebackground=ACCENT_DEEP, activeforeground="white",
                      cursor="hand2", command=command)


def secondary_button(parent, text, command):
    return tk.Button(parent, text=text, bg=CARD, fg=ACCENT_DEEP, font=FONT_BOLD, relief="flat",
                      padx=16, pady=8, highlightbackground=ACCENT_DIM, highlightthickness=1,
                      activebackground=ACCENT_DIM, activeforeground=ACCENT_DEEP,
                      cursor="hand2", command=command)


# ---------------------------------------------------------------- UC-06: Run Payroll
class PayrollPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app

        head = tk.Frame(self, bg=BG)
        head.pack(fill="x", padx=32, pady=(28, 18))
        tk.Label(head, text="Run payroll processing", bg=BG, fg=INK, font=FONT_H1).pack(anchor="w")
        tk.Label(head, text="Select a pay period end date and run payroll for all employees "
                             "using their configured salary structure (sample data).",
                 bg=BG, fg=MUTED, font=FONT_SMALL, wraplength=620, justify="left").pack(anchor="w", pady=(4, 0))

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=32)

        form_card = Card(body, title="Pay period")
        form_card.pack(fill="x", pady=(0, 16))
        self.msg = InlineMessage(form_card.body)

        row = tk.Frame(form_card.body, bg=CARD)
        row.pack(fill="x")
        self.f_period = LabeledEntry(row, "Pay period end date (YYYY-MM-DD)")
        self.f_period.pack(side="left", fill="x", expand=True)

        primary_button(form_card.body, "Run Payroll", self.on_run).pack(anchor="w", pady=(14, 0))

        self.stats_row = tk.Frame(body, bg=BG)
        self.stat_net = StatCard(self.stats_row, "Total Net Payout", accent=True)
        self.stat_net.pack(side="left", fill="both", expand=True)

        results_card = Card(body, title="Payroll results")
        self.results_card = results_card

        columns = ("id", "name", "gross", "pf", "prof_tax", "income_tax", "net")
        headers = ("Employee ID", "Employee Name", "Gross Pay", "PF", "Professional Tax", "Income Tax", "Net Pay")
        self.tree = ttk.Treeview(results_card.body, columns=columns, show="headings", height=6)
        for col, h in zip(columns, headers):
            self.tree.heading(col, text=h)
            self.tree.column(col, anchor="w", width=110)
        self.tree.pack(fill="both", expand=True)

        self.empty_label = tk.Label(body, text="Run payroll to see results here.",
                                     bg=BG, fg=MUTED, font=FONT_SMALL)
        self.empty_label.pack(pady=20)

    def on_run(self):
        period = self.f_period.get()
        if not period:
            self.msg.show("Please select a pay-period ending date.", "error")
            return
        self.app.payroll_period = period
        self.app.payroll_results = [compute_payroll(e) for e in SAMPLE_EMPLOYEES]
        self.msg.show(f"Payroll run complete for {len(SAMPLE_EMPLOYEES)} employee(s).", "success")
        self.refresh()

    def refresh(self):
        results = self.app.payroll_results
        for row in self.tree.get_children():
            self.tree.delete(row)

        if not results:
            self.stats_row.pack_forget()
            self.results_card.pack_forget()
            self.empty_label.pack(pady=20)
            return

        self.empty_label.pack_forget()
        self.stats_row.pack(fill="x", pady=(0, 16))
        self.results_card.pack(fill="both", expand=True, pady=(0, 20))

        total_net = 0
        for r in results:
            total_net += r["net"]
            self.tree.insert("", "end", values=(
                r["id"], r["name"], format_inr(r["gross"]), format_inr(r["pf"]),
                format_inr(r["prof_tax"]), format_inr(r["income_tax"]), format_inr(r["net"])
            ))
        self.stat_net.set(format_inr(total_net))


class PayslipPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        self.current = None 

        head = tk.Frame(self, bg=BG)
        head.pack(fill="x", padx=32, pady=(28, 18))
        tk.Label(head, text="Generate and view payslip", bg=BG, fg=INK, font=FONT_H1).pack(anchor="w")
        tk.Label(head, text="Pick an employee and a pay period to view their payslip (sample data).",
                 bg=BG, fg=MUTED, font=FONT_SMALL, wraplength=620, justify="left").pack(anchor="w", pady=(4, 0))

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=32)

        form_card = Card(body, title="Payslip lookup")
        form_card.pack(fill="x", pady=(0, 16))
        self.msg = InlineMessage(form_card.body)

        row = tk.Frame(form_card.body, bg=CARD)
        row.pack(fill="x")
        row.grid_columnconfigure(0, weight=1, uniform="c")
        row.grid_columnconfigure(1, weight=1, uniform="c")

        names = [e["name"] for e in SAMPLE_EMPLOYEES]
        self.f_emp = LabeledCombo(row, "Employee name", names)
        self.f_emp.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.f_period = LabeledEntry(row, "Pay period (e.g. July 2026)")
        self.f_period.grid(row=0, column=1, sticky="ew", padx=(10, 0))

        primary_button(form_card.body, "View Payslip", self.on_view).pack(anchor="w", pady=(14, 0))

        self.area = tk.Frame(body, bg=BG)
        self.area.pack(fill="both", expand=True, pady=(0, 20))
        self.placeholder = tk.Label(self.area, text="Select an employee above to view their payslip.",
                                     bg=BG, fg=MUTED, font=FONT_SMALL)
        self.placeholder.pack(pady=20)

    def on_view(self):
        name = self.f_emp.get()
        period = self.f_period.get()
        if not name or not period:
            self.msg.show("Please select an employee and enter a pay period.", "error")
            return

        emp = find_employee(name=name)
        if not emp:
            self.msg.show("Employee not found.", "error")
            return

        r = compute_payroll(emp)
        total_deduct = r["pf"] + r["prof_tax"] + r["income_tax"]
        self.current = {"emp": emp, "period": period, "r": r, "total_deduct": total_deduct}
        self.render_payslip()

    def render_payslip(self):
        for w in self.area.winfo_children():
            w.destroy()

        if not self.current:
            self.placeholder = tk.Label(self.area, text="Select an employee above to view their payslip.",
                                         bg=BG, fg=MUTED, font=FONT_SMALL)
            self.placeholder.pack(pady=20)
            return

        emp, r, period = self.current["emp"], self.current["r"], self.current["period"]
        total_deduct = self.current["total_deduct"]

        card = Card(self.area)
        card.pack(fill="x")

        head_row = tk.Frame(card.body, bg=CARD)
        head_row.pack(fill="x", pady=(0, 14))
        left = tk.Frame(head_row, bg=CARD)
        left.pack(side="left")
        tk.Label(left, text=emp["name"], bg=CARD, fg=INK, font=("Segoe UI", 14, "bold")).pack(anchor="w")
        tk.Label(left, text=f'{emp["id"]} \u00b7 {emp["desig"]} \u00b7 {emp["dept"]}',
                 bg=CARD, fg=MUTED, font=FONT_SMALL).pack(anchor="w", pady=(2, 0))
        tk.Label(head_row, text=f"Period: {period}", bg=ACCENT_DIM, fg=ACCENT_DEEP,
                 font=FONT_BOLD, padx=10, pady=5).pack(side="right")

        def ps_row(label, value, deduct=False):
            row = tk.Frame(card.body, bg=CARD)
            row.pack(fill="x", pady=3)
            tk.Label(row, text=label, bg=CARD, fg=MUTED if not deduct else RED, font=FONT).pack(side="left")
            prefix = "\u2212 " if deduct else ""
            tk.Label(row, text=prefix + value, bg=CARD, fg=RED if deduct else INK, font=FONT_BOLD).pack(side="right")

        ps_row("Basic salary", format_inr(emp["basic"]))
        ps_row("HRA", format_inr(emp["hra"]))
        ps_row("Other allowances", format_inr(emp["allow"]))
        ps_row("Gross earnings", format_inr(r["gross"]))
        tk.Frame(card.body, bg=LINE, height=1).pack(fill="x", pady=8)
        ps_row("Provident fund (12%)", format_inr(r["pf"]), deduct=True)
        ps_row("Professional tax", format_inr(r["prof_tax"]), deduct=True)
        ps_row("Income tax", format_inr(r["income_tax"]), deduct=True)
        ps_row("Total deductions", format_inr(total_deduct), deduct=True)
        tk.Frame(card.body, bg=LINE, height=1).pack(fill="x", pady=8)

        total_row = tk.Frame(card.body, bg=ACCENT_DIM)
        total_row.pack(fill="x", pady=(4, 0))
        tk.Label(total_row, text="Net Pay", bg=ACCENT_DIM, fg=ACCENT_DEEP,
                 font=("Segoe UI", 12, "bold"), padx=12, pady=10).pack(side="left")
        tk.Label(total_row, text=format_inr(r["net"]), bg=ACCENT_DIM, fg=ACCENT_DEEP,
                 font=("Segoe UI", 14, "bold"), padx=12, pady=10).pack(side="right")

        btn_row = tk.Frame(self.area, bg=BG)
        btn_row.pack(fill="x", pady=(14, 0))
        secondary_button(btn_row, "Print", self.on_print).pack(side="left")
        primary_button(btn_row, "Save as PDF", self.on_save_pdf).pack(side="left", padx=(10, 0))

    def _payslip_lines(self):
        # The PDF's built-in Helvetica font can't render the ₹ glyph, so the
        # exported document uses "Rs." instead — the on-screen payslip still
        # shows ₹ normally; this substitution only affects the saved/printed PDF.
        def rs(n):
            return format_inr(n).replace("\u20B9", "Rs. ")

        emp, r, period = self.current["emp"], self.current["r"], self.current["period"]
        total_deduct = self.current["total_deduct"]
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

    def on_print(self):
        if not self.current:
            self.msg.show("View a payslip before printing.", "error")
            return
        tmp_path = os.path.join(tempfile.gettempdir(),
                                 f"payslip_{self.current['emp']['id']}.pdf")
        save_lines_as_pdf(tmp_path, f"Payslip \u2014 {self.current['emp']['name']}", self._payslip_lines())
        opened = open_with_default_app(tmp_path)
        if opened:
            self.msg.show("Payslip opened in your default PDF viewer \u2014 use its Print option.", "success")
        else:
            self.msg.show(f"Couldn't auto-open a viewer. Payslip saved to: {tmp_path}", "error")

    def on_save_pdf(self):
        if not self.current:
            self.msg.show("View a payslip before saving.", "error")
            return
        default_name = f"Payslip_{self.current['emp']['id']}_{self.current['period']}.pdf".replace(" ", "_")
        path = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile=default_name,
                                             filetypes=[("PDF file", "*.pdf")])
        if not path:
            return
        save_lines_as_pdf(path, f"Payslip \u2014 {self.current['emp']['name']}", self._payslip_lines())
        self.msg.show(f"Payslip saved to {path}", "success")


# ---------------------------------------------------------------- UC-08: Reports
class ReportsPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app

        head = tk.Frame(self, bg=BG)
        head.pack(fill="x", padx=32, pady=(28, 18))
        tk.Label(head, text="Payroll and workforce reports", bg=BG, fg=INK, font=FONT_H1).pack(anchor="w")
        tk.Label(head, text="Generate a summary report across payroll, department headcount, "
                             "leave, and attendance (sample data).",
                 bg=BG, fg=MUTED, font=FONT_SMALL, wraplength=620, justify="left").pack(anchor="w", pady=(4, 0))

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=32)

        form_card = Card(body, title="Report filters")
        form_card.pack(fill="x", pady=(0, 16))
        self.msg = InlineMessage(form_card.body)

        row = tk.Frame(form_card.body, bg=CARD)
        row.pack(fill="x")
        for c in range(3):
            row.grid_columnconfigure(c, weight=1, uniform="c")

        depts = ["All Departments"] + sorted({e["dept"] for e in SAMPLE_EMPLOYEES})
        self.f_type = LabeledCombo(row, "Report type",
                                    ["Payroll Summary", "Workforce Summary", "Leave & Attendance Summary"],
                                    default="Payroll Summary")
        self.f_type.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.f_dept = LabeledCombo(row, "Department", depts, default="All Departments")
        self.f_dept.grid(row=0, column=1, sticky="ew", padx=10)
        self.f_period = LabeledEntry(row, "Pay period (e.g. July 2026)")
        self.f_period.grid(row=0, column=2, sticky="ew", padx=(10, 0))

        primary_button(form_card.body, "Generate Report", self.on_generate).pack(anchor="w", pady=(14, 0))

        self.results_area = tk.Frame(body, bg=BG)
        self.results_area.pack(fill="both", expand=True, pady=(0, 20))
        self.placeholder = tk.Label(self.results_area, text="Set your filters and generate a report to see it here.",
                                     bg=BG, fg=MUTED, font=FONT_SMALL)
        self.placeholder.pack(pady=20)

    def on_generate(self):
        if not self.f_period.get():
            self.msg.show("Please enter a pay period.", "error")
            return
        self.msg.show("Report generated.", "success")
        self.render_report()

    def render_report(self):
        for w in self.results_area.winfo_children():
            w.destroy()

        dept_filter = self.f_dept.get()
        period = self.f_period.get()
        employees = [e for e in SAMPLE_EMPLOYEES if dept_filter == "All Departments" or e["dept"] == dept_filter]
        emp_names = {e["name"] for e in employees}

        results = [compute_payroll(e) for e in employees]
        total_gross = sum(r["gross"] for r in results)
        total_deduct = sum(r["pf"] + r["prof_tax"] + r["income_tax"] for r in results)
        total_net = sum(r["net"] for r in results)

        tk.Label(self.results_area, text=f"Report for {period} \u2014 {dept_filter}",
                 bg=BG, fg=MUTED, font=FONT_SMALL).pack(anchor="w", pady=(0, 10))

        stats_row = tk.Frame(self.results_area, bg=BG)
        stats_row.pack(fill="x", pady=(0, 16))
        for label, value in (("Total Gross Payroll", format_inr(total_gross)),
                              ("Total Deductions", format_inr(total_deduct)),
                              ("Total Net Payout", format_inr(total_net))):
            sc = StatCard(stats_row, label, value, accent=(label == "Total Net Payout"))
            sc.pack(side="left", fill="both", expand=True, padx=(0, 10))

        two_col = tk.Frame(self.results_area, bg=BG)
        two_col.pack(fill="both", expand=True)
        two_col.grid_columnconfigure(0, weight=1)
        two_col.grid_columnconfigure(1, weight=1)

        dept_card = Card(two_col, title="Department-wise employee count")
        dept_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=(0, 12))
        dept_counts = {}
        for e in employees:
            dept_counts[e["dept"]] = dept_counts.get(e["dept"], 0) + 1
        dept_tree = ttk.Treeview(dept_card.body, columns=("dept", "count"), show="headings", height=5)
        dept_tree.heading("dept", text="Department")
        dept_tree.heading("count", text="Employee count")
        dept_tree.column("dept", width=160)
        dept_tree.column("count", width=100)
        for d, c in dept_counts.items():
            dept_tree.insert("", "end", values=(d, c))
        dept_tree.pack(fill="both", expand=True)

        leave_card = Card(two_col, title="Leave summary")
        leave_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=(0, 12))
        relevant_leave = [l for l in SAMPLE_LEAVE if l["emp"] in emp_names]
        approved = len([l for l in relevant_leave if l["status"] == "Approved"])
        pending = len([l for l in relevant_leave if l["status"] == "Pending"])
        rejected = len([l for l in relevant_leave if l["status"] == "Rejected"])
        for label, val, color in (("Approved", approved, GREEN), ("Pending", pending, AMBER),
                                   ("Rejected", rejected, RED), ("Total requests", len(relevant_leave), INK)):
            r = tk.Frame(leave_card.body, bg=CARD)
            r.pack(fill="x", pady=3)
            tk.Label(r, text=label, bg=CARD, fg=MUTED, font=FONT).pack(side="left")
            tk.Label(r, text=str(val), bg=CARD, fg=color, font=FONT_BOLD).pack(side="right")

        att_card = Card(self.results_area, title="Attendance table")
        att_card.pack(fill="both", expand=True)
        relevant_att = [a for a in SAMPLE_ATTENDANCE if a["emp"] in emp_names]
        att_tree = ttk.Treeview(att_card.body, columns=("emp", "date", "status"), show="headings", height=5)
        for col, h in zip(("emp", "date", "status"), ("Employee", "Date", "Status")):
            att_tree.heading(col, text=h)
            att_tree.column(col, width=150)
        att_tree.tag_configure("PRESENT", foreground=GREEN)
        att_tree.tag_configure("ABSENT", foreground=RED)
        att_tree.tag_configure("ONLEAVE", foreground=AMBER)
        for a in relevant_att:
            tag = a["status"].replace(" ", "")
            att_tree.insert("", "end", values=(a["emp"], a["date"], a["status"]), tags=(tag,))
        att_tree.pack(fill="both", expand=True)
        if not relevant_att:
            tk.Label(att_card.body, text="No attendance records for this filter.",
                     bg=CARD, fg=MUTED, font=FONT_SMALL).pack(pady=10)


# ---------------------------------------------------------------- app shell
class PayrollApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Payroll System")
        self.geometry("1180x760")
        self.configure(bg=BG)
        self.minsize(980, 640)

        # shared, in-memory-only state (no backend / file / database)
        self.payroll_period = None
        self.payroll_results = []

        self._build_style()
        self._build_sidebar()
        self._build_main()
        self.show_page("payroll")

    def _build_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Treeview", background=CARD, fieldbackground=CARD, foreground=INK,
                         rowheight=26, font=FONT, borderwidth=0)
        style.configure("Treeview.Heading", background=BG, foreground=MUTED, font=FONT_SMALL)
        style.map("Treeview", background=[("selected", ACCENT_DIM)], foreground=[("selected", ACCENT_DEEP)])

    def _build_sidebar(self):
        self.sidebar = tk.Frame(self, bg=CARD, width=230, highlightbackground=LINE, highlightthickness=1)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        brand = tk.Frame(self.sidebar, bg=CARD)
        brand.pack(fill="x", padx=16, pady=(22, 26))
        tk.Label(brand, text="P", bg=ACCENT, fg="white", font=FONT_BOLD, width=3, height=1).pack(side="left")
        tk.Label(brand, text="Payroll System", bg=CARD, fg=INK, font=FONT_BOLD).pack(side="left", padx=10)

        self.nav_buttons = {}
        for key, label in (("PAYROLL", "Run Payroll"),
                           ("PAYSLIP", "Payslip"),
                           ("REPORTS", "Reports")):
            b = tk.Button(self.sidebar, text=label, anchor="w", bg=CARD, fg=MUTED, font=FONT,
                          relief="flat", bd=0, padx=14, pady=10, activebackground=ACCENT_DIM,
                          activeforeground=ACCENT_DEEP, cursor="hand2",
                          command=lambda k=key: self.show_page(k))
            b.pack(fill="x", padx=10, pady=1)
            self.nav_buttons[key] = b

    def _build_main(self):
        self.main = tk.Frame(self, bg=BG)
        self.main.pack(side="left", fill="both", expand=True)
        self.pages = {
            "PAYROLL": PayrollPage(self.main, self),
            "PAYSLIP": PayslipPage(self.main, self),
            "REPORTS": ReportsPage(self.main, self),
        }
        for page in self.pages.values():
            page.place(relx=0, rely=0, relwidth=1, relheight=1)

    def show_page(self, key):
        for k, b in self.nav_buttons.items():
            active = (k == key)
            b.configure(bg=ACCENT_DIM if active else CARD,
                        fg=ACCENT_DEEP if active else MUTED,
                        font=FONT_BOLD if active else FONT)
        self.pages[key].tkraise()


if __name__ == "__main__":
    app = PayrollApp()
    app.mainloop()