
import tkinter as tk
from tkinter import ttk

# ---------------------------------------------------------------- palette
ACCENT      = "#3E54D3"
ACCENT_DIM  = "#E8EAFA"
ACCENT_DEEP = "#2E3FA8"
BG          = "#EFF7F2"
CARD        = "#FFFFFF"
INK         = "#132523"
MUTED       = "#6F8B87"
LINE        = "#DCEFEC"
GREEN       = "#2E9D6B"
GREEN_SOFT  = "#E6F6EE"
RED         = "#DA4A4A"
RED_SOFT    = "#FCEAEA"
AMBER       = "#C9891E"
AMBER_SOFT  = "#FBF1DF"

FONT        = ("Segoe UI", 10)
FONT_BOLD   = ("Segoe UI", 10, "bold")
FONT_H1     = ("Segoe UI", 16, "bold")
FONT_H3     = ("Segoe UI", 11, "bold")
FONT_SMALL  = ("Segoe UI", 9)


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


def initials(name):
    words = name.strip().split()
    return "".join(w[0] for w in words[:2]).upper()


# ---------------------------------------------------------------- widgets
class Card(tk.Frame):
    """A white panel with a border, standing in for the web app's '.card'."""
    def __init__(self, parent, title=None, **kw):
        super().__init__(parent, bg=CARD, highlightbackground=LINE,
                          highlightthickness=1, bd=0, **kw)
        self.body = tk.Frame(self, bg=CARD)
        self.body.pack(fill="both", expand=True, padx=20, pady=18)
        if title:
            tk.Label(self.body, text=title, bg=CARD, fg=INK,
                      font=FONT_H3).pack(anchor="w", pady=(0, 12))


class InlineMessage(tk.Label):
    """Small colored banner used for success/error feedback, auto-clears."""
    def __init__(self, parent):
        super().__init__(parent, text="", bg=BG, fg=BG, font=FONT_SMALL,
                          anchor="w", padx=10, pady=6)
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
        self.entry = tk.Entry(self, textvariable=self.var, font=FONT,
                               bg=BG, fg=INK, relief="flat",
                               highlightbackground=LINE, highlightthickness=1, **entry_kw)
        self.entry.pack(fill="x", ipady=5, pady=(5, 0))

    def get(self):
        return self.var.get().strip()

    def clear(self):
        self.var.set("")


class LabeledCombo(tk.Frame):
    def __init__(self, parent, label, values, editable=False):
        super().__init__(parent, bg=CARD)
        tk.Label(self, text=label, bg=CARD, fg=MUTED, font=FONT_SMALL).pack(anchor="w")
        self.var = tk.StringVar()
        state = "normal" if editable else "readonly"
        self.combo = ttk.Combobox(self, textvariable=self.var, values=values,
                                   state=state, font=FONT)
        self.combo.pack(fill="x", ipady=3, pady=(5, 0))

    def get(self):
        return self.var.get().strip()

    def clear(self):
        self.var.set("")

    def set_values(self, values):
        current = self.var.get()
        self.combo["values"] = values
        self.var.set(current if current in values else "")


