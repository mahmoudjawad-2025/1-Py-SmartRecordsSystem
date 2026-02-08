import customtkinter as ctk
from tkinter import ttk, filedialog, messagebox
import db
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

# Smart Records System
# GUI application for managing customers and their records.
# - Uses customtkinter for modern-styled widgets
# - Persists data via functions in the `db` module
# - Can export a summary PDF report using ReportLab

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    """Main application window.

    Holds UI state (current user, selected customer) and
    manages switching between login and dashboard screens.
    """
    def __init__(self):
        super().__init__()
        self.title("Smart Records System")
        self.geometry("1400x700")
        self.resizable(True, True)

        try:
            db.test_db()
        except Exception as e:
            print("DB Error:", e)

        self.user_id = None
        self.username = ""

        self.selected_customer_id = None

        self.root_frame = ctk.CTkFrame(self)
        self.root_frame.pack(fill="both", expand=True)

        self.show_login()

    def clear(self):
        # Remove all widgets from the main root frame.
        for w in self.root_frame.winfo_children():
            w.destroy()

    # ---------------- LOGIN ----------------
    def show_login(self):
        """Render the login / create-account form in the root frame."""
        self.clear()

        box = ctk.CTkFrame(self.root_frame, corner_radius=15)
        box.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(box, text="Smart Records System", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(20, 8), padx=25)
        ctk.CTkLabel(box, text="Login", font=ctk.CTkFont(size=14)).pack(pady=(0, 10))

        self.e_user = ctk.CTkEntry(box, placeholder_text="Username", width=280)
        self.e_user.pack(pady=7, padx=25)

        self.e_pass = ctk.CTkEntry(box, placeholder_text="Password", show="*", width=280)
        self.e_pass.pack(pady=7, padx=25)

        self.msg = ctk.CTkLabel(box, text="", text_color="tomato")
        self.msg.pack(pady=(5, 5))

        btns = ctk.CTkFrame(box, fg_color="transparent")
        btns.pack(pady=(10, 20))

        ctk.CTkButton(btns, text="Login", width=130, command=self.do_login).grid(row=0, column=0, padx=6)
        ctk.CTkButton(btns, text="Create Account", width=130, command=self.do_signup).grid(row=0, column=1, padx=6)

    def do_signup(self):
        """Create a new user account using `db.create_user`.

        Displays feedback in `self.msg` for success or failure.
        """
        u = self.e_user.get().strip()
        p = self.e_pass.get().strip()
        if u == "" or p == "":
            self.msg.configure(text="Fill username and password!")
            return
        ok = db.create_user(u, p)
        if ok:
            self.msg.configure(text="Account created ✅", text_color="green")
        else:
            self.msg.configure(text="Username exists!", text_color="tomato")

    def do_login(self):
        """Authenticate the user via `db.login_user` and open dashboard on success."""
        u = self.e_user.get().strip()
        p = self.e_pass.get().strip()
        if u == "" or p == "":
            self.msg.configure(text="Fill username and password!")
            return

        uid = db.login_user(u, p)
        if uid is None:
            self.msg.configure(text="Wrong login!", text_color="tomato")
        else:
            self.user_id = uid
            self.username = u
            self.show_dashboard()

    # ---------------- DASHBOARD ----------------
    def show_dashboard(self):
        """Build the dashboard UI showing customers and records."""
        self.clear()

        top = ctk.CTkFrame(self.root_frame)
        top.pack(fill="x", padx=15, pady=15)

        ctk.CTkLabel(top, text=f"Smart Records System - {self.username}",
                    font=ctk.CTkFont(size=18, weight="bold")).pack(side="left", padx=10)

        ctk.CTkButton(top, text="Export Report (PDF)", command=self.open_report_window).pack(side="right", padx=10)
        ctk.CTkButton(top, text="Logout", fg_color="tomato", command=self.show_login).pack(side="right", padx=10)

        body = ctk.CTkFrame(self.root_frame)
        body.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # LEFT: Customers
        left = ctk.CTkFrame(body)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10), pady=10)

        ctk.CTkLabel(left, text="Customers", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=10, pady=(10, 0))

        cform = ctk.CTkFrame(left)
        cform.pack(fill="x", padx=10, pady=10)

        self.c_name = ctk.CTkEntry(cform, placeholder_text="Customer Name")
        self.c_name.grid(row=0, column=0, padx=6, pady=6, sticky="ew")
        self.c_phone = ctk.CTkEntry(cform, placeholder_text="Phone")
        self.c_phone.grid(row=0, column=1, padx=6, pady=6, sticky="ew")

        ctk.CTkButton(cform, text="Add", width=80, command=self.add_customer).grid(row=0, column=2, padx=6, pady=6)
        ctk.CTkButton(cform, text="Update", width=80, command=self.update_customer).grid(row=0, column=3, padx=6, pady=6)
        ctk.CTkButton(cform, text="Delete", width=80, fg_color="tomato", command=self.delete_customer).grid(row=0, column=4, padx=6, pady=6)

        cform.grid_columnconfigure(0, weight=2)
        cform.grid_columnconfigure(1, weight=1)

        self.customers_table = ttk.Treeview(left, columns=("name", "phone", "created"), show="headings")
        self.customers_table.heading("name", text="Name")
        self.customers_table.heading("phone", text="Phone")
        self.customers_table.heading("created", text="Created")
        self.customers_table.column("name", width=220)
        self.customers_table.column("phone", width=120)
        self.customers_table.column("created", width=160)
        self.customers_table.pack(fill="both", expand=True, padx=10, pady=(0,10))

        self.customers_table.bind("<<TreeviewSelect>>", self.on_customer_select)

        # RIGHT: Records
        right = ctk.CTkFrame(body)
        right.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)

        ctk.CTkLabel(right, text="Records (for selected customer)", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=10, pady=(10, 0))

        rform = ctk.CTkFrame(right)
        rform.pack(fill="x", padx=10, pady=10)

        self.r_title = ctk.CTkEntry(rform, placeholder_text="Record Title")
        self.r_title.grid(row=0, column=0, padx=6, pady=6, sticky="ew")
        self.r_details = ctk.CTkEntry(rform, placeholder_text="Details")
        self.r_details.grid(row=0, column=1, padx=6, pady=6, sticky="ew")

        ctk.CTkButton(rform, text="Add", width=80, command=self.add_record).grid(row=0, column=2, padx=6, pady=6)
        ctk.CTkButton(rform, text="Update", width=80, command=self.update_record).grid(row=0, column=3, padx=6, pady=6)
        ctk.CTkButton(rform, text="Delete", width=80, fg_color="tomato", command=self.delete_record).grid(row=0, column=4, padx=6, pady=6)

        rform.grid_columnconfigure(0, weight=2)
        rform.grid_columnconfigure(1, weight=3)

        self.records_table = ttk.Treeview(right, columns=("title", "details", "created"), show="headings")
        self.records_table.heading("title", text="Title")
        self.records_table.heading("details", text="Details")
        self.records_table.heading("created", text="Created")
        self.records_table.column("title", width=200)
        self.records_table.column("details", width=260)
        self.records_table.column("created", width=160)
        self.records_table.pack(fill="both", expand=True, padx=10, pady=(0,10))

        self.records_table.bind("<<TreeviewSelect>>", self.on_record_select)

        self.refresh_customers()
        self.refresh_records()

        self.status = ctk.CTkLabel(self.root_frame, text="", text_color="tomato")
        self.status.pack(pady=(0, 10))

    def refresh_customers(self):
        """Reload the customers list from the database into the treeview."""
        for i in self.customers_table.get_children():
            self.customers_table.delete(i)

        rows = db.get_customers(self.user_id)
        for r in rows:
            cid, name, phone, created = r
            self.customers_table.insert("", "end", iid=str(cid), values=(name, phone, str(created)))

    def on_customer_select(self, _e=None):
        """Handle selection of a customer in the customers treeview.

        Loads the selected customer's details into the form and
        refreshes the records list for that customer.
        """
        sel = self.customers_table.selection()
        if not sel:
            return
        self.selected_customer_id = int(sel[0])
        vals = self.customers_table.item(sel[0])["values"]
        self.c_name.delete(0, "end")
        self.c_phone.delete(0, "end")
        self.c_name.insert(0, vals[0])
        self.c_phone.insert(0, vals[1])
        self.refresh_records()

    def add_customer(self):
        """Validate and add a new customer to the DB, then refresh list."""
        name = self.c_name.get().strip()
        phone = self.c_phone.get().strip()
        if name == "":
            self.status.configure(text="Enter customer name!")
            return
        db.add_customer(self.user_id, name, phone)
        self.c_name.delete(0, "end")
        self.c_phone.delete(0, "end")
        self.status.configure(text="Customer added ✅", text_color="green")
        self.refresh_customers()

    def update_customer(self):
        """Update the selected customer's info in the DB."""
        sel = self.customers_table.selection()
        if not sel:
            self.status.configure(text="Select a customer first!", text_color="tomato")
            return
        cid = int(sel[0])
        name = self.c_name.get().strip()
        phone = self.c_phone.get().strip()
        if name == "":
            return
        db.update_customer(cid, name, phone)
        self.status.configure(text="Customer updated ✅", text_color="green")
        self.refresh_customers()

    def delete_customer(self):
        """Delete the selected customer and clear related UI state."""
        sel = self.customers_table.selection()
        if not sel:
            self.status.configure(text="Select a customer first!", text_color="tomato")
            return
        cid = int(sel[0])
        db.delete_customer(cid)
        self.selected_customer_id = None
        self.c_name.delete(0, "end")
        self.c_phone.delete(0, "end")
        self.status.configure(text="Customer deleted ✅", text_color="green")
        self.refresh_customers()
        self.refresh_records()

    # ------------ Records actions ------------
    def refresh_records(self):
        """Reload records for the currently selected customer into the treeview."""
        for i in self.records_table.get_children():
            self.records_table.delete(i)

        if self.selected_customer_id is None:
            return

        rows = db.get_records(self.selected_customer_id)
        for r in rows:
            rid, title, details, created = r
            self.records_table.insert("", "end", iid=str(rid), values=(title, details, str(created)))

    def on_record_select(self, _e=None):
        """Populate the record form when a record is selected."""
        sel = self.records_table.selection()
        if not sel:
            return
        vals = self.records_table.item(sel[0])["values"]
        self.r_title.delete(0, "end")
        self.r_details.delete(0, "end")
        self.r_title.insert(0, vals[0])
        self.r_details.insert(0, vals[1])

    def add_record(self):
        """Add a new record for the selected customer."""
        if self.selected_customer_id is None:
            self.status.configure(text="Select a customer first!", text_color="tomato")
            return
        title = self.r_title.get().strip()
        details = self.r_details.get().strip()
        if title == "":
            return
        db.add_record(self.selected_customer_id, title, details)
        self.r_title.delete(0, "end")
        self.r_details.delete(0, "end")
        self.status.configure(text="Record added ✅", text_color="green")
        self.refresh_records()

    def update_record(self):
        """Update the selected record in the database."""
        sel = self.records_table.selection()
        if not sel:
            self.status.configure(text="Select a record first!", text_color="tomato")
            return
        rid = int(sel[0])
        title = self.r_title.get().strip()
        details = self.r_details.get().strip()
        if title == "":
            return
        db.update_record(rid, title, details)
        self.status.configure(text="Record updated ✅", text_color="green")
        self.refresh_records()

    def delete_record(self):
        """Delete the selected record and refresh the list."""
        sel = self.records_table.selection()
        if not sel:
            self.status.configure(text="Select a record first!", text_color="tomato")
            return
        rid = int(sel[0])
        db.delete_record(rid)
        self.r_title.delete(0, "end")
        self.r_details.delete(0, "end")
        self.status.configure(text="Record deleted ✅", text_color="green")
        self.refresh_records()

    # ------------ Report ------------
    def open_report_window(self):
        """Simple export window: choose Selected/All then Print or Cancel."""

        win = ctk.CTkToplevel(self)
        win.title("Export Report")
        win.geometry("420x260")
        win.resizable(False, False)
        win.grab_set()
        win.focus()

        title = ctk.CTkLabel(win, text="Export Report", font=ctk.CTkFont(size=18, weight="bold"))
        title.pack(pady=(15, 5))

        subtitle = ctk.CTkLabel(win, text="Choose what to include in the PDF:")
        subtitle.pack(pady=(0, 10))

        mode_var = ctk.StringVar(value="selected")
        if self.selected_customer_id is None:
            mode_var.set("all")

        box = ctk.CTkFrame(win)
        box.pack(fill="x", padx=20, pady=5)

        ctk.CTkRadioButton(box, text="Selected Customer", variable=mode_var, value="selected").pack(anchor="w", padx=15, pady=8)
        ctk.CTkRadioButton(box, text="All Customers", variable=mode_var, value="all").pack(anchor="w", padx=15, pady=8)

        hint = ctk.CTkLabel(win, text="", text_color="tomato")
        hint.pack(pady=(8, 0))

        btns = ctk.CTkFrame(win, fg_color="transparent")
        btns.pack(fill="x", padx=20, pady=15)

        def do_cancel():
            win.destroy()

        def do_print():
            mode = mode_var.get()

            if mode == "selected" and self.selected_customer_id is None:
                hint.configure(text="No customer selected. Select one or choose 'All'.")
                return

            win.destroy()
            self.export_report(mode)  # this must exist

        cancel_btn = ctk.CTkButton(btns, text="Cancel", fg_color="tomato", command=do_cancel, width=120)
        cancel_btn.pack(side="right", padx=5)

        print_btn = ctk.CTkButton(btns, text="Print (Export PDF)", command=do_print, width=180)
        print_btn.pack(side="right", padx=5)

    def export_report(self, mode="selected"):
        """Generate a PDF report. mode = 'selected' or 'all'."""

        filepath = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            title="Save Report As",
            initialfile="smart_report.pdf"
        )
        if not filepath:
            return

        try:
            summary = db.report_summary(self.user_id)

            # supports dict OR tuple
            if isinstance(summary, tuple) and len(summary) == 3:
                total_customers, total_records, top_customers = summary
            else:
                total_customers = summary.get("total_customers", 0)
                total_records = summary.get("total_records", 0)
                top_customers = summary.get("top_customers", [])

            c = canvas.Canvas(filepath, pagesize=A4)
            width, height = A4
            x = 50
            y = height - 50

            def new_page():
                nonlocal y
                c.showPage()
                y = height - 50

            def need_space(pixels=20):
                nonlocal y
                if y - pixels < 60:
                    new_page()

            def text_line(s, size=11, bold=False, dy=14, indent=0):
                nonlocal y
                need_space(dy + 5)
                c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
                c.drawString(x + indent, y, str(s))
                y -= dy

            text_line("Smart Records System - Report", size=16, bold=True, dy=22)
            text_line(f"Username: {self.username}", size=11)
            text_line(f"Total Customers: {total_customers}", size=11)
            text_line(f"Total Records: {total_records}", size=11)
            y -= 6

            text_line("Top 5 Customers by Records:", bold=True)
            if not top_customers:
                text_line("- No data", indent=10)
            else:
                i = 1
                for name, cnt in top_customers:
                    text_line(f"{i}) {name} - {cnt} records", indent=10)
                    i += 1

            y -= 10
            text_line("Details:", bold=True, dy=18)

            def table_header():
                nonlocal y
                need_space(30)
                c.setFont("Helvetica-Bold", 10)
                c.drawString(x + 5, y, "Title")
                c.drawString(x + 220, y, "Details")
                c.drawString(x + 420, y, "Date")
                y -= 10
                c.line(x, y, width - x, y)
                y -= 14

            def cut(s, n):
                s = "" if s is None else str(s)
                return s[:n]

            def print_customer_block(cid, cname, phone):
                nonlocal y
                need_space(40)
                c.setFont("Helvetica-Bold", 12)
                c.drawString(x, y, f"Customer: {cname}   Phone: {phone}")
                y -= 16

                table_header()

                rows = db.get_records(cid)
                c.setFont("Helvetica", 9)

                if not rows:
                    text_line("- No records", indent=10, size=10)
                    y -= 6
                    return

                for r in rows:
                    # r = (id, title, details, created_at)
                    need_space(16)
                    c.setFont("Helvetica", 9)
                    c.drawString(x + 5, y, cut(r[1], 30))
                    c.drawString(x + 220, y, cut(r[2], 30))
                    c.drawString(x + 420, y, cut(r[3], 19))
                    y -= 12

                y -= 12

            if mode == "all":
                customers = db.get_customers(self.user_id)
                if not customers:
                    text_line("No customers found.")
                else:
                    for cu in customers:
                        cid, cname, phone, created = cu
                        print_customer_block(cid, cname, phone if phone else "")
            else:
                # selected
                cid = self.selected_customer_id
                # get name/phone from UI table (simple)
                sel = self.customers_table.selection()
                if sel:
                    vals = self.customers_table.item(sel[0])["values"]  # (name, phone, created)
                    cname = vals[0]
                    phone = vals[1]
                else:
                    cname = "Selected Customer"
                    phone = ""
                print_customer_block(cid, cname, phone)

            c.save()
            messagebox.showinfo("Report Exported", f"Report saved to:\n{filepath}")

        except PermissionError:
            messagebox.showerror("Permission Error", "Close the PDF file and try again.")
        except Exception as e:
            messagebox.showerror("Error", str(e))
            print("PDF Error:", e)



if __name__ == "__main__":
    App().mainloop()
