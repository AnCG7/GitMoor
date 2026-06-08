# VeilTK

一个基于 Python Tkinter 的现代化 UI 组件库，无需安装任何第三方依赖，即可拥有接近现代前端框架的交互体验和视觉风格。自行开发与封装，目前运用于此工具。

## 特性

- **零额外依赖** — 仅依赖 Python 标准库 Tkinter，无需 pip install 任何包
- **现代化交互** — 按钮悬停/按下/聚焦状态反馈、输入框聚焦高亮、列表项悬停选中、链接按钮等
- **Light / Dark 双主题** — 内置亮色与暗色主题，运行时一键切换，所有组件自动响应
- **国际化支持** — 内置 `LocalizationManager` + `LocalizedText`，通过 JSON 文件管理多语言文本，切换语言后组件自动刷新
- **事件驱动架构** — `Event` 广播/监听机制，组件间解耦通信
- **丰富的组件** — 涵盖常用 UI 元素，开箱即用

## 系统要求

- 测试环境：Python 3.12
- Tkinter（Python 标准库，通常随 Python 自带）

## 快速开始

直接运行示例即可查看所有组件效果：

```bash
python examples/demo.py
```

## 组件一览

| 组件 | 类名 | 说明 |
|------|------|------|
| 应用入口 | `App` | 单例主窗口，管理 Tk 根窗口生命周期 |
| 框架 | `Frame` | 容器组件，自动跟随主题色 |
| 标签 | `Label` | 支持 Normal / Warning / Error / Success 四种颜色类型，支持自适应换行 |
| 按钮 | `NormalButton` | Primary / Secondary 样式，Small / Normal / Large 尺寸，完整交互状态 |
| 输入框 | `Entry` | 支持禁用、只读、聚焦高亮 |
| 多行文本框 | `Text` | 支持 Normal / Readonly / Display / Disable / Label 多种模式，内置滚动条，可设换行模式 |
| 下拉框 | `Combobox` | 自定义弹出列表，悬停/选中/禁用状态 |
| 复选框 | `CheckButton` | 自绘指示器，支持选中/禁用组合状态 |
| 链接按钮 | `LinkButton` | 超链接风格，可绑定 URL |
| 滚动列表 | `ScrollListbox` | 带自定义滚动条的列表，支持项悬停/选中 |
| 进度条 | `Progress` | 水平/垂直方向，支持禁用状态 |
| 菜单导航 | `Menu` | 左侧/顶部导航，支持 Cache / Destroy 页面模式 |
| 提示框 | `Alert` | 确认对话框、普通提示框，超长内容自动滚动 |
| 加载动画 | `Loading` | Rect / Chase / Line 三种动画风格，支持定时自动关闭 |
| 浏览输入框 | `BrowseEntry` | 带浏览按钮的文件选择输入框 |
| 滚动条 | `Scrollbar` | 自定义绘制，跟随主题色 |

## 主题系统

主题颜色通过 JSON 配置文件定义，位于 `veiltk/assets/styles/` 目录：

- `light.json` — 亮色主题色值
- `dark.json` — 暗色主题色值
- `components.json` — 各组件在各状态下的颜色映射

运行时切换主题：

```python
vk.UIStyleManager.get_instance().set_theme('dark')   # 切换到暗色
vk.UIStyleManager.get_instance().set_theme('light')  # 切换到亮色
```

所有已创建的组件会自动响应主题变更，无需手动刷新。

## 国际化

通过 `LocalizedText` 包裹文本，组件会自动从 `localization/` 目录下的 JSON 文件加载对应语言：

```python
vk.Label(self, text=vk.LocalizedText("hello"))
```

切换语言后所有组件自动刷新：

```python
vk.LocalizationManager.get_instance().set_language('en')
```

## 事件系统

组件提供 `Event` 对象，通过 `add_listener` / `remove_listener` 注册和移除回调：

```python
btn = vk.NormalButton(self, text=vk.LocalizedText("点击"))
btn.on_click.add_listener(lambda: print("按钮被点击"))
```

## 项目结构

```
veil_tkinter/
├── examples/
│   └── demo.py              # 演示程序
├── veiltk/
│   ├── __init__.py           # 公开 API 导出
│   ├── assets/
│   │   └── images/theme/    # 主题图片资源
│   ├── src/
│   │   ├── core/
│   │   │   ├── application.py    # App 单例
│   │   │   ├── engine.py         # 引擎初始化
│   │   │   ├── view.py           # 视图基类
│   │   │   ├── window.py         # 窗口基类
│   │   │   ├── manager/
│   │   │   │   ├── event_manager.py         # 事件系统
│   │   │   │   ├── localization_manager.py   # 国际化管理
│   │   │   │   └── ui_style_manager.py       # 主题样式管理
│   │   │   └── utils/
│   │   │       ├── asset_loader.py
│   │   │       └── utils.py
│   │   └── components/      # 所有 UI 组件
│   └── assets/
│       ├── images/
│       └── styles/
│           ├── light.json        # 亮色主题
│           ├── dark.json         # 暗色主题
│           └── components.json   # 组件样式映射
└── README.md
```

