import os
import re
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import tkinter.font as tkfont

from condition_row import ConditionRow
from utilities import ToolTip, parse_hex, fmt_addr_token, build_condition_string

from app_ui import UIBuilder
from file_handler import AssetFileHandler

class RARangeBuilder(tk.Tk, UIBuilder, AssetFileHandler):
    def __init__(self):
        super().__init__()

        ui_font = "Segoe UI"
        text_font = "Cascadia Code"
        
        default_font = tkfont.nametofont("TkDefaultFont")
        default_font.configure(family=ui_font, size=8)
        
        text_font_obj = tkfont.nametofont("TkTextFont")
        text_font_obj.configure(family=text_font, size=8)
        
        fixed_font = tkfont.nametofont("TkFixedFont")
        fixed_font.configure(family=text_font, size=8)

        self.title("RA Range Builder")
        self.geometry("1300x800")

        self.option_add("*Font", "Calibri 9")

        self.condition_rows = []
        self.user_file_path = tk.StringVar(value="")
        self.file_raw_lines = []
        self.parsed_assets = []
        
        self.current_title_var = tk.StringVar(value="Select an achievement...")
        self.current_desc_var = tk.StringVar(value="Select an achievement...")
        self.selected_asset_index = -1

        self.file_monitor_thread = None
        self.stop_monitor = threading.Event()
        self.last_mod_time = 0
        self.current_points_var = tk.StringVar(value="5")
        self.points_options = [1, 2, 3, 4, 5, 10, 25, 50, 100]

        self._build_ui()
        
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _on_decimal_toggle(self):
        is_decimal = self.decimal_var.get()
        
        for row in self.condition_rows:
            current_text = row.value_entry.get().strip()
            
            try:
                integer_value = parse_hex(current_text)
            except ValueError:
                continue
            
            if is_decimal:
                new_text = str(integer_value)
            else:
                new_text = f"0x{integer_value:02x}"
                
            row.value_entry.delete(0, tk.END)
            row.value_entry.insert(0, new_text)

    def _reselect_asset(self, target_id):
        for new_index, asset in enumerate(self.parsed_assets):
            if asset["id"] == target_id:
                new_iid = new_index
                self.achievement_tree.selection_set(new_iid)
                self.achievement_tree.see(new_iid)
                self._on_treeview_select()
                return

    def _on_treeview_select(self, event=None):
        selected_items = self.achievement_tree.selection()
        generated_text = self.output.get("1.0", tk.END).strip()
        
        if selected_items and generated_text:
            self.apply_logic_btn.configure(state="normal")
        else:
            self.apply_logic_btn.configure(state="disabled")

        if selected_items:
            try:
                asset_index = int(selected_items[0])
                asset_data = self.parsed_assets[asset_index]
                self.selected_asset_index = asset_index

                self.title_entry.configure(state="normal")
                self.desc_entry.configure(state="normal")
                self.update_metadata_btn.configure(state="normal")
                self.points_combo.configure(state="readonly")

                self.current_title_var.set(asset_data["title"])
                self.current_desc_var.set(asset_data["description"])
                self.current_points_var.set(str(asset_data["points"]))

                conditions_string = asset_data["conditions"]
                current_chars = len(conditions_string)
                max_chars = 65535

                self.raw_conditions_text.configure(state="normal")
                self.raw_conditions_text.delete("1.0", tk.END)
                self.raw_conditions_text.insert("1.0", conditions_string)
                self.raw_conditions_text.configure(state="disabled")

                if current_chars > max_chars:
                    color = "red"
                elif current_chars > 60000:
                    color = "orange"
                else:
                    color = self.raw_default_label_color

                self.raw_char_count_label.config(
                    text=f"Raw Chars: {current_chars}/{max_chars}",
                    foreground=color
                )

            except IndexError:
                self.selected_asset_index = -1
                self._clear_detail_panel()
        else:
            self.selected_asset_index = -1
            self._clear_detail_panel()

    def _clear_detail_panel(self):
        self.current_title_var.set("Select an achievement...")
        self.current_desc_var.set("Select an achievement...")
        
        self.title_entry.configure(state="readonly")
        self.desc_entry.configure(state="readonly")
        self.update_metadata_btn.configure(state="disabled")
        
        self.raw_conditions_text.configure(state="normal")
        self.raw_conditions_text.delete("1.0", tk.END)
        self.raw_conditions_text.configure(state="disabled")
        self.raw_char_count_label.config(text="Raw Chars: 0/65535", foreground=self.raw_default_label_color)

    def add_condition_row(self):
        row = ConditionRow(self.row_container, app_instance=self, start_entry=self.start_entry)
        self.condition_rows.append(row)
        row.pack(fill="x", pady=2)

    def remove_condition_row(self):
        if self.condition_rows:
            row = self.condition_rows.pop()
            row.destroy()
            
    def on_generate(self):
        try:
            start = parse_hex(self.start_entry.get())
            end = parse_hex(self.end_entry.get())
            step = parse_hex(self.step_entry.get())
            if step <= 0: raise ValueError("Offset must be > 0")
            if start > end: raise ValueError("Start address must be <= End address")
        except Exception as e:
            messagebox.showerror("Invalid range", f"Problem parsing range inputs:\n{e}")
            return

        pieces = []
        addr = start
        while addr <= end:
            for row in self.condition_rows:
                vals = row.get_values()

                value_text = vals["value"]
                if vals["memval"] in ("Mem", "Delta", "Prior", "BCD", "Invert"):
                    size_code = vals["value_size"]
                    value_text = fmt_addr_token(size_code, addr)

                pieces.append(build_condition_string(
                    vals["flag"], vals["type"], vals["size"], addr,
                    vals["cmp"], vals["memval"], vals["value_size"],
                    value_text, vals["hits"]
                ))
            addr += step

        self.output.configure(state="normal")
        self.output.delete("1.0", tk.END)

        if self.alt_var.get():
            alt_output = ""
            addr = start
            while addr <= end:
                group_pieces = []
                for row in self.condition_rows:
                    vals = row.get_values()

                    value_text = vals["value"]
                    if vals["memval"] == "Mem":
                        size_code = vals["value_size"]
                        value_text = fmt_addr_token(size_code, addr)

                    group_pieces.append(build_condition_string(
                        vals["flag"], vals["type"], vals["size"], addr,
                        vals["cmp"], vals["memval"], vals["value_size"],
                        value_text, vals["hits"]
                    ))
                alt_output += "S" + "_".join(group_pieces)
                addr += step
            self.output.insert("1.0", alt_output)
        else:
            self.output.insert("1.0", "_".join(pieces))

        self.output.configure(state="normal")
        text = self.output.get("1.0", "end-1c")
        self.output.configure(state="disabled")

        max_chars = 65535
        current_chars = len(text)

        if current_chars > max_chars:
            color = "red"
        elif current_chars > 60000:
            color = "orange"
        else:
            color = self.default_label_color

        self.char_count_label.config(
            text=f"{current_chars}/{max_chars}",
            foreground=color
        )
        
        self._on_treeview_select()

    def copy_to_clip(self):
        text = self.output.get("1.0", tk.END).strip()
        
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            
            self.copy_btn.configure(text="Copied!")
            self.after(1500, lambda: self.copy_btn.configure(text="Copy to clipboard"))

        elif text == "":
            messagebox.showwarning("Empty Output", "Please generate a logic string before copying.")
        else:
            messagebox.showwarning("Empty Output", "Output is empty.")

if __name__ == "__main__":
    app = RARangeBuilder()
    app.mainloop()