# ---------------------------------------------------------------- pages
class EmployeesPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app

        head = tk.Frame(self, bg=BG)
        head.pack(fill="x", padx=32, pady=(28, 18))
        tk.Label(head, text="Employee records", bg=BG, fg=INK, font=FONT_H1).pack(anchor="w")
        tk.Label(head, text="Add employees with department, designation, and salary "
                             "structure, or remove a record for someone who's left.",
                 bg=BG, fg=MUTED, font=FONT_SMALL, wraplength=560, justify="left").pack(anchor="w", pady=(4, 0))

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=32)

        form_card = Card(body, title="Add employee")
        form_card.pack(fill="x", pady=(0, 16))
        self.msg = InlineMessage(form_card.body)

        grid = tk.Frame(form_card.body, bg=CARD)
        grid.pack(fill="x")
        for c in range(3):
            grid.grid_columnconfigure(c, weight=1, uniform="col")

        self.f_name = LabeledEntry(grid, "Full name")
        self.f_name.grid(row=0, column=0, sticky="ew", padx=(0, 10), pady=6)
        self.f_dept = LabeledCombo(grid, "Department",
                                    ["Engineering", "Sales", "Finance", "Operations", "Human Resources"])
        self.f_dept.grid(row=0, column=1, sticky="ew", padx=10, pady=6)
        self.f_desig = LabeledEntry(grid, "Designation")
        self.f_desig.grid(row=0, column=2, sticky="ew", padx=(10, 0), pady=6)

        self.f_basic = LabeledEntry(grid, "BASIC SALARY(\u20B9)")
        self.f_basic.grid(row=1, column=0, sticky="ew", padx=(0, 10), pady=6)
        self.f_hra = LabeledEntry(grid, "HRA (\u20B9)")
        self.f_hra.grid(row=1, column=1, sticky="ew", padx=10, pady=6)
        self.f_allow = LabeledEntry(grid, "Other allowances (\u20B9)")
        self.f_allow.grid(row=1, column=2, sticky="ew", padx=(10, 0), pady=6)

        btn = tk.Button(form_card.body, text="+ Add employee", bg=ACCENT, fg="white",
                         font=FONT_BOLD, relief="flat", padx=16, pady=8,
                         activebackground=ACCENT_DEEP, activeforeground="white",
                         command=self.on_add)
        btn.pack(anchor="w", pady=(14, 0))

        roster_card = Card(body, title="Roster")
        roster_card.pack(fill="both", expand=True, pady=(0, 20))

        columns = ("id", "name", "desig", "dept", "basic", "hra", "allow")
        headers = ("ID", "Name", "Designation", "Department", "Basic", "HRA", "Allowances")
        self.tree = ttk.Treeview(roster_card.body, columns=columns, show="headings", height=8)
        for col, head_text in zip(columns, headers):
            self.tree.heading(col, text=head_text)
            self.tree.column(col, anchor="w", width=110)
        self.tree.pack(fill="both", expand=True)

        self.empty_label = tk.Label(roster_card.body, text="No employees yet. Add your first employee above.",
                                     bg=CARD, fg=MUTED, font=FONT_SMALL)

        remove_btn = tk.Button(roster_card.body, text="Remove selected", bg=CARD, fg=RED,
                                font=FONT_BOLD, relief="flat", padx=14, pady=6,
                                highlightbackground=RED_SOFT, highlightthickness=1,
                                activebackground=RED_SOFT, activeforeground=RED,
                                command=self.on_remove)
        remove_btn.pack(anchor="w", pady=(10, 0))

    def on_add(self):
        name = self.f_name.get()
        dept = self.f_dept.get()
        desig = self.f_desig.get()
        basic = self.f_basic.get()
        hra = self.f_hra.get() or "0"
        allow = self.f_allow.get() or "0"

        if not name or not dept or not desig or basic == "":
            self.msg.show("Please fill in name, department, designation, and basic salary.", "error")
            return
        try:
            basic_v, hra_v, allow_v = float(basic), float(hra), float(allow)
        except ValueError:
            self.msg.show("Salary fields must be non-negative numbers.", "error")
            return
        if basic_v < 0 or hra_v < 0 or allow_v < 0:
            self.msg.show("Salary fields must be non-negative numbers.", "error")
            return

        emp_id = self.app.add_employee(name, dept, desig, basic_v, hra_v, allow_v)
        for f in (self.f_name, self.f_desig, self.f_basic, self.f_hra, self.f_allow):
            f.clear()
        self.f_dept.clear()
        self.msg.show(f"{emp_id} \u2014 {name} added to the roster.", "success")

    def on_remove(self):
        sel = self.tree.selection()
        if not sel:
            return
        emp_id = self.tree.item(sel[0], "values")[0]
        self.app.remove_employee(emp_id)

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for e in self.app.employees:
            self.tree.insert("", "end", values=(
                e["id"], e["name"], e["desig"], e["dept"],
                format_inr(e["basic"]), format_inr(e["hra"]), format_inr(e["allow"])
            ))
        if self.app.employees:
            self.empty_label.pack_forget()
        else:
            self.empty_label.pack(pady=10)


