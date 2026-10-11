"""Software compatibility catalog.

compat levels per family:
  native  - official build, works out of the box
  good    - works well via Proton / ports / first-class community packaging
  partial - usable with workarounds, Wine, or a degraded port
  web     - no desktop build, but the web version covers most needs
  none    - effectively unavailable
"""

CATEGORIES = [
    ("office", "办公"),
    ("social", "社交与协作"),
    ("creative", "创意与设计"),
    ("video", "影音与剪辑"),
    ("industry", "专业行业软件"),
    ("gaming", "游戏"),
    ("dev", "开发工具"),
    ("finance", "金融与政务"),
    ("peripheral", "专业外设"),
]


def _s(sid, name, category, windows, macos, linux, bsd, note=""):
    return {
        "id": sid,
        "name": name,
        "category": category,
        "compat": {"windows": windows, "macos": macos, "linux": linux, "bsd": bsd},
        "note": note,
    }


SOFTWARE = [
    # ---------------------------------------------------------------- 办公
    _s("microsoft-office", "Microsoft Office 全套", "office",
       "native", "native", "none", "none",
       "Linux 与 BSD 上没有官方版本，只能靠 WPS、LibreOffice 或网页版"),
    _s("wps-office", "WPS Office", "office",
       "native", "native", "native", "partial", "Linux 有官方版本，功能完整"),
    _s("libreoffice", "LibreOffice", "office",
       "native", "native", "native", "native", ""),
    _s("notion", "Notion", "office",
       "web", "web", "web", "web", "桌面端为套壳应用，网页版体验一致"),
    _s("onenote", "OneNote", "office",
       "native", "native", "web", "web", "Linux 上只能使用网页版"),
    _s("tencent-docs", "腾讯文档 / 石墨文档", "office",
       "web", "web", "web", "web", ""),
    _s("foxit", "福昕 / Adobe Acrobat PDF", "office",
       "native", "native", "partial", "partial", "Linux 上有替代阅读器，但表单与批注功能受限"),

    # ------------------------------------------------------------ 社交与协作
    _s("wechat", "微信", "social",
       "native", "native", "native", "none", "Linux 已有官方版本，BSD 上只能靠网页版或 Wine"),
    _s("qq", "QQ", "social",
       "native", "native", "native", "none", ""),
    _s("dingtalk", "钉钉", "social",
       "native", "native", "native", "none", ""),
    _s("feishu", "飞书", "social",
       "native", "native", "native", "none", ""),
    _s("wecom", "企业微信", "social",
       "native", "native", "web", "web", ""),
    _s("tencent-meeting", "腾讯会议", "social",
       "native", "native", "partial", "none", "Linux 版本功能落后于 Windows 客户端"),
    _s("zoom", "Zoom", "social",
       "native", "native", "native", "partial", ""),

    # ------------------------------------------------------------ 创意与设计
    _s("photoshop", "Adobe Photoshop", "creative",
       "native", "native", "none", "none", "Linux / BSD 上需用 GIMP、Krita 或 Photopea 网页版替代"),
    _s("illustrator", "Adobe Illustrator", "creative",
       "native", "native", "none", "none", "替代品为 Inkscape"),
    _s("lightroom", "Adobe Lightroom", "creative",
       "native", "native", "none", "none", "替代品为 darktable、RawTherapee"),
    _s("figma", "Figma", "creative",
       "web", "web", "web", "web", "网页优先，桌面端为套壳"),
    _s("sketch", "Sketch", "creative",
       "none", "native", "none", "none", "macOS 独占"),
    _s("krita", "Krita / GIMP / Inkscape", "creative",
       "native", "native", "native", "partial", ""),
    _s("cad-autocad", "AutoCAD", "creative",
       "native", "partial", "none", "none", "macOS 版本功能弱于 Windows，Linux / BSD 无官方版本"),

    # ------------------------------------------------------------ 影音与剪辑
    _s("premiere", "Adobe Premiere Pro", "video",
       "native", "native", "none", "none", "替代品为 DaVinci Resolve、Kdenlive"),
    _s("after-effects", "Adobe After Effects", "video",
       "native", "native", "none", "none", ""),
    _s("final-cut", "Final Cut Pro", "video",
       "none", "native", "none", "none", "macOS 独占"),
    _s("davinci-resolve", "DaVinci Resolve", "video",
       "native", "native", "native", "partial", "Linux 版本免费且功能完整"),
    _s("capcut", "剪映专业版", "video",
       "native", "native", "none", "none", ""),
    _s("obs", "OBS Studio", "video",
       "native", "native", "native", "partial", ""),
    _s("blender", "Blender", "video",
       "native", "native", "native", "partial", ""),

    # -------------------------------------------------------- 专业行业软件
    _s("solidworks", "SolidWorks", "industry",
       "native", "none", "none", "none", "Windows 独占，工程行业刚需"),
    _s("3ds-max", "3ds Max", "industry",
       "native", "none", "none", "none", "Windows 独占"),
    _s("cinema4d", "Cinema 4D", "industry",
       "native", "native", "none", "none", ""),
    _s("industrial-cae", "Solid Edge / NX / CATIA", "industry",
       "native", "none", "partial", "none", "部分工业软件只在 Linux 上提供服务器版本"),
    _s("matlab", "MATLAB", "industry",
       "native", "native", "native", "none", "Linux 有官方版本，BSD 无支持"),
    _s("eda", "EDA 与电路仿真", "industry",
       "native", "partial", "native", "partial", "多数 EDA 工具原生支持 Linux"),

    # ------------------------------------------------------------- 游戏
    _s("steam", "Steam 本体", "gaming",
       "native", "native", "good", "partial", "Linux 有原生客户端，BSD 依赖 Linux 兼容层"),
    _s("aaa-games", "单机 3A 大作", "gaming",
       "native", "partial", "good", "none", "Linux 靠 Proton 兼容，多数可玩但需调优"),
    _s("anticheat-games", "竞技网游（反作弊）", "gaming",
       "native", "partial", "none", "none", "LOL、瓦罗兰特、永劫无间等反作弊不支持 Linux"),
    _s("minecraft", "Minecraft", "gaming",
       "native", "native", "native", "partial", ""),
    _s("emulator", "手游模拟器", "gaming",
       "native", "partial", "partial", "none", "Linux 上可用的模拟器较少且性能一般"),

    # ------------------------------------------------------------- 开发
    _s("vscode", "VS Code", "dev",
       "native", "native", "native", "partial", ""),
    _s("jetbrains", "JetBrains IDE", "dev",
       "native", "native", "native", "partial", "BSD 上需自行编译或走 Linux 兼容层"),
    _s("docker", "Docker / Podman", "dev",
       "native", "native", "native", "partial", "BSD 上用 Jail 或 Linux 虚拟机替代"),
    _s("git", "Git", "dev",
       "native", "native", "native", "native", ""),
    _s("visual-studio", "Visual Studio（非 VS Code）", "dev",
       "native", "none", "none", "none", "Windows 独占，macOS 版本已停止支持"),
    _s("xcode", "Xcode / iOS 开发", "dev",
       "none", "native", "none", "none", "只能在 macOS 上开发 iOS 应用"),
    _s("wsl", "WSL 与 .NET 开发", "dev",
       "native", "partial", "none", "none", "只能在 Windows 上使用 WSL"),

    # --------------------------------------------------------- 金融与政务
    _s("bank-usbkey", "网银 U 盾", "finance",
       "native", "partial", "none", "none", "国内网银 U 盾几乎只有 Windows 驱动"),
    _s("gov-app", "个税 / 社保 / 政务客户端", "finance",
       "native", "partial", "none", "none", "多数只提供 Windows 客户端"),
    _s("alipay-web", "支付宝 / 12306 / 政务服务", "finance",
       "web", "web", "web", "web", "网页版可完成绝大部分操作"),
    _s("tax-software", "增值税开票 / 财务软件", "finance",
       "native", "none", "none", "none", "财务与开票软件基本是 Windows 专用"),

    # ------------------------------------------------------------ 专业外设
    _s("printer-driver", "打印机厂商驱动", "peripheral",
       "native", "native", "partial", "partial", "Linux 上部分型号缺乏官方驱动，需依赖通用驱动"),
    _s("drawing-tablet", "数位板 / 手绘屏驱动", "peripheral",
       "native", "native", "partial", "none", "Wacom 有 Linux 驱动，其他品牌支持参差"),
    _s("logitech-hub", "罗技 G HUB 等外设软件", "peripheral",
       "native", "native", "none", "none", "Linux 上只能用第三方工具改键"),
    _s("common-input", "普通键鼠与显示器", "peripheral",
       "native", "native", "native", "native", ""),
]

SOFTWARE_MAP = {s["id"]: s for s in SOFTWARE}

# Software whose availability effectively binds the user to a desktop ecosystem.
ECOSYSTEM_CRITICAL = {
    "microsoft-office", "bank-usbkey", "gov-app", "tax-software",
    "solidworks", "3ds-max", "visual-studio", "wsl",
    "photoshop", "illustrator", "premiere", "after-effects", "lightroom",
    "anticheat-games", "final-cut", "sketch", "xcode",
}
