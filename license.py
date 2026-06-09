"""license.py — نظام الترخيص والتفعيل"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import hashlib, json, tkinter as tk
from tkinter import messagebox
from datetime import datetime
from config import SECRET, TRIAL_DAYS, LICENSE_FILE

def _get_machine_id() -> str:
    import uuid, platform
    mac  = uuid.getnode()
    host = platform.node()
    raw  = f"{mac}::{host}::ButterfliesHW"
    return hashlib.sha256(raw.encode()).hexdigest()[:16].upper()

class LicenseManager:

    @staticmethod
    def generate_key(customer_name: str, machine_id: str = "") -> str:
        """
        Key = SHA256(name + machineID + SECRET + YearMonth)
        Binding to machineID → key only works on the specific PC.
        Binding to YearMonth → key expires naturally if shared (optional — see keygen).
        """
        from datetime import datetime
        ym = datetime.now().strftime("%Y%m")
        mid = machine_id or _get_machine_id()
        raw = customer_name.strip() + mid + SECRET + ym
        h = hashlib.sha256(raw.encode("utf-8")).hexdigest().upper()
        k = h[:16]
        return f"{k[0:4]}-{k[4:8]}-{k[8:12]}-{k[12:16]}"

    @staticmethod
    def validate_key(customer_name: str, key: str) -> bool:
        from datetime import datetime, timedelta
        key = key.strip().upper()
        mid = _get_machine_id()
        for delta in [0, -1]:
            dt = datetime.now() + timedelta(days=delta*31)
            ym = dt.strftime("%Y%m")
            raw = customer_name.strip() + mid + SECRET + ym
            h = hashlib.sha256(raw.encode("utf-8")).hexdigest().upper()
            k = h[:16]
            candidate = f"{k[0:4]}-{k[4:8]}-{k[8:12]}-{k[12:16]}"
            if candidate == key:
                return True
        return False

    @staticmethod
    def _read() -> dict:
        try:
            with open(LICENSE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    @staticmethod
    def _write(data: dict):
        with open(LICENSE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @staticmethod
    def init_if_new():
        data = LicenseManager._read()
        if "install_date" not in data:
            data["install_date"] = datetime.now().strftime("%Y-%m-%d")
            data["activated"] = False
            LicenseManager._write(data)

    @staticmethod
    def days_used() -> int:
        data = LicenseManager._read()
        try:
            install = datetime.strptime(data["install_date"], "%Y-%m-%d")
            today_str = datetime.now().strftime("%Y-%m-%d")
            seen_max_str = data.get("max_date", today_str)
            seen_max = datetime.strptime(seen_max_str, "%Y-%m-%d")
            today = datetime.now()
            effective_today = today if today > seen_max else seen_max
            if today > seen_max:
                data["max_date"] = today_str
                LicenseManager._write(data)
            return (effective_today - install).days
        except Exception:
            return 0

    @staticmethod
    def is_activated() -> bool:
        return LicenseManager._read().get("activated", False)

    @staticmethod
    def is_trial_expired() -> bool:
        if LicenseManager.is_activated():
            return False
        return LicenseManager.days_used() > TRIAL_DAYS

    @staticmethod
    def activate(customer_name: str, key: str) -> bool:
        if LicenseManager.validate_key(customer_name, key):
            data = LicenseManager._read()
            data["activated"] = True
            data["customer_name"] = customer_name.strip()
            data["activation_date"] = datetime.now().strftime("%Y-%m-%d")
            LicenseManager._write(data)
            return True
        return False

    @staticmethod
    def customer_name() -> str:
        return LicenseManager._read().get("customer_name", "")


class ActivationWindow:
    def __init__(self, root, on_success):
        self.root = root
        self.on_success = on_success
        self.activated = False

        root.title("انتهت فترة التجربة - تفعيل البرنامج")
        root.geometry("480x560")
        root.configure(bg="#f0f2f5")
        root.resizable(False, False)
        self._center(480, 560)
        root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._build_ui()

    def _center(self, w, h):
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _build_ui(self):
        frm = tk.Frame(self.root, bg="white", relief="ridge", bd=2)
        frm.pack(expand=True, fill="both", padx=30, pady=30)

        tk.Label(frm, text="🔒", font=("Arial", 48), bg="white").pack(pady=(15, 5))
        tk.Label(frm, text="انتهت فترة التجربة المجانية", font=("Arial", 16, "bold"),
                 bg="white", fg="#e74c3c").pack()
        tk.Label(frm, text="لمتابعة استخدام البرنامج، أدخل بيانات التفعيل",
                 font=("Arial", 11), bg="white", fg="#7f8c8d").pack(pady=6)

        tk.Frame(frm, height=1, bg="#ecf0f1").pack(fill="x", padx=20, pady=8)

        tk.Label(frm, text="👤 اسم العميل (كما تم الاتفاق):", font=("Arial", 11), bg="white").pack(anchor="w", padx=25)
        self.name_var = tk.StringVar()
        tk.Entry(frm, textvariable=self.name_var, font=("Arial", 12), width=30, justify="center").pack(pady=4)

        tk.Label(frm, text="🔑 Product Key:", font=("Arial", 11), bg="white").pack(anchor="w", padx=25)
        self.key_var = tk.StringVar()
        tk.Entry(frm, textvariable=self.key_var, font=("Arial", 12), width=30, justify="center").pack(pady=4)

        tk.Button(frm, text="✅ تفعيل البرنامج", bg="#9b59b6", fg="white",
                  font=("Arial", 13, "bold"), padx=20, pady=6,
                  cursor="hand2", command=self._do_activate).pack(pady=18)

        mid = _get_machine_id()
        mid_card = tk.Frame(frm, bg="#eaf4ff", relief="ridge", bd=1)
        mid_card.pack(fill="x", padx=20, pady=(0, 8))

        tk.Label(mid_card, text="🖥️  Your Machine ID  —  send this to the vendor",
                 font=("Arial", 9, "bold"), bg="#eaf4ff", fg="#2980b9").pack(pady=(8, 2))

        mid_inner = tk.Frame(mid_card, bg="#eaf4ff")
        mid_inner.pack(pady=(0, 6))

        mid_var = tk.StringVar(value=mid)
        mid_entry = tk.Entry(
            mid_inner, textvariable=mid_var, font=("Courier New", 13, "bold"),
            width=18, justify="center", state="readonly",
            readonlybackground="#ddeeff", fg="#1a3a5c",
            relief="flat", bd=4
        )
        mid_entry.pack(side="left", padx=(0, 6))

        copied_var = tk.StringVar(value="📋  Click to Copy")

        def _copy_mid():
            frm.clipboard_clear()
            frm.clipboard_append(mid)
            copied_var.set("✅  Copied!")
            mid_card.after(2000, lambda: copied_var.set("📋  Click to Copy"))

        tk.Button(
            mid_inner, textvariable=copied_var,
            bg="#2980b9", fg="white",
            font=("Arial", 10, "bold"),
            padx=12, pady=6, relief="flat",
            cursor="hand2", activebackground="#1a6fa8",
            command=_copy_mid
        ).pack(side="left")

        tk.Label(mid_card,
                 text="One-click copies your Machine ID to the clipboard",
                 font=("Arial", 8), bg="#eaf4ff", fg="#7f8c8d").pack(pady=(0, 6))

        tk.Label(frm, text="Contact the vendor to get your activation key",
                 font=("Arial", 9), bg="white", fg="#bdc3c7").pack()

    def _do_activate(self):
        name = self.name_var.get().strip()
        key  = self.key_var.get().strip()
        if not name or not key:
            messagebox.showwarning("تنبيه", "الرجاء إدخال الاسم والمفتاح", parent=self.root)
            return
        if LicenseManager.activate(name, key):
            messagebox.showinfo("تم التفعيل ✅", f"أهلاً {name}!\nتم تفعيل البرنامج بنجاح.", parent=self.root)
            self.activated = True
            self.root.destroy()
            self.on_success()
        else:
            messagebox.showerror("خطأ ❌", "المفتاح غير صحيح\nتأكد من الاسم والمفتاح ثم حاول مجدداً", parent=self.root)

    def _on_close(self):
        if not self.activated:
            self.root.destroy()

