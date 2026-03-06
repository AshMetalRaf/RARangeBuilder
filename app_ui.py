import tkinter as tk
from tkinter import ttk, messagebox
import threading
import os
import time

class UIBuilder:
    def _disable_scroll(self, combobox):
        def ignore_scroll(event):
            return "break"
        combobox.bind("<MouseWheel>", ignore_scroll)
        combobox.bind("<Button-4>", ignore_scroll)
        combobox.bind("<Button-5>", ignore_scroll)

    def _build_ui(self):
        pad = 6
        main = ttk.Frame(self, padding=pad)
        main.pack(fill="both", expand=True)
        
        top_frame = ttk.Frame(main)
        top_frame.pack(fill="both", expand=True, padx=pad, pady=pad)
        top_frame.grid_columnconfigure(0, weight=1)
        top_frame.grid_columnconfigure(1, weight=1)
        top_frame.grid_rowconfigure(0, weight=1)
        
        cond_out_frame = ttk.Frame(top_frame)
        cond_out_frame.grid(row=0, column=0, sticky="nsew", padx=(0, pad))
        cond_out_frame.grid_rowconfigure(0, weight=1)
        cond_out_frame.grid_columnconfigure(0, weight=1)

        from utilities import ToolTip
        from condition_row import ConditionRow

        cond_frame = ttk.LabelFrame(cond_out_frame, text="Condition rows")
        cond_frame.grid(row=0, column=0, sticky="nsew", padx=pad, pady=pad)

        header_row = ConditionRow(cond_frame, app_instance=self, is_header=True)
        header_row.pack(fill="x", pady=(0,2))

        canvas_frame = tk.Frame(cond_frame)
        canvas_frame.pack(fill="both", expand=True)

        canvas = tk.Canvas(canvas_frame, height=200)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        self.row_container = tk.Frame(canvas)
        canvas.create_window((0, 0), window=self.row_container, anchor="nw")

        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        self.row_container.bind("<Configure>", on_frame_configure)

        def _on_mousewheel(event):
            if event.num == 4: canvas.yview_scroll(-1, "units")
            elif event.num == 5: canvas.yview_scroll(1, "units")

        canvas.bind_all("<Button-4>", _on_mousewheel)
        canvas.bind_all("<Button-5>", _on_mousewheel)

        self.after(50, lambda: canvas.yview_moveto(0))

        btn_frame = ttk.Frame(cond_frame)
        btn_frame.pack(side="bottom", fill="x", pady=pad)
        
        btn_frame.grid_columnconfigure(3, weight=1)
        
        self.add_btn = ttk.Button(btn_frame, text="New", command=self.add_condition_row)
        self.add_btn.grid(row=0, column=0, padx=4, pady=4)
        
        self.remove_btn = ttk.Button(btn_frame, text="Remove", command=self.remove_condition_row)
        self.remove_btn.grid(row=0, column=1, padx=4, pady=4)

        self.decimal_var = tk.BooleanVar(value=False)
        self.decimal_check = ttk.Checkbutton(btn_frame, text="Show Decimal", 
                                             variable=self.decimal_var,
                                             command=self._on_decimal_toggle)
        self.decimal_check.grid(row=0, column=3, sticky="e", padx=10, pady=4)
        
        self.alt_var = tk.BooleanVar(value=False)
        self.alt_check = ttk.Checkbutton(btn_frame, text="Use Alt Groups [?]",
                                             variable=self.alt_var)
        self.alt_check.grid(row=0, column=2, sticky="e", padx=10, pady=4)
        ToolTip(
            self.alt_check,
            "This is treated as Copied Def which is processed manually,\n"
            "since RAInt doesn't support direct groups pasting into the Assets Editor:\n"
            "1. Load the 12345-User.txt found inside RACache>Data.\n"
            "2. Highlight the achievement you wish to apply the change.\n"
            "2. Apply the generated string."
        )

        rangef = ttk.LabelFrame(cond_out_frame, text="Range controls")
        rangef.grid(row=1, column=0, sticky="ew", padx=pad, pady=pad)
        
        ttk.Label(rangef, text="Start address").grid(row=0, column=0, sticky="w")
        self.start_entry = ttk.Entry(rangef, width=16)
        self.start_entry.grid(row=1, column=0, sticky="w", padx=4)
        self.start_entry.insert(0, "0x00001000")

        ttk.Label(rangef, text="End address").grid(row=0, column=1, sticky="w")
        self.end_entry = ttk.Entry(rangef, width=16)
        self.end_entry.grid(row=1, column=1, sticky="w", padx=4)
        self.end_entry.insert(0, "0x00002000")

        ttk.Label(rangef, text="Offset (Hex)").grid(row=0, column=2, sticky="w")
        self.step_entry = ttk.Entry(rangef, width=12)
        self.step_entry.grid(row=1, column=2, sticky="w", padx=4)
        self.step_entry.insert(0, "0x10")
        rangef.grid_columnconfigure(3, weight=1)

        outf = ttk.LabelFrame(cond_out_frame, text="Generated logic string")
        outf.grid(row=2, column=0, sticky="nsew", padx=pad, pady=pad)
        outf.grid_rowconfigure(1, weight=1)
        outf.grid_columnconfigure(0, weight=1)

        btnf = ttk.Frame(outf)
        btnf.grid(row=0, column=0, sticky="ew", padx=6, pady=6)

        self.generate_btn = ttk.Button(btnf, text="Generate", command=self.on_generate)
        self.generate_btn.pack(side="left", padx=6)
        self.copy_btn = ttk.Button(btnf, text="Copy to clipboard", command=self.copy_to_clip)
        self.copy_btn.pack(side="left", padx=6)

        self.output = tk.Text(outf, wrap="none", height=3, highlightthickness=0, relief="flat")
        self.output.grid(row=1, column=0, sticky="nsew", padx=6, pady=(0,0))
        self.output.configure(state="disabled")
        self.char_count_label = ttk.Label(outf, text="Characters: 0/65535", anchor="e")
        self.char_count_label.grid(row=2, column=0, sticky="e", pady=(0, 4))
        self.default_label_color = self.char_count_label.cget("foreground")

        file_viewer_frame = ttk.Frame(top_frame)
        file_viewer_frame.grid(row=0, column=1, sticky="nsew", padx=(pad, 0))
        file_viewer_frame.grid_rowconfigure(1, weight=1)
        file_viewer_frame.grid_columnconfigure(0, weight=1)

        tree_lf = ttk.LabelFrame(file_viewer_frame, text="Achievements List")
        tree_lf.grid(row=0, column=0, sticky="nsew", padx=pad, pady=(pad, 0))
        tree_lf.grid_rowconfigure(0, weight=1)
        tree_lf.grid_columnconfigure(0, weight=1)
        
        file_control_frame = ttk.Frame(tree_lf)
        file_control_frame.grid(row=0, column=0, sticky="ew", padx=pad, pady=(4, 4))
        file_control_frame.grid_columnconfigure(1, weight=1)

        from tkinter import filedialog
        self.browse_btn = ttk.Button(file_control_frame, text="Browse...", command=self.browse_user_file)
        self.browse_btn.grid(row=0, column=0, sticky="w", padx=(0, 4))

        self.file_path_entry = ttk.Entry(file_control_frame, textvariable=self.user_file_path, state="readonly")
        self.file_path_entry.grid(row=0, column=1, sticky="ew")

        tree_inner_frame = ttk.Frame(tree_lf)
        tree_inner_frame.grid(row=1, column=0, sticky="nsew", padx=pad, pady=(0, pad))
        tree_inner_frame.grid_columnconfigure(0, weight=1)
        tree_inner_frame.grid_rowconfigure(0, weight=1)

        self.achievement_tree = ttk.Treeview(tree_inner_frame, columns=("#", "Title", "Description"), show="headings", height=17)
        self.achievement_tree.heading("#", text="#")
        self.achievement_tree.column("#", width=40, anchor="center", stretch=tk.NO)
        
        self.achievement_tree.heading("Title", text="Title")
        self.achievement_tree.heading("Description", text="Description")
        self.achievement_tree.column("Title", width=200, anchor="w")
        self.achievement_tree.column("Description", width=300, anchor="w")

        v_scroll = ttk.Scrollbar(tree_inner_frame, orient="vertical", command=self.achievement_tree.yview)
        h_scroll = ttk.Scrollbar(tree_inner_frame, orient="horizontal", command=self.achievement_tree.xview)
        self.achievement_tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        self.achievement_tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")
        
        self.achievement_tree.bind("<<TreeviewSelect>>", self._on_treeview_select)
        
        detail_lf = ttk.LabelFrame(file_viewer_frame, text="Selected Achievement Details / Editor")
        detail_lf.grid(row=1, column=0, sticky="nsew", padx=pad, pady=pad)
        detail_lf.grid_columnconfigure(0, weight=1)

        ttk.Label(detail_lf, text="Title:").grid(row=0, column=0, sticky="w", padx=4, pady=(4, 0))
        self.title_entry = ttk.Entry(detail_lf, textvariable=self.current_title_var, state="readonly")
        self.title_entry.grid(row=1, column=0, sticky="ew", padx=4, pady=(0, 4))

        ttk.Label(detail_lf, text="Description:").grid(row=2, column=0, sticky="w", padx=4, pady=(4, 0))
        self.desc_entry = ttk.Entry(detail_lf, textvariable=self.current_desc_var, state="readonly")
        self.desc_entry.grid(row=3, column=0, sticky="ew", padx=4, pady=(0, 4))

        ttk.Label(detail_lf, text="Points:").grid(row=4, column=0, sticky="w", padx=4, pady=(4, 0))
        
        self.points_combo = ttk.Combobox(
            detail_lf,
            textvariable=self.current_points_var,
            values=self.points_options,
            state="readonly",
            width=6
        )
        self.points_combo.grid(row=5, column=0, sticky="w", padx=4, pady=(0, 4))
        self._disable_scroll(self.points_combo)
        
        action_btn_frame = ttk.Frame(detail_lf)
        action_btn_frame.grid(row=6, column=0, sticky="ew", padx=4, pady=(4, 8))
        action_btn_frame.grid_columnconfigure(0, weight=1)
        action_btn_frame.grid_columnconfigure(1, weight=1)

        self.update_metadata_btn = ttk.Button(action_btn_frame, text="Update Title/Desc in File", 
                                             command=self.update_achievement_metadata, state="disabled")
        self.update_metadata_btn.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        
        self.apply_logic_btn = ttk.Button(action_btn_frame, text="Apply Generated Logic", 
                                             command=self.apply_generated_logic, state="disabled")
        self.apply_logic_btn.grid(row=0, column=1, sticky="ew", padx=(4, 0))

        raw_cond_lf = ttk.LabelFrame(detail_lf, text="Raw Conditions (Current)")
        raw_cond_lf.grid(row=7, column=0, sticky="nsew", padx=4, pady=(4, 4))
        raw_cond_lf.grid_rowconfigure(0, weight=1)
        raw_cond_lf.grid_columnconfigure(0, weight=1)

        self.raw_conditions_text = tk.Text(raw_cond_lf, wrap="none", height=5, state="disabled", highlightthickness=0, relief="sunken")
        self.raw_conditions_text.grid(row=0, column=0, sticky="nsew")
        
        raw_h_scroll = ttk.Scrollbar(raw_cond_lf, orient="horizontal", command=self.raw_conditions_text.xview)
        self.raw_conditions_text.configure(xscrollcommand=raw_h_scroll.set)
        raw_h_scroll.grid(row=1, column=0, sticky="ew")

        self.raw_char_count_label = ttk.Label(raw_cond_lf, text="Raw Chars: 0/65535", anchor="e")
        self.raw_char_count_label.grid(row=2, column=0, sticky="e", pady=(0, 4))
        self.raw_default_label_color = self.raw_char_count_label.cget("foreground")