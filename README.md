# GPT Image 2 Skill

语言 / Language: **简体中文** | [English](README.en.md)

通过 Dreamfield 的 OpenAI 兼容 `gpt-image-2` 图像 API，为 Codex 提供文生图、图生图和局部编辑能力的 skill。

## 功能

- 文生图、图生图和剪贴板图片输入
- 局部编辑和 inpainting 遮罩
- 自动遮罩、手绘遮罩和遮罩预览图
- 输入图片预处理、结果索引和离线自检
- 内置打包脚本，便于重新生成 skill zip

## 安装

从 GitHub 仓库路径安装该 skill：

```bash
python3 install-skill-from-github.py --repo OWNER/REPO --path skills/gpt-image2
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
