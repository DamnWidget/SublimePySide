**Sublime PySide**
================

status: beta

Overview
========

Sublime PySide adds Qt (PySide and PyQt4) support for Sublime Text 2 and Sublime Text 3 on Python.

Python support is build for PySide and PyQt4 as well. This has been tested on Linux and Mac OSX

Copyright (C) 2012 Oscar Campos <oscar.campos@member.fsf.org>

**WARNING**: SublimeRope features doesn't work in Sublime Text 3. When convert a file from PySide to PyQt4 or viceversa in Sublime Text 3, you should save the file and reopen it again because the cursor is lost (trying to fix it already).


Getting Started
---------------

Unzip / git clone the SublimePySide directory into your ST2's Packages directory. To create a new PySide Qt project just use your Operating System keybindings:

    ctrl+shift+q on Linux
    ctrl+super+q on Mac OSX
    ctrl+alt+q on Windows

Then select the type of project you want to create and answer the questions.

You can also use the Tools menu at the toolbar to create a new project. You can configure SublimePySide to always use PySide or PyQt4 in the plugin settings file or just let it asks you when you generate a new project.

To convert PySide to PyQt4 syntax you can use the keybindings:

    ctrl+shift+c, ctrl+shift+q on Linux
    ctrl+super+c, ctrl+super+q on Mac OSX
    ctrl+shift+c, ctrl+shift+q on Windows

To convert PyQt4 to PySide syntax you can use the keybindings:

    ctrl+shift+c, ctrl+shift+p on Linux
    ctrl+super+c, ctrl+super+p on Mac OSX
    ctrl+shift+c, ctrl+shift+p on Windows


**NOTES**: Conversion from PyQt4 API 1 QVariant toWhatever methods to PySide is not automatic yet so maybe you should edit your code by hand after conversion. PySide only converts to PyQt4 API 2.


**IMPORTANT**: This plugin use SublimeRope if installed to generate Rope projects in an automatic way.

Features
----------

* QML file syntax highligth
* QMLProject file syntax highlight
* PySide and PyQt4 project creation
* PySide and PyQt4 autocompletion via SublimeRope
* PySide to PyQt4 syntax conversion
* PyQt4 to PySide syntax conversion

Supported Templates
--------------------

* Qt Quick Application (Python + QML)
* Qt Uick UI (Pure QML)
* Qt Gui Application (Pure Python)
* Qt Console Application (Pure Python)
* Qt Unit Test (dumb skeleton)

License:
--------
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with this program; if not, write to the Free Software Foundation, Inc.,
    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

Have a look at "LICENSE.txt" file for more information.

