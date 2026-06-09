"""printer.py — نظام الطباعة وحفظ الفواتير"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import os, tkinter as tk
from tkinter import messagebox
from datetime import datetime
from config import BASE_DIR


# ── دعم الخطوط العربية في PDF ─────────────────────────────────────
def _get_arabic_font():
    """
    يبحث عن خط عربي TTF على النظام ويُرجع مساره.
    الأولوية: مجلد المشروع أولاً، ثم خطوط النظام.
    """
    # خطوط مُدرجة مباشرة في مجلد المشروع (الأولوية القصوى)
    project_fonts = [
        os.path.join(BASE_DIR, "fonts", "Amiri-Regular.ttf"),
        os.path.join(BASE_DIR, "fonts", "Cairo-Regular.ttf"),
        os.path.join(BASE_DIR, "fonts", "NotoNaskhArabic-Regular.ttf"),
        os.path.join(BASE_DIR, "Amiri-Regular.ttf"),
        os.path.join(BASE_DIR, "Cairo-Regular.ttf"),
    ]

    # خطوط النظام (Windows / Linux / Mac)
    system_fonts = [
        # Windows
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\times.ttf",
        r"C:\Windows\Fonts\trado.ttf",       # Traditional Arabic
        r"C:\Windows\Fonts\simpo.ttf",
        # Linux
        "/usr/share/fonts/truetype/arabeyes/ae_AlArabiya.ttf",
        "/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        # Mac
        "/Library/Fonts/Arial Unicode.ttf",
    ]

    for path in project_fonts + system_fonts:
        if os.path.exists(path):
            return path
    return None


def _register_arabic_font():
    """
    يسجّل الخط العربي في reportlab ويُرجع اسمه.
    إذا لم يُعثر على خط عربي يُرجع None.
    """
    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        # إن كان مسجّلاً مسبقاً لا داعي لإعادة التسجيل
        if "Arabic" in pdfmetrics.getRegisteredFontNames():
            return "Arabic"

        font_path = _get_arabic_font()
        if font_path:
            pdfmetrics.registerFont(TTFont("Arabic", font_path))
            return "Arabic"
    except Exception:
        pass
    return None


def _process_arabic(text):
    """
    يُعيد تشكيل النص العربي ليُعرض بشكل صحيح في PDF:
      1. arabic_reshaper  → يربط الحروف المنفصلة
      2. python-bidi      → يعكس الاتجاه (RTL)
    """
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    except ImportError:
        # إذا لم تكن المكتبات مثبَّتة نُرجع النص كما هو
        return text


class Printer:
    def __init__(self, parent):
        self.parent = parent
        self.invoices_dir = os.path.join(BASE_DIR, "invoices")
        os.makedirs(self.invoices_dir, exist_ok=True)

    # ── اختيار الطابعة ──────────────────────────────────────────────
    @staticmethod
    def get_available_printers():
        """إرجاع قائمة الطابعات المتاحة على النظام"""
        printers = []
        try:
            import win32print
            for p in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS):
                printers.append(p[2])
        except ImportError:
            try:
                import subprocess
                result = subprocess.run(["lpstat", "-a"], capture_output=True, text=True)
                for line in result.stdout.splitlines():
                    if line.strip():
                        printers.append(line.split()[0])
            except Exception:
                pass
        return printers

    @staticmethod
    def get_default_printer():
        """الحصول على الطابعة الافتراضية"""
        try:
            import win32print
            return win32print.GetDefaultPrinter()
        except ImportError:
            try:
                import subprocess
                result = subprocess.run(["lpstat", "-d"], capture_output=True, text=True)
                if "system default destination:" in result.stdout:
                    return result.stdout.split(":")[-1].strip()
            except Exception:
                pass
        return None

    def choose_printer_dialog(self):
        """نافذة اختيار الطابعة - تُرجع اسم الطابعة المختارة أو None"""
        printers = self.get_available_printers()
        default = self.get_default_printer()

        if not printers:
            messagebox.showwarning("تنبيه", "لم يتم العثور على طابعات مثبتة على هذا الجهاز.", parent=self.parent)
            return None

        dialog = tk.Toplevel(self.parent)
        dialog.title("🖨️ اختيار الطابعة")
        dialog.geometry("420x320")
        dialog.configure(bg="#f0f2f5")
        dialog.resizable(False, False)
        dialog.grab_set()

        dialog.update_idletasks()
        sw = dialog.winfo_screenwidth()
        sh = dialog.winfo_screenheight()
        dialog.geometry(f"420x320+{(sw-420)//2}+{(sh-320)//2}")

        tk.Label(dialog, text="🖨️ اختر الطابعة", font=("Arial", 14, "bold"),
                 bg="#f0f2f5", fg="#4a148c").pack(pady=(18, 5))
        tk.Label(dialog, text="اختر الطابعة التي تريد الطباعة عليها:",
                 font=("Arial", 10), bg="#f0f2f5", fg="#555").pack()

        list_frame = tk.Frame(dialog, bg="#f0f2f5")
        list_frame.pack(pady=10, padx=20, fill="both", expand=True)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")

        listbox = tk.Listbox(list_frame, font=("Arial", 11), selectmode="single",
                             yscrollcommand=scrollbar.set, activestyle="dotbox",
                             selectbackground="#9b59b6", selectforeground="white",
                             height=6, relief="ridge", bd=2)
        scrollbar.config(command=listbox.yview)

        selected_index = 0
        for i, p in enumerate(printers):
            label = f"✅ {p} (افتراضي)" if p == default else f"   {p}"
            listbox.insert("end", label)
            if p == default:
                selected_index = i

        listbox.pack(side="left", fill="both", expand=True)
        listbox.selection_set(selected_index)
        listbox.see(selected_index)

        chosen = [None]

        def on_print():
            sel = listbox.curselection()
            if sel:
                chosen[0] = printers[sel[0]]
            dialog.destroy()

        def on_cancel():
            dialog.destroy()

        btn_frame = tk.Frame(dialog, bg="#f0f2f5")
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="🖨️ طباعة", bg="#9b59b6", fg="white",
                  font=("Arial", 11, "bold"), padx=20, pady=5,
                  cursor="hand2", command=on_print).pack(side="left", padx=8)
        tk.Button(btn_frame, text="❌ إلغاء", bg="#e74c3c", fg="white",
                  font=("Arial", 11, "bold"), padx=20, pady=5,
                  cursor="hand2", command=on_cancel).pack(side="left", padx=8)

        dialog.wait_window()
        return chosen[0]

    def send_to_printer(self, file_path, printer_name=None):
        """إرسال الملف مباشرة إلى الطابعة"""
        try:
            import win32api
            import win32print
            if printer_name:
                win32api.ShellExecute(0, "printto", file_path, f'"{printer_name}"', ".", 0)
            else:
                win32api.ShellExecute(0, "print", file_path, None, ".", 0)
            return True
        except ImportError:
            try:
                import subprocess
                cmd = ["lpr", file_path]
                if printer_name:
                    cmd = ["lpr", "-P", printer_name, file_path]
                subprocess.run(cmd, check=True)
                return True
            except Exception as e:
                messagebox.showerror("خطأ في الطباعة", f"تعذّر إرسال الملف للطابعة:\n{e}", parent=self.parent)
                return False

    def print_invoice(self, invoice_data):
        text = self.create_invoice_text(invoice_data)
        self.save_and_print(text, "invoice")

    def print_exchange_invoice(self, exchange_data):
        text = self.create_exchange_invoice_text(exchange_data)
        return self.save_and_print(text, "exchange")

    def create_invoice_text(self, invoice_data):
        text = f"""
{'='*55}
                    🦋 مكتبة الفراشات
{'='*55}
                     فاتورة بيع
{'='*55}
📋 رقم الفاتورة: {invoice_data['invoice_number']}
📅 التاريخ: {invoice_data['date']}
👤 العميل: {invoice_data['customer']}
{'='*55}
{'المنتج':<25} {'الكمية':^10} {'السعر':^10} {'الإجمالي':^10}
{'-'*55}
"""
        for item in invoice_data['items']:
            text += f"{item['name']:<25} {item['quantity']:>8.2f}   {item['price']:>8.2f}   {item['total']:>8.2f}\n"

        text += f"""
{'-'*55}
💰 الإجمالي قبل الخصم:                    {invoice_data['subtotal']:.2f}
🎁 الخصم ({invoice_data['discount_percent']}%):                           -{invoice_data['discount_amount']:.2f}
{'-'*55}
💎 الإجمالي النهائي:                         {invoice_data['total']:.2f}
{'='*55}
🌟 شكراً لتسوقكم في مكتبة الفراشات 🌟
🦋
"""
        return text

    def create_exchange_invoice_text(self, exchange_data):
        new_invoice_total = exchange_data['original_total'] - exchange_data['returned_total'] + exchange_data['new_total']

        text = f"""
{'='*60}
                    🦋 مكتبة الفراشات
{'='*60}
                    فاتورة تبديل منتج
{'='*60}
📋 رقم عملية التبديل: {exchange_data['exchange_number']}
📅 التاريخ: {exchange_data['date']}
👤 العميل: {exchange_data['customer_name']}
📋 الفاتورة الأصلية: {exchange_data['original_invoice']}
{'='*60}

