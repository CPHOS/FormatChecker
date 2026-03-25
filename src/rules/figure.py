"""图片格式检查规则（支持 figure、wrapfigure、subfigure）。"""

import re
from src.rules.base import BaseRule
from src.models import Issue, Severity


class FigureCaptionRule(BaseRule):
    rule_id = "FIG-001"
    description = "检查 figure/wrapfigure/subfigure 环境中是否包含 \\caption"

    # 需要检查 \caption 的环境
    _ENVS = ("figure", "wrapfigure", "subfigure")

    def check(self, content: str, lines: list[str]) -> list[Issue]:
        issues: list[Issue] = []
        # 用栈跟踪嵌套，每层记录 (env_name, start_line, has_caption)
        stack: list[tuple[str, int, bool]] = []

        for i, line in enumerate(lines):
            for env in self._ENVS:
                if re.search(rf"\\begin\{{{env}\}}", line):
                    stack.append((env, i + 1, False))
                if re.search(rf"\\end\{{{env}\}}", line):
                    # 弹出最近匹配的同名环境
                    for j in range(len(stack) - 1, -1, -1):
                        if stack[j][0] == env:
                            env_name, start, has_cap = stack.pop(j)
                            if not has_cap:
                                issues.append(Issue(
                                    self.rule_id, Severity.WARNING,
                                    f"{env_name} 环境缺少 \\caption{{题注}}",
                                    line=start,
                                    suggestion=f"在 \\end{{{env_name}}} 前添加 \\caption{{描述}}",
                                ))
                            break

            # 检查 caption 归属到最近的栈顶环境
            if stack and re.search(r"\\caption\{", line):
                env_name, start, _ = stack[-1]
                stack[-1] = (env_name, start, True)

        return issues


class FigureLabelRule(BaseRule):
    rule_id = "FIG-002"
    description = "检查 figure/wrapfigure/subfigure 环境中是否包含 \\label"

    _ENVS = ("figure", "wrapfigure", "subfigure")

    def check(self, content: str, lines: list[str]) -> list[Issue]:
        issues: list[Issue] = []
        stack: list[tuple[str, int, bool]] = []

        for i, line in enumerate(lines):
            for env in self._ENVS:
                if re.search(rf"\\begin\{{{env}\}}", line):
                    stack.append((env, i + 1, False))
                if re.search(rf"\\end\{{{env}\}}", line):
                    for j in range(len(stack) - 1, -1, -1):
                        if stack[j][0] == env:
                            env_name, start, has_lbl = stack.pop(j)
                            if not has_lbl:
                                issues.append(Issue(
                                    self.rule_id, Severity.WARNING,
                                    f"{env_name} 环境缺少 \\label{{标签}}，无法被 \\ref 引用",
                                    line=start,
                                    suggestion=f"添加 \\label{{fig:描述}} 以便引用",
                                ))
                            break

            if stack and re.search(r"\\label\{", line):
                env_name, start, _ = stack[-1]
                stack[-1] = (env_name, start, True)

        return issues


class FigurePlacementRule(BaseRule):
    rule_id = "FIG-003"
    description = "检查 figure 环境是否指定了浮动位置 [H]"

    def check(self, content: str, lines: list[str]) -> list[Issue]:
        issues: list[Issue] = []
        for i, line in enumerate(lines):
            # 只检查顶层 figure（不检查 wrapfigure/subfigure，它们有各自的定位方式）
            if re.search(r"\\begin\{figure\}(?!\[)", line):
                issues.append(Issue(
                    self.rule_id, Severity.INFO,
                    "figure 环境建议指定浮动位置，如 [H] 以固定位置",
                    line=i + 1,
                    suggestion="使用 \\begin{figure}[H]",
                ))
        return issues


class FigureCenteringRule(BaseRule):
    rule_id = "FIG-004"
    description = "检查 figure 环境中是否使用 \\centering"

    def check(self, content: str, lines: list[str]) -> list[Issue]:
        issues: list[Issue] = []
        in_figure = False
        figure_start = 0
        has_centering = False
        depth = 0  # 跟踪嵌套层级，只检查顶层 figure

        for i, line in enumerate(lines):
            if re.search(r"\\begin\{figure\}", line):
                depth += 1
                if depth == 1:
                    in_figure = True
                    figure_start = i + 1
                    has_centering = False
            # wrapfigure 不需要 \centering
            if in_figure and depth == 1 and "\\centering" in line:
                has_centering = True
            if re.search(r"\\end\{figure\}", line):
                if depth == 1 and in_figure and not has_centering:
                    issues.append(Issue(
                        self.rule_id, Severity.INFO,
                        "figure 环境建议使用 \\centering 居中图片",
                        line=figure_start,
                        suggestion="在 \\begin{figure} 后添加 \\centering",
                    ))
                depth = max(0, depth - 1)
                if depth == 0:
                    in_figure = False
        return issues
