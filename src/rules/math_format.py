"""数学公式格式检查规则。"""

import re
from src.rules.base import BaseRule
from src.models import Issue, Severity


class DifferentialFormatRule(BaseRule):
    rule_id = "MATH-001"
    description = "检查微分符号 d 是否使用正体 \\mathrm{d}"

    def check(self, content: str, lines: list[str]) -> list[Issue]:
        issues: list[Issue] = []
        in_math = False
        for i, line in enumerate(lines):
            stripped = line.lstrip()
            if stripped.startswith("%"):
                continue

            # 检测行间公式环境
            if re.search(r"\\begin\{equation\}", line):
                in_math = True
            if re.search(r"\\end\{equation\}", line):
                in_math = False
                continue

            if in_math or re.search(r"\$.*\$", line):
                # 查找积分中的 dx, dy 等但没用 \mathrm{d} 的情况
                # 匹配 \,dx 或直接的 dx（不在 \mathrm{d} 后）
                bad_matches = re.finditer(
                    r"(?<!\\mathrm\{)(?<!\\text\{)\\?d([xyzfgtsSuVvl]|\\theta|\\phi|\\varphi|\\omega|\\tau)\b",
                    line,
                )
                for m in bad_matches:
                    # 排除已经正确使用的情况
                    prefix = line[max(0, m.start() - 10):m.start()]
                    if "\\mathrm{d}" in prefix or "mathrm{d" in prefix:
                        continue
                    if "\\mathrm" in m.group(0):
                        continue
                    issues.append(Issue(
                        self.rule_id, Severity.WARNING,
                        f"微分符号 d 应使用正体: \\mathrm{{d}}",
                        line=i + 1,
                        suggestion="将 d 替换为 \\mathrm{d}，积分中使用 \\,\\mathrm{d}",
                    ))
        return issues

class DifferentialSpacingRule(BaseRule):
    rule_id = "MATH-007"
    description = "检查微分号前是否缺失间距 commands \\,"

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

            if in_math or re.search(r"\$.*\$", line):
                matches = re.finditer(r"\\mathrm\{d\}", line)
                for m in matches:
                    start = m.start()
                    if start == 0:
                        continue
                    
                    prefix = line[:start].rstrip()
                    if not prefix:
                        continue
                        
                    # 1. 以间距命令结尾：\, \; \! \ \quad \qquad \hspace \hfill
                    if re.search(r"\\(?:,|;|!| |quad|qquad|hspace\{[^}]*\}|hfill)$", prefix):
                        continue
                        
                    # 2. 以数学操作符、关系符、左括号等符号结尾
                    if re.search(r"[-+*/=<>\(\[{&^_:\$]$", prefix):
                        continue
                        
                    # 3. 特例处理 \cdot, \times, \otimes 等运算符与排版符号
                    if re.search(r"\\(?:cdot|times|otimes|oplus|pm|mp|div|equiv|approx|propto|sim|leq|geq|ll|gg|limits)\s*$", prefix):
                        continue
                        
                    # 4. 积分号等开头直接跟 d
                    if re.search(r"\\(?:i+nt|oint|sum|prod)\s*$", prefix):
                        continue
                        
                    # 5. 前面是 \partial, \nabla
                    if re.search(r"\\(?:partial|nabla)\s*$", prefix):
                        continue
                        
                    # 6. 波浪号空格
                    if prefix.endswith("~"):
                        continue

                    # 其他情况统统报警（多半是前面跟了变量、右括号、数字等，未分排）
                    issues.append(Issue(
                        self.rule_id, Severity.WARNING,
                        "微分符号 \\mathrm{d} 与前方变量（或右括号、数字等）之间应添加物理间距 \\,",
                        line=i + 1,
                        suggestion="在 \\mathrm{d} 前添加 \\,"
                    ))
        return issues


class SpecialConstantsRule(BaseRule):
    rule_id = "MATH-002"
    description = "检查特殊常数（e, π, i）是否使用正体"

    PATTERNS = [
        # (错误用法正则, 正确写法, 描述)
        (r"(?<![a-zA-Z\\])(?<!\\mathrm\{)e\^", "\\mathrm{e}^", "自然常数 e 应使用正体 \\mathrm{e} (表示元电荷、电子等物理量时可忽略该建议)"),
        (r"(?<!\\up)\\pi(?![a-zA-Z])", "\\uppi", "圆周率 π 应使用 \\uppi"),
    ]

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

            if not in_math and not re.search(r"\$", line):
                continue

            for pattern, correct, desc in self.PATTERNS:
                if re.search(pattern, line):
                    issues.append(Issue(
                        self.rule_id, Severity.INFO,
                        desc,
                        line=i + 1,
                        suggestion=f"使用 {correct}",
                    ))
        return issues


