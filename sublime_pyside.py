# -*- coding: utf8 -*-

# Copyright (C) 2012 - Oscar Campos <oscar.campos@member.fsf.org>
# This plugin is Free Software see LICENSE file for details

"""
Sublime PySide adds support for Digia's PySide and Riberbancks PyQt libraries
"""

import os
import sys
import shutil
import functools
import threading
import subprocess
from glob import glob

import sublime
import sublime_plugin

try:
    import rope
    import ropemate
    assert ropemate
    from rope.base.exceptions import RopeError, ResourceNotFoundError
    ROPE_SUPPORT = True
except ImportError:
    ROPE_SUPPORT = False


if sys.version_info < (3, 3):
    from converter import pyqt2pyside, pyside2pyqt
    from converter.base import sip_api_2
    SUBLIME_TEXT_3 = False
else:
    from PySide.converter import pyqt2pyside, pyside2pyqt
    from PySide.converter.base import sip_api_2
    SUBLIME_TEXT_3 = True


# =============================================================================
# Sublime Plugin subclasses
# =============================================================================
class CreateQtProjectCommand(sublime_plugin.WindowCommand):
    """
    Creates a new PySide/PyQt4 application from a template
    """

    def __init__(self, window):
        """Constructor
        """

        sublime_plugin.WindowCommand.__init__(self, window)
        self.window = window

    def run(self):
        """WindowCommand entry point
        """

        CreateQtProjectThread(self.window).start()


class ConvertPyQt42PySideCommand(sublime_plugin.TextCommand):
    """Converts a PyQt4 buffer to PySide syntax
    """

    def __init__(self, *args, **kwargs):
        sublime_plugin.TextCommand.__init__(self, *args, **kwargs)

    def run(self, edit):
        """Run the command"""

        if SUBLIME_TEXT_3 is False:
            PyQt42PySideWorker(self.view).start()
        else:
            PyQt42PySideWorker(self.view, edit).run()

    def is_enabled(self):
        """Determine if this command is enabled
        """

        if 'from PyQt4' in self.view.substr(
            sublime.Region(0, self.view.size())
        ):
            return True

        return False


class ConvertPySide2PyQt4Command(sublime_plugin.TextCommand):
    """Converts a PySide buffer to PyQt4 syntax
    """

    def __init__(self, *args, **kwargs):
        sublime_plugin.TextCommand.__init__(self, *args, **kwargs)

    def run(self, edit):
        """Run the command
        """

        if SUBLIME_TEXT_3 is False:
            PySide2PyQt4Worker(self.view).start()
        else:
            PySide2PyQt4Worker(self.view, edit).run()

    def is_enabled(self):
        """Determine if this command is enabled
        """

        if 'from PySide' in self.view.substr(
            sublime.Region(0, self.view.size())
        ):
            return True

        return False


class OpenFileInDesignerCommand(sublime_plugin.WindowCommand):
    """Open the actual view buffer in Qt Designer if is a valid ui file
    """

    def run(self):
        """Run the command
        """

        command = QtDesignerCommand(self.window)
        command.open_file_in_designer()

    def is_enabled(self):
        """Determine if this command is enbaled in determinate conditions
        """

        if self.window.active_view() is None:
            return False

        file_name = self.window.active_view().file_name()
        if file_name is not None:
            return self.window.active_view().file_name().endswith('.ui')

        return False


class NewDialogCommand(sublime_plugin.WindowCommand):
    """Create a new dialog with buttons at bottom for QtDesigner
    """

    def run(self, dirs=[]):
        """Run the command
        """

        command = QtDesignerCommand(self.window)
        command.new_dialog(dirs, buttons=True, position='right')

    def is_enabled(self):
        """Determine if this command is enbaled in determinate conditions
        """

        designer = get_settings('sublimepyside_qt_tools_map').get('designer')
        if designer is None:
            return False

        return True


class OpenQdbusviewerCommand(sublime_plugin.WindowCommand):
    """Open the QDbusViewer application
    """

    def run(self):
        """Run the command
        """

        QDBusViewerCommand()


class OpenLinguistCommand(sublime_plugin.WindowCommand):
    """Open the Qt Linguist application
    """

    def run(self):
        """Run the command
        """

        LinguistCommand().open_linguist()


