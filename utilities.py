import tkinter as tk
from tkinter import ttk

# constants
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        widget.bind("<Enter>", self.show_tip)
        widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tip_window or not self.text:
            return

        style = ttk.Style()
        try:
            bg = style.lookup("TLabel", "background")
            fg = style.lookup("TLabel", "foreground")
            if not bg:
                bg = self.widget.cget("background")
            if not fg:
                fg = self.widget.cget("foreground")
        except tk.TclError:
            bg, fg = "#ffffe0", "#000000"

        x = self.widget.winfo_rootx() + 25
        y = self.widget.winfo_rooty() + 20
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")

        label = ttk.Label(
            tw,
            text=self.text,
            background=bg,
            foreground=fg,
            relief="solid",
            borderwidth=1,
            padding=(4, 2),
        )
        label.pack()

    def hide_tip(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
        self.tip_window = None

FLAG_MAP = {
    "": "",
    "PauseIf": "P:",
    "ResetIf": "R:",
    "ResetNextIf": "Z:",
    "AddSource": "A:",
    "SubSource": "B:",
    "AddHits": "C:",
    "SubHits": "D:",
    "AddAddress": "I:",
    "AndNext": "N:",
    "OrNext": "O:",
    "Measured": "M:",
    "Measured%": "G:",
    "MeasuredIf": "Q:",
    "Trigger": "T:",
    "Remember": "K:"
}

TYPE_MAP = {
    "Mem": "",
    "Value": "",
    "Delta": "d",
    "Prior": "p",
    "BCD": "b",
    "Float": "f",
    "Invert": "~",
    "Recall": "{recall}"
}

SIZE_MAP = {
    "Bit0": "0xM", "Bit1": "0xN", "Bit2": "0xO", "Bit3": "0xP",
    "Bit4": "0xQ", "Bit5": "0xR", "Bit6": "0xS", "Bit7": "0xT",
    "Lower4": "0xL", "Upper4": "0xU", "8-bit": "0xH", "16-bit": "0x",
    "24-bit": "0xW", "32-bit": "0xX", "16-bit BE": "0xI", "24-bit BE": "0xJ",
    "32-bit BE": "0xG", "BitCount": "0xK", "Float": "fF", "Float BE": "fB",
    "Double32": "fH", "Double32 BE": "fI", "MBF32": "fM", "MBF32 LE": "fL"
}

CMP_OPTIONS = ["=", "<", "<=", ">", ">=", "!="]

# utility functions
def parse_hex(s):
    s = s.strip()
    if s.lower().startswith("0x"):
        s = s[2:]
    return int(s, 16)

def fmt_addr_token(size_code, addr_int):
    return f"{size_code}{addr_int:08x}" if size_code and size_code != "0x" else f"0x{addr_int:08x}"

def build_condition_string(flag_code, type_code, size_code, addr_int, cmp_sym, rhs_type, rhs_size_code, rhs_value_text, hits_text):
    addr_token = fmt_addr_token(size_code, addr_int)
    
    value_fragment = ""
    
    if rhs_type == "Mem":
        try:
            rhs_addr_int = parse_hex(rhs_value_text)
            rhs_token = fmt_addr_token(rhs_size_code, rhs_addr_int)
        except ValueError:
            rhs_token = rhs_value_text 
            
        value_fragment = rhs_token
        
    elif rhs_type != "Value":
        type_prefix = TYPE_MAP.get(rhs_type, "")
        try: 
            rhs_value_int = parse_hex(rhs_value_text)
            rhs_value_decimal_str = str(rhs_value_int)
        except ValueError:
            rhs_value_decimal_str = rhs_value_text
            
        value_fragment = type_prefix + rhs_value_decimal_str
        
    else:
        try:
            rhs_value_int = parse_hex(rhs_value_text)
            value_fragment = str(rhs_value_int)
        except ValueError:
            value_fragment = rhs_value_text
    
    hits_fragment = f".{hits_text.strip()}." if hits_text.strip() else ""
    
    return f"{flag_code}{type_code}{addr_token}{cmp_sym}{value_fragment}{hits_fragment}"