class AttendancePage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app

        head = tk.Frame(self, bg=BG)
        head.pack(fill="x", padx=32, pady=(28, 18))
        tk.Label(head, text="Daily attendance", bg=BG, fg=INK, font=FONT_H1).pack(anchor="w")
        tk.Label(head, text="Record the status \u2014 Present, Absent, or On Leave \u2014 "
                             "for an employee on a given date.",
                 bg=BG, fg=MUTED, font=FONT_SMALL, wraplength=560, justify="left").pack(anchor="w", pady=(4, 0))

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=32)

        form_card = Card(body, title="Record attendance")
        form_card.pack(fill="x", pady=(0, 16))
        self.msg = InlineMessage(form_card.body)

        grid = tk.Frame(form_card.body, bg=CARD)
        grid.pack(fill="x")
        for c in range(3):
            grid.grid_columnconfigure(c, weight=1, uniform="col")

        self.f_emp = LabeledCombo(grid, "Employee", [])
        self.f_emp.grid(row=0, column=0, sticky="ew", padx=(0, 10), pady=6)
        self.f_date = LabeledEntry(grid, "Date (YYYY-MM-DD)")
        self.f_date.grid(row=0, column=1, sticky="ew", padx=10, pady=6)
        self.f_status = LabeledCombo(grid, "Status", ["Present", "Absent", "On Leave"])
        self.f_status.var.set("Present")
        self.f_status.grid(row=0, column=2, sticky="ew", padx=(10, 0), pady=6)

        btn = tk.Button(form_card.body, text="Record attendance", bg=ACCENT, fg="white",
                         font=FONT_BOLD, relief="flat", padx=16, pady=8,
                         activebackground=ACCENT_DEEP, activeforeground="white",
                         command=self.on_record)
        btn.pack(anchor="w", pady=(14, 0))

        log_card = Card(body, title="Attendance log")
        log_card.pack(fill="both", expand=True, pady=(0, 20))

        columns = ("emp", "date", "status")
        self.tree = ttk.Treeview(log_card.body, columns=columns, show="headings", height=8)
        for col, head_text in zip(columns, ("Employee", "Date", "Status")):
            self.tree.heading(col, text=head_text)
            self.tree.column(col, anchor="w", width=150)
        self.tree.tag_configure("Present", foreground=GREEN)
        self.tree.tag_configure("Absent", foreground=RED)
        self.tree.tag_configure("OnLeave", foreground=AMBER)
        self.tree.pack(fill="both", expand=True)

        self.empty_label = tk.Label(log_card.body, text="No attendance recorded yet.",
                                     bg=CARD, fg=MUTED, font=FONT_SMALL)

    def on_record(self):
        emp = self.f_emp.get()
        date = self.f_date.get()
        status = self.f_status.get() or "Present"
        if not emp or not date:
            self.msg.show("Please select an employee and a date.", "error")
            return
        self.app.record_attendance(emp, date, status)
        self.msg.show(f"Attendance recorded for {emp}.", "success")

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for a in self.app.attendance_log:
            tag = a["status"].replace(" ", "")
            self.tree.insert("", "end", values=(a["emp"], a["date"], a["status"]), tags=(tag,))
        if self.app.attendance_log:
            self.empty_label.pack_forget()
        else:
            self.empty_label.pack(pady=10)

    def sync_employee_list(self, names):
        self.f_emp.set_values(names)


