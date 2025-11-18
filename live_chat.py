import sys
import os
import json
from dotenv import load_dotenv
from PyQt6 import QtCore, QtWidgets, QtGui
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
import win32gui
from datetime import datetime

load_dotenv()
SESSDATA = os.getenv("SESSDATA", "")
CONFIG_FILE = "config.json"

with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

LOG_FILE = "log.txt"
_original_print = print

def print(*args, **kwargs):
    try:
        message = " ".join(str(a) for a in args)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        log_line = f"{timestamp}  {message}"

        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_line + "\n")

        _original_print(*args, **kwargs)
    except Exception as e:
        _original_print(f"print error: {e}")

def find_hwnd(title_substring: str):
    try:
        result = None
        title_substring = title_substring.lower()

        def enum_handler(hwnd, _):
            nonlocal result
            try:
                if not win32gui.IsWindowVisible(hwnd):
                    return
                t = win32gui.GetWindowText(hwnd) or ""
                if title_substring in t.lower():
                    result = hwnd
            except:
                pass

        win32gui.EnumWindows(enum_handler, None)
    except Exception as e:
        print(f"find hwnd error: {e}")
    return result

class StartDialog(QtWidgets.QDialog):
    def __init__(self, config, config_file, parent=None):
        try:
            super().__init__(parent)
            self.config = config
            self.config_file = config_file
            self.platform = ""
            self.url = ""

            self.setWindowFlags(
                QtCore.Qt.WindowType.FramelessWindowHint |
                QtCore.Qt.WindowType.Dialog
            )
            self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)

            outer = QtWidgets.QVBoxLayout(self)
            outer.setContentsMargins(0, 0, 0, 0)

            frame = QtWidgets.QFrame()
            frame.setObjectName("mainFrame")
            outer.addWidget(frame)

            self.setStyleSheet("""
                #mainFrame {
                    background-color: rgba(25, 25, 35, 230);
                    border-radius: 16px;
                }
                QLabel {
                    color: #ffffff;
                    font-size: 14px;
                }
                QRadioButton {
                    color: #ffffff;
                    font-size: 13px;
                }
                QLineEdit {
                    background-color: #1e1e1e;
                    border: 1px solid #555555;
                    border-radius: 8px;
                    padding: 6px 10px;
                    color: #ffffff;
                 }
                QCheckBox {
                    color: #dddddd;
                    font-size: 12px;
                }
                QPushButton {
                    background-color: #3daee9;
                    color: #ffffff;
                    border-radius: 10px;
                    padding: 6px 18px;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #5dc6ff;
                }
                QPushButton#cancelButton {
                    background-color: #444444;
                }
                QPushButton#cancelButton:hover {
                    background-color: #666666;
                }
            """)

            layout = QtWidgets.QVBoxLayout(frame)
            layout.setContentsMargins(20, 20, 20, 20)
            layout.setSpacing(12)

            title = QtWidgets.QLabel("选择直播平台")
            font = title.font()
            font.setPointSize(16)
            font.setBold(True)
            title.setFont(font)
            layout.addWidget(title)

            platform_layout = QtWidgets.QHBoxLayout()
            self.bili_radio = QtWidgets.QRadioButton("Bilibili")
            self.bili_radio.setChecked(True)
            self.yt_radio = QtWidgets.QRadioButton("YouTube")
            platform_layout.addWidget(self.bili_radio)
            platform_layout.addWidget(self.yt_radio)
            platform_layout.addStretch(1)
            layout.addLayout(platform_layout)

            self.use_saved_checkbox = QtWidgets.QCheckBox("使用 config.json 中保存的 URL（若有）")
            self.use_saved_checkbox.setChecked(True)
            layout.addWidget(self.use_saved_checkbox)

            self.save_to_config_checkbox = QtWidgets.QCheckBox("将本次输入的 URL 保存到 config.json")
            self.save_to_config_checkbox.setChecked(False)
            layout.addWidget(self.save_to_config_checkbox)

            self.url_edit = QtWidgets.QLineEdit()
            self.url_edit.setPlaceholderText("在这里输入自定义直播 URL（如不使用保存的 URL）")
            layout.addWidget(self.url_edit)

            default_bili = self.config.get("bili_live_url")
            default_yt = self.config.get("yt_live_url")
            if default_bili:
                self.url_edit.setText(default_bili)
            elif default_yt:
                self.url_edit.setText(default_yt)

            btn_layout = QtWidgets.QHBoxLayout()
            btn_layout.addStretch(1)
            cancel_btn = QtWidgets.QPushButton("取消")
            cancel_btn.setObjectName("cancelButton")
            ok_btn = QtWidgets.QPushButton("确定")
            btn_layout.addWidget(cancel_btn)
            btn_layout.addWidget(ok_btn)
            layout.addLayout(btn_layout)

            cancel_btn.clicked.connect(self.reject)
            ok_btn.clicked.connect(self.on_accept)
            self.bili_radio.toggled.connect(self.on_platform_changed)

            self.resize(420, 260)
            self._update_url_preview()
        except Exception as e:
            print(f"[StartDialog] __init__ error: {e}")

    def on_platform_changed(self, checked: bool):
        try:
            self._update_url_preview()
        except Exception as e:
            print(f"on platform changed error: {e}")

    def _update_url_preview(self):
        try:
            if self.bili_radio.isChecked():
                default = self.config.get("bili_live_url", "")
            else:
                default = self.config.get("yt_live_url", "")
            if self.use_saved_checkbox.isChecked():
                self.url_edit.setText(default)
        except Exception as e:
            print(f"update url preview error: {e}")

    def on_accept(self):
        try:
            self.platform = "bili" if self.bili_radio.isChecked() else "yt"
            self.url = self.url_edit.text()

            if not self.url:
                QtWidgets.QMessageBox.warning(self, "提示", "URL 不能为空。")
                return
        
            if self.save_to_config_checkbox.isChecked():
                key = "bili_live_url" if self.platform == "bili" else "yt_live_url"
                self.config[key] = self.url

                with open(self.config_file, "w", encoding="utf-8") as f:
                    json.dump(self.config, f, ensure_ascii=False, indent=4)

            self.accept()
        except Exception as e:
            print(f"on accept error: {e}")

