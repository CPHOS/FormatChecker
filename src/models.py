"""数据模型：问题严重级别和检查结果。"""

from enum import IntEnum
from dataclasses import dataclass, field


class Severity(IntEnum):
    """问题严重级别，数值越大越严重。"""
    INFO = 0       # 建议性信息
    WARNING = 1    # 格式警告，不影响编译但不规范
    ERROR = 2      # 格式错误，可能导致编译失败或严重不规范


SEVERITY_LABELS = {
    Severity.INFO: "💡 信息",
    Severity.WARNING: "⚠️  警告",
    Severity.ERROR: "❌ 错误",
}

SEVERITY_COLORS = {
    Severity.INFO: "\033[36m",     # cyan
    Severity.WARNING: "\033[33m",  # yellow
    Severity.ERROR: "\033[31m",    # red
}

RESET_COLOR = "\033[0m"


@dataclass
class Issue:
    """一条检查问题。"""
    rule_id: str          # 规则标识，如 "STRUCT-001"
    severity: Severity
    message: str          # 问题描述
    line: int | None = None        # 出现行号（1-based），可为空
    suggestion: str = ""  # 修改建议
    line_content: str = ""  # 该行原始内容（用于生成忽略指纹）

    def to_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "severity": self.severity.name,
            "message": self.message,
            "line": self.line,
            "suggestion": self.suggestion,
            "line_content": self.line_content,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Issue":
        return cls(
            rule_id=d["rule_id"],
            severity=Severity[d["severity"]],
            message=d["message"],
            line=d.get("line"),
            suggestion=d.get("suggestion", ""),
            line_content=d.get("line_content", ""),
        )

    def fingerprint(self) -> str:
        """基于 rule_id + 源码行内容生成稳定指纹，用于 ignore 匹配。"""
        import hashlib
        key = f"{self.rule_id}|{self.line_content.strip()}"
        return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]

    def format(self, color: bool = True, index: int | None = None) -> str:
        color_code = SEVERITY_COLORS[self.severity] if color else ""
        reset = RESET_COLOR if color else ""
        label = SEVERITY_LABELS[self.severity]
        loc = f"第{self.line}行 " if self.line else ""
        idx = f"#{index} " if index is not None else ""
        parts = [f"{idx}{color_code}[{self.rule_id}] {label}{reset} {loc}{self.message}"]
        if self.suggestion:
            parts.append(f"  ↳ 建议: {self.suggestion}")
        return "\n".join(parts)


@dataclass
class CheckResult:
    """单个文件的完整检查结果。"""
    filepath: str
    issues: list[Issue] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.WARNING)

    @property
    def info_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.INFO)

    def format_summary(self, color: bool = True, show_index: bool = False) -> str:
        lines = [f"\n{'='*60}", f"检查文件: {self.filepath}", f"{'='*60}"]
        if not self.issues:
            lines.append("✅ 未发现格式问题。")
            return "\n".join(lines)

        for idx, issue in enumerate(
            sorted(self.issues, key=lambda i: (-i.severity, i.line or 0)), start=1
        ):
            lines.append(issue.format(color, index=idx if show_index else None))

        lines.append(f"\n--- 汇总: {self.error_count} 个错误, "
                      f"{self.warning_count} 个警告, "
                      f"{self.info_count} 个信息 ---")
        return "\n".join(lines)

    def get_issue_by_index(self, index: int) -> Issue | None:
        """按展示排序后的序号(1-based)获取 Issue。"""
        sorted_issues = sorted(self.issues, key=lambda i: (-i.severity, i.line or 0))
        if 1 <= index <= len(sorted_issues):
            return sorted_issues[index - 1]
        return None
