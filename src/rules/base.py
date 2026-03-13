"""规则基类与自动注册机制。"""

from __future__ import annotations
from abc import ABC, abstractmethod
from src.models import Issue


class RuleRegistry:
    """全局规则注册表——所有规则子类自动注册。"""
    _rules: list[type[BaseRule]] = []

    @classmethod
    def register(cls, rule_cls: type[BaseRule]) -> type[BaseRule]:
        cls._rules.append(rule_cls)
        return rule_cls

    @classmethod
    def all_rules(cls) -> list[type[BaseRule]]:
        return list(cls._rules)

    @classmethod
    def clear(cls) -> None:
        cls._rules.clear()


class BaseRule(ABC):
    """
    规则基类。所有检查规则继承此类并实现 check() 方法。

    子类需要：
      - 设置 rule_id: str     (唯一标识，如 "STRUCT-001")
      - 设置 description: str (描述该规则检查什么)
      - 实现 check(content, lines) -> list[Issue]
    """

    rule_id: str = ""
    description: str = ""

    @abstractmethod
    def check(self, content: str, lines: list[str]) -> list[Issue]:
        """
        执行检查。

        Args:
            content: 文件完整文本
            lines:   按行拆分的列表（0-indexed）

        Returns:
            发现的问题列表
        """
        ...

    def __init_subclass__(cls, **kwargs):
        """子类定义时自动注册到 RuleRegistry。"""
        super().__init_subclass__(**kwargs)
        if cls.rule_id:  # 只注册有 rule_id 的具体规则
            RuleRegistry.register(cls)
