from __future__ import annotations

from pathlib import Path
from tkinter import Button, Entry, Label, OptionMenu, StringVar, Tk, filedialog, messagebox

from .converter import ConversionError, convert_spass_to_csv, default_output_path
from .exporters import ExportFormat, SPassExporter


def run_gui() -> None:
    root = Tk()
    root.title("SPass CSV Converter")
    root.geometry("680x320")
    root.resizable(False, False)

    input_var = StringVar()
    output_var = StringVar()
    password_var = StringVar()
    format_var = StringVar(value=ExportFormat.CHROME)
    status_var = StringVar(value="Select a .spass file and enter its Samsung Pass export password.")

    def refresh_output_path() -> None:
        if input_var.get():
            output_var.set(str(default_output_path(input_var.get(), format_var.get())))

    def choose_input() -> None:
        selected = filedialog.askopenfilename(
            title="Choose SPass export file",
            filetypes=[("SPass files", "*.spass"), ("All files", "*.*")],
        )
        if not selected:
            return
        input_var.set(selected)
        refresh_output_path()
        status_var.set("Ready to convert.")

    def choose_output() -> None:
        extension = ".json" if format_var.get() == ExportFormat.BITWARDEN_JSON else ".csv"
        filetypes = [("JSON files", "*.json")] if extension == ".json" else [("CSV files", "*.csv")]
        selected = filedialog.asksaveasfilename(
            title="Save output as",
            defaultextension=extension,
            filetypes=filetypes,
        )
        if selected:
            output_var.set(selected)

    def convert() -> None:
        if not input_var.get():
            messagebox.showwarning("Missing file", "Please choose a .spass file first.")
            return
        if not password_var.get():
            messagebox.showwarning("Missing password", "Please enter the Samsung Pass export password.")
            return
        output_path = output_var.get() or str(default_output_path(input_var.get(), format_var.get()))
        try:
            result = convert_spass_to_csv(
                input_var.get(),
                output_path,
                password=password_var.get(),
                format_name=format_var.get(),
                allow_plain_fallback=False,
            )
        except ConversionError as exc:
            status_var.set("Conversion failed.")
            messagebox.showerror("Conversion failed", str(exc))
            return

        status = f"Saved {result.row_count} {result.format_name} items to {result.output_path}"
        if result.warnings:
            status += "\n\nWarnings:\n" + "\n".join(f"- {warning}" for warning in result.warnings)
        status_var.set(status)
        messagebox.showinfo("Done", status)

    def format_changed(_value: str) -> None:
        refresh_output_path()

    Label(root, text="SPass export file").place(x=24, y=24)
    Entry(root, textvariable=input_var, width=66).place(x=24, y=50)
    Button(root, text="Browse", command=choose_input, width=12).place(x=550, y=46)

    Label(root, text="Export password").place(x=24, y=88)
    Entry(root, textvariable=password_var, show="*", width=32).place(x=24, y=114)

    Label(root, text="Output format").place(x=330, y=88)
    format_menu = OptionMenu(root, format_var, *sorted(SPassExporter.FORMATS), command=format_changed)
    format_menu.config(width=18)
    format_menu.place(x=330, y=108)

    Label(root, text="Output file").place(x=24, y=152)
    Entry(root, textvariable=output_var, width=66).place(x=24, y=178)
    Button(root, text="Save as", command=choose_output, width=12).place(x=550, y=174)

    Button(root, text="Convert", command=convert, width=18).place(x=262, y=222)
    Label(root, textvariable=status_var, anchor="w", justify="left", wraplength=630).place(x=24, y=264)

    root.mainloop()
