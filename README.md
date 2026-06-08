# GitMoor — 本地 Git 仓库配对工具

轻量级 Git 桌面工具，裸仓库（bare）与工作仓库（work）配对。支持本地磁盘、局域网共享目录，轻松搭建本地 Git 远程仓库。


## 功能特性

- **一键创建仓库**：支持同时创建裸仓库（bare）和工作仓库（work）。路径支持本地磁盘、局域网共享目录（UNC）、甚至 IP 地址访问，轻松在本地网络搭建 Git 远程仓库。创建后用你喜欢的 Git 工具打开工作仓库（work）进行提交，裸仓库（bare）已经配置为本地网络中的远程仓库
- **中英双语界面**：运行时一键切换，全部 UI 文本实时刷新
- **亮色/暗色主题**：内置 Light / Dark 双主题，界面风格一键切换
- **现代化 UI 交互**：按钮悬停态、输入框聚焦高亮、列表项悬停效果等，交互体验丝滑

## 环境要求

| 依赖 | 版本要求 | 说明 |
|------|----------|------|
| Python | 3.8+ | 测试环境 Python 3.12 |
| Git | 2.0+ | 测试环境 Git 2.51 |
| Git LFS | 2.10+（可选） | 测试环境 Git LFS 3.7 |

> **不需要安装任何第三方 Python 包** — GUI 框架基于 Tkinter（Python 标准库），UI 组件库 [VeilTK](#关于-veiltk) 也是零外部依赖。

## 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/yourusername/GitMoor.git
cd GitMoor

# 2. 直接运行
python main.py
```

无需额外安装依赖，直接运行即可启动应用。

## 打包为 EXE（Windows）

使用 `build_tool_windows.py` 一键打包为 Windows 可执行程序：

```bash
python external_tools/build_tools/build_tool_windows.py
```

脚本会自动完成依赖检查 → 图标合成 → PyInstaller 打包 → 资源复制全流程，产物输出到 `external_tools/build_tools/dist/GitMoor/`，`GitMoor`文件夹即可分发。

## 项目目录说明

```
GitMoor/
├── main.py                        # 应用入口
├── app_setting.json               # 默认配置（只读，打包进程序内部）
├── assets/                        # 运行时资源（打包后用户可直接修改）
├── src/                           # 应用源码
├── veil_tkinter/                  # VeilTK — 自研 UI 组件库（详见下方说明）
├── external_tools/                # 外部工具
├── dev/                           # 开发期资源（不参与打包分发）
└── saved/                         # 用户运行时保存的数据，运行时自动创建
```

## FAQ

### 如何在局域网中使用 GitMoor？

将裸仓库路径填写为局域网共享目录的 UNC 路径即可（需先在目标电脑上共享文件夹），内部自动转为 `file://` 协议。

### UNC 路径怎么写？

格式：`\\<主机名或IP>\<共享名>\<子路径>`，如 `\\MyPC\share\repos` 或 `\\192.168.1.50\share\repos`。

## 参考

### Git 规则文件

- [GitHub gitignore templates](https://github.com/github/gitignore)
- [GitHub gitattributes templates](https://github.com/gitattributes/gitattributes)
