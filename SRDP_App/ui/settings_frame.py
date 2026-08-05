import customtkinter as ctk
from tkinter import messagebox, colorchooser

class SettingsFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        lbl = ctk.CTkLabel(self, text="Application Settings", font=ctk.CTkFont(size=24, weight="bold"))
        lbl.pack(pady=(20, 10), padx=20, anchor="w")
        
        # Form Frame
        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="x", padx=20, pady=10)
        
        # Theme
        ctk.CTkLabel(form, text="Appearance Theme:").grid(row=0, column=0, sticky="w", pady=10)
        self.combo_theme = ctk.CTkComboBox(form, values=["System", "Dark", "Light"])
        self.combo_theme.grid(row=0, column=1, sticky="w", padx=20, pady=10)
        
        # Line Width
        ctk.CTkLabel(form, text="Graph Line Width:").grid(row=1, column=0, sticky="w", pady=10)
        self.ent_line_width = ctk.CTkEntry(form)
        self.ent_line_width.grid(row=1, column=1, sticky="w", padx=20, pady=10)
        
        # Smoothing Window
        ctk.CTkLabel(form, text="Rolling Average (Data Smoothing):").grid(row=2, column=0, sticky="w", pady=10)
        self.ent_smoothing = ctk.CTkEntry(form)
        self.ent_smoothing.grid(row=2, column=1, sticky="w", padx=20, pady=10)
        
        ctk.CTkLabel(form, text="* Set to 1 for no smoothing.").grid(row=3, column=1, sticky="w", padx=20)
        
        # Custom Colors
        lbl_colors = ctk.CTkLabel(form, text="Interactive Line Colors (Click color block to edit):")
        lbl_colors.grid(row=4, column=0, columnspan=2, sticky="w", pady=(30, 5))
        
        self.color_vars = []
        self.color_buttons = []
        
        self.default_palette = [
            "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
            "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"
        ]

        def choose_color(idx):
            current_color = self.color_vars[idx].get()
            color = colorchooser.askcolor(initialcolor=current_color, title=f"Select Color for Line {idx+1}")
            if color[1]:
                self.color_vars[idx].set(color[1])
                self.color_buttons[idx].configure(fg_color=color[1], hover_color=color[1])

        for i in range(10):
            var = ctk.StringVar()
            self.color_vars.append(var)
            
            c_frame = ctk.CTkFrame(form, fg_color="transparent")
            c_frame.grid(row=5 + (i//2), column=i%2, sticky="w", padx=5, pady=5)
            
            ctk.CTkLabel(c_frame, text=f"Line {i+1}:", width=50, anchor="w").pack(side="left")
            
            btn = ctk.CTkButton(c_frame, text="", width=60, height=30, border_width=2, border_spacing=0, border_color="#333333",
                                command=lambda idx=i: choose_color(idx))
            btn.pack(side="left", padx=5)
            self.color_buttons.append(btn)
        
        # Save Button
        btn_save = ctk.CTkButton(self, text="Save Settings", command=self.save_settings)
        btn_save.pack(pady=40, padx=20, anchor="w")
        
    def on_show(self):
        settings = self.controller.settings_manager.settings
        self.combo_theme.set(settings.get("theme", "System"))
        
        self.ent_line_width.delete(0, 'end')
        self.ent_line_width.insert(0, str(settings.get("line_width", 1.5)))
        
        self.ent_smoothing.delete(0, 'end')
        self.ent_smoothing.insert(0, str(settings.get("rolling_average_window", 1)))
        
        colors = settings.get("line_colors", [])
        for i in range(10):
            color = colors[i] if i < len(colors) and colors[i] else self.default_palette[i]
            self.color_vars[i].set(color)
            self.color_buttons[i].configure(fg_color=color, hover_color=color)
        
    def save_settings(self):
        theme = self.combo_theme.get()
        
        try:
            line_width = float(self.ent_line_width.get())
            if line_width <= 0: raise ValueError
        except ValueError:
            messagebox.showwarning("Warning", "Line width must be a positive number.")
            return
            
        try:
            smoothing = int(self.ent_smoothing.get())
            if smoothing < 1: raise ValueError
        except ValueError:
            messagebox.showwarning("Warning", "Smoothing must be an integer >= 1.")
            return
            
        line_colors = [var.get() for var in self.color_vars]
            
        new_settings = {
            "theme": theme,
            "line_width": line_width,
            "rolling_average_window": smoothing,
            "line_colors": line_colors
        }
        
        self.controller.settings_manager.save_settings(new_settings)
        ctk.set_appearance_mode(theme)
        
        messagebox.showinfo("Success", "Settings saved successfully! Future graphs will use these settings.")
