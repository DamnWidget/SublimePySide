# -*- coding: utf8 -*-

# Copyright (C) 2012 - Oscar Campos <oscar.campos@member.fsf.org>
# This plugin is Free Software see LICENSE file for details

"""
Base class for converters
"""


class BaseConverter(object):
    """
    Base class for PySide <--> PyQt4 converters
    """

    def __init__(self, view, pattern):
        super(BaseConverter, self).__init__()
        self.view = view
        self.pattern = pattern

    def convert(self):
        """Try to convert the file"""

        edit = self.view.begin_edit()
        for key in self.pattern:
            matches = self.view.find_all(key)
            matches.reverse()

            for item in matches:
                self.view.replace(edit, item, self.pattern[key])

        self.view.end_edit(edit)
