---
name: gpt-image2
description: Generate and edit images with Dreamfield's OpenAI-compatible gpt-image-2 image API. Use when the user asks Codex to create, test, or save an image from a text description, make wallpaper or illustration assets, perform image-to-image generation from reference images, use masks/inpainting, verify Dreamfield image generation, or troubleshoot image-generation responses such as empty data, b64_json, URL output, quota errors, or content policy errors.
---

# GPT Image 2

Use Dreamfield's OpenAI-compatible image endpoints to generate images from user descriptions or edit/generate from reference images:

```text
POST https://www.dreamfield.top/v1/images/generations
POST https://www.dreamfield.top/v1/images/edits
```

Use `scripts/generate_image2.py` for actual calls. It handles JSON generation requests, multipart image edit requests, input validation, conservative retry, JSON response saving, `b64_json` decoding, optional URL download, multi-image output, and optional strict wallpaper resizing.

## Workflow

1. Decide whether the task is text-to-image or image-to-image:
   - If the user provides one or more local image paths, asks to use a reference image, asks to edit an existing image, or asks for "image-to-image", call the edits endpoint by passing `--image`.
   - If the user says the image is copied to the OS clipboard, pass `--clipboard-image`; the script saves the clipboard image to a temporary PNG and then uses it as `--image`.
   - If the user only provides a text description and no usable local image path, call the generations endpoint without `--image`.
2. Convert the user's image description into a concise English prompt before calling the API. Keep user intent intact, and add practical constraints such as `no text` or `no watermark` when useful.
3. Do not use `/v1/chat/completions` for image generation or image editing.
4. Use the environment variable `NEW_image2_API_KEY` by default. Do not print or hard-code the key.
5. Prefer `response_format: "b64_json"` so the script can save local PNG files deterministically.
6. Choose the requested API size from the prompt: use `1792x1024` for wide wallpaper or cinematic scenes, `1024x1024` for square images or troubleshooting, and other supported sizes only when the provider accepts them.
7. Use `--n` only for variants of one prompt. The script saves all returned images; with one result it uses `BASENAME_TIMESTAMP.png`, with multiple results it uses `BASENAME_TIMESTAMP_1.png`, `BASENAME_TIMESTAMP_2.png`, etc.
8. Return the generated image as-is by default. Do not crop, resize, or post-process unless the user explicitly asks for exact pixel dimensions or strict aspect-ratio output.
9. If exact output is explicitly requested, pass `--target-size WIDTHxHEIGHT`; the script will crop and resize every returned image if Pillow is available.
10. Show the final image path(s) with local absolute Markdown links when the interface supports images.

## Image-to-Image

Use `--image PATH` for reference-image generation or whole-image edits. Repeat `--image` to provide multiple references. Use `--clipboard-image` when the user has copied an image or image file to the OS clipboard. Use `--mask PATH` only when the user asks for a localized edit/inpainting; the mask applies to the first input image.

The script validates local input paths before upload:

- `--image`, `--mask`, and `--prompt-file` support `~` expansion.
- Missing files, empty files, and obvious non-image input files fail before the API request.
- Error messages print normalized absolute paths so the failed input is easy to find.

The script automatically switches to:

```text
POST https://www.dreamfield.top/v1/images/edits
Content-Type: multipart/form-data
```

when `--image` is present, and uploads reference images as `image[]` fields.

Clipboard images are saved under `OUTPUT_DIR/clipboard-inputs` by default. Use `--clipboard-dir PATH` to choose another snapshot directory.

Clipboard backend support:

- Windows / WSL: uses `powershell.exe` and the Windows clipboard API.
- Linux Wayland: uses `wl-paste`.
- Linux X11: uses `xclip`.

If the clipboard contains a copied image file instead of raw image pixels, the script tries to convert that file to PNG. Non-PNG file conversion requires Pillow.

If the user provides an inline chat image but no accessible local file path, ask the user to copy the image to the OS clipboard and run with `--clipboard-image`, provide a local image path, or use a previously generated local image path from the conversation. Do not pretend the script can read an inline chat image unless it exists on disk or is available from the OS clipboard.

## Reliability

The script uses conservative internal retry without adding CLI flags:

- Retries network errors, timeouts, HTTP `408`, `429`, and `5xx` up to two times with short exponential backoff.
- Does not retry `401`, `403`, `insufficient_quota`, or `content_policy_violation`.
- Retries one empty `data` response once, then reports the saved response JSON path.
- Saves failed attempt responses as `BASENAME_TIMESTAMP.response.attemptN.json`-style files, while the final successful response uses `BASENAME_TIMESTAMP.response.json`.

Use `--dry-run` to confirm mode, endpoint, payload, input images, mask, response path, and planned output image paths without calling the API.

## Command Pattern

Run from any working directory. Resolve the script path from the installed skill directory:

