# GPT Image 2 Skill

Codex skill for generating and editing images through Dreamfield's OpenAI-compatible `gpt-image-2` image API.

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

Author note: this skill is tested with Dreamfield for personal use. At the time of writing, the author's usage is about `0.1` per image generation and supports 4K output; check Dreamfield for current pricing and model limits.

Set the API key before using the skill:

```bash
export NEW_image2_API_KEY='your_api_key'
```
