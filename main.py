"""
CPHOS LaTeX 格式检查器
用法:
    python main.py <file.tex> [file2.tex ...]      检查文件
    python main.py --list-rules                     列出所有规则
    python main.py --min-severity warning <file>    只显示 warning 及以上
    python main.py --exclude MATH-001 <file>        排除某些规则
    python main.py --ignore 1,3 <file>              忽略序号为 1 和 3 的问题
    python main.py --list-ignores <file>            查看已忽略的问题
    python main.py --clear-ignores <file>           清除所有忽略
"""

import argparse
import sys
from pathlib import Path
from src.checker import Checker
from src.models import Severity
from src import cache as cache_mod


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="CPHOS LaTeX 文档格式检查器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "files", nargs="*", help="要检查的 .tex 文件路径",
    )
    parser.add_argument(
        "--list-rules", action="store_true", help="列出所有可用的检查规则",
    )
    parser.add_argument(
        "--min-severity",
        choices=["info", "warning", "error"],
        default="info",
        help="最低报告级别 (默认: info)",
    )
    parser.add_argument(
        "--exclude",
        nargs="*",
        default=[],
        help="排除的规则 ID，如 MATH-001 FIG-003",
    )
    parser.add_argument(
        "--include",
        nargs="*",
        default=None,
        help="只运行指定的规则 ID",
    )
    parser.add_argument(
        "--no-color", action="store_true", help="禁用彩色输出",
    )
    parser.add_argument(
        "--no-cache", action="store_true", help="禁用缓存，强制重新检查",
    )
    # ignore 相关
    parser.add_argument(
        "--ignore",
        type=str,
        default=None,
        help="忽略指定序号的问题（逗号分隔），如 --ignore 1,3",
    )
    parser.add_argument(
        "--list-ignores", action="store_true", help="列出已忽略的问题",
    )
    parser.add_argument(
        "--clear-ignores", action="store_true", help="清除所有忽略项",
    )
    parser.add_argument(
        "--remove-ignore",
        type=str,
        default=None,
        help="移除指定指纹的忽略项",
    )
    return parser.parse_args()


SEVERITY_MAP = {
    "info": Severity.INFO,
    "warning": Severity.WARNING,
    "error": Severity.ERROR,
}


def main() -> int:
    args = parse_args()

    if args.list_rules:
        rules = Checker.list_rules()
        print(f"\n已注册 {len(rules)} 条检查规则:\n")
        for r in rules:
            print(f"  {r['rule_id']:12s}  {r['description']}")
        print()
        return 0

    if not args.files:
        print("错误: 请指定要检查的 .tex 文件，或使用 --list-rules 查看规则。", file=sys.stderr)
        return 1

    # 验证文件存在
    filepaths: list[Path] = []
    for f in args.files:
        p = Path(f)
        if not p.exists():
            print(f"错误: 文件不存在: {f}", file=sys.stderr)
            return 1
        filepaths.append(p)

    # ── 忽略管理命令 ────────────────────────────────

    if args.list_ignores:
        for fp in filepaths:
            ignores = cache_mod.list_ignores(fp)
            print(f"\n文件: {fp}")
            if not ignores:
                print("  无忽略项。")
            else:
                for item in ignores:
                    print(f"  [{item['rule_id']}] {item['description']}")
                    print(f"    指纹: {item['fingerprint']}")
        return 0

    if args.clear_ignores:
        for fp in filepaths:
            count = cache_mod.clear_ignores(fp)
            print(f"已清除 {fp} 的 {count} 个忽略项。")
        return 0

    if args.remove_ignore:
        for fp in filepaths:
            ok = cache_mod.remove_ignore(fp, args.remove_ignore)
            if ok:
                print(f"已移除忽略项: {args.remove_ignore}")
            else:
                print(f"未找到指纹为 {args.remove_ignore} 的忽略项。")
        return 0

    # ── 检查 + ignore 工作流 ────────────────────────

    checker = Checker(
        min_severity=SEVERITY_MAP[args.min_severity],
        exclude_rules=set(args.exclude),
        include_rules=set(args.include) if args.include else None,
        use_cache=not args.no_cache,
    )

    use_color = not args.no_color
    total_errors = 0

    # 如果指定了 --ignore，需要先执行一次检查拿到未过滤的问题列表，
    # 然后根据序号收集要忽略的 issue，再重新过滤展示。
    if args.ignore is not None:
        try:
            ignore_indices = [int(x.strip()) for x in args.ignore.split(",") if x.strip()]
        except ValueError:
            print("错误: --ignore 参数格式不正确，应为逗号分隔的数字，如 1,3", file=sys.stderr)
            return 1

        for fp in filepaths:
            result, from_cache = checker.check_file(fp)
            to_ignore = []
            for idx in ignore_indices:
                issue = result.get_issue_by_index(idx)
                if issue:
                    to_ignore.append(issue)
                else:
                    print(f"警告: 序号 #{idx} 超出范围，已跳过。", file=sys.stderr)
            if to_ignore:
                added = cache_mod.add_ignores(fp, to_ignore)
                print(f"已为 {fp} 新增 {added} 个忽略项。")
            # 重新检查以展示更新后的结果
            result, from_cache = checker.check_file(fp)
            cache_hint = " (来自缓存)" if from_cache else ""
            print(result.format_summary(color=use_color, show_index=True) + cache_hint)
            total_errors += result.error_count
    else:
        for fp in filepaths:
            result, from_cache = checker.check_file(fp)
            cache_hint = " (来自缓存)" if from_cache else ""
            print(result.format_summary(color=use_color, show_index=True) + cache_hint)
            total_errors += result.error_count

    return 1 if total_errors > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
