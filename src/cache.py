"""缓存管理：文件哈希、JSON 存储、ignore 管理。"""

import hashlib
import json
from pathlib import Path
from src.models import Issue, CheckResult


CACHE_DIR_NAME = ".format_cache"


def _cache_dir(tex_path: Path) -> Path:
    """缓存目录位于 tex 文件所在目录下的 .format_cache/。"""
    return tex_path.resolve().parent / CACHE_DIR_NAME


def _cache_file(tex_path: Path) -> Path:
    return _cache_dir(tex_path) / (tex_path.name + ".json")


def compute_file_hash(filepath: Path) -> str:
    data = filepath.read_bytes()
    return hashlib.sha256(data).hexdigest()


def _read_cache(tex_path: Path) -> dict | None:
    cf = _cache_file(tex_path)
    if not cf.exists():
        return None
    with cf.open("r", encoding="utf-8") as f:
        return json.load(f)


def _write_cache(tex_path: Path, data: dict) -> None:
    d = _cache_dir(tex_path)
    d.mkdir(parents=True, exist_ok=True)
    cf = _cache_file(tex_path)
    with cf.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ── 缓存读写 ───────────────────────────────────────────────

def load_cached_result(tex_path: Path) -> tuple[CheckResult | None, str]:
    """
    尝试从缓存加载检查结果。

    Returns:
        (result_or_None, current_file_hash)
        如果缓存命中（哈希一致），返回 (CheckResult, hash)；
        否则返回 (None, hash)。
    """
    current_hash = compute_file_hash(tex_path)
    cache = _read_cache(tex_path)
    if cache is None or cache.get("file_hash") != current_hash:
        return None, current_hash

    # 从缓存重建 CheckResult（包含全量 issues）
    issues = [Issue.from_dict(d) for d in cache.get("issues", [])]
    result = CheckResult(filepath=str(tex_path), issues=issues)
    return result, current_hash


def save_cached_result(tex_path: Path, result: CheckResult, file_hash: str) -> None:
    """
    将全量检查结果写入缓存。

    注意：存储的是完整结果，不受 min_severity / exclude 等筛选影响。
    """
    cache = _read_cache(tex_path) or {}
    cache["file_hash"] = file_hash
    cache["issues"] = [issue.to_dict() for issue in result.issues]
    # 保留已有的 ignores
    if "ignores" not in cache:
        cache["ignores"] = []
    _write_cache(tex_path, cache)


# ── Ignore 管理 ─────────────────────────────────────────────

def load_ignores(tex_path: Path) -> set[str]:
    """加载该文件的忽略指纹集合。"""
    cache = _read_cache(tex_path)
    if cache is None:
        return set()
    return {item["fingerprint"] for item in cache.get("ignores", [])}


def add_ignores(tex_path: Path, issues: list[Issue]) -> int:
    """
    将指定 issues 添加到忽略列表。

    Returns:
        实际新增的忽略数量。
    """
    cache = _read_cache(tex_path) or {"file_hash": "", "issues": [], "ignores": []}
    existing = {item["fingerprint"] for item in cache["ignores"]}
    added = 0
    for issue in issues:
        fp = issue.fingerprint()
        if fp not in existing:
            cache["ignores"].append({
                "fingerprint": fp,
                "rule_id": issue.rule_id,
                "description": issue.message,
            })
            existing.add(fp)
            added += 1
    _write_cache(tex_path, cache)
    return added


def list_ignores(tex_path: Path) -> list[dict]:
    """列出该文件所有的忽略项。"""
    cache = _read_cache(tex_path)
    if cache is None:
        return []
    return cache.get("ignores", [])


def clear_ignores(tex_path: Path) -> int:
    """清除该文件所有的忽略项，返回清除数量。"""
    cache = _read_cache(tex_path)
    if cache is None:
        return 0
    count = len(cache.get("ignores", []))
    cache["ignores"] = []
    _write_cache(tex_path, cache)
    return count


def remove_ignore(tex_path: Path, fingerprint: str) -> bool:
    """移除单个忽略项。"""
    cache = _read_cache(tex_path)
    if cache is None:
        return False
    before = len(cache.get("ignores", []))
    cache["ignores"] = [
        item for item in cache.get("ignores", [])
        if item["fingerprint"] != fingerprint
    ]
    _write_cache(tex_path, cache)
    return len(cache["ignores"]) < before
