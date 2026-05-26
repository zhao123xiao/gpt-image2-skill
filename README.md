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

GPT Image 2 Skill 是一个面向 Codex 的 Dreamfield 图像生成与编辑技能。它基于 Dreamfield 的 OpenAI 兼容 `gpt-image-2` 图像接口，让 Codex 可以根据用户需求完成文生图、图生图、局部编辑和遮罩处理等工作。

## 项目定位

该 skill 主要用于把自然语言创作需求转化为稳定的图像生成流程。用户可以描述想要的画面、提供参考图、指定需要局部修改的区域，Codex 会根据 skill 中的流程选择合适的生成或编辑方式，并保存本地结果。

## 核心能力

- 文生图：根据文本描述生成插画、壁纸、素材图等图像。
- 图生图：基于本地图片或剪贴板图片进行参考生成。
- 局部编辑：通过遮罩只修改指定区域，保留其余画面。
- 自动遮罩：支持全图、中心、边框、矩形、圆形和透明区域等常见遮罩方式。
- 手绘遮罩：提供本地手绘遮罩工具，适合精确圈选需要修改的区域。
- 遮罩预览：生成红色区域预览图，方便确认实际编辑范围。
- 输入预处理：对输入图片进行必要的尺寸和格式处理，提高接口调用稳定性。
- 结果索引：记录输入、遮罩、响应和输出路径，便于追踪每次生成结果。
- 离线自检：检查运行环境、依赖、剪贴板能力和脚本可用性。

## Dreamfield 环境

该 skill 已在 [Dreamfield](https://www.dreamfield.top/) 中测试，供个人使用。支持 4K 输出。至于细节，可以查看 Dreamfield 的最新价格和模型限制。

## 文档结构

- `skills/gpt-image2/SKILL.md`：Codex 使用该 skill 时读取的核心说明。
- `skills/gpt-image2/references/cli.md`：命令行参数说明。
- `skills/gpt-image2/references/mask.md`：遮罩语义、自动遮罩和手绘遮罩说明。
- `skills/gpt-image2/references/troubleshooting.md`：自检、重试、剪贴板和手绘遮罩故障排查。
