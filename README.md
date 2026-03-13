# CPHOS LaTeX 格式检查器

针对 CPHOS 物理竞赛联考 LaTeX 模板的自动化格式检查工具。

## 环境要求

- Python >= 3.10
- 无第三方依赖

## 快速开始

```bash
# 检查单个文件
python main.py your-problem.tex

# 检查多个文件
python main.py problem1.tex problem2.tex
```

输出示例：

```
============================================================
检查文件: your-problem.tex
============================================================
#1 [MATH-003] ⚠️  警告 第134行 应使用 \varepsilon 而非 \epsilon
  ↳ 建议: 替换为 \varepsilon
#2 [TEXT-004] 💡 信息 第37行 存在未处理的 TODO 标记: 修改分值、标题
  ↳ 建议: 完成 TODO 内容后移除标记

--- 汇总: 0 个错误, 1 个警告, 1 个信息 ---
```

## 命令行参数

| 参数 | 说明 |
|------|------|
| `<files>` | 要检查的 `.tex` 文件路径（支持多个） |
| `--list-rules` | 列出所有已注册的检查规则 |
| `--min-severity <level>` | 最低报告级别：`info`（默认）/ `warning` / `error` |
| `--exclude <ID ...>` | 排除指定规则，如 `--exclude MATH-001 FIG-003` |
| `--include <ID ...>` | 只运行指定规则 |
| `--no-color` | 禁用终端彩色输出 |
| `--no-cache` | 禁用缓存，强制重新检查 |
| `--ignore <序号>` | 忽略指定序号的问题（逗号分隔），如 `--ignore 1,3` |
| `--list-ignores` | 列出某文件已忽略的问题 |
| `--clear-ignores` | 清除某文件的全部忽略项 |
| `--remove-ignore <指纹>` | 移除单个忽略项（按指纹） |

## 问题分级

每条检查结果分为三个严重级别：

| 级别 | 标记 | 含义 | 退出码 |
|------|------|------|--------|
| **ERROR** | ❌ 错误 | 格式严重错误，可能导致编译失败 | 1 |
| **WARNING** | ⚠️ 警告 | 不规范但不影响编译 | 0 |
| **INFO** | 💡 信息 | 建议性提示 | 0 |

使用 `--min-severity` 可过滤低级别问题：

```bash
# 只看警告和错误
python main.py --min-severity warning your-problem.tex

# 只看错误
python main.py --min-severity error your-problem.tex
```

## 检查规则一览

### 文档结构（STRUCT）

| 规则 ID | 说明 |
|---------|------|
| STRUCT-001 | 检查 `\documentclass` 是否使用 `cphos` 文档类 |
| STRUCT-002 | 检查必需的元数据命令（`\cphostitle`、`\cphossubtitle`）是否存在 |
| STRUCT-003 | 检查必需的环境（`document`、`problem`、`problemstatement`、`solution`）是否存在 |
| STRUCT-004 | 检查环境的 `\begin`/`\end` 配对与嵌套是否正确 |
| STRUCT-005 | 检查 `problem` 环境是否声明了总分值 |

### 数学排版（MATH）

| 规则 ID | 说明 |
|---------|------|
| MATH-001 | 检查微分符号 d 是否使用正体 `\mathrm{d}` |
| MATH-002 | 检查特殊常数（e, π, i）是否使用正体 |
| MATH-003 | 检查介电常量是否使用 `\varepsilon` 而非 `\epsilon` |
| MATH-004 | 检查矢量是否使用 `\vec{}` 而非加粗 |
| MATH-005 | 检查数值与单位之间的格式（`\text{~ 单位}`） |

### 图片规范（FIG）

| 规则 ID | 说明 |
|---------|------|
| FIG-001 | 检查 `figure` 环境中是否包含 `\caption` |
| FIG-002 | 检查 `figure` 环境中是否包含 `\label` |
| FIG-003 | 检查 `figure` 环境是否指定了浮动位置 `[H]` |
| FIG-004 | 检查 `figure` 环境中是否使用 `\centering` |

### 评分系统（SCORE）

