# GPT Image 2 Troubleshooting

## Self Test

Run offline checks:

```bash
python3 scripts/generate_image2.py --self-test
```

Checks include Python, Pillow, API key environment variable, configured endpoints, clipboard backend, output directory write access, and script path.
It also reports whether `tkinter` and `scripts/mask_painter.py` are available for `--mask-draw`.

## API Key

Default API key environment variable:

```text
NEW_image2_API_KEY
```

Override with:

```bash
--api-key-env OTHER_ENV_NAME
```

## Retry Behavior

The script retries:

- network errors
- timeouts
- HTTP `408`, `429`, and `5xx`
- one empty `data` response

It does not retry:

- `401`
- `403`
- `insufficient_quota`
- `content_policy_violation`

Failed attempt responses are saved next to the normal response JSON with `.attemptN`.

## Clipboard Backends

- Windows / WSL: `powershell.exe`
- Linux Wayland: `wl-paste`
- Linux X11: `xclip`

If no backend is available, use `--image PATH` instead.

## Manual Mask Painter

`--mask-draw` opens a local Tk window. If it fails:

- confirm Python `tkinter` is installed
- confirm a graphical desktop/display is available
- in WSL, use WSLg or another X/Wayland display setup
- if no GUI is available, create a mask file manually and pass it with `--mask PATH`
