import os


class Config:
    APP_NAME = "Elves"
    APP_DATA = os.getenv("LOCALAPPDATA") + fr"\{APP_NAME}"
    USER_CONFIG_PATH = APP_DATA + r"\Config\User"
    SYS_CONFIG_PATH = APP_DATA + r"\Config\Sys"
    STORAGE_PATH = APP_DATA + r"\pywebview"
    THRESHOLD = 0.85
    BOX = (0, 0, 1335, 750)
    TIMEOUT = 1.8
    OVERTIME = 2
    SWITCH_CHARACTER_STATE = {}
    THRESHOLD_IMAGE = {
        "按钮世界挂机": 0.75,
        "标志寻路中": 0.7,
        "标志地图加载": 0.7,
        "标志地图加载_1": 0.7,
        "按钮地图世界区域": 0.8,
        "按钮任务帮派": 0.8,
        "按钮关闭": 0.7,
        "按钮关闭_1": 0.7,
        "按钮关闭_V1": 0.7,
        "按钮商城购买": 0.9,
        "按钮课业确定": 0.8,
        "按钮江湖急送菜品送达": 0.8,
        "按钮江湖急送菜品打包": 0.8,
        "标志本体位置": 0.8,
        "标志本体位置_V2": 0.8,
        "标志本体位置_V3": 0.8,
        "z`": 0.9,
        "按钮大世界对话": 0.8,
        "标志江湖英雄榜敌方": 0.9,
        "标志单人论剑我方": 0.9,
    }
