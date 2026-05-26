# GPT Image 2 Skill

Language: [简体中文](README.md) | **English**

A Codex skill for generating and editing images through Dreamfield's OpenAI-compatible `gpt-image-2` image API.

## Features

- Text-to-image, image-to-image, and clipboard image input
- Localized editing and inpainting masks
- Auto masks, manual mask painting, and mask overlay previews
- Input image preprocessing, result summaries, and offline self-test
- Built-in packaging script for regenerating the skill zip

## Install

Install this skill from the repository path:

```bash
python3 install-skill-from-github.py --repo OWNER/REPO --path skills/gpt-image2
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
