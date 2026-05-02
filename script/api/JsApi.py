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
        window.useCharacterStore.getState().popExecute({hwnd})
        """
        return self.window.evaluate_js(code)


js = JsApi()
