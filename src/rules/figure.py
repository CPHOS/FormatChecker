"""图片格式检查规则。"""

import re
from src.rules.base import BaseRule
from src.models import Issue, Severity


class FigureCaptionRule(BaseRule):
    rule_id = "FIG-001"
    description = "检查 figure 环境中是否包含 \\caption"

    def check(self, content: str, lines: list[str]) -> list[Issue]:
        issues: list[Issue] = []
        in_figure = False
        figure_start = 0
        has_caption = False

        for i, line in enumerate(lines):
            if re.search(r"\\begin\{figure\}", line):
                in_figure = True
                figure_start = i + 1
                has_caption = False
            if in_figure and re.search(r"\\caption\{", line):
                has_caption = True
            if re.search(r"\\end\{figure\}", line):
                if in_figure and not has_caption:
                    issues.append(Issue(
                        self.rule_id, Severity.WARNING,
                        "figure 环境缺少 \\caption{题注}",
                        line=figure_start,
                        suggestion="在 \\end{figure} 前添加 \\caption{图片描述}",
                    ))
                in_figure = False
        return issues


class FigureLabelRule(BaseRule):
    rule_id = "FIG-002"
    description = "检查 figure 环境中是否包含 \\label"

    def check(self, content: str, lines: list[str]) -> list[Issue]:
        issues: list[Issue] = []
        in_figure = False
        figure_start = 0
        has_label = False

        for i, line in enumerate(lines):
            if re.search(r"\\begin\{figure\}", line):
                in_figure = True
                figure_start = i + 1
                has_label = False
            if in_figure and re.search(r"\\label\{", line):
                has_label = True
            if re.search(r"\\end\{figure\}", line):
                if in_figure and not has_label:
                    issues.append(Issue(
                        self.rule_id, Severity.WARNING,
                        "figure 环境缺少 \\label{标签}，无法被 \\ref 引用",
                        line=figure_start,
                        suggestion="添加 \\label{fig:描述} 以便引用",
                    ))
                in_figure = False
        return issues


class FigurePlacementRule(BaseRule):
    rule_id = "FIG-003"
    description = "检查 figure 环境是否指定了浮动位置 [H]"

    def check(self, content: str, lines: list[str]) -> list[Issue]:
        issues: list[Issue] = []
        for i, line in enumerate(lines):
            m = re.search(r"\\begin\{figure\}(?!\[)", line)
            if m:
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

        for i, line in enumerate(lines):
            if re.search(r"\\begin\{figure\}", line):
                in_figure = True
                figure_start = i + 1
                has_centering = False
            if in_figure and "\\centering" in line:
                has_centering = True
            if re.search(r"\\end\{figure\}", line):
                if in_figure and not has_centering:
                    issues.append(Issue(
                        self.rule_id, Severity.INFO,
                        "figure 环境建议使用 \\centering 居中图片",
                        line=figure_start,
                        suggestion="在 \\begin{figure} 后添加 \\centering",
                    ))
                in_figure = False
        return issues
