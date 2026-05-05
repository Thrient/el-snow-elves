import json
import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

from script.config.Setting import APP_DATA

LOG_DIR = os.path.join(APP_DATA, "logs")
LOG_FILE = os.path.join(LOG_DIR, "app.log")
MAX_BYTES = 1 * 1024 * 1024  # 1MB
BACKUP_COUNT = 4  # app.log + app.log.1 ~ app.log.4 = 5 个文件

_log_total_cache = {"path": "", "size": 0, "total": 0}


class JsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }, ensure_ascii=False)


def setup_logging():
    Path(LOG_DIR).mkdir(parents=True, exist_ok=True)

    handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.addHandler(handler)


def _get_total_lines(filepath):
    global _log_total_cache
    try:
        current_size = os.path.getsize(filepath)
    except OSError:
        return 0

    if filepath == _log_total_cache["path"] and current_size == _log_total_cache["size"]:
        return _log_total_cache["total"]

    if filepath != _log_total_cache["path"] or current_size < _log_total_cache["size"]:
        _log_total_cache = {"path": filepath, "size": 0, "total": 0}

    prev_size = _log_total_cache["size"]
    with open(filepath, "rb") as f:
        f.seek(prev_size)
        new_bytes = f.read()
        new_lines = new_bytes.count(b"\n") if new_bytes else 0

    _log_total_cache["size"] = current_size
    _log_total_cache["total"] += new_lines
    return _log_total_cache["total"]


def _parse_entries(lines):
    entries = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries


def read_logs(page=1, page_size=50, level=None, search=None):
    if not os.path.isfile(LOG_FILE):
        return {"logs": [], "total": 0, "page": page, "page_size": page_size}

    file_size = os.path.getsize(LOG_FILE)
    if file_size == 0:
        return {"logs": [], "total": 0, "page": page, "page_size": page_size}

    if level or search:
        return _read_scan(LOG_FILE, page, page_size, level, search)

    total = _get_total_lines(LOG_FILE)
    skip = (page - 1) * page_size
    need = skip + page_size

    lines = _read_tail_lines(LOG_FILE, need)
    entries = _parse_entries(lines[skip:skip + page_size])

    return {
        "logs": entries,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


def _read_scan(filepath, page, page_size, level, search):
    """全量扫描，支持等级筛选和关键词搜索。"""
    all_entries = []
    search_lower = search.lower() if search else None

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if level and entry.get("level", "").upper() != level.upper():
                    continue
                if search_lower and search_lower not in entry.get("message", "").lower():
                    continue
                all_entries.append(entry)
            except json.JSONDecodeError:
                continue

    all_entries.reverse()
    total = len(all_entries)
    start = (page - 1) * page_size
    end = start + page_size

    return {
        "logs": all_entries[start:end],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


def _read_tail_lines(filepath, n):
    """从文件末尾读取最后 n 行，返回列表（最新在前）。"""
    with open(filepath, "rb") as f:
        f.seek(0, 2)
        file_size = f.tell()
        if file_size == 0:
            return []

        lines = []
        chunk = b""
        pos = file_size

        while pos > 0 and len(lines) < n:
            read_size = min(8192, pos)
            pos -= read_size
            f.seek(pos)
            chunk = f.read(read_size) + chunk
            parts = chunk.split(b"\n")
            chunk = parts[0]
            for raw in reversed(parts[1:]):
                decoded = raw.decode("utf-8", errors="replace").strip()
                if not decoded:
                    continue
                lines.append(decoded)
                if len(lines) >= n:
                    break

        if chunk and len(lines) < n:
            decoded = chunk.decode("utf-8", errors="replace").strip()
            if decoded:
                lines.append(decoded)

        return lines


def get_log_files():
    """返回日志文件列表"""
    if not os.path.isdir(LOG_DIR):
        return []
    files = []
    for f in os.listdir(LOG_DIR):
        if f.endswith(".log"):
            fp = os.path.join(LOG_DIR, f)
            files.append({
                "name": f,
                "size": os.path.getsize(fp),
                "mtime": os.path.getmtime(fp),
            })
    files.sort(key=lambda x: x["mtime"], reverse=True)
    return files
