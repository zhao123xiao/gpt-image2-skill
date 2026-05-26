<!--
╔══════════════════════════════════════════════════════════════════════╗
║  DreamSeed 种梦计划 — AI创造者大赛  官方 README 模板                ║
║                                                                      ║
║  使用说明：                                                          ║
║  1. 将本模板放在参赛仓库根目录 README.md 的顶部                       ║
║  2. 头图使用 DreamField 官方公开活动图片地址                         ║
║  3. 请保留 DREAMFIELD_README_HEADER_START / END 标识                 ║
║  4. 分割线以下供创作者自由编写项目内容                               ║
╚══════════════════════════════════════════════════════════════════════╝
-->

<!-- DREAMFIELD_README_HEADER_START -->

<p align="center">
  <a href="https://www.dreamfield.top">
    <img src="https://www.dreamfield.top/dream-field/contest-readme/assets/dreamseed-readme-banner.png" alt="DreamSeed 种梦计划参赛作品" width="100%" />
  </a>
</p>

<!-- DREAMFIELD_README_HEADER_END -->

---

# GPT Image 2 Skill

语言 / Language: **简体中文** | [English](README.en.md)

这是一个用于 Codex 的 Dreamfield `gpt-image-2` 图像生成与编辑 skill。它通过 Dreamfield 的 OpenAI 兼容图像 API，支持文生图、图生图、剪贴板图片输入、局部编辑、自动遮罩、手绘遮罩和结果索引。

## 功能

- 文生图：根据文本提示词生成图片。
- 图生图：使用本地图片或剪贴板图片作为参考图。
- 局部编辑：通过遮罩进行 inpainting，只修改指定区域。
- 自动遮罩：支持全图、中心、边框、矩形、圆形和 alpha 透明区域。
- 手绘遮罩：通过 `mask_painter.py` 打开本地画笔界面，手动画出编辑区域。
- 遮罩预览：生成红色编辑区域 overlay，便于检查实际修改范围。
- 输入预处理：自动压缩或缩放输入图，降低上传风险。
- 结果索引：每次运行生成 `summary.json`，记录输入、遮罩、响应和输出路径。
- 离线自检：检查 Python、Pillow、tkinter、API key、剪贴板后端和脚本路径。
- 打包脚本：可重新生成可分发的 skill zip。

## 安装

从 GitHub 仓库路径安装该 skill：

```bash
python3 install-skill-from-github.py --repo zhao123xiao/gpt-image2-skill --path skills/gpt-image2
```

安装完成后，重启 Codex。

## 环境

推荐服务和模型：

- 服务商：[Dreamfield](https://www.dreamfield.top/)
- 模型：`gpt-image-2`
- API key 环境变量：`NEW_image2_API_KEY`

作者备注：该 skill 已在 Dreamfield 中测试，供个人使用。支持 4K 输出。至于细节，可以查看 Dreamfield 的最新价格和模型限制。

使用前设置 API key：

```bash
export NEW_image2_API_KEY='your_api_key'
```

## 快速使用

文生图：

```bash
SKILL_DIR="${CODEX_HOME:-$HOME/.codex}/skills/gpt-image2"
python3 "$SKILL_DIR/scripts/generate_image2.py" \
  --prompt "A cinematic 16:9 desktop wallpaper of golden lightning over green hills at sunset, no text, no watermark." \
  --size 1792x1024
```

图生图：

```bash
SKILL_DIR="${CODEX_HOME:-$HOME/.codex}/skills/gpt-image2"
python3 "$SKILL_DIR/scripts/generate_image2.py" \
  --image "/absolute/path/to/reference.png" \
  --prompt "Create a new photorealistic 16:9 wallpaper inspired by this reference image, no text, no watermark." \
  --size 1792x1024
```

矩形遮罩局部编辑：

```bash
SKILL_DIR="${CODEX_HOME:-$HOME/.codex}/skills/gpt-image2"
python3 "$SKILL_DIR/scripts/generate_image2.py" \
  --image "/absolute/path/to/source.png" \
  --mask-auto rect \
  --mask-rect 120,80,640,360 \
  --prompt "Replace only the masked area while preserving the rest of the image. No text, no watermark." \
  --size 1792x1024
```

手绘遮罩局部编辑：

```bash
SKILL_DIR="${CODEX_HOME:-$HOME/.codex}/skills/gpt-image2"
python3 "$SKILL_DIR/scripts/generate_image2.py" \
  --image "/absolute/path/to/source.png" \
  --mask-draw \
  --prompt "Replace only the painted area while preserving the rest of the image. No text, no watermark." \
  --size 1792x1024
```

离线自检：

```bash
SKILL_DIR="${CODEX_HOME:-$HOME/.codex}/skills/gpt-image2"
python3 "$SKILL_DIR/scripts/generate_image2.py" --self-test
```

重新打包：

```bash
SKILL_DIR="${CODEX_HOME:-$HOME/.codex}/skills/gpt-image2"
python3 "$SKILL_DIR/scripts/package_skill.py"
```

## 参考文档

- [SKILL.md](skills/gpt-image2/SKILL.md)：Codex 使用该 skill 时读取的核心说明。
- [CLI 参数](skills/gpt-image2/references/cli.md)：完整命令行参数。
- [遮罩说明](skills/gpt-image2/references/mask.md)：遮罩语义、自动遮罩和手绘遮罩。
- [故障排查](skills/gpt-image2/references/troubleshooting.md)：自检、重试、剪贴板和手绘遮罩问题。
