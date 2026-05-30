class JsApi:
    def __init__(self):
        self.window = None

    def init(self, window):
        """初始化"""
        self.window = window

    def update_character(self, data):
        code = f"""
        window.useCharacterStore.getState().update({data})
        """
        self.window.run_js(code)

    def get_execute_task(self, hwnd):
        code = f"""
        (function() {{
            const result = window.useCharacterStore.getState().popExecute({hwnd});
            return result ? JSON.stringify(result) : null;
        }})()
        """
        import json
        raw = self.window.evaluate_js(code)
        if raw is None:
            return None
        if isinstance(raw, dict):
            return raw
        return json.loads(raw)

    # ── 更新进度推送 ──

    def update_start_download(self, total_files: int, total_bytes: int):
        self.window.evaluate_js(f"window.useUpdateStore.getState().startDownload({total_files},{total_bytes})")

    def update_progress(self, path: str, completed_files: int, downloaded_bytes: int):
        escaped = path.replace("\\", "\\\\").replace("'", "\\'")
        self.window.evaluate_js(
            f"window.useUpdateStore.getState().updateProgress('{escaped}',{completed_files},{downloaded_bytes})")

    def update_finish_download(self):
        self.window.evaluate_js("window.useUpdateStore.getState().finishDownload()")


js = JsApi()