📦 المنتجات المرتجعة:
{'-'*50}
"""
        for item in exchange_data['returned_items']:
            text += f"   • {item['name']:<20} {item['quantity']:>6.2f} × {item['price']:>6.2f} = {item['total']:>8.2f}\n"

        text += f"""
{'-'*50}
🆕 المنتجات الجديدة:
{'-'*50}
"""
        for item in exchange_data['new_items']:
            text += f"   • {item['name']:<20} {item['quantity']:>6.2f} × {item['price']:>6.2f} = {item['total']:>8.2f}\n"

        text += f"""
{'-'*50}
💰 حساب الفاتورة:
{'-'*50}
   إجمالي الفاتورة الأصلية:        {exchange_data['original_total']:>10.2f}
   - قيمة المرتجعات:               {exchange_data['returned_total']:>10.2f}
   + قيمة المنتجات الجديدة:        {exchange_data['new_total']:>10.2f}
   {'='*50}
   إجمالي الفاتورة الجديد:         {new_invoice_total:>10.2f}
{'='*50}
"""
        if exchange_data['price_difference'] > 0:
            text += f"""
   💵 المبلغ الإضافي المطلوب:      {exchange_data['price_difference']:>10.2f}
"""
        elif exchange_data['price_difference'] < 0:
            text += f"""
   💰 المبلغ المسترد للعميل:       {abs(exchange_data['price_difference']):>10.2f}
