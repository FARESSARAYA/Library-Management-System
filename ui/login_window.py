"""login_window.py — نافذة تسجيل الدخول"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
from tkinter import messagebox
from theme_tk import TK, apply_theme, style_button, style_entry, style_label, make_card
from license import LicenseManager, _get_machine_id
from config import TRIAL_DAYS

class LoginWindow:
    def __init__(self, root, on_success):
        self.root = root
        self.on_success = on_success
        self.root.title("تسجيل الدخول - مكتبة الفراشات")
        self.root.geometry("500x560")
        self.root.configure(bg=TK.BG)
        self.center_window(500, 560)
        self.create_widgets()

    def center_window(self, width, height):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def create_widgets(self):
        main_frame = tk.Frame(self.root, bg=TK.BG)
        main_frame.pack(expand=True, fill='both')

        welcome_frame = tk.Frame(main_frame, bg=TK.CARD, relief='ridge', bd=2)
        welcome_frame.pack(expand=True, padx=35, pady=25, fill='both')

        tk.Label(welcome_frame, text="🦋", font=('Arial', 48), bg=TK.CARD).pack(pady=(10,2))
        tk.Label(welcome_frame, text="مرحباً بك في", font=('Arial', 18, 'bold'), bg=TK.CARD, fg=TK.TEXT).pack()
        tk.Label(welcome_frame, text="مكتبة الفراشات", font=('Arial', 24, 'bold'), bg=TK.CARD, fg=TK.ACCENT2).pack()
        tk.Label(welcome_frame, text="نظام البيع وإدارة المخزون", font=('Arial', 12), bg=TK.CARD, fg=TK.TEXT_SUB).pack(pady=4)

        if LicenseManager.is_activated():
            cname = LicenseManager.customer_name()
            banner_text = f"✅ مرخّص لـ: {cname}"
            banner_fg, banner_bg = TK.SUCCESS, TK.BG3
        else:
            days_left = max(0, TRIAL_DAYS - LicenseManager.days_used())
            banner_text = f"⏳ نسخة تجريبية · متبقي {days_left} يوم من أصل {TRIAL_DAYS}"
            banner_fg = TK.WARNING if days_left <= 2 else TK.ACCENT
            banner_bg = TK.BG3

        banner = tk.Frame(welcome_frame, bg=banner_bg, pady=4)
        banner.pack(fill="x", padx=20, pady=(4,0))
        tk.Label(banner, text=banner_text, font=('Arial', 10, 'bold'),
                 bg=banner_bg, fg=banner_fg).pack()

        if not LicenseManager.is_activated():
            tk.Button(welcome_frame, text="🔑 تفعيل البرنامج الآن",
                      bg="#9b59b6", fg="white", font=('Arial', 9, 'bold'),
                      cursor="hand2", relief="flat", padx=10, pady=3,
                      command=self._open_activation).pack(pady=(3,0))

        tk.Frame(welcome_frame, height=6, bg=TK.CARD).pack()

        tk.Label(welcome_frame, text="👤 اسم المستخدم:", font=('Arial', 12), bg=TK.CARD).pack(pady=(8, 3))
        self.username_entry = tk.Entry(welcome_frame, font=('Arial', 13), width=24, justify='center')
        self.username_entry.pack(pady=3)
        self.username_entry.focus()

        tk.Label(welcome_frame, text="🔒 كلمة المرور:", font=('Arial', 12), bg=TK.CARD).pack(pady=(8, 3))
        self.password_entry = tk.Entry(welcome_frame, font=('Arial', 13), width=24, justify='center', show='●')
        self.password_entry.pack(pady=3)

        self.username_entry.bind('<Return>', lambda e: self.password_entry.focus())
        self.password_entry.bind('<Return>', lambda e: self.check_login())

        tk.Button(welcome_frame, text="🚪 دخول", bg=TK.ACCENT2, fg=TK.WHITE, font=('Arial', 13, 'bold'),
                 command=self.check_login, padx=30, pady=6, cursor='hand2').pack(pady=14)

        tk.Label(welcome_frame, text="🔑 admin / 1234", font=('Arial', 10), bg=TK.CARD, fg=TK.TEXT_DIM).pack()

    def _open_activation(self):
        win = tk.Toplevel(self.root)
        win.title("Activate Program")
        win.geometry("460x400")
        win.configure(bg=TK.BG)
        apply_theme(win)
        win.resizable(False, False)
        win.grab_set()
        sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
        win.geometry(f"460x400+{(sw-460)//2}+{(sh-400)//2}")

        frm = tk.Frame(win, bg="white", relief="ridge", bd=2)
        frm.pack(expand=True, fill="both", padx=20, pady=20)

        tk.Label(frm, text="🔑 Activate Program", font=("Arial", 16, "bold"),
                 bg="white", fg="#9b59b6").pack(pady=(15, 5))
        tk.Label(frm, text="Enter the name and key you received from the vendor",
                 font=("Arial", 10), bg="white", fg="#7f8c8d").pack()

        tk.Frame(frm, height=1, bg=TK.BORDER).pack(fill="x", padx=20, pady=8)

        tk.Label(frm, text="👤 Customer Name:", font=("Arial", 11), bg="white").pack(anchor="w", padx=25, pady=(4, 0))
        name_var = tk.StringVar()
        tk.Entry(frm, textvariable=name_var, font=("Arial", 12), width=30, justify="center").pack()

        tk.Label(frm, text="🔑 Product Key:", font=("Arial", 11), bg="white").pack(anchor="w", padx=25, pady=(8, 0))
        key_var = tk.StringVar()
        tk.Entry(frm, textvariable=key_var, font=("Arial", 12), width=30, justify="center").pack()

        def do_activate():
            name = name_var.get().strip()
            key = key_var.get().strip()
            if not name or not key:
                messagebox.showwarning("Warning", "Please enter both name and key", parent=win)
                return
            if LicenseManager.activate(name, key):
                messagebox.showinfo("Activated ✅", f"Welcome {name}!\nProgram activated successfully.", parent=win)
                win.destroy()
                self.root.destroy()
                new_root = tk.Tk()
                LoginWindow(new_root, self.on_success)
                new_root.mainloop()
            else:
                messagebox.showerror("Error ❌", "Invalid key\nCheck the name and key and try again", parent=win)

        tk.Button(frm, text="✅ Activate", bg="#9b59b6", fg="white",
                  font=("Arial", 12, "bold"), padx=20, pady=5,
                  cursor="hand2", command=do_activate).pack(pady=10)

        mid = _get_machine_id()
        mid_card = tk.Frame(frm, bg=TK.BG2, relief="ridge", bd=1)
        mid_card.pack(fill="x", padx=20, pady=(4, 10))
        tk.Label(mid_card, text="🖥️  Your Machine ID  —  send this to the vendor",
                 font=("Arial", 9, "bold"), bg=TK.BG2, fg=TK.ACCENT).pack(pady=(6, 2))
        mid_inner = tk.Frame(mid_card, bg=TK.BG2)
        mid_inner.pack(pady=(0, 4))
        mid_var = tk.StringVar(value=mid)
        tk.Entry(mid_inner, textvariable=mid_var, font=("Courier New", 12, "bold"),
                 width=18, justify="center", state="readonly",
                 readonlybackground="#ddeeff", fg=TK.TEXT, relief="flat", bd=4
                 ).pack(side="left", padx=(0, 6))
        copied_lbl = tk.StringVar(value="📋  Click to Copy")

        def _copy():
            frm.clipboard_clear(); frm.clipboard_append(mid)
            copied_lbl.set("✅  Copied!")
            mid_card.after(2000, lambda: copied_lbl.set("📋  Click to Copy"))

        tk.Button(mid_inner, textvariable=copied_lbl, bg="#2980b9", fg="white",
                  font=("Arial", 9, "bold"), padx=10, pady=5, relief="flat",
                  cursor="hand2", activebackground="#1a6fa8", command=_copy
                  ).pack(side="left")

    def check_login(self):
        if self.username_entry.get() == "admin" and self.password_entry.get() == "1234":
            self.root.destroy()
            self.on_success()
        else:
            messagebox.showerror("خطأ", "اسم المستخدم أو كلمة المرور غير صحيحة")
            self.username_entry.delete(0, tk.END)
            self.password_entry.delete(0, tk.END)
            self.username_entry.focus()

