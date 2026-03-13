"""检查引擎：加载规则、执行检查、缓存管理、汇总结果。"""

from pathlib import Path
from src.models import Issue, CheckResult, Severity
from src.rules.base import RuleRegistry, BaseRule
from src import cache as cache_mod

# 导入规则模块以触发自动注册
import src.rules.structure      # noqa: F401
import src.rules.math_format    # noqa: F401
import src.rules.figure         # noqa: F401
import src.rules.scoring        # noqa: F401
import src.rules.text_format    # noqa: F401


class Checker:
    """格式检查引擎。"""

    def __init__(
        self,
        min_severity: Severity = Severity.INFO,
        exclude_rules: set[str] | None = None,
        include_rules: set[str] | None = None,
        use_cache: bool = True,
    ):
        """
        Args:
            min_severity:  只报告 >= 此级别的问题
            exclude_rules: 要排除的规则 ID 集合
            include_rules: 只运行这些规则（为 None 则运行全部）
            use_cache:     是否启用文件哈希缓存
        """
        self.min_severity = min_severity
        self.exclude_rules = exclude_rules or set()
        self.include_rules = include_rules
        self.use_cache = use_cache

    def _get_active_rules(self) -> list[BaseRule]:
        rules = []
        for rule_cls in RuleRegistry.all_rules():
            rid = rule_cls.rule_id
            if rid in self.exclude_rules:
                continue
            if self.include_rules is not None and rid not in self.include_rules:
                continue
            rules.append(rule_cls())
        return rules

    def _run_all_rules(self, filepath: Path) -> CheckResult:
        """运行全部规则，返回未经筛选的完整结果。"""
        content = filepath.read_text(encoding="utf-8")
        lines = content.splitlines()

        result = CheckResult(filepath=str(filepath))
        for rule_cls in RuleRegistry.all_rules():
            rule = rule_cls()
            issues = rule.check(content, lines)
            # 为每个 issue 补充 line_content
            for issue in issues:
                if issue.line and 1 <= issue.line <= len(lines):
                    issue.line_content = lines[issue.line - 1]
            result.issues.extend(issues)
        return result

    def _filter_issues(self, issues: list[Issue], ignores: set[str]) -> list[Issue]:
        """按筛选条件和 ignore 列表过滤 issues。"""
        filtered = []
        for issue in issues:
            if issue.severity < self.min_severity:
                continue
            if issue.rule_id in self.exclude_rules:
                continue
            if self.include_rules is not None and issue.rule_id not in self.include_rules:
                continue
            if issue.fingerprint() in ignores:
                continue
            filtered.append(issue)
        return filtered

    def check_file(self, filepath: str | Path) -> tuple[CheckResult, bool]:
        """
        检查文件并返回过滤后的结果。

        Returns:
            (filtered_result, from_cache)
        """
        filepath = Path(filepath)
        ignores = cache_mod.load_ignores(filepath)

        full_result: CheckResult | None = None
        from_cache = False

        if self.use_cache:
            cached, file_hash = cache_mod.load_cached_result(filepath)
            if cached is not None:
                full_result = cached
                from_cache = True

        if full_result is None:
            full_result = self._run_all_rules(filepath)
            if self.use_cache:
                file_hash = cache_mod.compute_file_hash(filepath)
                cache_mod.save_cached_result(filepath, full_result, file_hash)

        # 筛选 + ignore 过滤
        filtered_issues = self._filter_issues(full_result.issues, ignores)
        filtered_result = CheckResult(filepath=str(filepath), issues=filtered_issues)
        return filtered_result, from_cache

    def check_files(self, filepaths: list[str | Path]) -> list[tuple[CheckResult, bool]]:
        return [self.check_file(fp) for fp in filepaths]

    @staticmethod
    def list_rules() -> list[dict]:
        """列出所有已注册的规则。"""
        return [
            {"rule_id": r.rule_id, "description": r.description}
            for r in RuleRegistry.all_rules()
        ]
