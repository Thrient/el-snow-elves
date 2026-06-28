"""Hub API 客户端 — 任务版本查询 + 下载"""
import base64
import httpx

HUB_URL = "https://elves.elarion.cn"


class HubSync:
    """同步 HTTP 客户端，在后台线程中使用。"""

    def __init__(self):
        self.client = httpx.Client(timeout=10.0, verify=True)

    def lookup(self, author: str, title: str) -> dict | None:
        """按作者名+任务名精确查询 Hub 上的任务。返回 {id, title, version, author_name} 或 None。"""
        try:
            r = self.client.get(
                f"{HUB_URL}/api/v1/tasks/lookup",
                params={"author": author, "title": title},
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
        """对比本地任务与 Hub 版本。返回可更新列表 [{name, author, localVersion, hubVersion}]。"""
        updates = []
        for task in local_tasks:
            author = task.get("author", "")
            if not author or author == "匿名作者":
                continue
            name = task.get("name", "")
            local_version = task.get("latest", "")
            info = self.lookup(author, name)
            if info and info.get("version") and info["version"] != local_version:
                updates.append({
                    "name": name,
                    "author": author,
                    "localVersion": local_version,
                    "hubVersion": info["version"],
                })
        return updates

    def download_and_import(self, author: str, title: str) -> dict:
        """查找 → 下载 → 导入。返回 import_task 的结果。"""
        # 1. 查找
        info = self.lookup(author, title)
        if not info:
            return {"error": f"Hub 上未找到任务: {title} @{author}"}

        # 2. 下载
        try:
            r = self.client.get(
                f"{HUB_URL}/api/v1/tasks/{info['id']}/download",
            )
            if r.status_code != 200:
                return {"error": f"下载失败 (HTTP {r.status_code})"}
            zip_bytes = r.content
        except Exception as e:
            return {"error": f"下载失败: {e}"}

        # 3. 导入（复用现有管线）
        # filename 格式: name_version_author.zip — _import_single 会从中解析 author
        zip_b64 = base64.b64encode(zip_bytes).decode("utf-8")
        from script.task import get_repo
        repo = get_repo()
        result = repo.import_task({
            "base64": zip_b64,
            "filename": f"{title}_{info['version']}_{author}.zip",
        })
        return result
