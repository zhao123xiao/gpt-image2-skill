#!/usr/bin/env python3
"""Generate or edit images through Dreamfield gpt-image-2."""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import shutil
import sys
import time
import subprocess
import socket
import urllib.parse
import urllib.error
import urllib.request
from pathlib import Path


BASE_URL = "https://www.dreamfield.top/v1"
GENERATIONS_ENDPOINT = f"{BASE_URL}/images/generations"
EDITS_ENDPOINT = f"{BASE_URL}/images/edits"
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp", ".tif", ".tiff"}
RETRYABLE_HTTP_STATUSES = {408, 429, 500, 502, 503, 504}
MAX_RETRIES = 2
EMPTY_DATA_RETRIES = 1


def parse_size(value: str) -> tuple[int, int]:
    try:
        width_text, height_text = value.lower().split("x", 1)
        width = int(width_text)
        height = int(height_text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("size must look like WIDTHxHEIGHT") from exc
    if width <= 0 or height <= 0:
        raise argparse.ArgumentTypeError("size dimensions must be positive")
    return width, height


def request_json(url: str, api_key: str, payload: dict, timeout: int) -> tuple[int, dict]:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = response.status
            raw = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        status = exc.code
        raw = exc.read().decode("utf-8", errors="replace")
    except (TimeoutError, socket.timeout, urllib.error.URLError) as exc:
        raise RuntimeError(f"Request failed: {exc}") from exc

    try:
        return status, json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Response was not JSON, HTTP {status}: {raw[:1000]}") from exc


def normalize_path(path: Path) -> Path:
    return path.expanduser().resolve()


def validate_existing_file(path: Path, label: str) -> Path:
    normalized = normalize_path(path)
    if not normalized.is_file():
        raise ValueError(f"{label} does not exist or is not a file: {normalized}")
    if normalized.stat().st_size <= 0:
        raise ValueError(f"{label} is empty: {normalized}")
    return normalized


def validate_image_file(path: Path, label: str) -> Path:
    normalized = validate_existing_file(path, label)
    extension = normalized.suffix.lower()
    mime_type, _ = mimetypes.guess_type(normalized.name)
    if extension not in IMAGE_EXTENSIONS:
        raise ValueError(
            f"{label} must be an image file with one of these extensions "
            f"{sorted(IMAGE_EXTENSIONS)}: {normalized}"
        )
    if mime_type and not mime_type.startswith("image/"):
        raise ValueError(f"{label} has a non-image MIME type ({mime_type}): {normalized}")
    return normalized


def guess_mime_type(path: Path) -> str:
    mime_type, _ = mimetypes.guess_type(path.name)
    return mime_type or "application/octet-stream"


def request_multipart(
    url: str,
    api_key: str,
    fields: list[tuple[str, str]],
    files: list[tuple[str, Path]],
    timeout: int,
) -> tuple[int, dict]:
    boundary = f"----codex-gpt-image2-{time.time_ns()}"
    chunks: list[bytes] = []

    for name, value in fields:
        chunks.extend(
            [
                f"--{boundary}\r\n".encode("utf-8"),
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"),
                str(value).encode("utf-8"),
                b"\r\n",
            ]
        )

    for name, path in files:
        chunks.extend(
            [
                f"--{boundary}\r\n".encode("utf-8"),
                (
                    f'Content-Disposition: form-data; name="{name}"; '
                    f'filename="{path.name}"\r\n'
                ).encode("utf-8"),
                f"Content-Type: {guess_mime_type(path)}\r\n\r\n".encode("utf-8"),
                path.read_bytes(),
                b"\r\n",
            ]
        )

    chunks.append(f"--{boundary}--\r\n".encode("utf-8"))
    body = b"".join(chunks)
    request = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = response.status
            raw = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        status = exc.code
        raw = exc.read().decode("utf-8", errors="replace")
    except (TimeoutError, socket.timeout, urllib.error.URLError) as exc:
        raise RuntimeError(f"Request failed: {exc}") from exc

    try:
        return status, json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Response was not JSON, HTTP {status}: {raw[:1000]}") from exc


def save_response(payload: dict, path: Path) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def response_error(response_payload: dict) -> dict | None:
    error = response_payload.get("error")
    return error if isinstance(error, dict) else None


def error_text(error: dict | None) -> str:
    if not error:
        return "No structured API error was returned."
    parts = []
    for key in ("type", "code", "message"):
        value = error.get(key)
        if value:
            parts.append(f"{key}={value}")
    return "; ".join(parts) if parts else json.dumps(error, ensure_ascii=False)


def is_retryable_response(status: int, response_payload: dict) -> bool:
    error = response_error(response_payload)
    error_code = str(error.get("code") or "").lower() if error else ""
    error_type = str(error.get("type") or "").lower() if error else ""
    if status in {401, 403}:
        return False
    if "content_policy" in error_code or "content_policy" in error_type:
        return False
    if "insufficient_quota" in error_code or "insufficient_quota" in error_type:
        return False
    return status in RETRYABLE_HTTP_STATUSES


def has_api_error(status: int, response_payload: dict) -> bool:
    return status >= 400 or "error" in response_payload


def attempt_response_path(base_json_path: Path, attempt: int) -> Path:
    return base_json_path.with_name(f"{base_json_path.stem}.attempt{attempt}{base_json_path.suffix}")


def call_with_retries(
    request_fn,
    json_path: Path,
    empty_data_retries: int = EMPTY_DATA_RETRIES,
) -> tuple[int, dict, Path]:
    max_attempts = 1 + MAX_RETRIES
    empty_data_attempts = 0
    attempt = 1
    while True:
        try:
            status, response_payload = request_fn()
        except RuntimeError as exc:
            response_payload = {
                "error": {
                    "type": "network_error",
                    "message": str(exc),
                }
            }
            failed_path = attempt_response_path(json_path, attempt)
            save_response(response_payload, failed_path)
            if attempt >= max_attempts:
                return 0, response_payload, failed_path
            print(f"Attempt {attempt} failed with network error; retrying...")
            time.sleep(min(2 ** (attempt - 1), 8))
            attempt += 1
            continue

        response_path = json_path if status < 400 else attempt_response_path(json_path, attempt)
        save_response(response_payload, response_path)

        if has_api_error(status, response_payload):
            if attempt >= max_attempts or not is_retryable_response(status, response_payload):
                return status, response_payload, response_path
            print(f"Attempt {attempt} failed with retryable API error; retrying...")
            time.sleep(min(2 ** (attempt - 1), 8))
            attempt += 1
            continue

        data = response_payload.get("data") or []
        if not data and empty_data_attempts < empty_data_retries:
            failed_path = attempt_response_path(json_path, attempt)
            if response_path != failed_path:
                save_response(response_payload, failed_path)
            print(f"Attempt {attempt} returned empty data; retrying once...")
            empty_data_attempts += 1
            attempt += 1
            continue

        if response_path != json_path:
            save_response(response_payload, json_path)
            response_path = json_path
        return status, response_payload, response_path


def download_url(url: str, path: Path, timeout: int) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "Codex gpt-image2 skill"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        path.write_bytes(response.read())


def decode_image(item: dict, path: Path, timeout: int) -> bool:
    if item.get("b64_json"):
        path.write_bytes(base64.b64decode(item["b64_json"]))
        return True
    if item.get("url"):
        download_url(item["url"], path, timeout)
        return True
    return False


def output_image_path(output_dir: Path, stem: str, index: int, total: int) -> Path:
    if total == 1:
        return output_dir / f"{stem}.png"
    return output_dir / f"{stem}_{index}.png"


def target_image_path(output_dir: Path, stem: str, index: int, total: int, target: tuple[int, int]) -> Path:
    target_width, target_height = target
    if total == 1:
        return output_dir / f"{stem}_{target_width}x{target_height}.png"
    return output_dir / f"{stem}_{index}_{target_width}x{target_height}.png"


def planned_output_paths(output_dir: Path, stem: str, count: int, target: tuple[int, int] | None) -> dict:
    paths: dict[str, list[str]] = {
        "images": [str(output_image_path(output_dir, stem, index, count)) for index in range(1, count + 1)]
    }
    if target:
        paths["target_images"] = [
            str(target_image_path(output_dir, stem, index, count, target)) for index in range(1, count + 1)
        ]
    return paths


def crop_resize(src: Path, dst: Path, target: tuple[int, int]) -> tuple[int, int] | None:
    try:
        from PIL import Image
    except ImportError:
        return None

    target_width, target_height = target
    target_ratio = target_width / target_height

    image = Image.open(src).convert("RGB")
    width, height = image.size
    current_ratio = width / height

    if current_ratio > target_ratio:
        new_width = round(height * target_ratio)
        left = (width - new_width) // 2
        image = image.crop((left, 0, left + new_width, height))
    elif current_ratio < target_ratio:
        new_height = round(width / target_ratio)
        top = (height - new_height) // 2
        image = image.crop((0, top, width, top + new_height))

    image = image.resize((target_width, target_height), Image.Resampling.LANCZOS)
    image.save(dst)
    return image.size


def to_windows_path(path: Path) -> str:
    if not shutil.which("wslpath"):
        return str(path)
    result = subprocess.run(
        ["wslpath", "-w", str(path)],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return str(path)
    return result.stdout.strip()


def save_image_file_as_png(source: Path, target: Path) -> None:
    try:
        from PIL import Image
    except ImportError as exc:
        if source.suffix.lower() == ".png":
            shutil.copyfile(source, target)
            return
        raise RuntimeError(
            f"Pillow is required to convert copied file to PNG: {source}"
        ) from exc

    with Image.open(source) as image:
        image.save(target, format="PNG")


def clipboard_file_candidates_from_uri_list(data: bytes) -> list[Path]:
    candidates: list[Path] = []
    for raw_line in data.decode("utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("file://"):
            parsed = urllib.parse.urlparse(line)
            candidates.append(Path(urllib.parse.unquote(parsed.path)))
        else:
            candidates.append(Path(line))
    return candidates


def save_linux_clipboard_image(path: Path) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    image_targets = ["image/png", "image/jpeg", "image/bmp", "image/webp", "image/tiff"]

    wl_paste = shutil.which("wl-paste")
    if wl_paste:
        for target in image_targets:
            result = subprocess.run(
                [wl_paste, "--no-newline", "--type", target],
                check=False,
                capture_output=True,
            )
            if result.returncode == 0 and result.stdout:
                if target == "image/png":
                    path.write_bytes(result.stdout)
                else:
                    temp_path = path.with_suffix(f".clipboard-source{mimetypes.guess_extension(target) or '.img'}")
                    temp_path.write_bytes(result.stdout)
                    save_image_file_as_png(temp_path, path)
                    temp_path.unlink(missing_ok=True)
                return True

        result = subprocess.run(
            [wl_paste, "--no-newline", "--type", "text/uri-list"],
            check=False,
            capture_output=True,
        )
        if result.returncode == 0 and result.stdout:
            for candidate in clipboard_file_candidates_from_uri_list(result.stdout):
                if candidate.is_file() and candidate.suffix.lower() in IMAGE_EXTENSIONS:
                    save_image_file_as_png(candidate, path)
                    return True

    xclip = shutil.which("xclip")
    if xclip:
        for target in image_targets:
            result = subprocess.run(
                [xclip, "-selection", "clipboard", "-t", target, "-o"],
                check=False,
                capture_output=True,
            )
            if result.returncode == 0 and result.stdout:
                if target == "image/png":
                    path.write_bytes(result.stdout)
                else:
                    temp_path = path.with_suffix(f".clipboard-source{mimetypes.guess_extension(target) or '.img'}")
                    temp_path.write_bytes(result.stdout)
                    save_image_file_as_png(temp_path, path)
                    temp_path.unlink(missing_ok=True)
                return True

        result = subprocess.run(
            [xclip, "-selection", "clipboard", "-t", "text/uri-list", "-o"],
            check=False,
            capture_output=True,
        )
        if result.returncode == 0 and result.stdout:
            for candidate in clipboard_file_candidates_from_uri_list(result.stdout):
                if candidate.is_file() and candidate.suffix.lower() in IMAGE_EXTENSIONS:
                    save_image_file_as_png(candidate, path)
                    return True

    return False


def save_windows_clipboard_image(path: Path) -> bool:
    powershell = shutil.which("powershell.exe")
    if not powershell:
        return False

    path.parent.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["CODEX_CLIPBOARD_IMAGE_OUT"] = to_windows_path(path)
    script = r"""
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$OutputPath = [Environment]::GetEnvironmentVariable('CODEX_CLIPBOARD_IMAGE_OUT')
$Image = [System.Windows.Forms.Clipboard]::GetImage()
if ($null -ne $Image) {
    $Image.Save($OutputPath, [System.Drawing.Imaging.ImageFormat]::Png)
    $Image.Dispose()
    exit 0
}
$Files = [System.Windows.Forms.Clipboard]::GetFileDropList()
foreach ($File in $Files) {
    if (-not [System.IO.File]::Exists($File)) {
        continue
    }
    $Extension = [System.IO.Path]::GetExtension($File).ToLowerInvariant()
    if (@('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp', '.tif', '.tiff') -notcontains $Extension) {
        continue
    }
    $FileImage = [System.Drawing.Image]::FromFile($File)
    $FileImage.Save($OutputPath, [System.Drawing.Imaging.ImageFormat]::Png)
    $FileImage.Dispose()
    exit 0
}
[Console]::Error.WriteLine('Clipboard does not contain an image or copied image file.')
exit 2
"""
    result = subprocess.run(
        [powershell, "-NoProfile", "-STA", "-ExecutionPolicy", "Bypass", "-Command", script],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    if result.returncode != 0:
        message = (result.stderr or result.stdout or "Unknown PowerShell clipboard error.").strip()
        raise RuntimeError(message)
    return True


def save_clipboard_image(path: Path) -> None:
    errors: list[str] = []
    try:
        if save_windows_clipboard_image(path):
            return
    except RuntimeError as exc:
        errors.append(f"Windows clipboard: {exc}")

    try:
        if save_linux_clipboard_image(path):
            return
    except RuntimeError as exc:
        errors.append(f"Linux clipboard: {exc}")

    details = " ".join(errors) if errors else "No supported clipboard image backend found."
    raise RuntimeError(
        "Clipboard does not contain a readable image or copied image file. "
        "Supported backends: Windows powershell.exe, Linux wl-paste, Linux xclip. "
        f"{details}"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate or edit an image with Dreamfield gpt-image-2.")
    prompt_group = parser.add_mutually_exclusive_group(required=True)
    prompt_group.add_argument("--prompt", help="English image prompt to send to the model.")
    prompt_group.add_argument("--prompt-file", type=Path, help="UTF-8 text file containing the prompt.")
    parser.add_argument("--model", default="gpt-image-2")
    parser.add_argument(
        "--image",
        action="append",
        type=Path,
        default=[],
        help="Input/reference image for image-to-image editing. Repeat for multiple images.",
    )
    parser.add_argument(
        "--clipboard-image",
        action="store_true",
        help="Save the current OS clipboard image as a temporary PNG and use it as an input image.",
    )
    parser.add_argument(
        "--clipboard-dir",
        type=Path,
        help="Directory for clipboard image snapshots. Defaults to OUTPUT_DIR/clipboard-inputs.",
    )
    parser.add_argument("--mask", type=Path, help="Optional alpha mask for editing the first input image.")
    parser.add_argument("--size", default="1792x1024", help="Requested image size, e.g. 1024x1024 or 1792x1024.")
    parser.add_argument("--target-size", type=parse_size, help="Crop and resize final image to exact WIDTHxHEIGHT.")
    parser.add_argument("--n", type=int, default=1)
    parser.add_argument("--response-format", default="b64_json", choices=["b64_json", "url"])
    parser.add_argument("--output-dir", type=Path, default=Path.cwd() / "gpt-image2-output")
    parser.add_argument("--basename", default="image2")
    parser.add_argument("--api-key-env", default="NEW_image2_API_KEY")
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--dry-run", action="store_true", help="Print request metadata without calling the API.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.prompt_file is not None:
        try:
            args.prompt_file = validate_existing_file(args.prompt_file, "Prompt file")
        except ValueError as exc:
            print(exc, file=sys.stderr)
            return 1
        prompt = args.prompt_file.read_text(encoding="utf-8").strip()
    else:
        prompt = args.prompt.strip() if args.prompt is not None else ""
    if not prompt:
        print("Prompt is empty.", file=sys.stderr)
        return 1
    if args.n <= 0:
        print("--n must be a positive integer.", file=sys.stderr)
        return 1
    try:
        parse_size(args.size)
    except argparse.ArgumentTypeError as exc:
        print(f"--size {exc}", file=sys.stderr)
        return 1

    args.output_dir = normalize_path(args.output_dir)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    stem = f"{args.basename}_{timestamp}"
    if args.clipboard_image:
        clipboard_dir = normalize_path(args.clipboard_dir) if args.clipboard_dir else (args.output_dir / "clipboard-inputs")
        clipboard_path = clipboard_dir / f"{stem}_clipboard.png"
        try:
            save_clipboard_image(clipboard_path)
        except RuntimeError as exc:
            print(f"Failed to save clipboard image: {exc}", file=sys.stderr)
            return 1
        args.image.append(clipboard_path)
        print(f"Clipboard image saved to: {clipboard_path}")

    if args.mask and not args.image:
        print("--mask requires at least one --image.", file=sys.stderr)
        return 1
    try:
        args.image = [validate_image_file(image_path, "Input image") for image_path in args.image]
        if args.mask:
            args.mask = validate_image_file(args.mask, "Mask image")
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 1

    json_path = args.output_dir / f"{stem}.response.json"
    endpoint = EDITS_ENDPOINT if args.image else GENERATIONS_ENDPOINT
    mode = "edit" if args.image else "generation"

    payload = {
        "model": args.model,
        "prompt": prompt,
        "size": args.size,
        "n": args.n,
        "response_format": args.response_format,
    }

    if args.dry_run:
        print("Dry run; no API request was sent.")
        print(f"Mode: {mode}")
        print(f"Endpoint: {endpoint}")
        print(f"Output directory: {args.output_dir}")
        print(f"Response path: {json_path}")
        print(
            json.dumps(
                {
                    **payload,
                    "image": [str(path) for path in args.image],
                    "mask": str(args.mask) if args.mask else None,
                    "planned_output": planned_output_paths(args.output_dir, stem, args.n, args.target_size),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    api_key = os.environ.get(args.api_key_env)
    if not api_key:
        print(
            f"Missing environment variable {args.api_key_env}. "
            f"Set it first, for example: export {args.api_key_env}='your_api_key'",
            file=sys.stderr,
        )
        return 1

    print(f"Calling Dreamfield image {mode} API...")
    if args.image:
        def request_fn() -> tuple[int, dict]:
            fields = [(key, str(value)) for key, value in payload.items()]
            files = [("image[]", path) for path in args.image]
            if args.mask:
                files.append(("mask", args.mask))
            return request_multipart(endpoint, api_key, fields, files, args.timeout)
    else:
        def request_fn() -> tuple[int, dict]:
            return request_json(endpoint, api_key, payload, args.timeout)

    status, response_payload, response_path = call_with_retries(request_fn, json_path)
    print(f"HTTP status: {status}")
    print(f"Response saved to: {response_path}")

    if has_api_error(status, response_payload):
        print(f"API error: {error_text(response_error(response_payload))}", file=sys.stderr)
        return 2

    data = response_payload.get("data") or []
    print(f"data length: {len(data)}")
    if not data:
        print(f"No image data returned. Inspect the saved response JSON: {response_path}", file=sys.stderr)
        return 3

    total = len(data)
    for index, item in enumerate(data, start=1):
        image_path = output_image_path(args.output_dir, stem, index, total)
        if not decode_image(item, image_path, args.timeout):
            print(f"Response item {index} contains neither b64_json nor url.", file=sys.stderr)
            print(f"Item keys: {sorted(item.keys())}", file=sys.stderr)
            return 3

        print(f"Image {index} saved to: {image_path}")

        if args.target_size:
            target_path = target_image_path(args.output_dir, stem, index, total, args.target_size)
            resized_size = crop_resize(image_path, target_path, args.target_size)
            if resized_size is None:
                print("Pillow is not installed; skipped exact target-size post-processing.", file=sys.stderr)
            else:
                print(f"Target image {index} saved to: {target_path}")
                print(f"Target dimensions: {resized_size[0]}x{resized_size[1]}")

        if item.get("url"):
            print(f"URL {index}: {item['url']}")
        if item.get("revised_prompt"):
            print(f"Revised prompt {index}: {item['revised_prompt']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
