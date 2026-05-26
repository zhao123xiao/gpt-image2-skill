# Mask Editing Reference

Masks are used only with `/v1/images/edits`, so they require at least one `--image`.

The edits convention is:

- transparent pixels are edited
- opaque pixels are preserved

The script always uploads a normalized PNG alpha mask saved under `OUTPUT_DIR/generated-masks/`.

## User-Provided Mask

```bash
python3 scripts/generate_image2.py \
  --image /absolute/source.png \
  --mask /absolute/mask.png \
  --prompt "Replace only the masked area. Preserve everything else."
```

Rules:

- alpha PNG masks preserve alpha semantics
- non-alpha masks use `white/bright = edit`, `black/dark = preserve`
- masks are resized to the first processed input image size

## Generated Masks

- `--mask-auto full`: edit the full image
- `--mask-auto center`: edit center 60%
- `--mask-auto border`: edit outer 15%
- `--mask-auto rect --mask-rect X,Y,W,H`: edit rectangle
- `--mask-auto circle --mask-circle X,Y,R`: edit circle
- `--mask-auto alpha`: edit transparent pixels from the first input image

## Manual Drawing

Use `--mask-draw` when the edit area needs to be painted or circled by hand:

```bash
python3 scripts/generate_image2.py \
  --image /absolute/source.png \
  --mask-draw \
  --prompt "Replace only the painted area. Preserve everything else."
```

The painter supports:

- brush painting
- rectangle selection
- circle selection
- eraser mode
- right-click erasing
- brush size changes
- save/cancel

Painted red areas become edit areas. The script saves the drawn mask under
`OUTPUT_DIR/drawn-masks/`, normalizes it to the API alpha-mask convention under
`OUTPUT_DIR/generated-masks/`, and then sends the normalized mask to `/v1/images/edits`.

The painter can also be used standalone:

```bash
python3 scripts/mask_painter.py \
  --image /absolute/source.png \
  --output /absolute/mask.png
```

`--mask-draw` requires a graphical desktop session with Python `tkinter`.

Modifiers:

- `--mask-invert`: swap edit/preserve
- `--mask-feather PX`: soften mask edge
- `--no-mask-overlay`: skip overlay preview

Mask overlays are saved under `OUTPUT_DIR/mask-overlays/` with red edit-area preview.
