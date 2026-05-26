# GPT Image 2 CLI Reference

Run:

```bash
SKILL_DIR="${CODEX_HOME:-$HOME/.codex}/skills/gpt-image2"
python3 "$SKILL_DIR/scripts/generate_image2.py" [options]
```

## Core Inputs

- `--prompt TEXT`: prompt text. Mutually exclusive with `--prompt-file`.
- `--prompt-file PATH`: UTF-8 prompt file.
- `--model MODEL`: default `gpt-image-2`.
- `--size WIDTHxHEIGHT`: API request size. Default `1792x1024`.
- `--n N`: number of variants. Default `1`.
- `--response-format b64_json|url`: default `b64_json`.

## Image-To-Image

- `--image PATH`: input/reference image. Repeat for multiple images.
- `--clipboard-image`: save OS clipboard image to a temporary PNG and use it as `--image`.
- `--clipboard-dir PATH`: directory for clipboard snapshots. Default `OUTPUT_DIR/clipboard-inputs`.

## Mask Editing

- `--mask PATH`: user-provided mask image.
- `--mask-draw`: open a manual painter to brush, rectangle, or circle the edit area.
- `--mask-auto full|center|border|rect|circle|alpha`: generate a mask.
- `--mask-rect X,Y,W,H`: rectangle for `--mask-auto rect`.
- `--mask-circle X,Y,R`: circle for `--mask-auto circle`.
- `--mask-invert`: invert edit/preserve areas.
- `--mask-feather PX`: blur mask edge by this many pixels.
- `--no-mask-overlay`: do not create overlay preview.

Manual painter standalone usage:

```bash
SKILL_DIR="${CODEX_HOME:-$HOME/.codex}/skills/gpt-image2"
python3 "$SKILL_DIR/scripts/mask_painter.py" \
  --image /absolute/source.png \
  --output /absolute/mask.png
```

## Preprocessing

Preprocessing is enabled by default for input images.

- `--no-preprocess`: upload original input image files.
- `--max-input-side N`: default `2048`.
- `--max-input-megapixels N`: default `8`.
- `--jpeg-quality N`: default `92`.

Processed copies are saved under `OUTPUT_DIR/processed-inputs/`.

## Output

- `--output-dir PATH`: default `./gpt-image2-output`.
- `--basename NAME`: default `image2`.
- `--target-size WIDTHxHEIGHT`: crop/resize each result after generation.
- `--dry-run`: validate and print request details without calling the API.
- `--self-test`: run offline environment checks and exit.

Each run writes a `BASENAME_TIMESTAMP.summary.json` result index unless it exits before request setup.

## Packaging

```bash
SKILL_DIR="${CODEX_HOME:-$HOME/.codex}/skills/gpt-image2"
python3 "$SKILL_DIR/scripts/package_skill.py" [OUTPUT_ZIP]
```
