from __future__ import annotations

import queue
import subprocess
import sys
import threading
from pathlib import Path
from tkinter import (
    BooleanVar,
    Button,
    Checkbutton,
    E,
    Entry,
    Frame,
    Label,
    OptionMenu,
    StringVar,
    Tk,
    W,
    filedialog,
    messagebox,
)

from .converter import ConversionError, ConversionResult, convert_spass_to_csv, default_output_path
from .exporters import ExportFormat, SPassExporter


def _open_in_file_manager(path: Path) -> None:
    """Reveal the given file in Finder / Explorer / the default file manager."""
    try:
        if sys.platform == "darwin":
            subprocess.run(["open", "-R", str(path)], check=False)
        elif sys.platform.startswith("win"):
            subprocess.run(["explorer", "/select,", str(path)], check=False)
        else:
            subprocess.run(["xdg-open", str(path.parent)], check=False)
    except OSError:
        pass


def _create_root() -> tuple[Tk, bool, object]:
    """Create the root window, enabling drag-and-drop only when tkinterdnd2 fully works.

    tkinterdnd2 can fail in two ways: the Python package is missing (ImportError),
    or the bundled native tkdnd library fails to load at Tk() creation time
    (TclError/RuntimeError — common in PyInstaller builds). Fall back to a plain
    Tk window in every failure case instead of crashing on startup.
    """
    try:
        from tkinterdnd2 import DND_FILES, TkinterDnD  # type: ignore[import-not-found]
    except Exception:
        return Tk(), False, None
    try:
        return TkinterDnD.Tk(), True, DND_FILES
    except Exception:
        return Tk(), False, None