class OpenInLinguistCommand(sublime_plugin.WindowCommand):
    """Open a TS or QM file with Qt Linguist
    """

    def run(self):
        """Run the command
        """

        LinguistCommand().open_file_in_linguist(self.window.active_view())

    def is_enabled(self):
        """Determine if this command is enabled or not
        """

        if (self.window.active_view() is not None and (
                self.window.active_view().file_name().endswith('.ts')
                or self.window.active_view().file_name().endswith('.qm'))):
            return True

        return False


class GenerateTranslationsCommand(sublime_plugin.WindowCommand):
    """Generate Qt Linguist TS files
    """

    def run(self, files=[], dirs=[]):
        """Run the command
        """

        if not files and not dirs:
            sublime.error_message(
                'You have to call this function from the side bar context menu'
            )
            return

        PySideLupdateCommand(self.window).generate_translations(files, dirs)

    def is_enabled(self, files=[], dirs=[]):
        """Determine if the command is enabled
        """

        if files:
            for filename in files:
                if filename.endswith('.py') or filename.endswith('.pro'):
                    return True

        for dirname in dirs:
            for filename in glob('{}/{}'.format(dirname, '*[.py,.pro]')):
                if filename.endswith('.py') or filename.endswith('.pro'):
                    return True

        return False


class CompileCommons:
    """Compile commons methods and parameters
    """

    def is_enabled(self, files=[]):
        """Determine if a command is enabled
        """

        if not files:
            if (not self.window.active_view() or not
                    self.window.active_view().file_name().endswith(self.ext)):
                return False
        else:
            for filename in files:
                if not filename.endswith(self.ext):
                    return False

        return True


class CompileResourceCommand(sublime_plugin.WindowCommand, CompileCommons):
    """Compile Qt Resources
    """

    def run(self, files=[]):
        """Run the command
        """

        if not files:
            if (not self.window.active_view() or not
                    self.window.active_view().file_name().endswith('.qrc')):
                sublime.error_message(
                    'This command will process QRC files only.'
                )
            else:
                RCCCommand(self.window).compile()
        else:
            for filename in files:
                RCCCommand(self.window).compile(filename)

    def is_enabled(self, files=[]):
        """Determine if the command is enabled
        """

        self.ext = '.qrc'
        return CompileCommons.is_enabled(self, files)


class CompileUiCommand(sublime_plugin.WindowCommand, CompileCommons):
    """Compile Qt UI files
    """

    def run(self, files=[]):
        """Run the command
        """

        if not files:
            PyUicCommand(self.window).compile()
        else:
            for filename in files:
                PyUicCommand(self.window).compile(filename)

    def is_enabled(self, files=[]):
        """Determine if the command is enabled
        """

        self.ext = '.ui'
        return CompileCommons.is_enabled(self, files)


class PreviewUiCommand(sublime_plugin.WindowCommand):
    """Preview an UI file
    """

    def run(self):
        """Run the command
        """

        PyUicCommand(self.window).preview()

    def is_enabled(self):
        """Determine if the command is enabled
        """

        if self.window.active_view() is not None:
            if self.window.active_view().file_name().endswith('.ui'):
                return True

        return False


