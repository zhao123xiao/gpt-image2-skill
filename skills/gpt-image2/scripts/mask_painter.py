#!/usr/bin/env python3
"""Interactive mask painter for Dreamfield image edits."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Paint an edit mask for gpt-image2 image edits.")
    parser.add_argument("--image", required=True, type=Path, help="Source image to annotate.")
    parser.add_argument("--output", required=True, type=Path, help="Output PNG alpha mask path.")
    parser.add_argument("--overlay", type=Path, help="Optional red edit-area overlay preview path.")
    parser.add_argument("--max-display-side", type=int, default=1200, help="Maximum displayed image side.")
    parser.add_argument("--brush-size", type=int, default=48, help="Initial brush size in source-image pixels.")
    parser.add_argument("--feather", type=float, default=0.0, help="Optional feather radius for saved mask.")
    return parser.parse_args()


def require_gui_deps():
    try:
        import tkinter as tk
        from tkinter import ttk
    except ImportError as exc:
        raise RuntimeError("tkinter is required for the manual mask painter.") from exc
    try:
        from PIL import Image, ImageDraw, ImageFilter, ImageOps, ImageTk
    except ImportError as exc:
        raise RuntimeError("Pillow is required for the manual mask painter.") from exc
    return tk, ttk, Image, ImageDraw, ImageFilter, ImageOps, ImageTk


class MaskPainter:
    def __init__(self, args: argparse.Namespace) -> None:
        tk, ttk, Image, ImageDraw, ImageFilter, ImageOps, ImageTk = require_gui_deps()
        self.tk = tk
        self.ttk = ttk
        self.Image = Image
        self.ImageDraw = ImageDraw
        self.ImageFilter = ImageFilter
        self.ImageOps = ImageOps
        self.ImageTk = ImageTk

        self.source_path = args.image.expanduser().resolve()
        self.output_path = args.output.expanduser().resolve()
        self.overlay_path = args.overlay.expanduser().resolve() if args.overlay else None
        self.max_display_side = args.max_display_side
        self.feather = args.feather

        with Image.open(self.source_path) as image:
            self.base = ImageOps.exif_transpose(image).convert("RGBA")
        self.width, self.height = self.base.size
        self.edit_mask = Image.new("L", self.base.size, 0)
        self.draw = ImageDraw.Draw(self.edit_mask)

        scale = min(1.0, self.max_display_side / max(self.width, self.height))
        self.display_size = (max(1, round(self.width * scale)), max(1, round(self.height * scale)))
        self.scale = self.display_size[0] / self.width
        self.display_base = self.base.resize(self.display_size, Image.Resampling.LANCZOS)

        self.root = tk.Tk()
        self.root.title("gpt-image2 Manual Mask Painter")
        self.root.protocol("WM_DELETE_WINDOW", self.cancel)
        self.mode = tk.StringVar(value="brush")
        self.brush_size = tk.IntVar(value=max(1, args.brush_size))
        self.status = tk.StringVar(value="Paint red areas to edit. Save writes API-ready alpha mask.")
        self.start_xy: tuple[int, int] | None = None
        self.last_xy: tuple[int, int] | None = None
        self.preview_id: int | None = None
        self.photo = None
        self.saved = False

        self.build_ui()
        self.bind_keys()
        self.render()

    def build_ui(self) -> None:
        frame = self.ttk.Frame(self.root, padding=8)
        frame.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)

        toolbar = self.ttk.Frame(frame)
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        for text, value in (("Brush", "brush"), ("Rect", "rect"), ("Circle", "circle"), ("Eraser", "erase")):
            self.ttk.Radiobutton(toolbar, text=text, value=value, variable=self.mode).pack(side="left", padx=(0, 6))

        self.ttk.Label(toolbar, text="Brush").pack(side="left", padx=(12, 4))
        self.ttk.Scale(toolbar, from_=4, to=240, variable=self.brush_size, orient="horizontal", length=160).pack(
            side="left"
        )
        self.ttk.Button(toolbar, text="Clear", command=self.clear).pack(side="left", padx=(12, 4))
        self.ttk.Button(toolbar, text="Save", command=self.save).pack(side="right", padx=(4, 0))
        self.ttk.Button(toolbar, text="Cancel", command=self.cancel).pack(side="right")

        self.canvas = self.tk.Canvas(
            frame,
            width=self.display_size[0],
            height=self.display_size[1],
            highlightthickness=0,
            cursor="crosshair",
        )
        self.canvas.grid(row=1, column=0, sticky="nsew")
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<ButtonPress-3>", self.on_right_press)
        self.canvas.bind("<B3-Motion>", self.on_right_drag)

        self.ttk.Label(frame, textvariable=self.status).grid(row=2, column=0, sticky="ew", pady=(8, 0))

    def bind_keys(self) -> None:
        self.root.bind("b", lambda _event: self.mode.set("brush"))
        self.root.bind("r", lambda _event: self.mode.set("rect"))
        self.root.bind("c", lambda _event: self.mode.set("circle"))
        self.root.bind("e", lambda _event: self.mode.set("erase"))
        self.root.bind("<Control-s>", lambda _event: self.save())
        self.root.bind("<Escape>", lambda _event: self.cancel())
        self.root.bind("+", lambda _event: self.adjust_brush(6))
        self.root.bind("=", lambda _event: self.adjust_brush(6))
        self.root.bind("-", lambda _event: self.adjust_brush(-6))

    def adjust_brush(self, delta: int) -> None:
        self.brush_size.set(max(1, min(240, self.brush_size.get() + delta)))

    def image_xy(self, event) -> tuple[int, int]:
        x = min(max(int(event.x / self.scale), 0), self.width - 1)
        y = min(max(int(event.y / self.scale), 0), self.height - 1)
        return x, y

    def display_xy(self, point: tuple[int, int]) -> tuple[int, int]:
        return round(point[0] * self.scale), round(point[1] * self.scale)

    def render(self) -> None:
        display_mask = self.edit_mask.resize(self.display_size, self.Image.Resampling.LANCZOS)
        overlay_alpha = self.Image.eval(display_mask, lambda pixel: round(pixel * 0.45))
        overlay = self.Image.new("RGBA", self.display_size, (255, 0, 0, 0))
        overlay.putalpha(overlay_alpha)
        composite = self.Image.alpha_composite(self.display_base, overlay)
        self.photo = self.ImageTk.PhotoImage(composite)
        self.canvas.delete("image")
        self.canvas.create_image(0, 0, image=self.photo, anchor="nw", tags="image")
        self.canvas.tag_lower("image")

    def draw_brush_at(self, point: tuple[int, int], fill: int) -> None:
        radius = max(1, self.brush_size.get() // 2)
        x, y = point
        self.draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=fill)

    def draw_brush_line(self, start: tuple[int, int], end: tuple[int, int], fill: int) -> None:
        width = max(1, self.brush_size.get())
        self.draw.line([start, end], fill=fill, width=width)
        self.draw_brush_at(end, fill)

    def on_press(self, event) -> None:
        point = self.image_xy(event)
        self.start_xy = point
        self.last_xy = point
        if self.mode.get() in {"brush", "erase"}:
            self.draw_brush_at(point, 0 if self.mode.get() == "erase" else 255)
            self.render()

    def on_drag(self, event) -> None:
        point = self.image_xy(event)
        mode = self.mode.get()
        if mode in {"brush", "erase"} and self.last_xy:
            self.draw_brush_line(self.last_xy, point, 0 if mode == "erase" else 255)
            self.last_xy = point
            self.render()
            return
        if mode in {"rect", "circle"} and self.start_xy:
            self.update_shape_preview(self.start_xy, point, mode)

    def on_release(self, event) -> None:
        if not self.start_xy:
            return
        point = self.image_xy(event)
        mode = self.mode.get()
        if mode in {"rect", "circle"}:
            self.draw_shape(self.start_xy, point, mode, 255)
            self.clear_preview()
            self.render()
        self.start_xy = None
        self.last_xy = None

    def on_right_press(self, event) -> None:
        point = self.image_xy(event)
        self.last_xy = point
        self.draw_brush_at(point, 0)
        self.render()

    def on_right_drag(self, event) -> None:
        point = self.image_xy(event)
        if self.last_xy:
            self.draw_brush_line(self.last_xy, point, 0)
        self.last_xy = point
        self.render()

    def update_shape_preview(self, start: tuple[int, int], end: tuple[int, int], mode: str) -> None:
        self.clear_preview()
        x1, y1 = self.display_xy(start)
        x2, y2 = self.display_xy(end)
        if mode == "rect":
            self.preview_id = self.canvas.create_rectangle(x1, y1, x2, y2, outline="#ff3333", width=2)
        else:
            self.preview_id = self.canvas.create_oval(x1, y1, x2, y2, outline="#ff3333", width=2)

    def clear_preview(self) -> None:
        if self.preview_id is not None:
            self.canvas.delete(self.preview_id)
            self.preview_id = None

    def draw_shape(self, start: tuple[int, int], end: tuple[int, int], mode: str, fill: int) -> None:
        x1, x2 = sorted((start[0], end[0]))
        y1, y2 = sorted((start[1], end[1]))
        if abs(x2 - x1) < 2 or abs(y2 - y1) < 2:
            return
        if mode == "rect":
            self.draw.rectangle([x1, y1, x2, y2], fill=fill)
        else:
            self.draw.ellipse([x1, y1, x2, y2], fill=fill)

    def clear(self) -> None:
        self.edit_mask.paste(0)
        self.render()
        self.status.set("Mask cleared.")

    def save_overlay(self, edit_mask) -> None:
        if not self.overlay_path:
            return
        overlay_alpha = self.Image.eval(edit_mask, lambda pixel: round(pixel * 0.45))
        overlay = self.Image.new("RGBA", self.base.size, (255, 0, 0, 0))
        overlay.putalpha(overlay_alpha)
        self.overlay_path.parent.mkdir(parents=True, exist_ok=True)
        self.Image.alpha_composite(self.base, overlay).save(self.overlay_path, format="PNG")

    def save(self) -> None:
        edit_mask = self.edit_mask
        if self.feather > 0:
            edit_mask = edit_mask.filter(self.ImageFilter.GaussianBlur(radius=self.feather))
        alpha = self.Image.eval(edit_mask, lambda pixel: 255 - pixel)
        output = self.Image.new("RGBA", self.base.size, (255, 255, 255, 255))
        output.putalpha(alpha)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        output.save(self.output_path, format="PNG")
        self.save_overlay(edit_mask)
        self.saved = True
        self.status.set(f"Saved: {self.output_path}")
        self.root.after(250, self.root.destroy)

    def cancel(self) -> None:
        self.saved = False
        self.root.destroy()

    def run(self) -> int:
        self.root.mainloop()
        return 0 if self.saved else 2


def main() -> int:
    args = parse_args()
    try:
        app = MaskPainter(args)
        return app.run()
    except RuntimeError as exc:
        print(f"Mask painter error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Mask painter failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