```bash
SKILL_DIR="${CODEX_HOME:-$HOME/.codex}/skills/gpt-image2"
python3 "$SKILL_DIR/scripts/generate_image2.py" \
  --prompt "A cinematic 16:9 desktop wallpaper of golden lightning over green hills at sunset, dramatic clouds, vivid colors, no text, no watermark." \
  --size 1792x1024 \
  --output-dir "./gpt-image2-output"
```

Multiple text-to-image variants:

```bash
SKILL_DIR="${CODEX_HOME:-$HOME/.codex}/skills/gpt-image2"
python3 "$SKILL_DIR/scripts/generate_image2.py" \
  --prompt "Three photorealistic cinematic desktop wallpaper variants of a misty mountain lake at sunrise, no text, no watermark." \
  --size 1792x1024 \
  --n 3 \
  --output-dir "./gpt-image2-output"
```

Image-to-image / reference image:

```bash
SKILL_DIR="${CODEX_HOME:-$HOME/.codex}/skills/gpt-image2"
python3 "$SKILL_DIR/scripts/generate_image2.py" \
  --image "/absolute/path/to/reference.png" \
  --prompt "Create a new photorealistic 16:9 wallpaper inspired by this reference image: preserve the warm golden-hour lighting, right-side portrait composition, shallow depth of field, realistic skin texture, no text, no watermark." \
  --size 1792x1024 \
  --output-dir "./gpt-image2-output"
```

Image-to-image from the OS clipboard:

```bash
SKILL_DIR="${CODEX_HOME:-$HOME/.codex}/skills/gpt-image2"
python3 "$SKILL_DIR/scripts/generate_image2.py" \
  --clipboard-image \
  --prompt "Create a new photorealistic 16:9 wallpaper inspired by the clipboard reference image: preserve the warm golden-hour lighting, right-side portrait composition, shallow depth of field, realistic skin texture, no text, no watermark." \
  --size 1792x1024 \
  --output-dir "./gpt-image2-output"
```

Masked edit / inpainting:

```bash
SKILL_DIR="${CODEX_HOME:-$HOME/.codex}/skills/gpt-image2"
python3 "$SKILL_DIR/scripts/generate_image2.py" \
  --image "/absolute/path/to/source.png" \
  --mask "/absolute/path/to/mask.png" \
  --prompt "Replace only the masked background with a softly blurred sunset balcony scene while preserving the person, face, pose, clothing, and lighting continuity. No text, no watermark." \
  --size 1792x1024 \
  --output-dir "./gpt-image2-output"
```

For a quick compatibility test, use:

```bash
SKILL_DIR="${CODEX_HOME:-$HOME/.codex}/skills/gpt-image2"
python3 "$SKILL_DIR/scripts/generate_image2.py" \
  --prompt "Traditional Chinese ink wash landscape painting, misty distant mountains, winding stream, pine trees, elegant blank space, monochrome ink wash, high quality, no text." \
  --size 1024x1024
```

## Prompt Guidance

- Prefer English prompts. Prior testing showed Chinese prompts may be rewritten incorrectly by this provider.
- Include composition, style, subject, lighting, quality, and negative constraints.
- For image-to-image, describe exactly what should be preserved from the reference image and what should change. Use phrases like `preserve composition`, `preserve face identity only if the user owns or supplied the person image`, `new non-identical subject`, `same lighting`, `same aspect ratio`, or `change background`.
- For reference images of people, avoid implying the output should duplicate a real private person's identity unless the user explicitly asks to edit their supplied image. For "similar" requests, ask for a new non-identical subject with similar composition, lighting, and mood.
- For protected characters, franchises, or near-copies, do not try to bypass policy filters. If the provider returns `content_policy_violation`, explain that the prompt was rejected and offer an original alternative.
- If the API returns HTTP 200 with an empty `data` array, the script retries once automatically; if it is still empty, report the saved response JSON path and ask whether to simplify the prompt or try `1024x1024`.

## Error Handling

- `429 insufficient_quota`: the API key is valid enough to reach the service, but the account lacks image quota. The script does not retry quota failures.
- `401` or auth errors: check `NEW_image2_API_KEY`.
- `content_policy_violation`: revise the image concept to avoid protected or disallowed content.
- Empty `data`: inspect the saved response JSON; then retry manually with a simpler safe prompt or `1024x1024`.
- Missing `b64_json`: if a `url` field exists, the script tries to download it. Otherwise report the saved response.
- Image-to-image unsupported by provider: report the saved JSON path. Do not silently fall back to text-to-image; if the task can still be satisfied, ask before manually trying without `--mask` or with a single `--image`.
- Clipboard capture failed: make sure the user copied actual image pixels or copied an image file. Windows/WSL requires `powershell.exe`; Linux requires `wl-paste` or `xclip`. If no backend is available, ask for a local image path instead.
