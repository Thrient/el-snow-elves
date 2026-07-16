"""Hub API 客户端 — 任务版本查询 + 下载"""
import base64
import httpx

HUB_URL = "https://elves.elarion.cn"


class HubSync:
    """同步 HTTP 客户端，在后台线程中使用。"""

    def __init__(self):
        self.client = httpx.Client(timeout=10.0, verify=True)

    def lookup(self, task_id: int, title: str = "") -> dict | None:
        """按 task_id 查询 Hub 上的任务。返回 {id, title, version, author_name} 或 None。"""
        try:
            params = {"task_id": task_id}
            if title:
                params["title"] = title
            r = self.client.get(
                f"{HUB_URL}/api/v1/tasks/lookup",
                params=params,
            )
            if r.status_code != 200:
                return None
            data = r.json()
            if data.get("code") != 0:
                return None
            tasks = data.get("data", {}).get("tasks", [])
            return tasks[0] if tasks else None
        except Exception:
            return None

    def check_updates(self, local_tasks: list[dict]) -> list[dict]:
        """对比本地任务与 Hub 版本。返回可更新列表 [{name, hubTaskId, localVersion, hubVersion}]。"""
        updates = []
        for task in local_tasks:
            task_id = task.get("hub_task_id")
            if not task_id:
                continue
            name = task.get("name", "")
            local_version = task.get("latest", "")
            info = self.lookup(task_id, title=name)
            if info and info.get("version") and info["version"] != local_version:
                updates.append({
                    "name": name,
                    "hubTaskId": task_id,
                    "localVersion": local_version,
                    "hubVersion": info["version"],
                })
        return updates

    def download_and_import(self, task_id: int, title: str) -> dict:
        """下载 → 导入。从 Content-Disposition 提取文件名（含 author）。
        task_id 通过 dict 字段传入 import_task。"""
        try:
            r = self.client.get(
                f"{HUB_URL}/api/v1/tasks/{task_id}/download",
            )
            if r.status_code != 200:
                return {"error": f"下载失败 (HTTP {r.status_code})"}
            zip_bytes = r.content
        except Exception as e:
            return {"error": f"下载失败: {e}"}

        # 从 Content-Disposition 提取文件名（格式: {title}_{version}_{author}_{task_id}.zip）
        filename = f"{title}.zip"
        cd = r.headers.get("Content-Disposition", "")
        if cd:
            import re as _re
            m = _re.search(r"filename\*?=(?:UTF-8''|['\"])([^'\";]+)", cd)
            if m:
                from urllib.parse import unquote
                filename = unquote(m.group(1))

        zip_b64 = base64.b64encode(zip_bytes).decode("utf-8")
        from script.task import get_repo
        repo = get_repo()
        result = repo.import_task({
            "base64": zip_b64,
            "filename": filename,
            "hub_task_id": task_id,
        })
        return result