class EpsilonFormatRule(BaseRule):
    rule_id = "MATH-003"
    description = "检查介电常量是否使用 \\varepsilon 而非 \\epsilon"

    def check(self, content: str, lines: list[str]) -> list[Issue]:
        issues: list[Issue] = []
        for i, line in enumerate(lines):
            stripped = line.lstrip()
            if stripped.startswith("%"):
                continue
            # 查找裸 \epsilon（不是 \varepsilon）
            matches = re.finditer(r"(?<!var)\\epsilon(?![a-zA-Z])", line)
            for _ in matches:
                issues.append(Issue(
                    self.rule_id, Severity.WARNING,
                    "应使用 \\varepsilon 而非 \\epsilon",
                    line=i + 1,
                    suggestion="替换为 \\varepsilon",
                ))
        return issues


class VectorFormatRule(BaseRule):
    rule_id = "MATH-004"
    description = "检查矢量是否使用 \\vec{} 而非加粗"

    def check(self, content: str, lines: list[str]) -> list[Issue]:
        issues: list[Issue] = []
        for i, line in enumerate(lines):
            stripped = line.lstrip()
            if stripped.startswith("%"):
                continue
            # 检查是否在公式中使用了 \mathbf 或 \boldsymbol 表示矢量
            if re.search(r"\\(mathbf|boldsymbol)\{[a-zA-Z]\}", line):
                issues.append(Issue(
                    self.rule_id, Severity.WARNING,
                    "矢量应使用 \\vec{} 表示，不使用加粗",
                    line=i + 1,
                    suggestion="将 \\mathbf{v} / \\boldsymbol{v} 替换为 \\vec{v}",
                ))
        return issues


class UnitFormatRule(BaseRule):
    rule_id = "MATH-005"
    description = "检查数值与单位之间的格式"

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
                # 检查单位是否用了 \text{~ unit} 格式
                # 如果有数字后直接跟字母（可能是单位），且没有 \text
                matches = re.finditer(r"\d+\s*\\text\{([^}]*)\}", line)
                for m in matches:
                    unit_text = m.group(1)
                    if not unit_text.startswith("~"):
                        issues.append(Issue(
                            self.rule_id, Severity.INFO,
                            "数值和单位间建议用 \\text{~ 单位} 保持间距",
                            line=i + 1,
                            suggestion="使用 \\text{~m/s} 格式",
                        ))
        return issues


class UpperGreekItalicRule(BaseRule):
    rule_id = "MATH-006"
    description = "检查大写希腊字母是否使用斜体（\\var- 形式）"

    # 需要检查的大写希腊字母及其斜体替换
    _LETTERS = {
        "Gamma": "varGamma", "Delta": "varDelta", "Theta": "varTheta",
        "Lambda": "varLambda", "Xi": "varXi", "Pi": "varPi",
        "Sigma": "varSigma", "Upsilon": "varUpsilon", "Phi": "varPhi",
        "Psi": "varPsi", "Omega": "varOmega",
    }
    # 匹配正体大写希腊字母，排除已经是 \var- 形式的
    _PATTERN = re.compile(
        r"(?<!var)\\(" + "|".join(_LETTERS.keys()) + r")(?![a-zA-Z])"
    )

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

            if not in_math and not re.search(r"\$", line) and not re.search(r"\\\(", line):
                continue

            for m in self._PATTERN.finditer(line):
                name = m.group(1)
                replacement = self._LETTERS[name]
                issues.append(Issue(
                    self.rule_id, Severity.INFO,
                    f"大写希腊字母 \\{name} 默认为正体，物理公式中通常应使用斜体 \\{replacement}",
                    line=i + 1,
                    suggestion=f"将 \\{name} 替换为 \\{replacement} (若确实需要正体，如表述变化量的 \\Delta、特殊函数等情况可忽略该建议)",
                ))
        return issues
