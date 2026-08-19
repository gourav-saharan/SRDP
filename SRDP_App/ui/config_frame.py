import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox

class ConfigFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        lbl = ctk.CTkLabel(self, text="Graph Configuration", font=ctk.CTkFont(size=24, weight="bold"))
        lbl.pack(pady=(20, 10), padx=20, anchor="w")
        
        # X-Axis selection
        x_frame = ctk.CTkFrame(self, fg_color="transparent")
        x_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(x_frame, text="Select X-Axis:", width=100, anchor="w").pack(side="left")
        self.combo_x = ctk.CTkComboBox(x_frame, values=["No data loaded"])
        self.combo_x.pack(side="left", fill="x", expand=True, padx=10)
        
       
        ctk.CTkLabel(self, text="Select Y-Axis (Multiple):").pack(padx=20, pady=(10, 0), anchor="w")
        
        # Using native tk Listbox for massive performance boost when loading 1000+ columns
        list_container = ctk.CTkFrame(self)
        list_container.pack(fill="both", expand=True, padx=20, pady=5)
        
        scrollbar = ctk.CTkScrollbar(list_container)
        scrollbar.pack(side="right", fill="y")
        
        self.y_listbox = tk.Listbox(
            list_container, selectmode=tk.MULTIPLE,
            highlightthickness=0, borderwidth=0,
            font=("Arial", 12), yscrollcommand=scrollbar.set
        )
        self.y_listbox.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.configure(command=self.y_listbox.yview)
        
       
        self.btn_process = ctk.CTkButton(self, text="Process & View Graph", command=self.process_graph)
        self.btn_process.pack(pady=20)
        
    def on_show(self):
        cols = self.controller.data_manager.get_all_columns()
        
        # Save current selections if any
        selected_indices = self.y_listbox.curselection()
        current_selected_items = [self.y_listbox.get(i) for i in selected_indices]
        
        # Restore selections from controller if available (and nothing is currently selected)
        saved_items = []
        if hasattr(self.controller, "graph_config"):
            config = self.controller.graph_config
            saved_x = config.get("x_col")
            saved_items = config.get("y_cols", [])
            if saved_x and saved_x in cols:
                self.combo_x.set(saved_x)
        
        if cols:
            self.combo_x.configure(values=cols)
            if not self.combo_x.get() or self.combo_x.get() not in cols:
                self.combo_x.set(cols[0])
        else:
            self.combo_x.configure(values=["No data loaded"])
            self.combo_x.set("No data loaded")
            
        self.y_listbox.delete(0, tk.END)
        for c in cols:
            self.y_listbox.insert(tk.END, str(c))
            
        # Combine current and saved selections
        to_select = set(current_selected_items) | set(saved_items)
        xtrp_files = [
            file_info for file_info in self.controller.data_manager.files_data
            if file_info.get("source_format") == ".xtrp"
        ]
        if not to_select and xtrp_files and len(xtrp_files) == len(self.controller.data_manager.files_data):
            xtrp_x_col = "Frequency (Hz)" if "Frequency (Hz)" in cols else "Sample"
            if xtrp_x_col in cols:
                self.combo_x.set(xtrp_x_col)
                to_select = {str(c) for c in cols if str(c) != xtrp_x_col}

        for i, c in enumerate(cols):
            if str(c) in to_select:
                self.y_listbox.selection_set(i)
                
        # Adapt theme
        if ctk.get_appearance_mode() == "Light":
            self.y_listbox.configure(bg="#ffffff", fg="black", selectbackground="#1f538d")
        else:
            self.y_listbox.configure(bg="#2b2b2b", fg="white", selectbackground="#1f538d")

    def process_graph(self):
        x_val = self.combo_x.get()
        if x_val == "No data loaded" or not x_val:
            messagebox.showwarning("Warning", "Please upload data and select an X-Axis.")
            return
            
        selected_indices = self.y_listbox.curselection()
        y_vals = [self.y_listbox.get(i) for i in selected_indices]
        
        if not y_vals:
            messagebox.showwarning("Warning", "Please select at least one Y-Axis column.")
            return
            
        self.controller.graph_config = {
            "x_col": x_val,
            "y_cols": y_vals
        }
        
        self.controller.show_frame("GraphFrame")