# =============================================================================
# Thread working classes
# =============================================================================
class CreateQtProjectThread(threading.Thread):
    """
    Worker that creates a new application from a template
    """
    def __init__(self, window):
        self.window = window
        self.tplmanager = TplManager(
            sublime.packages_path(),
            get_settings('sublimepyside_package'),
            get_settings('sublimepyside_data_dir')
        )

        self.folders = self.window.folders()
        self.proj_dir = None
        self.proj_name = None
        self.proj_library = get_settings('sublimepyside_library')
        self.library_options = ['Use Digia\'s PySide', 'Use RiverBank PyQt4']

        threading.Thread.__init__(self)

    def run(self):
        """
        Starts the thread
        """

        def show_quick_pane():
            """Just a wrapper to get set_timeout on OSX and Windows"""
            if not self.tplmanager.get_template_list():
                sublime.error_message(
                    "{0}: There are no templates to list.".format(__name__))
                return

            self.window.show_quick_panel(
                list(self.tplmanager.get_template_list()), self.tpl_selected)

        sublime.set_timeout(show_quick_pane, 10)

    def tpl_selected(self, picked):
        """
        This method is called when user pickup a template from list
        """
        if picked == -1:
            return

        tpl_list = list(self.tplmanager.get_template_list())
        self.tplmanager.selected = tpl_list[picked].split('::')[0]

        suggest = self.folders[0] if self.folders else os.path.expanduser('~')
        self.window.show_input_panel(
            'Project root:', suggest, self.entered_proj_dir, None, None)

    def entered_proj_dir(self, path):
        """Called when user select an option in the quick panel"""
        if not os.path.exists(path):
            if sublime.ok_cancel_dialog(
                '{path} dont exists.\nDo you want to create it now?'.format(
                    path=path)):
                os.makedirs(path)
            else:
                return

        if not os.path.isdir(path):
            sublime.error_message(
                "{path} is not a directory".format(path=path))
            return

        self.proj_dir = path

        self.window.show_input_panel(
            'Give me a project name :', 'MyProject', self.entered_proj_name,
            None, None
        )

    def entered_proj_name(self, name):
        """Called when the user enter the project name"""
        if not name:
            sublime.error_message("You must use a project name")
            return

        self.proj_name = name

        if not get_settings('sublimepyside_library_ask', bool):
            self.generate_project()
        else:
            self.window.show_quick_panel(
                self.library_options, self.library_selected)

    def library_selected(self, picked):
        """Sets the selected library or PySide if none"""
        if picked == -1:
            self.proj_library = 'PySide'
            return

        self.proj_library = 'PyQt4' if picked == 1 else 'PySide'
        self.generate_project()

    def generate_project(self):
        """Generate the PySide or PyQt project"""

        project_library = (
            PySideProject if self.proj_library == 'PySide' else PyQt4Project
        )

        project = project_library(
            self.proj_dir, self.proj_name, self.tplmanager
        )

        if self.tplmanager.is_valid(self.tplmanager.get_selected()):
            project.generate_project()

            project.generate_st2_project()
            if SUBLIME_TEXT_3 is False:
                project.generate_rope_project()

            subprocess.Popen(
                [
                    sublime_executable_path(),
                    '--project',
                    '%s/%s.sublime-project' % (self.proj_dir, self.proj_name)
                ]
            )
        else:
            sublime.error_message(
                'Could not create Qt Project files for template "{0}"'.format(
                    self.tplmanager.get_selected())
            )


# =============================================================================
# Sublime Text 2 specific code
# =============================================================================
if SUBLIME_TEXT_3 is False:
    class ConversionWorker(threading.Thread):
        """
        Base worker class for PySide <--> PyQt4 converters

        This is only used in Sublime Text 2
        """
        def __init__(self, view):
            threading.Thread.__init__(self)
            self.view = view

        def run(self):
            """
            Starts the thread
            """

            def show_conversion_confirmation():
                """Shows a confirmation dialog and proceed if true"""

                if self.__class__.__name__ == 'PyQt42PySideWorker':
                    library = 'PySide'
                else:
                    library = 'PyQt4'

                if sublime.ok_cancel_dialog(
                    'Do you really want to convert this file to %s' % library
                ):
                    self.qt_conversion()

            sublime.set_timeout(show_conversion_confirmation, 10)

        def qt_conversion(self):
            """Must be reimplemnted"""

            raise NotImplementedError('qt_conversion not implemented yet')
# =============================================================================
# Sublime Text 3 specific code
# =============================================================================
else:
    class ConversionWorker(object):
        """
        Base worker class for PySide <--> PyQt4 converters

        This is only used in Sublime Text 3
        """
        def __init__(self, view):
            self.view = view

        def run(self):
            """
            Starts the thread
            """

            def show_conversion_confirmation():
                """Shows a confirmation dialog and proceed if true"""

                if self.__class__.__name__ == 'PyQt42PySideWorker':
                    library = 'PySide'
                else:
                    library = 'PyQt4'

                if sublime.ok_cancel_dialog(
                    'Do you really want to convert this file to %s' % library
                ):
                    self.qt_conversion()

            show_conversion_confirmation()

        def qt_conversion(self):
            """Must be reimplemnted"""

            raise NotImplementedError('qt_conversion not implemented yet')


