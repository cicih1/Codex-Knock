from __future__ import annotations

import argparse
import sys
import tkinter as tk
from tkinter import font


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Show a local Codex Nock desktop popup.")
    parser.add_argument("--title", default="Codex task finished")
    parser.add_argument("--body", default="")
    parser.add_argument("--timeout", type=int, default=0, help="Auto-close after N seconds. 0 keeps it open.")
    parser.add_argument("--fullscreen", action="store_true", help="Use a full-screen alert.")
    parser.add_argument("--accent", default="#12b981", help="Accent color.")
    args = parser.parse_args(argv)

    show_popup(args.title, args.body, args.timeout, args.fullscreen, args.accent)
    return 0


def show_popup(title: str, body: str, timeout: int, fullscreen: bool, accent: str) -> None:
    root = tk.Tk()
    root.title(title)
    root.configure(bg="#101418")
    root.attributes("-topmost", True)

    if fullscreen:
        root.attributes("-fullscreen", True)
    else:
        width, height = 760, 420
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = max(0, (screen_width - width) // 2)
        y = max(0, (screen_height - height) // 2)
        root.geometry(f"{width}x{height}+{x}+{y}")

    root.bind("<Escape>", lambda _event: root.destroy())
    root.bind("<Return>", lambda _event: root.destroy())
    root.bind("<space>", lambda _event: root.destroy())

    outer = tk.Frame(root, bg="#101418")
    outer.pack(fill="both", expand=True)

    bar = tk.Frame(outer, bg=accent, height=12)
    bar.pack(fill="x", side="top")

    content = tk.Frame(outer, bg="#101418", padx=48, pady=42)
    content.pack(fill="both", expand=True)
    content.grid_rowconfigure(0, weight=1)
    content.grid_rowconfigure(1, weight=0)
    content.grid_rowconfigure(2, weight=1)
    content.grid_columnconfigure(0, weight=1)

    title_font = font.Font(family="Segoe UI", size=44 if fullscreen else 32, weight="bold")
    body_font = font.Font(family="Segoe UI", size=22 if fullscreen else 17)
    hint_font = font.Font(family="Segoe UI", size=12)
    wraplength = max(320, root.winfo_screenwidth() - 180 if fullscreen else 660)

    center = tk.Frame(content, bg="#101418")
    center.grid(row=1, column=0, sticky="nsew")

    title_label = tk.Label(
        center,
        text=title,
        bg="#101418",
        fg="#f8fafc",
        font=title_font,
        justify="center",
        anchor="center",
        wraplength=wraplength,
    )
    title_label.pack(fill="x", anchor="center")

    body_label = tk.Label(
        center,
        text=body,
        bg="#101418",
        fg="#d7e0ea",
        font=body_font,
        justify="center",
        anchor="center",
        wraplength=wraplength,
    )
    body_label.pack(fill="x", anchor="center", pady=(30, 0))

    hint = "Press Enter, Space, or Esc to close"
    if timeout > 0:
        hint = f"{hint} - auto closes in {timeout}s"
    hint_label = tk.Label(content, text=hint, bg="#101418", fg="#93a4b5", font=hint_font, anchor="center")
    hint_label.grid(row=2, column=0, sticky="s", pady=(24, 0))

    if timeout > 0:
        root.after(timeout * 1000, root.destroy)

    root.focus_force()
    root.mainloop()


if __name__ == "__main__":
    raise SystemExit(main())
