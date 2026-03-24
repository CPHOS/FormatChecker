"""multisol 多解法环境检查规则。"""

import re
from src.rules.base import BaseRule
from src.models import Issue, Severity


class MultisolItemRule(BaseRule):
    rule_id = "MSOL-001"
    description = "检查 multisol 环境中是否包含至少两个 \\item"

    def check(self, content: str, lines: list[str]) -> list[Issue]:
        issues: list[Issue] = []
        in_multisol = False
        multisol_start = 0
        item_count = 0

        for i, line in enumerate(lines):
            if re.search(r"\\begin\{multisol\}", line):
                in_multisol = True
                multisol_start = i + 1
                item_count = 0
            if in_multisol and re.search(r"\\item\b", line):
                item_count += 1
            if re.search(r"\\end\{multisol\}", line):
                if in_multisol and item_count < 2:
                    issues.append(Issue(
                        self.rule_id, Severity.WARNING,
                        f"multisol 环境应包含至少两个 \\item（当前 {item_count} 个），"
                        "否则不需要使用 multisol",
                        line=multisol_start,
                        suggestion="添加多个 \\item 分别展示不同解法，或去掉 multisol 环境",
                    ))
                in_multisol = False
        return issues


class MultisolStarSuffixRule(BaseRule):
    rule_id = "MSOL-002"
    description = "检查 multisol 中第二条及后续解法的 \\eqtagscore 编号是否带 * 后缀"

    def check(self, content: str, lines: list[str]) -> list[Issue]:
        issues: list[Issue] = []
        in_multisol = False
        item_index = 0  # 当前是第几个 \item（1-based）

        for i, line in enumerate(lines):
            stripped = line.lstrip()
            if stripped.startswith("%"):
                continue

            if re.search(r"\\begin\{multisol\}", line):
                in_multisol = True
                item_index = 0
            if re.search(r"\\end\{multisol\}", line):
                in_multisol = False

            if not in_multisol:
                continue

            if re.search(r"\\item\b", line):
                item_index += 1

            # 检查后续解法（第2个及之后的 \item）
            if item_index >= 2:
                for m in re.finditer(r"\\eqtagscore\{([^}]+)\}", line):
                    tag = m.group(1)
                    if not tag.endswith("*"):
                        issues.append(Issue(
                            self.rule_id, Severity.WARNING,
                            f"multisol 中后续解法的 \\eqtagscore 编号 \"{tag}\" "
                            "建议加 \"*\" 后缀以区分（如 \"{tag}*\"）",
                            line=i + 1,
                            suggestion=f"将 \\eqtagscore{{{tag}}} 改为 \\eqtagscore{{{tag}*}}",
                        ))

            # 检查第一条解法不应带 * 后缀
            if item_index == 1:
                for m in re.finditer(r"\\eqtagscore\{([^}]+)\}", line):
                    tag = m.group(1)
                    if tag.endswith("*"):
                        issues.append(Issue(
                            self.rule_id, Severity.INFO,
                            f"multisol 中第一条解法的 \\eqtagscore 编号 \"{tag}\" "
                            "不应带 \"*\" 后缀",
                            line=i + 1,
                            suggestion=f"将 \\eqtagscore{{{tag}}} 改为 "
                            f"\\eqtagscore{{{tag.rstrip('*')}}}",
                        ))
        return issues


class MultisolScoreBalanceRule(BaseRule):
    rule_id = "MSOL-003"
    description = "检查 multisol 中各解法的分值总和是否一致"

    def check(self, content: str, lines: list[str]) -> list[Issue]:
        issues: list[Issue] = []
        in_multisol = False
        multisol_start = 0
        item_index = 0
        # 每个解法的分值列表
        sol_scores: list[int] = []
        current_score = 0

        for i, line in enumerate(lines):
            if re.search(r"\\begin\{multisol\}", line):
                in_multisol = True
                multisol_start = i + 1
                item_index = 0
                sol_scores = []
                current_score = 0
            if re.search(r"\\end\{multisol\}", line):
                if in_multisol:
                    # 保存最后一个解法的分值
                    if item_index > 0:
                        sol_scores.append(current_score)
                    # 检查各解法分值是否一致
                    if len(sol_scores) >= 2:
                        if len(set(sol_scores)) > 1:
                            desc = ", ".join(
                                f"解法{idx+1}={s}分"
                                for idx, s in enumerate(sol_scores)
                            )
                            issues.append(Issue(
                                self.rule_id, Severity.WARNING,
                                f"multisol 中各解法分值不一致: {desc}",
                                line=multisol_start,
                                suggestion="各解法的 \\eqtagscore 分值之和应当相同",
                            ))
                in_multisol = False

            if not in_multisol:
                continue

            if re.search(r"\\item\b", line):
                if item_index > 0:
                    sol_scores.append(current_score)
                item_index += 1
                current_score = 0

            # 收集当前解法的 eqtagscore 分值
            for m in re.finditer(r"\\eqtagscore\{[^}]+\}\{(\d+)\}", line):
                current_score += int(m.group(1))
            # 收集 addtext 分值
            for m in re.finditer(r"\\addtext\{[^}]*\}\{(\d+)\}", line):
                current_score += int(m.group(1))

        return issues
