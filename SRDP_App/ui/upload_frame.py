import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk
from datetime import datetime
import os
import shutil
import threading
import tkinter as tk

from core.data_manager import SUPPORTED_EXTENSIONS


SUPPORTED_FILE_PATTERN = " ".join(f"*{ext}" for ext in SUPPORTED_EXTENSIONS)


class CircularProgress(tk.Canvas):
    def __init__(self, parent, size=150, **kwargs):
        super().__init__(parent, width=size, height=size, bg="#F4F7FB", highlightthickness=0, **kwargs)
        self.size = size
        self.create_oval(15, 15, size-15, size-15, outline="#cbd5e1", width=10)
        self.arc_id = self.create_arc(15, 15, size-15, size-15, start=90, extent=0, outline="#0A192F", width=10, style="arc")
        self.text_id = self.create_text(size/2, size/2, text="0%", font=("Arial", 20, "bold"), fill="#0A192F")
        
    def set_progress(self, percentage):
        self.itemconfig(self.arc_id, extent=-(percentage/100 * 360))
        self.itemconfig(self.text_id, text=f"{int(percentage)}%")

class UploadFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.selected_file_index = None
        self.log_entries = []
        self.log_counts = {"INFO": 0, "SUCCESS": 0, "WARNING": 0, "ERROR": 0}
        self.import_running = False
        self.displayed_progress = 0.0
        self.target_progress = 0.0
        self.progress_animation_job = None
        self.file_progress_job = None
        self.current_file_limit = 0.0
        
        lbl = ctk.CTkLabel(self, text="Data & Upload", font=ctk.CTkFont(size=24, weight="bold"))
        lbl.pack(pady=(20, 10), padx=20, anchor="w")

        info = ctk.CTkLabel(
            self,
            text="Supported inputs: CSV, TXT, TSV, DAT, LOG, Excel, OpenDocument, JSON, JSONL, HTML tables, STMF, and XTRP",
            text_color="#64748b",
        )
        info.pack(pady=(0, 8), padx=20, anchor="w")
        
        self.file_list_frame = ctk.CTkFrame(self, corner_radius=8)
        self.file_list_frame.pack(fill="x", padx=20, pady=10)

        table_title = ctk.CTkFrame(self.file_list_frame, fg_color="transparent")
        table_title.pack(fill="x", padx=12, pady=(10, 4))
        ctk.CTkLabel(table_title, text="Uploaded Files", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")
        self.lbl_file_status = ctk.CTkLabel(table_title, text="0 files loaded", text_color="#64748b")
        self.lbl_file_status.pack(side="right")
        
        # Headers
        header_frame = ctk.CTkFrame(self.file_list_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=12, pady=(2, 5))
        ctk.CTkLabel(header_frame, text="File Name", font=ctk.CTkFont(weight="bold"), width=260, anchor="w").pack(side="left")
        ctk.CTkLabel(header_frame, text="Type", font=ctk.CTkFont(weight="bold"), width=105, anchor="w").pack(side="left")
        ctk.CTkLabel(header_frame, text="Rows", font=ctk.CTkFont(weight="bold"), width=90, anchor="w").pack(side="left")
        ctk.CTkLabel(header_frame, text="Columns", font=ctk.CTkFont(weight="bold"), width=90, anchor="w").pack(side="left")
        ctk.CTkLabel(header_frame, text="Legend Tag", font=ctk.CTkFont(weight="bold"), width=180, anchor="w").pack(side="left")
        ctk.CTkLabel(header_frame, text="Action", font=ctk.CTkFont(weight="bold"), width=260, anchor="w").pack(side="left", padx=10)
        
        self.rows_container = ctk.CTkScrollableFrame(self.file_list_frame, height=145, fg_color="#ffffff", corner_radius=6)
        self.rows_container.pack(fill="x", padx=12, pady=(0, 12))
        self.redraw_rows()

        self.preview_frame = ctk.CTkFrame(self, corner_radius=8)
        self.preview_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        preview_header = ctk.CTkFrame(self.preview_frame, fg_color="transparent")
        preview_header.pack(fill="x", padx=12, pady=(10, 6))
        ctk.CTkLabel(preview_header, text="Input Data Preview", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")
        self.lbl_preview_status = ctk.CTkLabel(preview_header, text="No file selected", text_color="#64748b")
        self.lbl_preview_status.pack(side="right")

        self.preview_table_frame = ctk.CTkFrame(self.preview_frame, fg_color="#ffffff", corner_radius=6)
        self.preview_table_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.preview_tree = ttk.Treeview(self.preview_table_frame, show="headings", height=8)
        self.preview_vscroll = ttk.Scrollbar(self.preview_table_frame, orient="vertical", command=self.preview_tree.yview)
        self.preview_hscroll = ttk.Scrollbar(self.preview_table_frame, orient="horizontal", command=self.preview_tree.xview)
        self.preview_tree.configure(yscrollcommand=self.preview_vscroll.set, xscrollcommand=self.preview_hscroll.set)
        self.preview_tree.grid(row=0, column=0, sticky="nsew")
        self.preview_vscroll.grid(row=0, column=1, sticky="ns")
        self.preview_hscroll.grid(row=1, column=0, sticky="ew")
        self.preview_table_frame.grid_rowconfigure(0, weight=1)
        self.preview_table_frame.grid_columnconfigure(0, weight=1)

        self._clear_preview("Upload a file to see parsed input data here.")
        
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.pack(fill="x", padx=20, pady=(8, 10))

        self.btn_add = ctk.CTkButton(action_frame, text="+ Add Data Files", width=180, command=self.add_files)
        self.btn_add.pack(side="left")

        self.btn_combine = ctk.CTkButton(action_frame, text="Combine Data", width=140, fg_color="#0f766e", hover_color="#115e59", command=self.combine_files)
        self.btn_combine.pack(side="left", padx=10)

        self.btn_clear_log = ctk.CTkButton(action_frame, text="Clear Log", width=110, fg_color="#64748b", hover_color="#475569", command=self.clear_log)
        self.btn_clear_log.pack(side="right", padx=(8, 0))

        self.btn_save_log = ctk.CTkButton(action_frame, text="Save Log", width=110, fg_color="#334155", hover_color="#1e293b", command=self.save_log)
        self.btn_save_log.pack(side="right")

        self.log_frame = ctk.CTkFrame(self, corner_radius=8)
        self.log_frame.pack(fill="x", padx=20, pady=(0, 18))

        log_header = ctk.CTkFrame(self.log_frame, fg_color="transparent")
        log_header.pack(fill="x", padx=12, pady=(10, 6))

        ctk.CTkLabel(log_header, text="Import Log", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")
        self.lbl_log_status = ctk.CTkLabel(log_header, text="No import activity yet", text_color="#64748b")
        self.lbl_log_status.pack(side="right")

        self.log_text = ctk.CTkTextbox(self.log_frame, height=105, wrap="word", font=("Consolas", 11))
        self.log_text.pack(fill="x", padx=12, pady=(0, 12))
        self.log_text.configure(state="disabled")
        self.add_log("INFO", "Import log ready.")

        # Loading Overlay
        self.overlay = ctk.CTkFrame(self, corner_radius=10, fg_color="#F4F7FB", border_width=2)
        self.progress_ring = CircularProgress(self.overlay, size=150)
        self.progress_ring.pack(padx=30, pady=(24, 10), expand=True)
        self.lbl_progress_title = ctk.CTkLabel(self.overlay, text="Preparing import", font=ctk.CTkFont(size=16, weight="bold"))
        self.lbl_progress_title.pack(padx=24, pady=(0, 4))
        self.lbl_progress_detail = ctk.CTkLabel(self.overlay, text="", text_color="#475569", wraplength=360)
        self.lbl_progress_detail.pack(padx=24, pady=(0, 8))
        self.progress_bar = ctk.CTkProgressBar(self.overlay, width=330, height=10)
        self.progress_bar.pack(padx=24, pady=(0, 24))
        self.progress_bar.set(0)

    def add_files(self):
        filepaths = filedialog.askopenfilenames(
            parent=self,
            title="Select Data Files",
            filetypes=(
                ("Supported Data Files", SUPPORTED_FILE_PATTERN),
                ("Text and CSV Files", "*.csv *.txt *.tsv *.tab *.dat *.log *.asc *.prn *.data"),
                ("Excel and OpenDocument Files", "*.xlsx *.xlsm *.xltx *.xltm *.xls *.xlsb *.ods"),
                ("JSON Files", "*.json *.jsonl *.ndjson"),
                ("HTML Tables", "*.html *.htm"),
                ("Recorder Files", "*.stmf *.xtrp"),
                ("All Files", "*.*"),
            )
        )
        if not filepaths:
            return

        self.add_log("INFO", f"Import started for {len(filepaths)} file(s).")
        self.btn_add.configure(state="disabled")
        self._show_import_progress(len(filepaths))
        
        threading.Thread(target=self._load_files_thread, args=(filepaths,), daemon=True).start()

    def _schedule_ui(self, delay_ms, callback, *args):
        try:
            if self.winfo_exists():
                self.after(delay_ms, callback, *args)
        except tk.TclError:
            pass

    def _show_import_progress(self, total_files):
        self.import_running = True
        self.displayed_progress = 0.0
        self.target_progress = 3.0
        self.current_file_limit = 92.0
        self.progress_ring.set_progress(0)
        self.progress_bar.set(0)
        self.lbl_progress_title.configure(text="Preparing import")
        self.lbl_progress_detail.configure(text=f"Queued {total_files} file{'s' if total_files != 1 else ''}.")
        self.overlay.place(relx=0.5, rely=0.42, anchor="center")
        self._animate_progress()

    def _set_progress_target(self, percentage, title=None, detail=None):
        self.target_progress = max(self.target_progress, min(100.0, float(percentage)))
        if title:
            self.lbl_progress_title.configure(text=title)
        if detail:
            self.lbl_progress_detail.configure(text=detail)

    def _animate_progress(self):
        if not self.import_running:
            self.progress_animation_job = None
            return

        gap = self.target_progress - self.displayed_progress
        if gap > 0:
            step = max(0.2, min(2.8, gap * 0.16))
            self.displayed_progress = min(self.target_progress, self.displayed_progress + step)
            self.progress_ring.set_progress(self.displayed_progress)
            self.progress_bar.set(self.displayed_progress / 100)

        self.progress_animation_job = self.after(45, self._animate_progress)

    def _begin_file_progress(self, filepath, index, total):
        base = (index / total) * 100
        segment = 100 / total
        self.current_file_limit = min(98.0, base + segment * 0.92)

        ext = os.path.splitext(filepath)[1].lower()
        if ext == ".csv":
            title = "Reading CSV file"
        elif ext in (".txt", ".tsv", ".tab", ".dat", ".log", ".asc", ".prn", ".data"):
            title = "Converting text to XLSX"
        elif ext in (".xlsx", ".xlsm", ".xltx", ".xltm", ".xls", ".xlsb", ".ods"):
            title = "Reading spreadsheet"
        elif ext == ".xtrp":
            title = "Reading XTRP recorder file"
        else:
            title = "Detecting table data"

        detail = f"{index + 1} of {total}: {os.path.basename(filepath)}"
        self._set_progress_target(base + segment * 0.12, title, detail)
        self._advance_file_progress()

    def _advance_file_progress(self):
        if not self.import_running:
            self.file_progress_job = None
            return

        if self.target_progress < self.current_file_limit:
            gap = self.current_file_limit - self.target_progress
            self.target_progress += max(0.15, min(1.4, gap * 0.08))

        self.file_progress_job = self.after(350, self._advance_file_progress)

    def _complete_file_progress(self, filepath, index, total, success):
        if self.file_progress_job:
            self.after_cancel(self.file_progress_job)
            self.file_progress_job = None

        title = "File imported" if success else "File skipped"
        detail = f"{index + 1} of {total}: {os.path.basename(filepath)}"
        self._set_progress_target(((index + 1) / total) * 100, title, detail)

    def _hide_import_progress(self):
        self.import_running = False
        if self.progress_animation_job:
            self.after_cancel(self.progress_animation_job)
            self.progress_animation_job = None
        if self.file_progress_job:
            self.after_cancel(self.file_progress_job)
            self.file_progress_job = None
        self.progress_ring.set_progress(100)
        self.progress_bar.set(1)
        self.overlay.place_forget()

    def _load_files_thread(self, filepaths):
        errors = []
        total = len(filepaths)
        loaded_indices = []
        for i, filepath in enumerate(filepaths):
            self._schedule_ui(0, self._begin_file_progress, filepath, i, total)
            self._schedule_ui(0, self.add_log, "INFO", f"Processing: {filepath}")
            
            default_tag = os.path.basename(filepath)
            success, msg = self.controller.data_manager.load_file(filepath, default_tag)
            if not success:
                errors.append(msg)
                self._schedule_ui(0, self.add_log, "ERROR", msg)
            else:
                loaded_index = len(self.controller.data_manager.files_data) - 1
                loaded_indices.append(loaded_index)
                file_info = self.controller.data_manager.files_data[loaded_index]
                self._schedule_ui(0, self.add_log, "SUCCESS", self._format_success_log(filepath, msg, file_info))
                for warning in file_info.get("warnings", []):
                    self._schedule_ui(0, self.add_log, "WARNING", f"{os.path.basename(filepath)}: {warning}")
                
            self._schedule_ui(0, self._complete_file_progress, filepath, i, total, success)
                
        self._schedule_ui(500, self._load_files_finished, errors, loaded_indices)

    def _load_files_finished(self, errors, loaded_indices=None):
        if not self.winfo_exists():
            return

        self._hide_import_progress()
        self.btn_add.configure(state="normal")
        if errors:
            self.add_log("ERROR", f"Import finished with {len(errors)} error(s). Review the log for details.")
            messagebox.showerror("Import Error", "Some files could not be imported:\n\n" + "\n".join(errors), parent=self)
        else:
            self.add_log("SUCCESS", "Import finished successfully.")

        if loaded_indices:
            self.selected_file_index = loaded_indices[-1]

        self.redraw_rows()
        self.refresh_preview()
        self.update_idletasks()

    def add_log(self, level, message):
        level = str(level).upper()
        if level not in self.log_counts:
            level = "INFO"

        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] [{level}] {message}"
        self.log_entries.append(entry)
        self.log_counts[level] += 1

        self.log_text.configure(state="normal")
        self.log_text.insert("end", entry + "\n\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
        self._update_log_status()

    def clear_log(self):
        self.log_entries.clear()
        self.log_counts = {"INFO": 0, "SUCCESS": 0, "WARNING": 0, "ERROR": 0}
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")
        self._update_log_status()
        self.add_log("INFO", "Import log cleared.")

    def save_log(self):
        if not self.log_entries:
            messagebox.showinfo("Import Log", "There are no log entries to save.", parent=self)
            return

        save_path = filedialog.asksaveasfilename(
            parent=self,
            title="Save Import Log",
            defaultextension=".txt",
            filetypes=(("Text Files", "*.txt"), ("All Files", "*.*")),
            initialfile=f"SRDP_Import_Log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        )
        if not save_path:
            return

        try:
            with open(save_path, "w", encoding="utf-8") as f:
                f.write("\n".join(self.log_entries))
            self.add_log("SUCCESS", f"Import log saved to: {save_path}")
        except Exception as e:
            self.add_log("ERROR", f"Failed to save import log: {e}")
            messagebox.showerror("Import Log", f"Failed to save import log:\n{e}", parent=self)

    def _update_log_status(self):
        total = sum(self.log_counts.values())
        if total == 0:
            self.lbl_log_status.configure(text="No import activity yet")
            return

        status = (
            f"{total} entries | "
            f"{self.log_counts['SUCCESS']} success | "
            f"{self.log_counts['WARNING']} warnings | "
            f"{self.log_counts['ERROR']} errors"
        )
        self.lbl_log_status.configure(text=status)

    def combine_files(self):
        if len(self.controller.data_manager.files_data) < 2:
            messagebox.showwarning("Combine Files", "Please load at least 2 files to combine.", parent=self)
            return
            
        self.add_log("INFO", "Starting combination of loaded files...")
        success, msg = self.controller.data_manager.combine_files()
        
        if success:
            self.add_log("SUCCESS", msg)
            self.selected_file_index = len(self.controller.data_manager.files_data) - 1
            self.redraw_rows()
            self.refresh_preview()
            messagebox.showinfo("Combine Files", msg, parent=self)
        else:
            self.add_log("ERROR", msg)
            messagebox.showerror("Combine Files", msg, parent=self)

    def _format_success_log(self, filepath, msg, file_info):
        details = file_info.get("import_details", {})
        columns = file_info.get("columns", [])
        preview = ", ".join(str(c) for c in columns[:8])
        if len(columns) > 8:
            preview += f", ... +{len(columns) - 8} more"

        detail_parts = [msg]
        if details.get("reader"):
            detail_parts.append(f"reader={details['reader']}")
        if details.get("sheet"):
            detail_parts.append(f"sheet={details['sheet']}")
        if details.get("engine"):
            detail_parts.append(f"engine={details['engine']}")
        if details.get("encoding"):
            detail_parts.append(f"encoding={details['encoding']}")
        if details.get("separator"):
            detail_parts.append(f"separator={details['separator']}")
        if details.get("header"):
            detail_parts.append(f"header={details['header']}")
        if details.get("tables_found"):
            detail_parts.append(f"tables_found={details['tables_found']}")
        if details.get("channels"):
            detail_parts.append(f"channels={details['channels']}")
        if details.get("sample_rate_hz"):
            detail_parts.append(f"sample_rate={details['sample_rate_hz']:.2f} Hz")
        if details.get("conversion"):
            detail_parts.append("converted_to_xlsx=yes")

        return (
            f"{os.path.basename(filepath)} | "
            f"{'; '.join(detail_parts)} | "
            f"columns: {preview}"
        )

    def update_tag(self, idx, new_tag):
        self.controller.data_manager.files_data[idx]["tag"] = new_tag

    def remove_file(self, idx):
        removed = self.controller.data_manager.files_data[idx]
        del self.controller.data_manager.files_data[idx]
        if self.selected_file_index == idx:
            self.selected_file_index = 0 if self.controller.data_manager.files_data else None
        elif self.selected_file_index is not None and self.selected_file_index > idx:
            self.selected_file_index -= 1
        self.add_log("INFO", f"Removed from upload list: {os.path.basename(removed['filepath'])}")
        self.redraw_rows()
        self.refresh_preview()

    def show_file_preview(self, idx):
        self.selected_file_index = idx
        self.redraw_rows()
        self.refresh_preview()

    def open_file_preview_window(self, idx):
        if idx < 0 or idx >= len(self.controller.data_manager.files_data):
            return

        file_info = self.controller.data_manager.files_data[idx]
        df = file_info.get("df")
        if df is None:
            messagebox.showwarning("Preview", "No data is available for this file.", parent=self)
            return

        preview = ctk.CTkToplevel(self)
        display_path = file_info.get("original_filepath") or file_info["filepath"]
        preview.title(f"Preview - {os.path.basename(display_path)}")
        preview.geometry("1100x650")
        preview.transient(self)

        header = ctk.CTkFrame(preview, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(16, 8))

        ctk.CTkLabel(
            header,
            text=os.path.basename(display_path),
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(anchor="w")

        details = file_info.get("import_details", {})
        detail_text = (
            f"Rows: {len(df):,} | Columns: {len(df.columns):,} | "
            f"Sheet: {details.get('sheet', 'n/a')} | Reader: {details.get('reader', 'n/a')}"
        )
        if file_info.get("converted_filepath"):
            detail_text += " | Converted XLSX available"
        ctk.CTkLabel(header, text=detail_text, text_color="#64748b").pack(anchor="w", pady=(2, 0))

        text = ctk.CTkTextbox(preview, wrap="none", font=("Consolas", 11))
        text.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        column_line = "Columns: " + ", ".join(str(col) for col in df.columns)
        data_preview = df.head(100).to_string(index=False)
        text.insert("1.0", f"{column_line}\n\n{data_preview}")
        text.configure(state="disabled")

    def save_combined_csv(self, idx):
        if idx < 0 or idx >= len(self.controller.data_manager.files_data):
            return

        file_info = self.controller.data_manager.files_data[idx]
        df = file_info.get("df")
        if df is None:
            messagebox.showwarning("Save CSV", "No data available to save.", parent=self)
            return

        default_name = file_info.get("tag", "Combined_Data").replace(" ", "_") + ".csv"
        save_path = filedialog.asksaveasfilename(
            parent=self,
            title="Save Combined CSV",
            defaultextension=".csv",
            initialfile=default_name,
            filetypes=(("CSV Files", "*.csv"), ("All Files", "*.*")),
        )
        if not save_path:
            return

        try:
            df.to_csv(save_path, index=False)
            self.add_log("SUCCESS", f"Combined CSV saved to: {save_path}")
        except Exception as e:
            self.add_log("ERROR", f"Failed to save combined CSV: {e}")
            messagebox.showerror("Save CSV", f"Failed to save combined CSV:\n{e}", parent=self)

    def save_converted_xlsx(self, idx):
        if idx < 0 or idx >= len(self.controller.data_manager.files_data):
            return

        file_info = self.controller.data_manager.files_data[idx]
        converted_path = file_info.get("converted_filepath")
        if not converted_path or not os.path.exists(converted_path):
            messagebox.showwarning("Converted XLSX", "No converted XLSX file is available for this upload.", parent=self)
            return

        original_path = file_info.get("original_filepath") or file_info.get("filepath") or "converted_data.txt"
        default_name = os.path.splitext(os.path.basename(original_path))[0] + ".xlsx"
        save_path = filedialog.asksaveasfilename(
            parent=self,
            title="Save Converted XLSX",
            defaultextension=".xlsx",
            initialfile=default_name,
            filetypes=(("Excel Workbook", "*.xlsx"), ("All Files", "*.*")),
        )
        if not save_path:
            return

        try:
            shutil.copy2(converted_path, save_path)
            self.add_log("SUCCESS", f"Converted XLSX saved to: {save_path}")
        except Exception as e:
            self.add_log("ERROR", f"Failed to save converted XLSX: {e}")
            messagebox.showerror("Converted XLSX", f"Failed to save converted XLSX:\n{e}", parent=self)

    def on_show(self):
        self.redraw_rows()
        self.refresh_preview()

    def redraw_rows(self):
        for widget in self.rows_container.winfo_children():
            widget.destroy()

        file_count = len(self.controller.data_manager.files_data)
        self.lbl_file_status.configure(text=f"{file_count} file{'s' if file_count != 1 else ''} loaded")

        if file_count == 0:
            self.selected_file_index = None
            empty = ctk.CTkLabel(
                self.rows_container,
                text="No files uploaded yet.",
                text_color="#64748b",
                anchor="center",
            )
            empty.pack(fill="x", padx=10, pady=35)
            return

        if self.selected_file_index is None or self.selected_file_index >= file_count:
            self.selected_file_index = 0

        for idx, file_info in enumerate(self.controller.data_manager.files_data):
            is_selected = idx == self.selected_file_index
            row_frame = ctk.CTkFrame(self.rows_container, fg_color="#dbeafe" if is_selected else "#f8fafc", corner_radius=6)
            row_frame.pack(fill="x", padx=4, pady=3)
            
            display_path = file_info.get("original_filepath") or file_info["filepath"]
            lbl_name = ctk.CTkLabel(row_frame, text=os.path.basename(display_path), width=260, anchor="w")
            lbl_name.pack(side="left", padx=(8, 0), pady=6)

            file_type = file_info.get("format") or os.path.splitext(file_info["filepath"])[1].lower() or "unknown"
            source_type = file_info.get("source_format")
            if file_info.get("converted_filepath") and source_type:
                type_label = f"{source_type.upper().lstrip('.')} -> XLSX"
            else:
                type_label = file_type.upper().lstrip(".")
            ctk.CTkLabel(row_frame, text=type_label, width=105, anchor="w").pack(side="left")
            ctk.CTkLabel(row_frame, text=f"{file_info.get('rows', len(file_info.get('df', []))):,}", width=90, anchor="w").pack(side="left")
            ctk.CTkLabel(row_frame, text=f"{len(file_info.get('columns', [])):,}", width=90, anchor="w").pack(side="left")
            
            tag_var = ctk.StringVar(master=self, value=file_info["tag"])
            # use a closure to capture current idx
            def on_tag_change(*args, i=idx, v=tag_var):
                self.update_tag(i, v.get())
            tag_var.trace_add("write", on_tag_change)
            
            ent_tag = ctk.CTkEntry(row_frame, textvariable=tag_var, width=160)
            ent_tag.pack(side="left", padx=(0, 20))
            
            btn_preview = ctk.CTkButton(row_frame, text="View", width=70,
                                        command=lambda i=idx: self.show_file_preview(i))
            btn_preview.pack(side="left", padx=(0, 8))

            btn_open = ctk.CTkButton(row_frame, text="Open", width=70, fg_color="#334155", hover_color="#1e293b",
                                     command=lambda i=idx: self.open_file_preview_window(i))
            btn_open.pack(side="left", padx=(0, 8))

            if file_info.get("converted_filepath"):
                btn_save_xlsx = ctk.CTkButton(
                    row_frame,
                    text="Save XLSX",
                    width=90,
                    fg_color="#0f766e",
                    hover_color="#115e59",
                    command=lambda i=idx: self.save_converted_xlsx(i),
                )
                btn_save_xlsx.pack(side="left", padx=(0, 8))

            if file_info.get("source_format") == "multiple":
                btn_save_csv = ctk.CTkButton(
                    row_frame,
                    text="Save CSV",
                    width=90,
                    fg_color="#0f766e",
                    hover_color="#115e59",
                    command=lambda i=idx: self.save_combined_csv(i),
                )
                btn_save_csv.pack(side="left", padx=(0, 8))

            btn_remove = ctk.CTkButton(row_frame, text="Remove", width=80, fg_color="#F44336", hover_color="#D32F2F",
                                       command=lambda i=idx: self.remove_file(i))
            btn_remove.pack(side="left")

    def refresh_preview(self):
        if self.selected_file_index is None or self.selected_file_index >= len(self.controller.data_manager.files_data):
            self._clear_preview("Upload a file to see parsed input data here.")
            return

        file_info = self.controller.data_manager.files_data[self.selected_file_index]
        df = file_info.get("df")
        if df is None or df.empty:
            self._clear_preview("Selected file has no previewable rows.")
            return

        max_rows = 200
        max_cols = 60
        preview_df = df.iloc[:max_rows, :max_cols].copy()
        columns = [str(column) for column in preview_df.columns]

        self.preview_tree.delete(*self.preview_tree.get_children())
        self.preview_tree["columns"] = columns

        for column in columns:
            width = max(90, min(220, len(column) * 9 + 28))
            self.preview_tree.heading(column, text=column)
            self.preview_tree.column(column, width=width, minwidth=70, stretch=False, anchor="w")

        for row in preview_df.itertuples(index=False, name=None):
            values = ["" if value is None or str(value) == "nan" else str(value) for value in row]
            self.preview_tree.insert("", "end", values=values)

        details = file_info.get("import_details", {})
        suffix = ""
        if len(df) > max_rows or len(df.columns) > max_cols:
            suffix = f" | preview limited to {min(len(df), max_rows)} rows x {min(len(df.columns), max_cols)} columns"

        status = (
            f"{os.path.basename(file_info.get('original_filepath') or file_info['filepath'])} | "
            f"{len(df):,} rows x {len(df.columns):,} columns | "
            f"{details.get('reader', 'reader n/a')}"
            f"{suffix}"
        )
        self.lbl_preview_status.configure(text=status)

    def _clear_preview(self, message):
        self.preview_tree.delete(*self.preview_tree.get_children())
        self.preview_tree["columns"] = ("message",)
        self.preview_tree.heading("message", text="Status")
        self.preview_tree.column("message", width=600, stretch=True, anchor="w")
        self.preview_tree.insert("", "end", values=(message,))
        self.lbl_preview_status.configure(text="No file selected")
