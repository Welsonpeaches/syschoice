"""The nine scoring dimensions.

Order matters: the same order is used for candidate vectors, user vectors and
the radar chart axes on the result page.
"""

DIMENSIONS = [
    ("ease", "易用性", "开箱即用的程度，以及日常使用的学习成本"),
    ("stability", "稳定性", "长期可靠、不容易出问题的程度"),
    ("gaming", "游戏", "游戏兼容性、反作弊支持与性能表现"),
    ("creative", "创作与专业软件", "音视频、设计、3D 等专业创作软件的支持情况"),
    ("office", "办公与商业软件", "办公套件、行业软件、网银与政务软件的兼容性"),
    ("dev", "开发与自动化", "命令行、包管理、容器与开发工具链的适配度"),
    ("customization", "可定制与掌控", "按自己意愿改造系统的自由度"),
    ("privacy", "隐私与安全", "数据可控性、隐私保护与安全加固能力"),
    ("lightweight", "轻量与老硬件", "低配与老旧设备上的流畅程度"),
]

DIMENSION_IDS = [d[0] for d in DIMENSIONS]
DIMENSION_LABELS = {d[0]: d[1] for d in DIMENSIONS}
DIMENSION_DESCRIPTIONS = {d[0]: d[2] for d in DIMENSIONS}

# Compact names for chart axes, where the full label would clip.
DIMENSION_SHORT = {
    "ease": "易用",
    "stability": "稳定",
    "gaming": "游戏",
    "creative": "创作",
    "office": "办公",
    "dev": "开发",
    "customization": "可定制",
    "privacy": "隐私",
    "lightweight": "轻量",
}
