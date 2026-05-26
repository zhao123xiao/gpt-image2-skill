# GPT Image 2 Skill

Language: [简体中文](README.md) | **English**

GPT Image 2 Skill is a Codex skill for Dreamfield image generation and editing. It uses Dreamfield's OpenAI-compatible `gpt-image-2` image API so Codex can handle text-to-image generation, image-to-image generation, localized edits, and mask-based workflows.

## Purpose

This skill turns natural-language image requests into a structured generation workflow. Users can describe an image, provide reference images, or specify areas that should be edited. Codex uses the skill instructions to choose the appropriate generation or editing mode and save local results.

## Core Capabilities

- Text-to-image generation for illustrations, wallpapers, and visual assets.
- Image-to-image generation from local files or clipboard images.
- Localized editing through masks while preserving the rest of the image.
- Auto masks for full image, center, border, rectangle, circle, and transparent areas.
- Manual mask painting for precise edit-region selection.
- Mask overlay previews for checking the actual edit area.
- Input preprocessing for size and format handling.
- Result summaries for tracking inputs, masks, responses, and outputs.
- Offline self-test for runtime dependencies, clipboard support, and script availability.

## Dreamfield Environment

This skill is designed for Dreamfield's `gpt-image-2` image model. It has been tested with Dreamfield for personal use and supports 4K output. Current pricing, model limits, and available sizes should be checked on Dreamfield.

## Documentation

- `skills/gpt-image2/SKILL.md`: core instructions loaded by Codex when using this skill.
- `skills/gpt-image2/references/cli.md`: command-line parameter reference.
- `skills/gpt-image2/references/mask.md`: mask semantics, auto masks, and manual mask painting.
- `skills/gpt-image2/references/troubleshooting.md`: self-test, retry, clipboard, and manual mask troubleshooting.
