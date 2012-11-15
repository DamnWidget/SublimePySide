# -*- coding: utf8 -*-

# Copyright (C) 2012 - Oscar Campos <oscar.campos@member.fsf.org>
# This plugin is Free Software see LICENSE file for details

"""
Converts a PySide script to PyQt
"""

from converter.base import BaseConverter


class Converter(BaseConverter):
    """
    Converts a PySide file to PyQt syntax
    """

    def __init__(self, filebuffer):
        pattern = {
            'PySide': 'PyQt4',
            'Signal': 'pyqtSignal',
            'Slot': 'pyqtSlot',
            'Property': 'pyqtProperty',
            'pyside-uic': 'pyuic4',
            'pyside-rcc': 'pyrcc4',
            'pyside-lupdate': 'pylupdate4'
        }
        super(Converter, self).__init__(filebuffer, pattern)

    def convert(self):
        """Convert a PySide syntax file to PyQt4"""

        return super(Converter, self).convert()

    def original_file(self):
        """Returns the original (unchanged) file"""

        return self.filebuffer
