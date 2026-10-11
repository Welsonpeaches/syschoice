"""Six terminal-flavoured questions. Correct answers raise the tech_level trait."""

CLI_QUESTIONS = [
    {
        "id": "cli1",
        "prompt": "sudo apt update",
        "title": "这条命令在做什么？",
        "options": [
            {"id": "a", "label": "更新软件包索引，知道有哪些新版本可用"},
            {"id": "b", "label": "把系统内核升级到最新版"},
            {"id": "c", "label": "安装一个叫 update 的软件"},
        ],
        "answer": "a",
        "explain": "apt update 只刷新可安装软件包的清单，真正的升级是 apt upgrade。",
    },
    {
        "id": "cli2",
        "prompt": "在 Linux 上安装软件，通常怎么做？",
        "title": "选一个最接近的答案。",
        "options": [
            {"id": "a", "label": "下载 exe 双击安装"},
            {"id": "b", "label": "用包管理器或图形软件商店"},
            {"id": "c", "label": "所有软件都必须自己编译源码"},
        ],
        "answer": "b",
        "explain": "apt、dnf、pacman 等包管理器是主流方式，少数软件才需要编译。",
    },
    {
        "id": "cli3",
        "prompt": "cd ~",
        "title": "这条命令会做什么？",
        "options": [
            {"id": "a", "label": "切换到当前用户的主目录"},
            {"id": "b", "label": "关机"},
            {"id": "c", "label": "删除主目录里的所有文件"},
        ],
        "answer": "a",
        "explain": "~ 代表当前用户的主目录，cd 是切换目录。",
    },
    {
        "id": "cli4",
        "prompt": "df -h",
        "title": "这条命令用来查看什么？",
        "options": [
            {"id": "a", "label": "磁盘剩余空间"},
            {"id": "b", "label": "当前目录的文件列表"},
            {"id": "c", "label": "网络能不能通"},
        ],
        "answer": "a",
        "explain": "df 显示文件系统使用情况，-h 让它以 GB / MB 这种易读方式显示。",
    },
    {
        "id": "cli5",
        "prompt": "chmod +x run.sh",
        "title": "这条命令的作用是？",
        "options": [
            {"id": "a", "label": "给脚本加上可执行权限"},
            {"id": "b", "label": "删除这个脚本"},
            {"id": "c", "label": "把这个脚本复制一份"},
        ],
        "answer": "a",
        "explain": "chmod 修改权限，+x 表示增加执行权限，这样脚本才能直接运行。",
    },
    {
        "id": "cli6",
        "prompt": "在终端里按下 Ctrl+C",
        "title": "通常会发生什么？",
        "options": [
            {"id": "a", "label": "中断当前正在运行的命令"},
            {"id": "b", "label": "复制选中的文字"},
            {"id": "c", "label": "立刻重启电脑"},
        ],
        "answer": "a",
        "explain": "Ctrl+C 发送中断信号，用来中止卡住的命令；复制在终端里通常是 Ctrl+Shift+C。",
    },
]

CLI_QUESTIONS_MAP = {q["id"]: q for q in CLI_QUESTIONS}
