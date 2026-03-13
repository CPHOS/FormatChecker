"""文本格式检查规则。"""

import re
from src.rules.base import BaseRule
from src.models import Issue, Severity


class EqtagInStatementRule(BaseRule):
    rule_id = "TEXT-001"
    description = "检查题干中的公式是否使用 \\eqtag（而非 \\eqtagscore）"

    def check(self, content: str, lines: list[str]) -> list[Issue]:
        issues: list[Issue] = []
        in_statement = False

        for i, line in enumerate(lines):
            if re.search(r"\\begin\{problemstatement\}", line):
                in_statement = True
            if re.search(r"\\end\{problemstatement\}", line):
                in_statement = False

            if in_statement and "\\eqtagscore" in line:
                issues.append(Issue(
                    self.rule_id, Severity.ERROR,
                    "题干中不应使用 \\eqtagscore，应使用 \\eqtag{编号}",
                    line=i + 1,
                    suggestion="将 \\eqtagscore{编号}{分值} 替换为 \\eqtag{编号}",
                ))
        return issues


class ChinesePunctuationRule(BaseRule):
    rule_id = "TEXT-002"
    description = "检查中文文本中的括号是否使用中文标点"

    def check(self, content: str, lines: list[str]) -> list[Issue]:
        issues: list[Issue] = []
        for i, line in enumerate(lines):
            stripped = line.lstrip()
            if stripped.startswith("%") or stripped.startswith("\\"):
                continue
            # 检查中文语境中的英文括号（中文字符紧邻英文括号）
            if re.search(r"[\u4e00-\u9fff]\([^)]*\)|\([^)]*\)[\u4e00-\u9fff]", line):
                issues.append(Issue(
                    self.rule_id, Severity.INFO,
                    "中文环境中建议使用中文括号（）而非英文括号()",
                    line=i + 1,
                    suggestion="将半角括号 () 替换为全角括号（）",
                ))
        return issues


class EnglishSpaceRule(BaseRule):
    rule_id = "TEXT-003"
    description = "检查英文逗号、句号后是否有空格"

    def check(self, content: str, lines: list[str]) -> list[Issue]:
        issues: list[Issue] = []
        in_math = False
        for i, line in enumerate(lines):
            stripped = line.lstrip()
            if stripped.startswith("%"):
                continue

            if re.search(r"\\begin\{equation\}", line):
                in_math = True
            if re.search(r"\\end\{equation\}", line):
                in_math = False
                continue

            if in_math:
                continue

            # 仅检查包含英文句子的行，查找逗号/句号后未跟空格或换行的情况
            # 排除 LaTeX 命令中的情况
            if stripped.startswith("\\"):
                continue
            matches = re.finditer(r"[a-zA-Z][,.][a-zA-Z]", line)
            for m in matches:
                # 排除小数、文件扩展名（.tex, .jpg 等）和 URL
                ctx = line[max(0, m.start()-5):m.end()+10]
                if re.search(r"\.[a-zA-Z]{1,4}\b", ctx) and '/' in line:
                    continue
                issues.append(Issue(
                    self.rule_id, Severity.INFO,
                    f"英文标点后建议加空格: \"{m.group(0)}\"",
                    line=i + 1,
                    suggestion="在逗号或句号后添加一个空格",
                ))
        return issues


class TodoCommentRule(BaseRule):
    rule_id = "TEXT-004"
    description = "检查文档中是否有未处理的 TODO 注释"

    def check(self, content: str, lines: list[str]) -> list[Issue]:
        issues: list[Issue] = []
        for i, line in enumerate(lines):
            if "TODO" in line:
                # 提取 TODO 内容
                m = re.search(r"TODO:?\s*(.*)", line)
                desc = m.group(1).strip() if m else ""
                issues.append(Issue(
                    self.rule_id, Severity.INFO,
                    f"存在未处理的 TODO 标记{': ' + desc if desc else ''}",
                    line=i + 1,
                    suggestion="完成 TODO 内容后移除标记",
                ))
        return issues
