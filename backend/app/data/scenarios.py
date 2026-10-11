"""Six scenario decisions, mapping to tinkering, stability and control traits."""

SCENARIO_QUESTIONS = [
    {
        "id": "S1",
        "title": "系统更新之后，Wi-Fi 突然连不上了",
        "context": "面对这种典型的驱动问题，你会怎么处理？",
        "type": "single",
        "options": [
            {
                "id": "rollback",
                "label": "等官方修复，或者先回滚到上一个版本",
                "traits": {"stability_pref": 0.7},
                "w": {"stability": 0.8, "ease": 0.4},
                "d": {"stability": 92},
            },
            {
                "id": "search",
                "label": "上网搜驱动，自己编译安装试试",
                "traits": {"tech_level": 0.45, "tinker": 0.55},
                "w": {"customization": 0.4, "dev": 0.3},
                "d": {"customization": 70},
            },
            {
                "id": "reinstall",
                "label": "重装一遍系统，反正也快",
                "traits": {"tinker": 0.3, "stability_pref": 0.4},
                "w": {"ease": 0.4, "stability": 0.4},
                "d": {"ease": 78},
            },
        ],
    },
    {
        "id": "S2",
        "title": "关于系统界面的外观，你更接近哪一种？",
        "type": "single",
        "options": [
            {
                "id": "fixed",
                "label": "默认好看就行，我不想花时间调",
                "traits": {"tinker": 0.25},
                "w": {"ease": 0.5},
                "d": {"ease": 85},
            },
            {
                "id": "theme",
                "label": "我喜欢换主题、改布局，越自由越好",
                "traits": {"tinker": 0.6, "customization_need": 0.6},
                "w": {"customization": 0.7},
                "d": {"customization": 80},
            },
            {
                "id": "any",
                "label": "无所谓，能用就行",
                "traits": {},
                "w": {},
                "d": {},
            },
        ],
    },
    {
        "id": "S3",
        "title": "想开启某个功能，但教程说必须敲一行命令",
        "type": "single",
        "options": [
            {
                "id": "follow",
                "label": "照着教程敲一遍，问题不大",
                "traits": {"tech_level": 0.6, "tinker": 0.5},
                "w": {"dev": 0.4, "customization": 0.4},
                "d": {"dev": 75, "customization": 70},
            },
            {
                "id": "giveup",
                "label": "太麻烦了，算了不用了",
                "traits": {"tech_level": 0.3},
                "w": {"ease": 1.0},
                "d": {"ease": 92},
            },
            {
                "id": "curious",
                "label": "很感兴趣，还想顺便搞清楚原理",
                "traits": {"tech_level": 0.75, "tinker": 0.8},
                "w": {"dev": 0.6, "customization": 0.7},
                "d": {"dev": 85, "customization": 85},
            },
        ],
    },
    {
        "id": "S4",
        "title": "系统突然开不了机，你希望怎么解决？",
        "type": "single",
        "options": [
            {
                "id": "gui",
                "label": "有个图形界面能一键修复",
                "traits": {"support_need": 0.6, "stability_pref": 0.6},
                "w": {"ease": 0.8, "stability": 0.6},
                "d": {"ease": 88, "stability": 88},
            },
            {
                "id": "logs",
                "label": "让我进恢复模式看日志，自己排查",
                "traits": {"tech_level": 0.75, "tinker": 0.75},
                "w": {"dev": 0.5, "customization": 0.5},
                "d": {"dev": 82, "customization": 78},
            },
            {
                "id": "reinstall",
                "label": "直接重装，资料我有备份",
                "traits": {"tinker": 0.35},
                "w": {"ease": 0.4},
                "d": {"ease": 75},
            },
        ],
    },
    {
        "id": "S5",
        "title": "在这台电脑上，你更在意哪一点？",
        "type": "single",
        "options": [
            {
                "id": "nothing",
                "label": "最好什么都不用我操心",
                "traits": {"tinker": 0.15, "stability_pref": 0.6},
                "w": {"ease": 1.0},
                "d": {"ease": 95},
            },
            {
                "id": "everything",
                "label": "每个细节我都要能改",
                "traits": {"tinker": 0.85, "customization_need": 0.9},
                "w": {"customization": 1.0},
                "d": {"customization": 95},
            },
            {
                "id": "stable",
                "label": "稳定压倒一切，别出幺蛾子",
                "traits": {"stability_pref": 0.85},
                "w": {"stability": 1.0},
                "d": {"stability": 95},
            },
        ],
    },
    {
        "id": "S6",
        "title": "朋友让你推荐一个系统，你会怎么说？",
        "type": "single",
        "options": [
            {
                "id": "direct",
                "label": "直接给一个结论，别让他纠结",
                "traits": {"tinker": 0.35},
                "w": {"ease": 0.4},
                "d": {"ease": 80},
            },
            {
                "id": "tradeoffs",
                "label": "把利弊讲清楚，让他自己选",
                "traits": {"tech_level": 0.6, "tinker": 0.5},
                "w": {"dev": 0.3, "customization": 0.3},
                "d": {"dev": 70},
            },
        ],
    },
]

SCENARIO_MAP = {q["id"]: q for q in SCENARIO_QUESTIONS}
