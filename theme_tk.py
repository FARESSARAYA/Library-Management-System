# theme_tk.py
import tkinter as tk
from tkinter import ttk

class TK:
    BG = "#B1BDDE"
    BG2 = "#445883"
    BG3 = "#CDD1D9"
    CARD = "#BCC4D6"
    BORDER = "#7EA3DF"
    ACCENT = "#5B8CFF"
    ACCENT2 = "#8B5CF6"
    SUCCESS = "#22D3A8"
    DANGER = "#FF4D6D"
    WARNING = "#FBBF24"
    TEXT = "#E2E8F0"
    TEXT_SUB = "#FC2180"
    TEXT_DIM = "#3078DB"
    WHITE = "#FFFFFF"

def apply_theme(window, theme_name="arc"):
    if isinstance(window, (tk.Tk, tk.Toplevel, tk.Frame)):
        window.configure(bg=TK.BG)

def style_button(button, style_type="primary"):
    colors = {
        "primary": {"bg": TK.ACCENT, "fg": TK.WHITE},
        "danger": {"bg": TK.DANGER, "fg": TK.WHITE},
        "success": {"bg": TK.SUCCESS, "fg": TK.TEXT_DIM},
        "warning": {"bg": TK.WARNING, "fg": TK.TEXT_DIM}
    }
    color = colors.get(style_type, colors["primary"])
    button.configure(bg=color["bg"], fg=color["fg"], relief=tk.FLAT, bd=0, padx=10, pady=5)

def style_entry(entry):
    entry.configure(bg=TK.WHITE, fg=TK.TEXT_DIM, relief=tk.SOLID, bd=1)

def style_label(label, label_type="normal"):
    styles = {
        "title": {'font': ('Arial', 16, 'bold'), 'fg': TK.TEXT},
        "subtitle": {'font': ('Arial', 12, 'bold'), 'fg': TK.TEXT_SUB},
        "error": {'font': ('Arial', 9, 'bold'), 'fg': TK.DANGER},
        "normal": {'font': ('Arial', 10), 'fg': TK.TEXT}
    }
    style = styles.get(label_type, styles["normal"])
    label.configure(bg=TK.BG, **style)

def make_card(parent, bg_color=TK.CARD, relief=tk.RAISED, bd=1):
    card = tk.Frame(parent, bg=bg_color, relief=relief, bd=bd)
def setup_treeview(treeview, colors=None):
    if colors is None:
        colors = {
            'bg': '#ffffff',
            'fg': '#000000',
            'select_bg': '#0078d4',
            'select_fg': '#ffffff'
        }
    
    style = ttk.Style()
    style.configure("Custom.Treeview", 
                   background=colors['bg'],
                   foreground=colors['fg'],
                   fieldbackground=colors['bg'],
                   rowheight=25)
    
    style.configure("Custom.Treeview.Heading",
                   font=('Helvetica', 10, 'bold'))
    
    style.map('Custom.Treeview',
             background=[('selected', colors['select_bg'])],
             foreground=[('selected', colors['select_fg'])])
    
    treeview.configure(style="Custom.Treeview")

def fill_treeview(treeview, data, columns):
    """تعبئة الجدول بالبيانات"""
    # مسح البيانات القديمة
    for item in treeview.get_children():
        treeview.delete(item)
    
    # إضافة البيانات الجديدة
    for row in data:
        treeview.insert('', 'end', values=row)

def style_button(button, style_type="primary"):
    """تنسيق الأزرار"""
    styles = {
        "primary": {'bg': '#0078d4', 'fg': 'white', 'activebackground': '#005a9e'},
        "secondary": {'bg': '#e0e0e0', 'fg': '#333333', 'activebackground': '#c0c0c0'},
        "danger": {'bg': '#d32f2f', 'fg': 'white', 'activebackground': '#b71c1c'},
        "success": {'bg': '#4caf50', 'fg': 'white', 'activebackground': '#388e3c'}
    }
    
    style = styles.get(style_type, styles['primary'])
    
    if hasattr(button, 'configure'):
        button.configure(
            bg=style['bg'],
            fg=style['fg'],
            activebackground=style['activebackground'],
            relief='flat',
            padx=10,
            pady=5,
            font=('Helvetica', 10, 'bold')
        )

def style_entry(entry):
    """تنسيق حقول الإدخال"""
    entry.configure(
        bg='#ffffff',
        fg='#000000',
        insertbackground='#0078d4',
        relief='solid',
        borderwidth=1,
        font=('Helvetica', 10)
    )

def make_card(parent, **kwargs):
    """إنشاء بطاقة بتنسيق جميل"""
    card = ttk.Frame(parent, **kwargs)
    
    style = ttk.Style()
    style.configure("Card.TFrame", 
                   background='#f5f5f5',
                   relief='raised',
                   borderwidth=2)
    
    card.configure(style="Card.TFrame")
    return card