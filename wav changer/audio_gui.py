"""Desktop GUI for the FFmpeg audio converter."""

from __future__ import annotations

import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import cast

from PIL import Image, ImageEnhance, ImageOps, ImageTk

from backsend import SUPPORTED_OUTPUT_FORMATS, ConversionError, convert_file


FORMAT_ORDER = ("wav", "mp3", "flac", "ogg", "opus", "m4a", "aac", "ac3", "mp4", "webm")
FORMAT_LABELS = {
    "wav": "WAV - uncompressed",
    "mp3": "MP3 - universal",
    "flac": "FLAC - lossless",
    "ogg": "OGG - open format",
    "opus": "OPUS - modern compressed",
    "m4a": "M4A - AAC audio",
    "aac": "AAC - compressed",
    "ac3": "AC3 - surround audio",
    "mp4": "MP4 - audio container",
    "webm": "WEBM - web audio",
}


class AudioConverterApp(tk.Tk):
    """Responsive desktop front end for :func:`backsend.convert_file`."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Waveforge Audio Converter")
        self.geometry("760x620")
        self.minsize(620, 500)
        self.configure(bg="#10151b")
        self._setup_visuals()

        self.input_path = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.output_name = tk.StringVar()
        self.output_format = tk.StringVar(value="wav")
        self.status_text = tk.StringVar(value="Ready when you are")
        self.file_detail = tk.StringVar(value="No audio file selected")
        self.is_converting = False
        self.events: queue.Queue[tuple[str, object]] = queue.Queue()

        self._configure_styles()
        self._build_ui()
        self.after(100, self._process_events)

    def _setup_visuals(self) -> None:
        asset_dir = Path(__file__).resolve().parent
        self.background_canvas = tk.Canvas(self, highlightthickness=0, bd=0, bg="#10151b")
        self.background_canvas.place(relx=0, rely=0, relwidth=1, relheight=1)

        background_path = asset_dir / "background.jpg"
        self._background_source = Image.open(background_path).convert("RGB")
        self._background_photo: ImageTk.PhotoImage | None = None
        self.background_canvas.bind("<Configure>", self._resize_background)

        icon_path = asset_dir / "icon.ico"
        icon_image = Image.open(icon_path).convert("RGBA")
        icon_image.thumbnail((64, 64), Image.Resampling.LANCZOS)
        self._icon_photo = ImageTk.PhotoImage(icon_image)
        self.iconphoto(False, cast(tk.PhotoImage, self._icon_photo))

    def _resize_background(self, event: tk.Event[tk.Misc]) -> None:
        width, height = max(event.width, 1), max(event.height, 1)
        image = ImageOps.fit(self._background_source, (width, height), method=Image.Resampling.LANCZOS)
        image = ImageEnhance.Brightness(image).enhance(0.42)
        image = Image.blend(Image.new("RGB", image.size, "#10151b"), image, 0.38)
        self._background_photo = ImageTk.PhotoImage(image)
        self.background_canvas.delete("background")
        self.background_canvas.create_image(0, 0, anchor="nw", image=self._background_photo, tags="background")

    def _configure_styles(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("App.TFrame", background="#10151b")
        style.configure("Panel.TFrame", background="#18222b")
        style.configure("Title.TLabel", background="#10151b", foreground="#f4f7f8", font=("Segoe UI", 25, "bold"))
        style.configure("Subtitle.TLabel", background="#10151b", foreground="#9cabb5", font=("Segoe UI", 10))
        style.configure("PanelTitle.TLabel", background="#18222b", foreground="#f4f7f8", font=("Segoe UI", 12, "bold"))
        style.configure("PanelText.TLabel", background="#18222b", foreground="#9cabb5", font=("Segoe UI", 9))
        style.configure("Value.TLabel", background="#18222b", foreground="#e8eef0", font=("Segoe UI", 10))
        style.configure("Status.TLabel", background="#10151b", foreground="#61d6a5", font=("Segoe UI", 10, "bold"))
        style.configure("Action.TButton", background="#39c693", foreground="#07120f", font=("Segoe UI", 11, "bold"), padding=(18, 11), borderwidth=0)
        style.map("Action.TButton", background=[("active", "#63e1b4"), ("disabled", "#40554e")], foreground=[("disabled", "#9ba9a4")])
        style.configure("Secondary.TButton", background="#26343f", foreground="#dbe6e9", font=("Segoe UI", 9, "bold"), padding=(12, 8), borderwidth=0)
        style.map("Secondary.TButton", background=[("active", "#344856")])
        style.configure("Format.TCombobox", fieldbackground="#22303a", background="#22303a", foreground="#e8eef0", arrowcolor="#61d6a5", padding=7)
        style.map("Format.TCombobox", fieldbackground=[("readonly", "#22303a")], foreground=[("readonly", "#e8eef0")])
        style.configure("Thin.Horizontal.TProgressbar", background="#39c693", troughcolor="#22303a", borderwidth=0, thickness=5)

    def _build_ui(self) -> None:
        root = ttk.Frame(self, style="App.TFrame", padding=(42, 34, 42, 30))
        root.pack(fill="both", expand=True)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(2, weight=1)

        heading = ttk.Frame(root, style="App.TFrame")
        heading.grid(row=0, column=0, sticky="ew", pady=(0, 25))
        ttk.Label(heading, text="WAVEFORGE", style="Title.TLabel").pack(anchor="w")
        ttk.Label(heading, text="Convert audio cleanly, in a few clicks.", style="Subtitle.TLabel").pack(anchor="w", pady=(4, 0))

        self._build_file_panel(root)
        self._build_options_panel(root)
        self._build_footer(root)

    def _build_file_panel(self, parent: ttk.Frame) -> None:
        panel = ttk.Frame(parent, style="Panel.TFrame", padding=22)
        panel.grid(row=1, column=0, sticky="ew", pady=(0, 14))
        panel.columnconfigure(0, weight=1)

        ttk.Label(panel, text="SOURCE AUDIO", style="PanelText.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(panel, textvariable=self.file_detail, style="PanelTitle.TLabel").grid(row=1, column=0, sticky="w", pady=(7, 2))
        ttk.Label(panel, textvariable=self.input_path, style="PanelText.TLabel").grid(row=2, column=0, sticky="w")
        ttk.Button(panel, text="Choose audio file", style="Secondary.TButton", command=self._choose_input).grid(row=1, column=1, rowspan=2, padx=(18, 0))

    def _build_options_panel(self, parent: ttk.Frame) -> None:
        panel = ttk.Frame(parent, style="Panel.TFrame", padding=22)
        panel.grid(row=2, column=0, sticky="nsew", pady=(0, 14))
        panel.columnconfigure(1, weight=1)

        ttk.Label(panel, text="OUTPUT SETTINGS", style="PanelText.TLabel").grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 20))
        ttk.Label(panel, text="Format", style="Value.TLabel").grid(row=1, column=0, sticky="w", padx=(0, 18))
        choices = [FORMAT_LABELS[format_name] for format_name in FORMAT_ORDER if format_name in SUPPORTED_OUTPUT_FORMATS]
        self.format_box = ttk.Combobox(panel, style="Format.TCombobox", state="readonly", values=choices, width=30)
        self.format_box.current(0)
        self.format_box.grid(row=1, column=1, sticky="ew")
        self.format_box.bind("<<ComboboxSelected>>", self._format_changed)
        ttk.Label(panel, text="Choose the file type you want to create", style="PanelText.TLabel").grid(row=2, column=1, sticky="w", pady=(5, 0))

        ttk.Label(panel, text="File name", style="Value.TLabel").grid(row=3, column=0, sticky="w", padx=(0, 18), pady=(26, 0))
        ttk.Entry(panel, textvariable=self.output_name).grid(row=3, column=1, sticky="ew", pady=(26, 0))
        ttk.Label(panel, text="Choose the name for the converted file", style="PanelText.TLabel").grid(row=4, column=1, sticky="w", pady=(5, 0))

        ttk.Label(panel, text="Save to", style="Value.TLabel").grid(row=5, column=0, sticky="w", padx=(0, 18), pady=(20, 0))
        self.folder_entry = ttk.Entry(panel, textvariable=self.output_dir, state="readonly")
        self.folder_entry.grid(row=5, column=1, sticky="ew", pady=(20, 0))
        ttk.Button(panel, text="Browse", style="Secondary.TButton", command=self._choose_output_dir).grid(row=5, column=2, padx=(12, 0), pady=(20, 0))
        ttk.Label(panel, text="Leave the folder unchanged to save beside the source file", style="PanelText.TLabel").grid(row=6, column=1, sticky="w", pady=(5, 0))

    def _build_footer(self, parent: ttk.Frame) -> None:
        footer = ttk.Frame(parent, style="App.TFrame")
        footer.grid(row=3, column=0, sticky="ew")
        footer.columnconfigure(0, weight=1)
        ttk.Label(footer, textvariable=self.status_text, style="Status.TLabel").grid(row=0, column=0, sticky="w")
        self.progress = ttk.Progressbar(footer, style="Thin.Horizontal.TProgressbar", mode="indeterminate", length=130)
        self.progress.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        self.convert_button = ttk.Button(footer, text="Convert audio", style="Action.TButton", command=self._start_conversion)
        self.convert_button.grid(row=0, column=1, rowspan=2, padx=(22, 0))

    def _choose_input(self) -> None:
        selected = filedialog.askopenfilename(
            title="Choose an audio file",
            filetypes=[("Audio files", "*.*"), ("All files", "*.*")],
        )
        if not selected:
            return
        source = Path(selected)
        self.input_path.set(str(source))
        self.file_detail.set(f"{source.name}  |  {self._format_size(source.stat().st_size)}")
        self.output_name.set(source.stem)
        if not self.output_dir.get():
            self.output_dir.set(str(source.parent))
        self.status_text.set("Ready to convert")

    def _choose_output_dir(self) -> None:
        selected = filedialog.askdirectory(title="Choose output folder")
        if selected:
            self.output_dir.set(selected)

    def _format_changed(self, _event: object = None) -> None:
        selected_format = self._selected_format()
        self.output_format.set(selected_format)
        self.status_text.set(f"Output format: {selected_format.upper()}")

    def _selected_format(self) -> str:
        return self.format_box.get().split(" ", 1)[0].lower()

    @staticmethod
    def _format_size(size: int) -> str:
        if size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        return f"{size / (1024 * 1024):.1f} MB"

    def _start_conversion(self) -> None:
        if self.is_converting:
            return
        if not self.input_path.get():
            messagebox.showinfo("Choose a file", "Select an audio file to begin.", parent=self)
            return

        source = Path(self.input_path.get())
        output_format = self._selected_format()
        destination_dir = Path(self.output_dir.get()) if self.output_dir.get() else source.parent
        output_name = self.output_name.get().strip()
        if not output_name:
            messagebox.showinfo("Enter a file name", "Give the converted file a name before converting.", parent=self)
            return
        output_name = Path(output_name).name
        if Path(output_name).suffix:
            output_name = Path(output_name).stem
        destination = destination_dir / f"{output_name}.{output_format}"

        if destination.resolve() == source.resolve():
            messagebox.showwarning("Choose another format", "The output format matches the source file. Choose a different format.", parent=self)
            return
        if destination.exists() and not messagebox.askyesno("Replace existing file?", f"{destination.name} already exists. Replace it?", parent=self):
            return

        self.is_converting = True
        self.convert_button.configure(state="disabled")
        self.progress.start(10)
        self.status_text.set("Converting audio...")
        worker = threading.Thread(target=self._convert_in_background, args=(source, destination), daemon=True)
        worker.start()

    def _convert_in_background(self, source: Path, destination: Path) -> None:
        try:
            result = convert_file(source, destination, overwrite=True)
            self.events.put(("success", result))
        except (ConversionError, OSError) as error:
            self.events.put(("error", str(error)))

    def _process_events(self) -> None:
        try:
            event, payload = self.events.get_nowait()
        except queue.Empty:
            self.after(100, self._process_events)
            return

        self.progress.stop()
        self.convert_button.configure(state="normal")
        self.is_converting = False
        if event == "success":
            self.status_text.set("Conversion complete")
            messagebox.showinfo("Done", f"Created:\n{payload}", parent=self)
        else:
            self.status_text.set("Conversion failed")
            messagebox.showerror("Conversion failed", str(payload), parent=self)
        self.after(100, self._process_events)


def main() -> None:
    app = AudioConverterApp()
    app.mainloop()


if __name__ == "__main__":
    main()
