import sys
import time
import threading
import feedparser
from PyQt5 import QtWidgets, QtGui, QtCore


class TrayApp(QtWidgets.QSystemTrayIcon):
    def __init__(self, icon, parent=None):
        super(TrayApp, self).__init__(icon, parent)
        self.setToolTip('Funky Clock Tray App')
        
        # Create a menu with an Exit option
        menu = QtWidgets.QMenu(parent)
        exit_action = menu.addAction("Exit")
        exit_action.triggered.connect(QtWidgets.qApp.quit)
        self.setContextMenu(menu)

        # Start the clock update thread
        self.clock_thread = threading.Thread(target=self.update_clock)
        self.clock_thread.daemon = True
        self.clock_thread.start()

        # Set up a timer to animate the icon
        self.animation_timer = QtCore.QTimer()
        self.animation_timer.timeout.connect(self.animate_icon)
        self.animation_timer.start(100)  # Update icon every 100 ms for animation

        # Animation-related attributes
        self.icon_colors = [
            QtGui.QColor("red"),
            QtGui.QColor("orange"),
            QtGui.QColor("yellow"),
            QtGui.QColor("green"),
            QtGui.QColor("blue"),
            QtGui.QColor("purple"),
        ]
        self.current_color_index = 0

        # RSS feed widget
        self.rss_widget = RSSWidget()

        # Track mouse hover events
        self.hover_timer = QtCore.QTimer()
        self.hover_timer.setInterval(100)
        self.hover_timer.timeout.connect(self.check_hover)
        self.hover_timer.start()
        self.hovering = False

    def update_clock(self):
        while True:
            # Get the current time
            current_time = time.strftime('%H:%M:%S')
            
            # Use Qt's signal-slot mechanism to update the tooltip on the main thread
            QtCore.QMetaObject.invokeMethod(
                self, "setToolTipSafe", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(str, f'Current Time: {current_time}'))
            
            time.sleep(1)  # Update every second

    @QtCore.pyqtSlot(str)
    def setToolTipSafe(self, text):
        self.setToolTip(text)

    def animate_icon(self):
        # Create a new icon with a funky color gradient
        pixmap = QtGui.QPixmap(64, 64)
        pixmap.fill(QtCore.Qt.transparent)

        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        gradient = QtGui.QRadialGradient(pixmap.rect().center(), 32)
        gradient.setColorAt(0, self.icon_colors[self.current_color_index])
        gradient.setColorAt(1, QtGui.QColor("black"))

        painter.setBrush(QtGui.QBrush(gradient))
        painter.drawEllipse(0, 0, 64, 64)
        painter.end()

        # Update the icon with the new pixmap
        self.setIcon(QtGui.QIcon(pixmap))

        # Cycle through colors for the next frame
        self.current_color_index = (self.current_color_index + 1) % len(self.icon_colors)

    def check_hover(self):
        pos = QtGui.QCursor.pos()
        tray_rect = self.geometry()
        if tray_rect.contains(pos) and not self.hovering:
            self.hovering = True
            self.on_hover()
        elif not tray_rect.contains(pos) and self.hovering:
            self.hovering = False
            self.on_hover_exit()

    def on_hover(self):
        # Show the RSS feed widget when hovering over the tray icon
        screen_geometry = QtWidgets.QApplication.primaryScreen().availableGeometry()
        widget_geometry = self.rss_widget.frameGeometry()
        x = screen_geometry.width() - widget_geometry.width() - 10
        y = screen_geometry.height() - widget_geometry.height() - 10
        self.rss_widget.move(x, y)
        self.rss_widget.show()

    def on_hover_exit(self):
        # Hide the RSS feed widget when no longer hovering over the tray icon
        self.rss_widget.hide()


class RSSWidget(QtWidgets.QWidget):
    def __init__(self):
        super(RSSWidget, self).__init__()
        self.setWindowTitle("RSS News Feed")
        self.setGeometry(100, 100, 300, 200)

        # Set up the RSS feed label
        self.label = QtWidgets.QLabel("Loading news...", self)
        self.label.setAlignment(QtCore.Qt.AlignTop)
        self.label.setWordWrap(True)
        self.label.setGeometry(10, 10, 280, 180)

        # Update RSS feed
        self.update_rss_feed()

    def update_rss_feed(self):
        # Fetch RSS feed from BBC
        feed = feedparser.parse("http://feeds.bbci.co.uk/news/rss.xml")
        if feed.entries:
            news_items = [f"- {entry.title}" for entry in feed.entries[:5]]
            news_text = "\n".join(news_items)
            self.label.setText(news_text)
        else:
            self.label.setText("Failed to load news feed.")


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # Set up and show the tray app
    icon = QtGui.QIcon("icon.png")  # Placeholder icon, will be animated
    tray_app = TrayApp(icon)
    tray_app.show()

    # Start the application event loop
    sys.exit(app.exec_())