| 规则 ID | 说明 |
|---------|------|
| SCORE-001 | 检查 `solution` 环境末尾是否有 `\scoring` 命令 |
| SCORE-002 | 检查解答中的公式是否通过 `\eqtagscore` 标记分值 |
| SCORE-003 | 检查 `\solsubq` 命令格式是否有两个参数 `{编号}{分值}` |
| SCORE-004 | 检查小问分值之和（`\eqtagscore` + `\addtext`）是否等于题目总分 |

### 文本格式（TEXT）

| 规则 ID | 说明 |
|---------|------|
| TEXT-001 | 检查题干中的公式是否使用 `\eqtag`（而非 `\eqtagscore`） |
| TEXT-002 | 检查中文文本中的括号是否使用中文标点 |
| TEXT-003 | 检查英文逗号、句号后是否有空格 |
| TEXT-004 | 检查文档中是否有未处理的 TODO 注释 |

## 缓存机制

首次检查时，工具会在 `.tex` 文件同目录下创建 `.format_cache/` 文件夹，以 JSON 格式存储检查结果和文件 SHA-256 哈希。再次检查同一文件时，若文件未修改则直接读取缓存（输出末尾显示 `(来自缓存)`）。

**设计要点**：缓存始终存储**全量检查结果**（运行所有规则、不过滤级别），`--min-severity`、`--exclude` 等筛选仅在展示时应用，确保缓存不会因筛选条件不同而遗漏问题。

```bash
# 强制跳过缓存
python main.py --no-cache your-problem.tex
```

## 忽略特定问题

检查输出中每条问题前有 `#序号`，可通过 `--ignore` 将特定问题加入忽略列表：

```bash
# 第一步：正常检查，查看序号
python main.py your-problem.tex

# 第二步：忽略 #2 和 #3
python main.py --ignore 2,3 your-problem.tex

# 查看已忽略的问题
python main.py --list-ignores your-problem.tex

# 清除所有忽略
python main.py --clear-ignores your-problem.tex

# 按指纹移除单条忽略
python main.py --remove-ignore <fingerprint> your-problem.tex
```

忽略机制基于 `rule_id + 源码行内容` 生成稳定指纹，因此：
- 插入/删除其他行导致行号变化 → 忽略仍有效
- 被忽略的行内容被修改 → 忽略自动失效

## 扩展自定义规则

在 `src/rules/` 下新建 `.py` 文件，继承 `BaseRule` 并设置 `rule_id` 即可自动注册，无需修改其他文件：

```python
from src.rules.base import BaseRule
from src.models import Issue, Severity

class MyCustomRule(BaseRule):
    rule_id = "CUSTOM-001"
    description = "我的自定义检查"

    def check(self, content: str, lines: list[str]) -> list[Issue]:
        issues = []
        for i, line in enumerate(lines):
            if "某个不规范写法" in line:
                issues.append(Issue(
                    rule_id=self.rule_id,
                    severity=Severity.WARNING,
                    message="检测到不规范写法",
                    line=i + 1,
                    suggestion="建议的修改方式",
                ))
        return issues
```

然后在 `src/checker.py` 中添加一行导入：

```python
import src.rules.your_module  # noqa: F401
```

## 项目结构

```
FormatChecker/
├── main.py                     # CLI 入口
├── README.md
├── LICENSE
├── src/
│   ├── __init__.py
│   ├── models.py               # 数据模型（Severity, Issue, CheckResult）
│   ├── checker.py              # 检查引擎（规则调度、缓存集成、过滤）
│   ├── cache.py                # 缓存与忽略管理（JSON 存储、哈希比对）
│   └── rules/
│       ├── __init__.py
│       ├── base.py             # BaseRule 基类 + RuleRegistry 自动注册
│       ├── structure.py        # 文档结构规则（5 条）
│       ├── math_format.py      # 数学排版规则（5 条）
│       ├── figure.py           # 图片规范规则（4 条）
│       ├── scoring.py          # 评分系统规则（4 条）
│       └── text_format.py      # 文本格式规则（4 条）
└── tests/
    └── example-problem.tex     # CPHOS 模板示例文件
```

## 许可证

[MIT License](LICENSE)