class PyQt42PySideWorker(ConversionWorker):
    """
    Worker class to convert PyQt4 buffer to PySide Syntax.

    Note that there is not automatically conversion from PyQt API 1
    to PySide yet so you should remove all the QVariant stuff yourself.

    This class is only used in Sublime Text 2
    """
    def __init__(self, view, edit=None):
        ConversionWorker.__init__(self, view)
        self.edit = edit

    def qt_conversion(self):
        """Converts Qt code"""
        pyqt2pyside.Converter(self.view).convert(self.edit)
        self.remove_api_imports()

    def remove_api_imports(self):
        """Remove api conversions for PyQt4 API 2"""

        # line_one = self.view.find('import sip', 0)
        line_one = self.view.find('# PyQT4 API 2 SetUp.', 0)
        if not line_one:
            line_one = self.view.find('from sip import setapi', 0)

        # At this point we already changed PyQt4 occurrences to PySide
        line_two = self.view.find('from PySide', 0)
        if not line_two:
            line_two = self.view.find('import PySide', 0)

        if not line_one or not line_two:
            return

        region = sublime.Region(line_one.a, self.view.line(line_two).a)

        edit = self.view.begin_edit() if self.edit is None else self.edit
        self.view.erase(edit, region)
        # self.view.insert(edit, line_one.a, '\n')
        self.view.end_edit(edit)


class PySide2PyQt4Worker(ConversionWorker):
    """
    Worker class to convert PySide buffer to PyQt4 Syntax.

    The conversion is just to PyQt4 API 2 so if you're running Python 3
    just remove the explicit api conversion lines.

    This class is only used in Sublime Text 2
    """
    def __init__(self, view, edit=None):
        ConversionWorker.__init__(self, view)
        self.edit = edit

    def qt_conversion(self):
        """Converts Qt code"""
        pyside2pyqt.Converter(self.view).convert(self.edit)
        self.insert_api_imports()

    def insert_api_imports(self):
        """Insert api conversions for PyQt4 API 2"""

        pyqt4import = self.view.find('from PyQt4', 0)
        if not pyqt4import:
            pyqt4import = self.view.find('import PyQt4', 0)
            if not pyqt4import:
                return

        prior_lines = self.view.lines(sublime.Region(0, pyqt4import.a))
        insert_import_str = '\n' + sip_api_2 + '\n'
        existing_imports_str = self.view.substr(
            sublime.Region(prior_lines[0].a, prior_lines[-1].b))

        if insert_import_str.rstrip() in existing_imports_str:
            return

        insert_import_point = prior_lines[-1].a

        edit = self.edit if self.edit is not None else self.view.begin_edit()
        self.view.insert(self.edit, insert_import_point, insert_import_str)
        self.view.end_edit(edit)


# =============================================================================
# Classes
# =============================================================================
class Project(object):
    """
    Project class for Sublime Text 2 and SublimeRope Projects
    """

    def __init__(self, root, name, tplmanager):
        super(Project, self).__init__()

        if sublime.platform() == 'windows':
            # os.path.normpath is not working
            root = root.replace('\\', '/')

        self.root = root
        self.name = name
        self.tplmanager = tplmanager
        self.ropemanager = RopeManager()
        self.lib = None

    def generate_rope_project(self):
        """
        Create Rope project structure
        """

        if not self.ropemanager.is_supported():
            return

        self.ropemanager.create_project(self.root)

    def generate_st2_project(self):
        """
        Create Sublime Text 2 project file
        """

        file_name = '{0}/{1}.sublime-project'.format(self.root, self.name)
        with open(file_name, 'w') as fdescriptor:
            template_name = '{0}/template.sublime-project'.format(
                self.tplmanager.get_template_dir())

            with open(template_name, 'r') as fhandler:
                file_buffer = fhandler.read().replace(
                    '${PATH}', self.root).replace('${QT_LIBRARY}', self.lib)

            fdescriptor.write(file_buffer)

    def generate_project(self):
        """
        Create the project files
        """

        templates_dir = '{0}/{1}/*'.format(
            self.tplmanager.get_template_dir(),
            self.tplmanager.get_selected(True)
        )

        for tpl in glob(templates_dir):
            path = '{0}/{1}'.format(self.root, os.path.basename(tpl))

            if os.path.isdir(tpl):
                sublime.status_message('Copying {0} tree...'.format(tpl))
                try:
                    shutil.copytree(tpl, path)
                except OSError as error:
                    if error.errno != 17:
                        message = '%d: %s' % (error.errno, error.strerror)
                        sublime.error_message(message)
                continue

            with open(tpl, 'r') as fhandler:
                app_name = (
                    self.name.encode('utf-8')
                    if SUBLIME_TEXT_3 is False else self.name
                )

                file_buffer = fhandler.read().replace(
                    '${APP_NAME}', app_name).replace(
                        '${QT_LIBRARY}', self.lib).replace(
                            '${PyQT_API_CHECK}', self.pyqt_api_check())

            with open(path, 'w') as fhandler:
                fhandler.write(file_buffer)
                sublime.status_message('Copying {0} file...'.format(tpl))

    def pyqt_api_check(self):
        """
        If PyQt4 is used then we add API 2
        """

        if self.lib == 'PyQt4':
            return sip_api_2

        return ''