def run_gui() -> None:
    root, dnd_available, dnd_files = _create_root()

    root.title("SPass CSV Converter")
    root.minsize(640, 340)

    input_var = StringVar()
    output_var = StringVar()
    password_var = StringVar()
    show_password_var = BooleanVar(value=False)
    format_var = StringVar(value=ExportFormat.CHROME)
    initial_hint = ".spass 파일을 선택하고 Samsung Pass 내보내기 비밀번호를 입력하세요."
    if dnd_available:
        initial_hint += " (창에 파일을 끌어다 놓아도 됩니다.)"
    status_var = StringVar(value=initial_hint)

    result_queue: "queue.Queue[ConversionResult | ConversionError]" = queue.Queue()
    last_output: dict[str, Path | None] = {"path": None}

    body = Frame(root, padx=20, pady=16)
    body.pack(fill="both", expand=True)
    body.columnconfigure(0, weight=1)

    def refresh_output_path() -> None:
        if input_var.get():
            output_var.set(str(default_output_path(input_var.get(), format_var.get())))

    def set_input(path: str) -> None:
        input_var.set(path)
        refresh_output_path()
        status_var.set("변환 준비 완료.")

    def choose_input() -> None:
        selected = filedialog.askopenfilename(
            title="SPass 내보내기 파일 선택",
            filetypes=[("SPass files", "*.spass"), ("All files", "*.*")],
        )
        if selected:
            set_input(selected)

    def choose_output() -> None:
        extension = ".json" if format_var.get() == ExportFormat.BITWARDEN_JSON else ".csv"
        filetypes = [("JSON files", "*.json")] if extension == ".json" else [("CSV files", "*.csv")]
        selected = filedialog.asksaveasfilename(
            title="저장 위치 선택",
            defaultextension=extension,
            filetypes=filetypes,
        )
        if selected:
            output_var.set(selected)

    def toggle_password() -> None:
        password_entry.config(show="" if show_password_var.get() else "*")

    def set_busy(busy: bool) -> None:
        convert_button.config(state="disabled" if busy else "normal", text="변환 중…" if busy else "변환하기")

    def poll_result() -> None:
        try:
            outcome = result_queue.get_nowait()
        except queue.Empty:
            root.after(100, poll_result)
            return
        set_busy(False)
        if isinstance(outcome, ConversionError):
            status_var.set("변환에 실패했습니다.")
            messagebox.showerror("변환 실패", str(outcome))
            return
        last_output["path"] = Path(outcome.output_path)
        open_button.grid()
        status = f"{outcome.row_count}개 항목을 {outcome.format_name} 형식으로 저장했습니다:\n{outcome.output_path}"
        if outcome.warnings:
            status += "\n\n주의:\n" + "\n".join(f"- {warning}" for warning in outcome.warnings)
        status += "\n\n출력 파일에는 평문 비밀번호가 들어 있으니 가져오기가 끝나면 안전하게 삭제하세요."
        status_var.set(status)

    def convert() -> None:
        if not input_var.get():
            messagebox.showwarning("파일 없음", "먼저 .spass 파일을 선택해주세요.")
            return
        if not password_var.get():
            messagebox.showwarning("비밀번호 없음", "Samsung Pass 내보내기 비밀번호를 입력해주세요.")
            return
        output_path = output_var.get() or str(default_output_path(input_var.get(), format_var.get()))
        set_busy(True)
        open_button.grid_remove()
        status_var.set("변환 중…")

        def worker() -> None:
            try:
                result = convert_spass_to_csv(
                    input_var.get(),
                    output_path,
                    password=password_var.get(),
                    format_name=format_var.get(),
                    allow_plain_fallback=False,
                )
            except ConversionError as exc:
                result_queue.put(exc)
            else:
                result_queue.put(result)

        threading.Thread(target=worker, daemon=True).start()
        root.after(100, poll_result)

    def open_output_folder() -> None:
        if last_output["path"] is not None:
            _open_in_file_manager(last_output["path"])

    def format_changed(_value: str) -> None:
        refresh_output_path()

    # --- input file row ---
    Label(body, text="SPass 내보내기 파일").grid(row=0, column=0, sticky=W)
    input_row = Frame(body)
    input_row.grid(row=1, column=0, sticky=W + E, pady=(2, 10))
    input_row.columnconfigure(0, weight=1)
    Entry(input_row, textvariable=input_var).grid(row=0, column=0, sticky=W + E, padx=(0, 8))
    Button(input_row, text="찾아보기", command=choose_input, width=10).grid(row=0, column=1)

    # --- password + format row ---
    middle = Frame(body)
    middle.grid(row=2, column=0, sticky=W + E, pady=(0, 10))
    middle.columnconfigure(0, weight=1)

    Label(middle, text="내보내기 비밀번호").grid(row=0, column=0, sticky=W)
    password_entry = Entry(middle, textvariable=password_var, show="*")
    password_entry.grid(row=1, column=0, sticky=W + E, padx=(0, 12))
    Checkbutton(middle, text="표시", variable=show_password_var, command=toggle_password).grid(row=1, column=1, sticky=W)

    Label(middle, text="출력 형식").grid(row=0, column=2, sticky=W, padx=(16, 0))
    format_menu = OptionMenu(middle, format_var, *sorted(SPassExporter.FORMATS), command=format_changed)
    format_menu.config(width=16)
    format_menu.grid(row=1, column=2, sticky=W, padx=(16, 0))

    # --- output file row ---
    Label(body, text="저장할 파일").grid(row=3, column=0, sticky=W)
    output_row = Frame(body)
    output_row.grid(row=4, column=0, sticky=W + E, pady=(2, 14))
    output_row.columnconfigure(0, weight=1)
    Entry(output_row, textvariable=output_var).grid(row=0, column=0, sticky=W + E, padx=(0, 8))
    Button(output_row, text="다른 이름으로", command=choose_output, width=10).grid(row=0, column=1)

    # --- action row ---
    action_row = Frame(body)
    action_row.grid(row=5, column=0)
    convert_button = Button(action_row, text="변환하기", command=convert, width=16)
    convert_button.grid(row=0, column=0, padx=4)
    open_button = Button(action_row, text="저장 폴더 열기", command=open_output_folder, width=14)
    open_button.grid(row=0, column=1, padx=4)
    open_button.grid_remove()

    Label(body, textvariable=status_var, anchor=W, justify="left", wraplength=600).grid(
        row=6, column=0, sticky=W + E, pady=(14, 0)
    )

    root.bind("<Return>", lambda _event: convert())

    if dnd_available:
        def on_drop(event: object) -> None:
            raw = getattr(event, "data", "")
            paths = root.tk.splitlist(raw)
            if paths:
                set_input(paths[0])

        try:
            root.drop_target_register(dnd_files)  # type: ignore[attr-defined]
            root.dnd_bind("<<Drop>>", on_drop)  # type: ignore[attr-defined]
        except Exception:
            pass

    root.mainloop()
