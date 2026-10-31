# AstrBot 小说语音朗读实战记录

用 AstrBot + Private Companion + Breeze TTS，把一篇中文长篇小说章节做成四段 QQ 语音投递的完整链路复盘。包含配置、日志证据、切分策略、清洗规则、故障处理，以及四段成品的 mp3。

> 所有配置、时间戳均来自 2026-10-31 的真实运行环境，API Key / QQ 号 / 音色 ID 已脱敏。

## 目录结构

```
.
├── README.md              项目说明
├── REPRODUCE.md           从原文到四段 mp3 的复现流程
├── NOTICE.md              版权与内容说明
├── docs/
│   ├── 创作总结.md         完整技术复盘（重点看这个）
│   └── audio/             四段成品音频（展示用副本）
├── audio/                 四段成品音频与说明
└── scripts/
    ├── tts_batch.py       可独立运行的批量合成脚本
    └── reproduce.ps1      一键跑通：环境检查 → 合成 → 校验
```

## 快速开始

```bash
# 1) 装依赖：只用标准库，无需 pip
python --version   # 3.9+

# 2) 设环境变量
export BREEZE_API_KEY=brz_xxx
export BREEZE_TTS_VOICE=voc_xxxxxxxx

# 3) 跑
python scripts/tts_batch.py --input chapter.txt --out ./audio --max-chars 700 --gap 3
```

Windows PowerShell：

```powershell
$env:BREEZE_API_KEY="brz_xxx"
$env:BREEZE_TTS_VOICE="voc_xxxxxxxx"
python scripts/tts_batch.py --input chapter.txt --out ./audio --max-chars 700 --gap 3
```

## 关键结论

| 结论 | 一句话 |
| --- | --- |
| 分段长度 | 500–700 字/段，60–90 秒，听感最舒服 |
| 场景切换 | 必须在换场景处断段，否则情绪会塌 |
| 引号处理 | 中文「」送进 TTS 会卡顿，一律换逗号 |
| 触发机制 | 关键词命中直接走语音，不看概率 |
| 概率陷阱 | 没命中关键词又没撞概率，模型根本收不到 TTS 指令 |
| 限流 | 503 产能满退避 15s 起，429 间隔拉到 3–5s |
| 发送 | 一条消息里语音组件别超过 2 个，多了会吞 |

## 音频

| 文件 | 大小 | 内容 |
| --- | --- | --- |
| `docs/audio/ch46_seg1.mp3` | 2.45 MB | 北域战场 |
| `docs/audio/ch46_seg2.mp3` | 2.60 MB | 承平出手 |
| `docs/audio/ch46_seg3.mp3` | 2.55 MB | 妖尊殿 |
| `docs/audio/ch46_seg4.mp3` | 2.17 MB | 收尾 |

## 版权

朗读素材为使用者自行提供，音频仅限私用。本仓库不含小说原文全文，如需公开演示请自行替换授权文本。详见 `NOTICE.md`。

## License

文档与脚本采用 MIT。音频仅限自用。