class PySideProject(Project):
    """
    PySide Qt Project
    """

    def __init__(self, root, name, manager):
        super(PySideProject, self).__init__(root, name, manager)

        self.lib = 'PySide'


class PyQt4Project(Project):
    """
    PyQt4 Qt Project
    """

    def __init__(self, root, name, manager):
        super(PyQt4Project, self).__init__(root, name, manager)

        self.lib = 'PyQt4'


class TplManager(object):
    """
    SublimePySide TemplateManager class
    """

    def __init__(self, packagespath, packagedir=None, datadir=None):
        super(TplManager, self).__init__()

        self.packagespath = packagespath
        self.packagedir = packagedir
        self.datadir = datadir
        self.selected = None

    def is_valid(self, template):
        """
        Check if the given project template is valid
        """

        tpl_list = list(self.get_template_list())
        if template not in [tpl.split('::')[0] for tpl in tpl_list]:
            return False

        return True

    def get_template_dir(self):
        """
        Return the templates dir
        """

        return '{0}/{1}/{2}/templates'.format(
            self.packagespath,
            self.packagedir,
            self.datadir
        )

    def get_template_list(self):
        """
        Generator for lazy templates list
        """

        file_name = '{0}/templates.lst'.format(self.get_template_dir())
        with open(file_name, 'r') as fhandler:
            for tpl in fhandler.read().split('\n'):
                if len(tpl):
                    tpl_split = tpl.split(':')
                    yield '{0}:: {1}'.format(tpl_split[0], tpl_split[1])

    def get_selected(self, dir_conversion=False):
        """Return the selected template"""

        return (self.selected.replace(' ', '_').lower()
                if dir_conversion else self.selected)


class RopeManager(object):
    """
    Manager for rope/SublimeRope features
    """

    def __init__(self):
        super(RopeManager, self).__init__()
        self.supported = ROPE_SUPPORT

    def is_supported(self):
        """Returns true if rope is supported, otherwise returns false"""

        return self.supported

    def create_project(self, projectroot=None):
        """
        Create a new Rope project
        """

        if not projectroot or not self.supported:
            return

        try:
            rope_project = rope.base.project.Project(projectroot)
            rope_project.close()
        except (ResourceNotFoundError, RopeError) as error:
            msg = 'Could not create rope project folder at {0}\nException: {1}'
            sublime.status_message(msg.format(self.root, str(error)))


class Command(object):
    """Base class for external commands
    """

    def __init__(self, command):
        self.command = command
        self.proc = None

    def launch(self):
        """Launch the external process
        """

        kwargs = {
            'cwd': os.path.dirname(os.path.abspath(__file__)),
            'bufsize': -1
        }

        if sublime.platform() == 'windows':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            kwargs['startupinfo'] = startupinfo

        sub_args = [self.command] + self.options
        self.proc = subprocess.Popen(sub_args, **kwargs)


