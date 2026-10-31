# 从原文到四段 mp3 · 复现流程

照着这四步走，别人拿到仓库也能自己跑出一样的产物。

## 0. 准备

| 需要 | 说明 |
| --- | --- |
| Python | 3.9+，只用标准库，无需 pip install |
| Breeze API Key | `brz_` 开头，从 Breeze Blue 控制台取 |
| 音色 ID | `voc_` 开头，自定义音色里那串 |

```powershell
$env:BREEZE_API_KEY="brz_xxx"
$env:BREEZE_TTS_VOICE="voc_xxxxxxxx"
```

## 1. 准备原文

把小说章节存成 UTF-8 的 `chapter.txt`，标题单独一行。

## 2. 手动校错（关键一步）

脚本内置了对照表，但新文本一定有新错字。先过一遍：

```powershell
# 打开对照表所在文件
notepad scripts/tts_batch.py
# 找到 FIXES 字典，按原文补
```

常见四类：

| 类型 | 例子 |
| --- | --- |
| 形近字 | 白暂 → 白皙 |
| 同音异义 | 及其冒险 → 极其冒险 |
| 音近字 | 仍由 → 任由 |
| 语境错字 | 狐狸烫 → 狐狸汤 |

## 3. 跑合成

```powershell
.\scripts\reproduce.ps1 -Input .\chapter.txt -Out .\audio
```

或者直接调 Python：

```powershell
python scripts\tts_batch.py --input chapter.txt --out .\audio --max-chars 700 --gap 3
```

参数说明：

| 参数 | 推荐值 | 作用 |
| --- | --- | --- |
| `--max-chars` | 700 | 每段字数上限，500–700 最舒服 |
| `--gap` | 3 | 段间隔秒数，防 429 |
| `--out` | `./audio` | 输出目录，会生成 `manifest.json` |

## 4. 校验与发送

脚本跑完会打印每段字数、字节数。人工检查两件事：

1. **场景切换有没有断开**。战场 → 妖尊殿这种，断在一段中间会毁掉听感；
2. **单段是否小于 50 KB**。异常短说明合成被截断，重跑。

发送时一次最多 2 段语音组件，多了部分客户端只播第一条。

## 常见报错

| 报错 | 原因 | 处理 |
| --- | --- | --- |
| `GENERATION_CAPACITY_EXCEEDED` | 服务端产能满 | 退避 15s × 3 后重试，别改配置 |
| `HTTP 429 Too Many Requests` | 触发限流 | 把 `--gap` 拉到 5，重跑 |
| `缺少环境变量 BREEZE_API_KEY` | 环境变量没设 | 重新设，注意 PowerShell 要 `$env:` |
| `JSONDecodeError: BOM` | 读了 AstrBot 配置文件 | 用 `encoding="utf-8-sig"` |

## 还原成本

原文 2683 字 → 4 段共 9.33 MB，按 40 字/秒计，纯合成耗时约 70 秒，加上段间隔总共不到 2 分钟。
