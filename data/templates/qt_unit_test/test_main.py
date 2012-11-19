#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

${PyQT_API_CHECK}from ${QT_LIBRARY}.QtGui import *


class QAppPresence(unittest.TestCase):

    def testQApp(self):
        #QtGui.qApp variable is instance of QApplication
        self.assert_(isinstance(qApp, QApplication))


def main():
    app = QApplication([])
    unittest.main()

if __name__ == '__main__':
    main()