class PyUicCommand(Command):
    """PySide-uic
    """

    def __init__(self, window):
        self.window = window
        self.options = []

        command = get_settings('sublimepyside_tools_map').get('uic')
        if command is None:
            self.is_valid = False
            sublime.error_message(
                'PySide-uic application path is not configured'
            )
        else:
            self.is_valid = True
            super(PyUicCommand, self).__init__(command)

    def preview(self, filename=None):
        """Show a preview of the given filename
        """

        if filename is None:
            filename = self.window.active_view().file_name()

        self.options += ['-p', filename]
        self.launch()

    def compile(self, filename=None):
        """Compile a UI file
        """

        if filename is None:
            filename = self.window.active_view().file_name()

        self.options += ['-o', filename.replace('.ui', '_ui.py'), filename]
        self.launch()


class RCCCommand(Command):
    """PySide-rcc
    """

    def __init__(self, window):
        self.window = window
        self.options = []

        command = get_settings('sublimepyside_tools_map').get('rcc')
        if command is None:
            self.is_valid = False
            sublime.error_message(
                'PySide-rcc application path is not configured'
            )
        else:
            self.is_valid = True
            super(RCCCommand, self).__init__(command)

    def compile(self, filename=None):
        """Compile a file
        """

        if filename is None:
            filename = self.window.active_view().file_name()

        if filename.lower().endswith('.qrc'):
            rcc_options = get_settings('sublimepyside_rcc_options')
            if rcc_options.get('output_file', '') != 'same_rc':
                self.window.show_input_panel(
                    'Output filename (with no extension):',
                    filename.replace('.qrc', '_rc'),
                    lambda name: self.compile_resource_file(
                        filename, '{0}.py'.format(name.strip()), rcc_options
                    ), None, None
                )
            else:
                self.compile_resource_file(
                    filename, filename.replace('.qrc', '_rc.py'), rcc_options
                )
        else:
            sublime.error_message('Unknown file extension')

    def compile_resource_file(self, input_file, filename, rcc_options):
        """Process a QRC file using PySide-rcc
        """

        self.options += ['-o', filename]

        root_path = rcc_options.get('root_path', '')
        no_compress = rcc_options.get('no_compress', False)
        compression_level = rcc_options.get('compression_level', -1)

        if compression_level != -1 and not no_compress:
            if compression_level >= 0 and compression_level <= 9:
                self.options += ['-compress', str(compression_level)]

        if no_compress:
            self.options.append('-no-compress')

        if root_path != '' and type(root_path) is str:
            self.options += ['-root', root_path]

        self.options.append(input_file)
        self.launch()


class LinguistCommand(Command):
    """Linguist
    """

    def __init__(self):
        self.options = []

        command = get_settings('sublimepyside_qt_tools_map').get('linguist')
        if command is None:
            self.is_valid = False
            sublime.error_message(
                'Qt Linguist application path is not configured'
            )
        else:
            self.is_valid = True
            super(LinguistCommand, self).__init__(command)

    def open_linguist(self):
        """Just open Qt Linguist
        """

        self.launch()

    def open_file_in_linguist(self, view):
        """Open the buffer file with linguist
        """

        if (view.file_name().lower().endswith('.ts')
                or view.file_name().lower().endswith('.qm')):
            self.options.append(view.file_name())
            self.launch()
        else:
            sublime.error_message('Unknown file extension...')


class PySideLupdateCommand(Command):
    """PySide Lupdate
    """

    def __init__(self, window):
        self.window = window
        self.options = []

        command = get_settings('sublimepyside_tools_map').get('lupdate')
        if command is None:
            self.is_valid = False
            sublime.error_message(
                'PySide Lupdate tool path is not configured'
            )
        else:
            self.is_valid = True
            super(PySideLupdateCommand, self).__init__(command)

    def generate_translations(self, files, dirs):
        """Generate TS files using project file or iterating over the directory
        """

        self.handle_files(files)
        self.handle_dirs(dirs)

    def handle_files(self, files):
        """Handle files to generate TS
        """

        for filename in files:
            if filename.endswith('.py'):
                self.generate_translation_from_file(filename)
            elif filename.endswith('.pro'):
                self.generate_translation_from_project(filename)

    def handle_dirs(self, dirs):
        """Hadnle dirs to generate TS
        """

        for dirname in dirs:
            self.handle_files(glob('{}/{}'.format(dirname, '*[.py,.pro]')))

    def generate_translation_from_file(self, filename):
        """Just a convenience method
        """

        self.options = []
        self.options += [filename, '-ts', filename.replace('.py', '.ts')]
        self.launch()

    def generate_translation_from_project(self, filename):
        """Just a convenience method
        """

        self.options = []
        self.options.append(filename)
        self.launch()


