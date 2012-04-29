import sys

from PySide.QtCore import QUrl
from PySide.QtGui import QApplication
from PySide.QtDeclarative import QDeclarativeView

if __name__ == "__main__":
    app = QApplication([])
    view = QDeclarativeView()

    ctxt = view.rootContext()
    ctxt.setContextProperty("myModel", "Hello ${APP_NAME}")

    url = QUrl('view.qml')
    view.setSource(url)

    view.engine().quit.connect(lambda: app.quit())

    view.show()

    sys.exit(app.exec_())