class OverlayWindow(QtWidgets.QWidget):
    def __init__(self, parent=None, size=(300, 600), main_window=None):  
        try:
            super().__init__(parent)

            self.main_window = main_window       
            self._drag_pos = None                
        
            if self.main_window.platform == "bili":
                self.close_rect = QtCore.QRect(249, 0, 45, 29) 
            elif self.main_window.platform == "yt":
                self.close_rect = QtCore.QRect(358, 0, 45, 29) 
    
            self.hovered_button = None  

            self.setWindowFlags(
                QtCore.Qt.WindowType.FramelessWindowHint |
                QtCore.Qt.WindowType.WindowStaysOnTopHint |
                QtCore.Qt.WindowType.Tool 
            )

            self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground, True)
            self.setMouseTracking(True)
            self.resize(*size)

            self.min_block = QtWidgets.QWidget(self)
            self.min_block.setStyleSheet("background-color: rgba(0, 0, 0, 1%);")
            self.min_block.setGeometry(0, 0, self.width(), 29)
            self.min_block.setAttribute(QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

            self.block_layer = QtWidgets.QWidget(self)
            self.block_layer.setStyleSheet("background-color: rgba(0, 0, 0, 1%);")
            self.block_layer.setGeometry(0, 29, self.width(), self.height() - 29)
            self.block_layer.setAttribute(QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        except Exception as e:
            print(f"[OverlayWindow] __init__ error: {e}")

    def paintEvent(self, event: QtGui.QPaintEvent):
        try:
            painter = QtGui.QPainter(self)
            painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

            if self.hovered_button == "close":
                painter.save()
                painter.setBrush(QtGui.QBrush(QtGui.QColor(255, 0, 0, 160))) 
                painter.setPen(QtCore.Qt.PenStyle.NoPen)
                painter.drawRect(self.close_rect)
                painter.restore()

            super().paintEvent(event)
        except Exception as e:
            print(f"paint Event error: {e}")

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        try:
            if event.button() == QtCore.Qt.MouseButton.LeftButton:
                pos = event.position().toPoint()

                if self.close_rect.contains(pos):
                    self.hovered_button = None
                    self.update()  
                    QtWidgets.QApplication.processEvents()  
                    self.main_window.exit_event()
                else:
                    self._drag_pos = event.globalPosition().toPoint() - self.main_window.frameGeometry().topLeft()

                event.accept()
        except Exception as e:
            print(f"mouse Press Event error: {e}")

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        try:
            pos = event.position().toPoint()
    
            if self.close_rect.contains(pos):
                self.hovered_button = "close"
                self.update()  
            elif self.hovered_button is not None:
                self.hovered_button = None
                self.update()  

            if (self._drag_pos is not None and (event.buttons() & QtCore.Qt.MouseButton.LeftButton)):
                self.main_window.move(event.globalPosition().toPoint() - self._drag_pos)
                event.accept()
        except Exception as e:
            print(f"mouse Move Event error: {e}")

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        try:
            self._drag_pos = None
            event.accept()
        except Exception as e:
            print(f"mouse Release Event error: {e}")

class LiveApp(QtWidgets.QMainWindow):
    def __init__(self):
        try:
            super().__init__()

            self.driver = None
            self.chrome_hwnd = None

            self.platform = None
            self.url = None
            self.app_size = (300, 600)

            self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground, True)
            self.setWindowFlags(
                QtCore.Qt.WindowType.FramelessWindowHint |
                QtCore.Qt.WindowType.WindowStaysOnTopHint |
                QtCore.Qt.WindowType.Tool 
            )
        
            self.move(0, 0)

            self._drag_pos = None
            self.overlay = None
        except Exception as e:
            print(f"[LiveApp] __init__ error: {e}")

    def moveEvent(self, event):
        try:
            if self.overlay:
                self.overlay.move(self.x(), self.y())
            super().moveEvent(event)
        except Exception as e:
            print(f"move Event error: {e}")

    def exit_event(self):
        try:
            if win32gui.IsWindow(self.chrome_hwnd):
                self.driver.quit()

            self.close()
            sys.exit()
        except Exception as e:
            print(f"exit event error: {e}")

    def start_driver_and_embed(self):
        try:
            self.resize(self.app_size[0], self.app_size[1])

            chrome_options = Options()
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_argument(f"--window-size={self.width()},{self.height()}")
            chrome_options.add_argument(f"--window-position={self.x()},{self.y()}")

            if self.platform == "bili":
                app_url = "https://www.bilibili.com"
            elif self.platform == "yt":
                app_url = self.url

            chrome_options.add_argument(f"--app={app_url}")
            self.driver = webdriver.Chrome(options=chrome_options)

            if self.platform == "bili":
                self.driver.add_cookie({"name": "SESSDATA", "value": SESSDATA, "domain": ".bilibili.com", "path": "/"})
                self.driver.get(app_url)
                self.driver.refresh()

            self.driver.get(self.url)
            self.chrome_hwnd = find_hwnd(self.driver.title)
            qwin = QtGui.QWindow.fromWinId(self.chrome_hwnd)
            container = QtWidgets.QWidget.createWindowContainer(qwin, self)
            container.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
            self.setCentralWidget(container)

            self.show()

            self.overlay = OverlayWindow(size=(self.width(), self.height()), main_window=self)
            self.overlay.move(self.x(), self.y())
            self.overlay.show()
            
            if self.platform == "bili":
                js = """
                    setTimeout(() => {
                        window.scrollTo(940, 85);
                        document.body.style.overflow = "hidden";

                        const sidebar = document.getElementsByClassName("side-bar-cntr")[0];
                        sidebar.style.display = "none";
           
                        document.querySelector(".control-btn.pause.pointer").click();
                    }, 12000);
                """
            elif self.platform == "yt":
                js = """
                    setTimeout(() => {
                        window.scrollTo(0, 370);
                        document.body.style.overflow = "hidden";

                        const playButton = document.getElementsByClassName("ytp-play-button ytp-button")[0];
                        playButton.click();

                        document.getElementById("masthead-container").style.display = "none";

                        document.querySelector("#dismiss-button").click();
                    }, 12000);
                """
                
            self.driver.execute_script(js)
        except Exception as e:
            print(f"start driver and embed error: {e}")
            self.exit_event()

qt_app = QtWidgets.QApplication(sys.argv)

start_dialog = StartDialog(CONFIG, CONFIG_FILE)
if start_dialog.exec() != QtWidgets.QDialog.DialogCode.Accepted:
    sys.exit()

live_app = LiveApp()
live_app.platform = start_dialog.platform
live_app.url = start_dialog.url

if live_app.platform == "bili":
    live_app.app_size = (300, 605)
elif live_app.platform == "yt":
    live_app.app_size = (410, 575)

QtCore.QTimer.singleShot(200, live_app.start_driver_and_embed)

sys.exit(qt_app.exec())