"""
        else:
            text += """
   ⚪ لا توجد فروق مالية
"""

        text += f"""
{'-'*50}
📝 سبب التبديل: {exchange_data['reason']}
{'='*60}
🌟 شكراً لتسوقكم في مكتبة الفراشات 🌟
🦋
"""
        return text

    def save_and_print(self, text, file_type):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if file_type == "invoice":
            filename = f"invoice_{timestamp}.txt"
        else:
            filename = f"exchange_{timestamp}.txt"

        file_path = os.path.join(self.invoices_dir, filename)
        with open(file_path, 'w', encoding='utf-8-sig') as f:
            f.write(text)

        pdf_path = self.save_as_pdf(text, filename.replace('.txt', '.pdf'))

        self._show_print_options(file_path, pdf_path)
        return file_path, pdf_path

    def _show_print_options(self, txt_path, pdf_path):
        """نافذة تسأل المستخدم: فتح الملف / طباعة مباشرة / إغلاق"""
        dialog = tk.Toplevel(self.parent)
        dialog.title("خيارات الطباعة")
        dialog.geometry("400x260")
        dialog.configure(bg="#f0f2f5")
        dialog.resizable(False, False)
        dialog.grab_set()

        sw = dialog.winfo_screenwidth()
        sh = dialog.winfo_screenheight()
        dialog.geometry(f"400x260+{(sw-400)//2}+{(sh-260)//2}")

        tk.Label(dialog, text="خيارات الطباعة", font=("Arial", 14, "bold"),
                 bg="#f0f2f5", fg="#4a148c").pack(pady=(18, 4))
        tk.Label(dialog, text="تم حفظ الفاتورة بنجاح. ماذا تريد ان تفعل؟",
                 font=("Arial", 10), bg="#f0f2f5", fg="#555").pack(pady=(0, 12))

        btn_frame = tk.Frame(dialog, bg="#f0f2f5")
        btn_frame.pack()

        def open_file():
            dialog.destroy()
            try:
                os.startfile(txt_path)
            except Exception as e:
                messagebox.showerror("خطأ", f"تعذّر فتح الملف:\n{e}")

        def direct_print():
            dialog.destroy()
            printer_name = self.choose_printer_dialog()
            if printer_name:
                target = pdf_path if (pdf_path and os.path.exists(pdf_path)) else txt_path
                success = self.send_to_printer(target, printer_name)
                if success:
                    messagebox.showinfo("طباعة", f"تم ارسال الفاتورة الى الطابعة:\n{printer_name}")

        def just_close():
            dialog.destroy()

        tk.Button(btn_frame, text="طباعة مباشرة على الطابعة",
                  bg="#9b59b6", fg="white", font=("Arial", 11, "bold"),
                  width=30, pady=7, cursor="hand2",
                  command=direct_print).pack(pady=4)

        tk.Button(btn_frame, text="فتح الفاتورة (معاينة)",
                  bg="#3498db", fg="white", font=("Arial", 11, "bold"),
                  width=30, pady=7, cursor="hand2",
                  command=open_file).pack(pady=4)

        tk.Button(btn_frame, text="اغلاق",
                  bg="#95a5a6", fg="white", font=("Arial", 10),
                  width=30, pady=5, cursor="hand2",
                  command=just_close).pack(pady=4)

    # ══════════════════════════════════════════════════════════════════
    # save_as_pdf — النسخة المُصلَحة مع دعم كامل للعربية
    # ══════════════════════════════════════════════════════════════════
    def save_as_pdf(self, text, filename):
        """
        تحويل نص الفاتورة إلى PDF مع دعم كامل للأحرف العربية.

        المشكلة الأصلية:
          - reportlab يستخدم خطوط Helvetica/Times المدمجة التي لا تحتوي
            على أي حرف عربي → تظهر مربعات سوداء أو رموز غير مقروءة.
          - لم يكن هناك معالجة لاتجاه النص (RTL) ولا تشكيل للحروف.

        الحل المُطبَّق:
          1. تسجيل خط TTF عربي (يبحث في مجلد المشروع ثم النظام).
          2. معالجة كل سطر بـ arabic_reshaper + python-bidi قبل الرسم.
          3. محاذاة يمين + اتجاه RTL لكل فقرة.
          4. fallback آمن: إن غابت المكتبات يُنشئ PDF بالخط الافتراضي
             (قد لا تظهر العربية لكن الملف لن يتعطل).
        """
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm
            from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT

            pdf_path = os.path.join(self.invoices_dir, filename)
            doc = SimpleDocTemplate(
                pdf_path,
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm,
            )

            # ── تسجيل الخط العربي ──────────────────────────────────
            arabic_font = _register_arabic_font()
            has_arabic_font = arabic_font is not None

            # ── تعريف الأنماط ───────────────────────────────────────
            styles = getSampleStyleSheet()

            if has_arabic_font:
                # نمط السطر العادي: خط عربي + محاذاة يمين + RTL
                line_style = ParagraphStyle(
                    "ArabicLine",
                    fontName=arabic_font,
                    fontSize=11,
                    leading=16,          # المسافة بين الأسطر
                    alignment=TA_RIGHT,
                    rightToLeft=True,
                    spaceAfter=1,
                )
                # نمط العنوان (السطور التي تحتوي مكتبة الفراشات)
                header_style = ParagraphStyle(
                    "ArabicHeader",
                    fontName=arabic_font,
                    fontSize=14,
                    leading=20,
                    alignment=TA_CENTER,
                    rightToLeft=True,
                    spaceAfter=2,
                    textColor=(0.27, 0.08, 0.55),  # بنفسجي
                )
                # نمط الأرقام والفاصلين (يبقى LTR)
                number_style = ParagraphStyle(
                    "NumberLine",
                    fontName=arabic_font,
                    fontSize=11,
                    leading=16,
                    alignment=TA_LEFT,
                    spaceAfter=1,
                )
            else:
                # Fallback: الخط الافتراضي بدون RTL
                line_style   = styles["Normal"]
                header_style = styles["Normal"]
                number_style = styles["Normal"]

            # ── بناء محتوى الـ PDF سطراً سطراً ─────────────────────
            story = []
            separator_chars = {"=", "-", "*"}   # أسطر الفواصل

            for raw_line in text.split("\n"):
                stripped = raw_line.strip()

                if not stripped:
                    story.append(Spacer(1, 0.15 * cm))
                    continue

                # هل السطر فاصل (====) أو (----) ؟
                is_separator = len(stripped) > 3 and all(ch in separator_chars for ch in stripped)

                # هل يحتوي السطر على النص الرئيسي للمتجر؟
                is_header = "مكتبة الفراشات" in stripped or "فاتورة" in stripped

                if has_arabic_font:
                    # معالجة العربية لكل سطر
                    processed = _process_arabic(stripped)
                    # HTML-escape للأحرف الخاصة التي تُربك reportlab
                    processed = (processed
                                 .replace("&", "&amp;")
                                 .replace("<", "&lt;")
                                 .replace(">", "&gt;"))

                    if is_separator:
                        p = Paragraph(processed, number_style)
                    elif is_header:
                        p = Paragraph(processed, header_style)
                    else:
                        p = Paragraph(processed, line_style)
                else:
                    # Fallback بدون معالجة عربية
                    safe = (stripped
                            .replace("&", "&amp;")
                            .replace("<", "&lt;")
                            .replace(">", "&gt;"))
                    p = Paragraph(safe, line_style)

                story.append(p)

            doc.build(story)
            return pdf_path

        except ImportError:
            # reportlab غير مثبّت
            return None
        except Exception as e:
            # أي خطأ آخر — لا نوقف البرنامج
            print(f"[PDF Error] {e}")
            return None