class LeavePage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app

        head = tk.Frame(self, bg=BG)
        head.pack(fill="x", padx=32, pady=(28, 18))
        tk.Label(head, text="Leave requests", bg=BG, fg=INK, font=FONT_H1).pack(anchor="w")
        tk.Label(head, text="Submit a leave request with type and date range, "
                             "then review and decide on pending requests.",
                 bg=BG, fg=MUTED, font=FONT_SMALL, wraplength=560, justify="left").pack(anchor="w", pady=(4, 0))

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=32)

        form_card = Card(body, title="Submit leave request")
        form_card.pack(fill="x", pady=(0, 16))
        self.msg = InlineMessage(form_card.body)

        grid = tk.Frame(form_card.body, bg=CARD)
        grid.pack(fill="x")
        for c in range(4):
            grid.grid_columnconfigure(c, weight=1, uniform="col")

        self.f_emp = LabeledCombo(grid, "Employee", [])
        self.f_emp.grid(row=0, column=0, sticky="ew", padx=(0, 8), pady=6)
        self.f_type = LabeledCombo(grid, "Leave type", ["Casual Leave", "Sick Leave", "Earned Leave"])
        self.f_type.var.set("Casual Leave")
        self.f_type.grid(row=0, column=1, sticky="ew", padx=8, pady=6)
        self.f_from = LabeledEntry(grid, "From date (DD-MM-YYYY)")
        self.f_from.grid(row=0, column=2, sticky="ew", padx=8, pady=6)
        self.f_to = LabeledEntry(grid, "To date (DD-MM-YYYY)")
        self.f_to.grid(row=0, column=3, sticky="ew", padx=(8, 0), pady=6)

        btn = tk.Button(form_card.body, text="Submit request", bg=ACCENT, fg="white",
                         font=FONT_BOLD, relief="flat", padx=16, pady=8,
                         activebackground=ACCENT_DEEP, activeforeground="white",
                         command=self.on_submit)
        btn.pack(anchor="w", pady=(14, 0))

        review_card = Card(body, title="Review requests")
        review_card.pack(fill="both", expand=True, pady=(0, 20))

        columns = ("who", "type", "from", "to", "status")
        self.tree = ttk.Treeview(review_card.body, columns=columns, show="headings", height=8)
        for col, head_text in zip(columns, ("Employee", "Leave type", "From", "To", "Status")):
            self.tree.heading(col, text=head_text)
            self.tree.column(col, anchor="w", width=130)
        self.tree.tag_configure("Pending", foreground=AMBER)
        self.tree.tag_configure("Approved", foreground=GREEN)
        self.tree.tag_configure("Rejected", foreground=RED)
        self.tree.pack(fill="both", expand=True)

        self.empty_label = tk.Label(review_card.body, text="No leave requests yet.",
                                     bg=CARD, fg=MUTED, font=FONT_SMALL)

        action_row = tk.Frame(review_card.body, bg=CARD)
        action_row.pack(fill="x", pady=(10, 0))
        tk.Button(action_row, text="Approve selected", bg=GREEN, fg="white", font=FONT_BOLD,
                  relief="flat", padx=14, pady=6, command=lambda: self.on_decide("Approved")).pack(side="left")
        tk.Button(action_row, text="Reject selected", bg=RED, fg="white", font=FONT_BOLD,
                  relief="flat", padx=14, pady=6, command=lambda: self.on_decide("Rejected")).pack(side="left", padx=(8, 0))

    def on_submit(self):
        emp = self.f_emp.get()
        ltype = self.f_type.get() or "Casual Leave"
        date_from = self.f_from.get()
        date_to = self.f_to.get()
        if not emp or not date_from or not date_to:
            self.msg.show("Please select an employee and both dates.", "error")
            return
        self.app.submit_leave(emp, ltype, date_from, date_to)
        self.f_from.clear()
        self.f_to.clear()
        self.msg.show(f"Leave request submitted for {emp}.", "success")

    def on_decide(self, decision):
        sel = self.tree.selection()
        if not sel:
            return
        idx = self.tree.index(sel[0])
        req = self.app.leave_requests[idx]
        if req["status"] == "Pending":
            self.app.decide_leave(req["id"], decision)

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for r in self.app.leave_requests:
            self.tree.insert("", "end", values=(r["emp"], r["type"], r["from"], r["to"], r["status"]),
                              tags=(r["status"],))
        if self.app.leave_requests:
            self.empty_label.pack_forget()
        else:
            self.empty_label.pack(pady=10)

    def sync_employee_list(self, names):
        self.f_emp.set_values(names)


