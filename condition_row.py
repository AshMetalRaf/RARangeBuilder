import tkinter as tk
from tkinter import ttk

from utilities import (
    FLAG_MAP, 
    TYPE_MAP, 
    SIZE_MAP, 
    CMP_OPTIONS, 
    fmt_addr_token, 
    parse_hex
)

class ConditionRow(tk.Frame):
    COL_WIDTHS = [95, 65, 95, 48, 70, 95, 75, 38]
    ROW_HEIGHT = 20

    def __init__(self, master, app_instance, start_entry=None, is_header=False, canvas=None): 
        super().__init__(master)
        self.master = app_instance 
        self.canvas = canvas
        self.start_entry = start_entry
        self._build_ui(is_header)

    def _build_ui(self, is_header):
        headers = ["Flag", "Type", "Size", "Cmp", "Type", "Size", "Mem/Val", "Hits"]
        self.cols = []

        for i, width in enumerate(self.COL_WIDTHS):
            col_frame = tk.Frame(self, width=width, height=self.ROW_HEIGHT)
            col_frame.grid(row=0, column=i, padx=2)
            col_frame.grid_propagate(False)
            col_frame.grid_columnconfigure(0, weight=1)
            col_frame.grid_rowconfigure(0, weight=1)
            self.cols.append(col_frame)

            if is_header:
                ttk.Label(col_frame, text=headers[i], anchor="w").grid(row=0, column=0, sticky='nsew')
            elif not is_header:
                opts = {"row": 0, "column": 0, "sticky": "ew"}
                
                if i == 0:
                    self.flag_var = tk.StringVar(value="")
                    cb = ttk.Combobox(col_frame, values=list(FLAG_MAP.keys()), textvariable=self.flag_var,
                                             state="readonly", height=20)
                    cb.grid(**opts)
                    self.master._disable_scroll(cb) 

                elif i == 1:
                    self.type_var = tk.StringVar(value="Mem")
                    cb = ttk.Combobox(col_frame, values=list(TYPE_MAP.keys()), textvariable=self.type_var,
                                             state="readonly")
                    cb.grid(**opts)
                    self.master._disable_scroll(cb)
                    cb.bind("<<ComboboxSelected>>", self._on_lhs_type_change)

                elif i == 2:
                    self.size_frame = col_frame
                    self.size_var = tk.StringVar(value="8-bit")

                    self.size_cb = ttk.Combobox(col_frame, values=list(SIZE_MAP.keys()), textvariable=self.size_var,
                                             state="readonly", height=25)
                    self.master._disable_scroll(self.size_cb)
                    
                    self.lhs_blank_label = ttk.Label(col_frame, text="", anchor="w")
                    self.size_cb.grid(**opts)

                elif i == 3:
                    self.cmp_var = tk.StringVar(value="=")
                    cb = ttk.Combobox(col_frame, values=CMP_OPTIONS, textvariable=self.cmp_var,
                                             state="readonly")
                    cb.grid(**opts)
                    self.master._disable_scroll(cb)

                elif i == 4:
                    self.memval_var = tk.StringVar(value="Value")
                    cb = ttk.Combobox(col_frame, values=["Mem","Value","Delta","Prior","BCD","Float","Invert","Recall"], textvariable=self.memval_var, state="readonly")
                    cb.grid(**opts)
                    self.master._disable_scroll(cb)
                    cb.bind("<<ComboboxSelected>>", self._on_rhs_type_change)

                elif i == 5:
                    self.value_size_frame = col_frame
                    self.value_size_var = tk.StringVar(value="8-bit")
                    
                    rhs_sizes = list(SIZE_MAP.keys())
                    self.value_size_cb = ttk.Combobox(col_frame, values=rhs_sizes, textvariable=self.value_size_var, 
                                                             state="readonly", height=25)
                    self.master._disable_scroll(self.value_size_cb)
                    
                    self.blank_label = ttk.Label(col_frame, text="", anchor="w")
                    self.blank_label.grid(**opts) 
                    
                elif i == 6:
                    self.value_entry = ttk.Entry(col_frame)
                    self.value_entry.grid(**opts)
                    self.value_entry.insert(0, "0x01")
                    
                elif i == 7:
                    self.hits_entry = ttk.Entry(col_frame)
                    self.hits_entry.grid(**opts)
                    self.hits_entry.insert(0, "")

    def get_values(self):
        return {
            "flag": FLAG_MAP.get(getattr(self, "flag_var", tk.StringVar()).get(), ""),
            "type": TYPE_MAP.get(getattr(self, "type_var", tk.StringVar()).get(), ""),
            "size": SIZE_MAP.get(getattr(self, "size_var", tk.StringVar()).get(), ""),
            "cmp": getattr(self, "cmp_var", tk.StringVar()).get().strip(),
            "memval": getattr(self, "memval_var", tk.StringVar()).get().strip(),
            "value_size": SIZE_MAP.get(getattr(self, "value_size_var", tk.StringVar()).get(), ""),
            "value": getattr(self, "value_entry", tk.Entry()).get().strip(),
            "hits": getattr(self, "hits_entry", tk.Entry()).get().strip()
        }

    def _on_lhs_type_change(self, event=None):
        selected_type = self.type_var.get()
        opts = {"row": 0, "column": 0, "sticky": "ew"}
        
        for widget in self.size_frame.winfo_children():
            widget.grid_forget()

        if selected_type == "Value": 
            self.size_var.set("") 
            self.lhs_blank_label.grid(**opts) 
            
        else: 
            if not self.size_var.get() in list(SIZE_MAP.keys()):
                self.size_var.set("8-bit")
                
            self.size_cb.grid(**opts)

    def _on_rhs_type_change(self, event=None):
        selected_type = self.memval_var.get()
        opts = {"row": 0, "column": 0, "sticky": "ew"}

        for widget in self.value_size_frame.winfo_children():
            widget.grid_forget()

        if selected_type == "Value" or selected_type == "Float":
            self.value_size_var.set("")
            self.blank_label.grid(**opts)

            self.value_entry.delete(0, tk.END)
            if selected_type == "Float":
                try:
                    start_addr_text = self.start_entry.get().strip()
                    start_addr_int = parse_hex(start_addr_text)
                    self.value_entry.insert(0, f"{float(start_addr_int):.1f}")
                except Exception:
                    self.value_entry.insert(0, "0.0")
            return

        if not self.value_size_var.get() in SIZE_MAP:
            self.value_size_var.set("8-bit")
        self.value_size_cb.grid(**opts)

        try:
            start_addr_text = self.start_entry.get().strip()
            if selected_type in ("Mem", "Delta", "Prior", "BCD", "Invert"):
                start_addr_int = parse_hex(start_addr_text)
                self.value_entry.delete(0, tk.END)
                self.value_entry.insert(0, f"0x{start_addr_int:08x}")
        except Exception:
            pass