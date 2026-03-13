"""文档结构检查规则。"""

import re
from src.rules.base import BaseRule
from src.models import Issue, Severity


class DocumentClassRule(BaseRule):
    rule_id = "STRUCT-001"
    description = "检查 \\documentclass 是否使用 cphos 文档类"

    def check(self, content: str, lines: list[str]) -> list[Issue]:
        issues: list[Issue] = []
        found = False
        for i, line in enumerate(lines):
            if re.match(r"^\s*\\documentclass", line):
                found = True
                if "cphos" not in line:
                    issues.append(Issue(
                        self.rule_id, Severity.ERROR,
                        f"文档类应为 cphos，当前为: {line.strip()}",
                        line=i + 1,
                        suggestion="使用 \\documentclass[answer]{cphos}",
                    ))
                break
        if not found:
            issues.append(Issue(
                self.rule_id, Severity.ERROR,
                "未找到 \\documentclass 声明",
                suggestion="在文件开头添加 \\documentclass[answer]{cphos}",
            ))
        return issues


class RequiredMetadataRule(BaseRule):
    rule_id = "STRUCT-002"
    description = "检查必需的元数据命令是否存在"

    REQUIRED_COMMANDS = [
        (r"\\cphostitle\{", "\\cphostitle{...}"),
        (r"\\cphossubtitle\{", "\\cphossubtitle{...}"),
    ]

    def check(self, content: str, lines: list[str]) -> list[Issue]:
        issues: list[Issue] = []
        for pattern, name in self.REQUIRED_COMMANDS:
            if not re.search(pattern, content):
                issues.append(Issue(
                    self.rule_id, Severity.WARNING,
                    f"缺少元数据命令 {name}",
                    suggestion=f"在 \\begin{{document}} 前添加 {name}",
                ))
        return issues


class RequiredEnvironmentsRule(BaseRule):
    rule_id = "STRUCT-003"
    description = "检查必需的环境是否存在"

    REQUIRED_ENVS = [
        ("document", "document"),
        ("problem", "problem"),
        ("problemstatement", "problemstatement（题干）"),
        ("solution", "solution（解答）"),
    ]

    def check(self, content: str, lines: list[str]) -> list[Issue]:
        issues: list[Issue] = []
        for env_name, display in self.REQUIRED_ENVS:
            begin_pat = rf"\\begin\{{{env_name}\}}"
            end_pat = rf"\\end\{{{env_name}\}}"
            has_begin = re.search(begin_pat, content)
            has_end = re.search(end_pat, content)
            if not has_begin:
                issues.append(Issue(
                    self.rule_id, Severity.ERROR,
                    f"缺少 \\begin{{{env_name}}} 环境（{display}）",
                ))
            elif not has_end:
                issues.append(Issue(
                    self.rule_id, Severity.ERROR,
                    f"找到 \\begin{{{env_name}}} 但缺少对应的 \\end{{{env_name}}}",
                ))
        return issues


class EnvironmentNestingRule(BaseRule):
    rule_id = "STRUCT-004"
    description = "检查环境的 begin/end 配对是否正确"

    def check(self, content: str, lines: list[str]) -> list[Issue]:
        issues: list[Issue] = []
        stack: list[tuple[str, int]] = []

        for i, line in enumerate(lines):
            # 跳过注释行
            stripped = line.lstrip()
            if stripped.startswith("%"):
                continue

            for m in re.finditer(r"\\begin\{(\w+)\}", line):
                stack.append((m.group(1), i + 1))

            for m in re.finditer(r"\\end\{(\w+)\}", line):
                env_name = m.group(1)
                if not stack:
                    issues.append(Issue(
                        self.rule_id, Severity.ERROR,
                        f"\\end{{{env_name}}} 没有匹配的 \\begin{{{env_name}}}",
                        line=i + 1,
                    ))
                else:
                    top_env, top_line = stack.pop()
                    if top_env != env_name:
                        issues.append(Issue(
                            self.rule_id, Severity.ERROR,
                            f"环境嵌套不匹配: 第{top_line}行的 \\begin{{{top_env}}} "
                            f"与第{i+1}行的 \\end{{{env_name}}} 不对应",
                            line=i + 1,
                        ))

        for env_name, line_num in stack:
            issues.append(Issue(
                self.rule_id, Severity.ERROR,
                f"\\begin{{{env_name}}} 在第{line_num}行打开但从未关闭",
                line=line_num,
            ))
        return issues


class ProblemScoreRule(BaseRule):
    rule_id = "STRUCT-005"
    description = "检查 problem 环境是否声明了分值"

    def check(self, content: str, lines: list[str]) -> list[Issue]:
        issues: list[Issue] = []
        for i, line in enumerate(lines):
            m = re.search(r"\\begin\{problem\}", line)
            if m:
                if not re.search(r"\\begin\{problem\}\[\d+\]", line):
                    issues.append(Issue(
                        self.rule_id, Severity.WARNING,
                        "\\begin{problem} 应声明总分值，如 \\begin{problem}[40]{标题}",
                        line=i + 1,
                        suggestion="添加总分值参数: \\begin{problem}[分值]{标题}",
                    ))
        return issues