# ---------------------------------------------------------------- app shell
class PayrollApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Payroll System")
        self.geometry("1180x720")
        self.configure(bg=BG)
        self.minsize(980, 620)

        # in-memory data only — no backend, no file, no database
        self.employees = []
        self.attendance_log = []
        self.leave_requests = []
        self.emp_seq = 0
        self.leave_seq = 0

        self._build_style()
        self._build_sidebar()
        self._build_main()
        self.show_page("employees")
        self.refresh_all()

    def _build_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Treeview", background=CARD, fieldbackground=CARD,
                         foreground=INK, rowheight=26, font=FONT, borderwidth=0)
        style.configure("Treeview.Heading", background=BG, foreground=MUTED,
                         font=FONT_SMALL)
        style.map("Treeview", background=[("selected", ACCENT_DIM)],
                  foreground=[("selected", ACCENT_DEEP)])

    def _build_sidebar(self):
        self.sidebar = tk.Frame(self, bg=CARD, width=230,
                                 highlightbackground=LINE, highlightthickness=1)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        brand = tk.Frame(self.sidebar, bg=CARD)
        brand.pack(fill="x", padx=16, pady=(22, 26))
        tk.Label(brand, text="P", bg=ACCENT, fg="white", font=FONT_BOLD,
                 width=3, height=1).pack(side="left")
        tk.Label(brand, text="Payroll System", bg=CARD, fg=INK,
                 font=FONT_BOLD).pack(side="left", padx=10)

        self.nav_buttons = {}
        for key, label in (("employees", "Employees"),
                            ("attendance", "Attendance"),
                            ("leave", "Leave Requests")):
            b = tk.Button(self.sidebar, text=label, anchor="w", bg=CARD, fg=MUTED,
                          font=FONT, relief="flat", bd=0, padx=14, pady=10,
                          activebackground=ACCENT_DIM, activeforeground=ACCENT_DEEP,
                          command=lambda k=key: self.show_page(k))
            b.pack(fill="x", padx=10, pady=1)
            self.nav_buttons[key] = b

        tk.Frame(self.sidebar, bg=CARD).pack(fill="both", expand=True)  # spacer

        stats = tk.Frame(self.sidebar, bg=CARD, highlightbackground=LINE,
                          highlightthickness=0)
        stats.pack(fill="x", padx=16, pady=18)
        tk.Frame(stats, bg=LINE, height=1).pack(fill="x", pady=(0, 10))
        self.stat_headcount = self._stat_row(stats, "Headcount")
        self.stat_attendance = self._stat_row(stats, "Attendance logged")
        self.stat_pending = self._stat_row(stats, "Leave pending")

    def _stat_row(self, parent, label):
        row = tk.Frame(parent, bg=CARD)
        row.pack(fill="x", pady=3)
        tk.Label(row, text=label, bg=CARD, fg=MUTED, font=FONT_SMALL).pack(side="left")
        val = tk.Label(row, text="0", bg=CARD, fg=INK, font=FONT_SMALL)
        val.configure(font=("Segoe UI", 9, "bold"))
        val.pack(side="right")
        return val

    def _build_main(self):
        self.main = tk.Frame(self, bg=BG)
        self.main.pack(side="left", fill="both", expand=True)
        self.pages = {
            "employees": EmployeesPage(self.main, self),
            "attendance": AttendancePage(self.main, self),
            "leave": LeavePage(self.main, self),
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

    # ---------------- data operations (same behavior as the web version) ----------------
    def add_employee(self, name, dept, desig, basic, hra, allow):
        self.emp_seq += 1
        emp_id = f"EMP{self.emp_seq:03d}"
        self.employees.append({
            "id": emp_id, "name": name, "dept": dept, "desig": desig,
            "basic": basic, "hra": hra, "allow": allow
        })
        self.refresh_all()
        return emp_id

    def remove_employee(self, emp_id):
        self.employees = [e for e in self.employees if e["id"] != emp_id]
        self.refresh_all()

    def record_attendance(self, emp_name, date, status):
        self.attendance_log.insert(0, {"emp": emp_name, "date": date, "status": status})
        self.refresh_all()

    def submit_leave(self, emp_name, ltype, date_from, date_to):
        self.leave_seq += 1
        self.leave_requests.insert(0, {
            "id": self.leave_seq, "emp": emp_name, "type": ltype,
            "from": date_from, "to": date_to, "status": "Pending"
        })
        self.refresh_all()

    def decide_leave(self, req_id, decision):
        for r in self.leave_requests:
            if r["id"] == req_id and r["status"] == "Pending":
                r["status"] = decision
                break
        self.refresh_all()

    def refresh_all(self):
        names = [f'{e["id"]} \u2014 {e["name"]}' for e in self.employees]
        self.pages["attendance"].sync_employee_list(names)
        self.pages["leave"].sync_employee_list(names)
        for page in self.pages.values():
            page.refresh()
        self.stat_headcount.configure(text=str(len(self.employees)))
        self.stat_attendance.configure(text=str(len(self.attendance_log)))
        pending = len([r for r in self.leave_requests if r["status"] == "Pending"])
        self.stat_pending.configure(text=str(pending))

if __name__ == "__main__":
    import sys

    if "--test" in sys.argv:
        try:
            run_tests()
            print("\nALL TESTS PASSED")
            print("JENKINS RESULT: SUCCESS")
            sys.exit(0)

        except Exception as e:
            print("\nTEST FAILED")
            print("ERROR:", e)
            print("JENKINS RESULT: FAILURE")
            sys.exit(1)

    # Normal VS Code mode
    app = PayrollApp()
    app.mainloop()
