# Elves (时雪)

基于图像识别的桌面自动化工具。使用 PyWebView + WebView2 构建图形界面，OpenCV 进行模板匹配，通过工作流引擎驱动自动化操作。

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | React + TypeScript + Vite + UnoCSS |
| 后端 | Python + PyWebView + WebView2 |
| 视觉 | OpenCV (模板匹配 / 屏幕截图) |
| 输入 | Win32 API (键鼠模拟) |
| 编译 | Nuitka (Python → pyd) + PyInstaller (打包) |

## 项目结构

```
├── Elves.py                  # 应用入口
├── Elves.spec                # PyInstaller 打包配置
├── resources/                # 静态资源
│   ├── config/               # 工作流 JSON 配置
│   │   ├── common.json       # 公共步骤定义
│   │   └── 课业任务/         # 任务配置
│   └── images/               # 模板图像
├── script/                   # 后端核心
│   ├── api/                  # 前后端 API 桥接
│   │   ├── Api.py            # 事件注册与分发
│   │   └── JsApi.py          # JS API 封装
│   ├── config/               # 全局配置
│   │   └── Setting.py        # 常量与参数
│   ├── core/                 # 核心引擎
│   │   ├── App.py            # 应用窗口与生命周期
│   │   ├── FlowEngine.py     # 工作流执行引擎
│   │   ├── Script.py         # 脚本调度
│   │   ├── ScreenCapture.py  # 屏幕截图
│   │   ├── TemplateMatcher.py# 模板匹配
│   │   ├── InputSimulator.py # 键鼠输入模拟
│   │   ├── MonitorEngine.py  # 状态监控
│   │   ├── VariableProcessor.py # 变量处理与表达式求值
│   │   └── Window.py         # 窗口管理
│   ├── functools/            # 函数工具
│   ├── task/                 # 任务基类
│   └── util/                 # 通用工具 (Win32)
├── dist/                     # 构建输出
├── build/                    # 构建缓存
└── script.pyd                # Nuitka 编译产物 (构建时生成)
```

## 前端项目

前端为独立项目，位于 `../el-snow-elves-react/`，基于 React + TypeScript + Vite 构建。

## 构建

### 手动分步执行

**1. 编译 Python 核心模块 (script → script.pyd)**

```bash
python -m nuitka --python-flag=no_warnings,-O,no_docstrings --remove-output --module script --include-package=script
```

**2. 重命名产物**

```bash
ren script.cp313-win_amd64.pyd script.pyd
```

**3. PyInstaller 打包**

```bash
pyinstaller Elves.spec --distpath dist --workpath build --noconfirm --clean
```

**4. 清理临时文件**

```bash
Remove-Item script.pyd -Force
Remove-Item script.pyi -Force
```

**5. 复制前端产物**

```bash
robocopy "D:\Code\el-snow-elves-react\dist" "dist\Elves\_internal\dist" /E
```

**6. 复制 resources**

```bash
robocopy "resources" "dist\Elves\_internal\resources" /E
```

**7. 清理旧压缩包**

```bash
Remove-Item 'dist\Elves.zip'  -Force
```

## 开发

安装依赖：

```bash
pip install -r requirements.txt
```

启动应用：

```bash
python Elves.py
```

调试模式（开启 WebView DevTools）：

```bash
python Elves.py --debug True
```

## 版本

v6.0.3
