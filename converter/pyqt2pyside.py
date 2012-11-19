# -*- coding: utf8 -*-

# Copyright (C) 2012 - Oscar Campos <oscar.campos@member.fsf.org>
# This plugin is Free Software see LICENSE file for details

"""
Converts a PyQt4 script to PySide
"""

from converter.base import BaseConverter


class Converter(BaseConverter):
    """
    Converts a PyQt file to PySide syntax
    """

    def __init__(self, view):
        pattern = {
            'PyQt4': 'PySide',
            'pyqtSignal': 'Signal',
            'pyqtSlot': 'Slot',
            'pyqtProperty': 'Property',
            'pyuic4': 'pyside-uic',
            'pyrcc4': 'pyside-rcc',
            'pylupdate4': 'pyside-lupdate'
        }
        super(Converter, self).__init__(view, pattern)

    def convert(self):
        """Convert a PySide syntax file to PyQt4"""

        return super(Converter, self).convert()

    def original_file(self):
        """Returns the original (unchanged) file"""

        return self.filebuffer
