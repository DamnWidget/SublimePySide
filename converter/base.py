# -*- coding: utf8 -*-

# Copyright (C) 2012 - Oscar Campos <oscar.campos@member.fsf.org>
# This plugin is Free Software see LICENSE file for details

"""
Base class for converters
"""

import re


class BaseConverter(object):
    """
    Base class for PySide <--> PyQt4 converters
    """

    def __init__(self, filebuffer, pattern):
        super(BaseConverter, self).__init__()
        self.filebuffer = filebuffer
        self.pattern = pattern

    def convert(self):
        """Try to convert the file"""

        regex = re.compile(
            '(%s)' % '|'.join([re.escape(tk) for tk in self.pattern.keys()]))

        return regex.sub(
            lambda x: str(self.pattern[x.string[x.start():x.end()]]),
            self.filebuffer
        )
