import sys

from PySide import QtCore

if __name__ == '__main__':

    app = QtCore.QCoreApplication(sys.argv)
    print "Initializing the main events loop"
    sys.exit(app.exec_())
