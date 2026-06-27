from __future__ import annotations

from pathlib import Path
from tkinter import Button, Entry, Label, StringVar, Tk, filedialog, messagebox

from .converter import ConversionError, convert_spass_to_csv


def run_gui() -> None:
    root = Tk()
    root.title("SPass CSV Converter")
    root.geometry("640x220")
    root.resizable(False, False)

    input_var = StringVar()
    output_var = StringVar()
    status_var = StringVar(value="Select a .spass file to convert.")

    def choose_input() -> None:
        selected = filedialog.askopenfilename(
            title="Choose SPass export file",
            filetypes=[("SPass files", "*.spass"), ("All files", "*.*")],
        )
        if not selected:
            return
        input_var.set(selected)
        output_var.set(str(Path(selected).with_suffix(".csv")))
        status_var.set("Ready to convert.")

    def choose_output() -> None:
        selected = filedialog.asksaveasfilename(
            title="Save CSV as",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
        )
        if selected:
            output_var.set(selected)

    def convert() -> None:
        if not input_var.get():
            messagebox.showwarning("Missing file", "Please choose a .spass file first.")
            return
        output_path = output_var.get() or str(Path(input_var.get()).with_suffix(".csv"))
        try:
            result = convert_spass_to_csv(input_var.get(), output_path)
        except ConversionError as exc:
            status_var.set("Conversion failed.")
            messagebox.showerror("Conversion failed", str(exc))
            return

        status = f"Saved {result.row_count} rows to {result.output_path}"
        if result.warnings:
            status += "\n\nWarnings:\n" + "\n".join(f"- {warning}" for warning in result.warnings)
        status_var.set(status)
        messagebox.showinfo("Done", status)

    Label(root, text="SPass export file").place(x=24, y=24)
    Entry(root, textvariable=input_var, width=62).place(x=24, y=50)
    Button(root, text="Browse", command=choose_input, width=12).place(x=520, y=46)

    Label(root, text="CSV output").place(x=24, y=88)
    Entry(root, textvariable=output_var, width=62).place(x=24, y=114)
    Button(root, text="Save as", command=choose_output, width=12).place(x=520, y=110)

    Button(root, text="Convert to CSV", command=convert, width=18).place(x=242, y=150)
    Label(root, textvariable=status_var, anchor="w", justify="left", wraplength=590).place(x=24, y=188)

    root.mainloop()
