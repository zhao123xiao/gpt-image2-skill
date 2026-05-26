# GPT Image 2 Skill

Language: [简体中文](README.md) | **English**

A Codex skill for Dreamfield `gpt-image-2` image generation and editing. It uses Dreamfield's OpenAI-compatible image API and supports text-to-image, image-to-image, clipboard image input, localized editing, auto masks, manual mask painting, and result summaries.

## Features

- Text-to-image generation from prompts.
- Image-to-image generation from local or clipboard reference images.
- Localized editing and inpainting through masks.
- Auto masks for full image, center, border, rectangle, circle, and alpha areas.
- Manual mask painting through `mask_painter.py`.
- Mask overlay previews for checking the actual edit area.
- Input image preprocessing to resize or compress uploads.
- `summary.json` result index for inputs, masks, responses, and outputs.
- Offline self-test for Python, Pillow, tkinter, API key, clipboard backend, and script paths.
- Packaging script for regenerating a distributable skill zip.

## Install

Install this skill from the repository path:

```bash
python3 install-skill-from-github.py --repo zhao123xiao/gpt-image2-skill --path skills/gpt-image2
```

After installation, restart Codex.

## Environment

Recommended provider and model:

- Provider: [Dreamfield](https://www.dreamfield.top/)
- Model: `gpt-image-2`
- API key environment variable: `NEW_image2_API_KEY`

Author note: this skill has been tested with Dreamfield for personal use. It supports 4K output. For details, check Dreamfield for current pricing and model limits.

Set the API key before using the skill:

```bash
export NEW_image2_API_KEY='your_api_key'
```

## Quick Start

Text-to-image:

```bash
SKILL_DIR="${CODEX_HOME:-$HOME/.codex}/skills/gpt-image2"
python3 "$SKILL_DIR/scripts/generate_image2.py" \
  --prompt "A cinematic 16:9 desktop wallpaper of golden lightning over green hills at sunset, no text, no watermark." \
  --size 1792x1024
```

Image-to-image:

```bash
SKILL_DIR="${CODEX_HOME:-$HOME/.codex}/skills/gpt-image2"
python3 "$SKILL_DIR/scripts/generate_image2.py" \
  --image "/absolute/path/to/reference.png" \
  --prompt "Create a new photorealistic 16:9 wallpaper inspired by this reference image, no text, no watermark." \
  --size 1792x1024
```

Localized edit with a rectangle mask:

```bash
SKILL_DIR="${CODEX_HOME:-$HOME/.codex}/skills/gpt-image2"
python3 "$SKILL_DIR/scripts/generate_image2.py" \
  --image "/absolute/path/to/source.png" \
  --mask-auto rect \
  --mask-rect 120,80,640,360 \
  --prompt "Replace only the masked area while preserving the rest of the image. No text, no watermark." \
  --size 1792x1024
```

Localized edit with manual mask painting:

```bash
SKILL_DIR="${CODEX_HOME:-$HOME/.codex}/skills/gpt-image2"
python3 "$SKILL_DIR/scripts/generate_image2.py" \
  --image "/absolute/path/to/source.png" \
  --mask-draw \
  --prompt "Replace only the painted area while preserving the rest of the image. No text, no watermark." \
  --size 1792x1024
```

Offline self-test:

```bash
SKILL_DIR="${CODEX_HOME:-$HOME/.codex}/skills/gpt-image2"
python3 "$SKILL_DIR/scripts/generate_image2.py" --self-test
```

Package the skill:

```bash
SKILL_DIR="${CODEX_HOME:-$HOME/.codex}/skills/gpt-image2"
python3 "$SKILL_DIR/scripts/package_skill.py"
```

## References

- [SKILL.md](skills/gpt-image2/SKILL.md): core instructions loaded by Codex when using this skill.
- [CLI reference](skills/gpt-image2/references/cli.md): full command-line parameters.
- [Mask reference](skills/gpt-image2/references/mask.md): mask semantics, auto masks, and manual mask painting.
- [Troubleshooting](skills/gpt-image2/references/troubleshooting.md): self-test, retry, clipboard, and manual mask issues.
