import os
import re
import time
import threading
from tkinter import messagebox, filedialog
import tkinter as tk

class AssetFileHandler:
    def _file_monitor(self):
        while not self.stop_monitor.is_set():
            file_path = self.user_file_path.get()
            if file_path and os.path.exists(file_path):
                try:
                    current_mod_time = os.path.getmtime(file_path)
                    
                    if self.last_mod_time != 0 and current_mod_time > self.last_mod_time:
                        self.last_mod_time = current_mod_time
                        self.after(0, self.load_user_file_content)
                        
                    self.last_mod_time = current_mod_time
                        
                except Exception:
                    pass
            time.sleep(1)

    def _start_monitoring(self):
        self._stop_monitoring()
        self.stop_monitor.clear()
        self.file_monitor_thread = threading.Thread(target=self._file_monitor, daemon=True)
        self.file_monitor_thread.start()

    def _stop_monitoring(self):
        if self.file_monitor_thread and self.file_monitor_thread.is_alive():
            self.stop_monitor.set()
            self.file_monitor_thread.join(timeout=2)

    def _on_closing(self):
        self._stop_monitoring()
        self.destroy()

    def _parse_achievement_line(self, line):
        line = line.strip()
        if not re.match(r'^\d{9,}:', line):
            return None

        try:
            match_quoted = re.search(r'(".*?")', line)
            if not match_quoted:
                return None

            full_quoted_conditions = match_quoted.group(1)
            conditions = full_quoted_conditions[1:-1]

            parts = line.split(full_quoted_conditions, 1)
            
            if len(parts) < 2:
                return None
            
            line_prefix = parts[0] + '"'
            line_suffix = parts[1]
            
            title_desc_parts = line_suffix.split(':', 3)
            
            if len(title_desc_parts) < 4:
                if len(title_desc_parts) >= 3:
                    title = title_desc_parts[1]
                    description = title_desc_parts[2]
                    return {
                        "line_index": 0, "id": parts[0].rstrip(':'),
                        "conditions": conditions, "title": title, "description": description,
                        "points": 5, "progression_tail": "",
                        "line_prefix": line_prefix, "line_suffix": line_suffix
                    }
                return None

            title = title_desc_parts[1]
            description = title_desc_parts[2]

            remainder = title_desc_parts[3]

            fixed_end_match = re.search(r'(:{5}\d{5})$', remainder)
            
            if not fixed_end_match:
                return None

            fixed_end_data = fixed_end_match.group(1)
            points_segment = remainder[:-len(fixed_end_data)]

            points_match = re.search(r':(\d+)$', points_segment)

            points_value = 5
            progression_tail = points_segment

            if points_match:
                points_value = int(points_match.group(1))
                progression_tail = points_segment[:points_match.start(1)-1]

            return {
                "line_index": 0,
                "id": parts[0].rstrip(':'),
                "conditions": conditions,
                "title": title,
                "description": description,
                "points": points_value,
                "progression_tail": progression_tail + fixed_end_data,
                "line_prefix": line_prefix,
                "line_suffix": line_suffix
            }
        except Exception:
            return None

    def browse_user_file(self):
        file_path = filedialog.askopenfilename(
            defaultextension=".txt",
            filetypes=[("User Asset File", "*-User.txt"), ("Text files", "*.txt"), ("All files", "*.*")],
            title="Select the 12345-User.txt or similar file"
        )
        if file_path:
            self.user_file_path.set(file_path)
            self.load_user_file_content()

    def load_user_file_content(self):
        file_path = self.user_file_path.get()
        self.file_raw_lines = []
        self.parsed_assets = []
        self.achievement_tree.delete(*self.achievement_tree.get_children())
        self._clear_detail_panel()

        if not file_path or not os.path.exists(file_path):
            self.apply_logic_btn.configure(state="disabled")
            self._stop_monitoring()
            return
            
        self._start_monitoring()

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.file_raw_lines = [line.rstrip('\n') for line in f.readlines()]
            
            self.last_mod_time = os.path.getmtime(file_path)

            asset_index = 0
            for i, line in enumerate(self.file_raw_lines):
                parsed_data = self._parse_achievement_line(line)
                if parsed_data:
                    parsed_data["line_index"] = i
                    self.parsed_assets.append(parsed_data)
                    
                    display_number = asset_index + 1
                    
                    self.achievement_tree.insert("", "end", iid=asset_index, values=(
                        display_number,
                        parsed_data["title"],
                        parsed_data["description"]
                    ))
                    asset_index += 1
            
            self._on_treeview_select()

        except Exception as e:
            messagebox.showerror("File Error", f"Could not read file:\n{e}")
            self.apply_logic_btn.configure(state="disabled")

    def update_achievement_metadata(self):
        if self.selected_asset_index == -1:
            messagebox.showwarning("No Selection", "Please select an achievement to update.")
            return

        try:
            asset_data = self.parsed_assets[self.selected_asset_index]
            asset_id = asset_data["id"]
            
            new_title = self.current_title_var.get().strip()
            new_desc = self.current_desc_var.get().strip()
            
            if not new_title:
                messagebox.showwarning("Invalid Title", "Title cannot be empty.")
                return

            original_line = self.file_raw_lines[asset_data["line_index"]]
            
            conditions_search = re.search(r'(".*?")', original_line)
            if not conditions_search:
                messagebox.showerror("Parsing Error", "Could not find condition string in the asset line.")
                return

            suffix_segment = original_line[conditions_search.end():]

            full_user_segment_with_old_points = asset_data.get("progression_tail", "")
            
            match_fixed_end_data = re.search(r'(:{5}\d+)$', suffix_segment)
            fixed_end_data = match_fixed_end_data.group(1)

            progression_prefix = full_user_segment_with_old_points.removesuffix(fixed_end_data)
            progression_prefix = re.sub(r':\d+$', '', progression_prefix)
            
            new_points = self.current_points_var.get()
            
            user_data_block = f'{progression_prefix}:{new_points}{fixed_end_data}'
            
            prefix = original_line[:conditions_search.end()]
            
            new_line = (
                f'{prefix}'
                f':{new_title}'
                f':{new_desc}'
                f':{user_data_block}'
            )

            self.file_raw_lines[asset_data["line_index"]] = new_line.rstrip('\n')

            file_path = self.user_file_path.get()
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(line + '\n' for line in self.file_raw_lines)
            
            self.last_mod_time = os.path.getmtime(file_path)
                        
            self.load_user_file_content()
            self._reselect_asset(asset_id)

        except Exception as e:
            messagebox.showerror("Update Metadata Error", f"An error occurred while updating metadata:\n{e}")

    def apply_generated_logic(self):
        selected_items = self.achievement_tree.selection()
        
        if not selected_items:
            messagebox.showwarning("No Selection", "Please select an achievement from the list to update.")
            return

        generated_logic = self.output.get("1.0", tk.END).strip()
        if not generated_logic:
            messagebox.showwarning("No Logic", "Please generate a logic string first.")
            return

        try:
            asset_index = int(selected_items[0])
            asset_data = self.parsed_assets[asset_index]

            asset_id = asset_data["id"]
            
            line_index = asset_data["line_index"]
            line_prefix = asset_data["line_prefix"]
            line_suffix = asset_data["line_suffix"]

            new_line = f'{line_prefix}{generated_logic}"{line_suffix}'
            
            self.file_raw_lines[line_index] = new_line.rstrip('\n')

            file_path = self.user_file_path.get()
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(line + '\n' for line in self.file_raw_lines)
            
            messagebox.showinfo("Success", f"Achievement '{asset_data['title']}' conditions have been updated and saved to file.")
            
            self.load_user_file_content()
            self._reselect_asset(asset_id)

        except Exception as e:
            messagebox.showerror("Update Metadata Error", f"An error occurred while updating metadata:\n{e}")