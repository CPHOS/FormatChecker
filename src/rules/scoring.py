"""评分相关检查规则。"""

import re
from src.rules.base import BaseRule
from src.models import Issue, Severity


class ScoringCommandRule(BaseRule):
    rule_id = "SCORE-001"
    description = "检查 solution 环境末尾是否有 \\scoring 命令"

    def check(self, content: str, lines: list[str]) -> list[Issue]:
        issues: list[Issue] = []
        if "\\begin{solution}" in content and "\\scoring" not in content:
            issues.append(Issue(
                self.rule_id, Severity.WARNING,
                "解答部分缺少 \\scoring 命令，无法自动生成评分标准",
                suggestion="在 \\end{solution} 前添加 \\scoring",
            ))
        return issues


class EqtagscoreInSolutionRule(BaseRule):
    rule_id = "SCORE-002"
    description = "检查解答中的公式是否通过 \\eqtagscore 标记分值"

    def check(self, content: str, lines: list[str]) -> list[Issue]:
        issues: list[Issue] = []
        in_solution = False
        in_equation = False

        for i, line in enumerate(lines):
            if re.search(r"\\begin\{solution\}", line):
                in_solution = True
            if re.search(r"\\end\{solution\}", line):
                in_solution = False

            if not in_solution:
                continue

            if re.search(r"\\begin\{equation\}", line):
                in_equation = True
            if re.search(r"\\end\{equation\}", line):
                if in_equation:
                    # 回溯检查这个 equation 环境中是否有 eqtagscore
                    eq_block = ""
                    for j in range(i, -1, -1):
                        eq_block = lines[j] + eq_block
                        if re.search(r"\\begin\{equation\}", lines[j]):
                            break
                    if "\\eqtagscore" not in eq_block and "\\eqtag" not in eq_block:
                        issues.append(Issue(
                            self.rule_id, Severity.WARNING,
                            "解答中的 equation 环境缺少 \\eqtagscore{编号}{分值} 标记",
                            line=i + 1,
                            suggestion="在公式末尾添加 \\eqtagscore{编号}{分数}",
                        ))
                in_equation = False
        return issues


class SolsubqFormatRule(BaseRule):
    rule_id = "SCORE-003"
    description = "检查 \\solsubq 命令格式是否正确"

    def check(self, content: str, lines: list[str]) -> list[Issue]:
        issues: list[Issue] = []
        for i, line in enumerate(lines):
            stripped = line.lstrip()
            if stripped.startswith("%"):
                continue
            # 检查 \solsubq 后是否同时有编号和分值两个参数
            matches = re.finditer(r"\\solsubq\{([^}]*)\}", line)
            for m in matches:
                rest = line[m.end():]
                if not re.match(r"\{(\d+)\}", rest):
                    issues.append(Issue(
                        self.rule_id, Severity.ERROR,
                        "\\solsubq 需要两个参数: {编号}{分值}",
                        line=i + 1,
                        suggestion="正确格式: \\solsubq{编号}{分值}",
                    ))
        return issues


class ScoreConsistencyRule(BaseRule):
    rule_id = "SCORE-004"
    description = "检查小问分值之和是否等于题目总分"

    def check(self, content: str, lines: list[str]) -> list[Issue]:
        issues: list[Issue] = []

        # 获取总分
        total_match = re.search(r"\\begin\{problem\}\[(\d+)\]", content)
        if not total_match:
            return issues
        total_score = int(total_match.group(1))

        # 收集 eqtagscore 分值
        eq_scores = sum(
            int(m.group(1))
            for m in re.finditer(r"\\eqtagscore\{\d+\}\{(\d+)\}", content)
        )
        # 收集 addtext 分值
        text_scores = sum(
            int(m.group(1))
            for m in re.finditer(r"\\addtext\{[^}]*\}\{(\d+)\}", content)
        )

        sum_score = eq_scores + text_scores
        if sum_score != total_score:
            issues.append(Issue(
                self.rule_id, Severity.WARNING,
                f"分值不一致: 题目声明总分 {total_score}，"
                f"但标记的分值之和为 {sum_score} "
                f"(公式分 {eq_scores} + 文字分 {text_scores})",
                suggestion="请检查 \\eqtagscore 和 \\addtext 的分值是否与总分一致",
            ))
        return issues
