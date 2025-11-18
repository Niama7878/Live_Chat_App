# Live Chat App

一个通过 Selenium + PyQt6 实现的直播窗口嵌入式显示工具，可用于 Bilibili 或 YouTube 直播间的无边框置顶呈现。
支持自定义直播 URL、自动注入 Cookies（B站）、自定义构建与自动日志记录。

---

## ✨ 功能特点

* 📺 **直播嵌入展示**
  使用 Chrome 的 App 模式，将直播页面嵌入 PyQt6 无边框窗口中。

* 🚀 **支持 Bilibili 与 YouTube**
  可在启动界面选择直播平台，并读取/保存 URL 到 `config.json`。

* 🪟 **透明 + 置顶窗口**
  支持拖动、点击关闭，自带透明遮罩 UI。

* 🧩 **自动执行脚本优化直播页面**
  （隐藏导航栏、自动播放、滚动到指定位置等）

* 🔧 **自动生成日志**
  程序运行错误会写入 `log.txt` 方便排查。

---

## 📁 项目结构

```
Live_Chat_App/
│  .env
│  app.zip
│  config.json
│  icon.ico
│  live_chat.py
│  README.md
```

### `.env`

用于放置敏感环境变量，目前主要用于：

```
SESSDATA=你的B站Cookie
```

---

## 🛠️ 安装依赖

### 必需依赖

```bash
pip install setuptools pywin32 selenium-wire blinker==1.4 PyQt6 python-dotenv
```

### 构建依赖（如需打包）

```bash
pip install pyinstaller
```

---

## ▶️ 运行说明

### 1. 填写 `.env`

程序运行需从 `.env` 加载 Bilibili 的 SESSDATA。运行前必须先填写 `.env`。

👉 **`.env` 所在路径：**

```
dist/live_chat/.env # 应用构建版本
Live_Chat_App/.env # 本地运行
```
如果你不知道怎么获取 `SESSDATA`，可以参考下面的演示视频（看任意一个即可）：

* [YouTube 教程](https://youtu.be/_9R8eSuDoQI?t=31)
* [Bilibili 教程](https://www.bilibili.com/video/BV1ubLMz8EK3?t=31.0)

未填写 `.env` 会导致 BiliBili 无法加载用户状态。

---

### 2. 注意：请不要同时存在两个同名窗口

代码使用：

```python
self.chrome_hwnd = find_hwnd(self.driver.title)
```

Chrome 的窗口标题必须唯一，否则可能嵌入错误窗口，导致程序异常。

⚠ 示例冲突情况：

* Chrome 已经打开你的直播间
* 程序内的 Driver 也打开相同标题的直播间

→ 容易导致找不到正确的窗口句柄。

---

### 3. 运行程序

直接执行：

```bash
python live_chat.py
```

启动后会出现平台选择窗口，可选择 Bilibili / YouTube，并填写（或使用 config.json 保存的）直播 URL。

程序运行期间的所有错误会写入：

```
log.txt
```

---

## 🧱 构建说明（可生成可执行程序）

执行：

```bash
pyinstaller --noconsole --icon=icon.ico live_chat.py
```

构建完成后将生成：

```
build/
dist/
live_chat.spec
```

其中：

### `dist/live_chat/`

这是完整的可执行应用目录：

❗ **你必须手动把以下文件复制进去：**

```
config.json
.env
```

否则程序无法运行。

---

## ⚙️ config.json 示例

```json
{
    "bili_live_url": "",
    "yt_live_url": ""
}
```

程序支持在启动界面读取/保存 URL。

---

## 📌 已知行为 / 注意事项

* 若直播页面脚本失效（如 YouTube UI 变动），嵌入后可能不会自动隐藏导航栏，需要更新 JS。
* B站播放器依赖登录状态，必须提供有效 `SESSDATA`。
* 程序关闭后会自动关闭 Chrome driver。