class QDBusViewerCommand(Command):
    """QDBusViewer
    """

    def __init__(self):
        self.options = []

        command = get_settings('sublimepyside_qt_tools_map').get('qdbusviewer')
        if command is None:
            self.is_valid = False
            sublime.error_message(
                'QDBusViewer application path is not configured'
            )
        else:
            self.is_valid = True
            super(QDBusViewerCommand, self).__init__(command)
            self.launch()


class QtDesignerCommand(Command):
    """Qt Designer
    """

    def __init__(self, window):
        self.window = window
        self.options = []
        self.dirs = []

        command = get_settings('sublimepyside_qt_tools_map').get('designer')
        if command is None:
            self.is_valid = False
            sublime.error_message(
                'Designer application path is not configured'
            )
        else:
            designer_dir = os.path.join(
                os.path.dirname(__file__), 'data', 'designer'
            )

            with open(designer_dir + '/templates.json', 'r') as json_file:
                self.designer_options = sublime.decode_value(json_file.read())

            self.is_valid = True
            super(QtDesignerCommand, self).__init__(command)

    def open_file_in_designer(self):
        """Open the view buffer into Qt Designer
        """

        try:
            self.options.append(self.window.active_view().file_name())
            self.launch()
        except AttributeError:
            sublime.error_message('There is no active view!')

    def new_dialog(self, dirs, buttons=True, position='right'):
        """Create a new template for QtDesigner and opens it
        """

        self.dirs = dirs
        self.window.show_quick_panel(
            self.designer_options['templates_list'], self.template_selected
        )

    def template_selected(self, picked):
        """Process the template selected by the user
        """

        if picked == -1:
            return

        self.tpl = self.designer_options['templates_list'][picked]
        self.window.show_input_panel(
            'UI name (don\'t add extension):',
            self.tpl, self._new_designer_template, None, None
        )

    def _new_designer_template(self, name):
        """Create the file and init the subprocess
        """

        tpl = os.path.join(
            os.path.dirname(__file__), 'data', 'designer', 'templates',
            '{}.ui'.format('_'.join(self.tpl.lower().split(' ')))
        )

        self.dirs.append(self.window.folders()[0])

        filename = os.path.join(self.dirs[0], name + '.ui')
        in_file = open(tpl, 'r')
        out_file = open(filename, 'w')

        out_file.write(in_file.read())
        in_file.close()
        out_file.close()

        self.options.append(filename)
        self.launch()

        sublime.message_dialog('Qt Designer is starting, please wait')


# =============================================================================
# Global functions
# =============================================================================
def sublime_executable_path():
    """
    Return the Sublime Text 2 installation path for each platform
    """
    platform = sublime.platform()
    error = sublime.set_timeout(
        functools.partial(get_settings, 'osx_st2_path'), 0)

    # in Sublime Text 3 we can just use `sublime.executable_path()
    if SUBLIME_TEXT_3 is True:
        return sublime.executable_path()

    if platform == 'osx':
        if not error:
            return ('/Applications/Sublime Text 2.app'
                    '/Contents/SharedSupport/bin/subl')
        else:
            return error

    if platform == 'linux':
        if os.path.exists('/proc/self/cmdline'):
            return open('/proc/self/cmdline').read().split(chr(0))[0]

    return sys.executable


def get_settings(name, typeof=str):
    """Get settings"""
    settings = sublime.load_settings('SublimePySide.sublime-settings')
    setting = settings.get(name)
    if setting:
        if typeof == str:
            return setting
        elif typeof == bool:
            return setting is True
        elif typeof == int:
            return int(settings.get(name, 500))
    else:
        if typeof == str:
            return ''
        else:
            return None
