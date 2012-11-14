# -*- coding: utf8 -*-

# Copyright (C) 2012 - Oscar Campos <oscar.campos@member.fsf.org>
# This plugin is Free Software see LICENSE file for details

"""
Sublime PySide adds support for Nokia's PySide and Riberbancks PyQt libraries
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
    from rope.base.exceptions import RopeError, ResourceNotFoundError
    ROPE_SUPPORT = True
except ImportError:
    ROPE_SUPPORT = False


# =============================================================================
# Sublime Plugin subclasses
# =============================================================================
class CreateQtProjectCommand(sublime_plugin.WindowCommand):
    """
    Creates a new PySide application from a template
    """

    def __init__(self, window):
        """Constructor"""

        sublime_plugin.WindowCommand.__init__(self, window)
        self.window = window

    def run(self):
        """WindowCommand entry point"""

        CreateQtProjectThread(self.window).start()


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
        self.window.show_input_panel('Project root:', suggest,
                                     self.entered_proj_dir, None, None)

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
            if ROPE_SUPPORT:
                project.generate_rope_project()
            project.generate_st2_project()

            subprocess.Popen(
                [
                    sublime_executable_path(),
                    '--project',
                    '%s/%s.sublime-project' % (self.proj_dir, self.proj_name)
                ]
            )

            if ROPE_SUPPORT:
                if sublime.ok_cancel_dialog(
                    'Do you want to regenerate the {0} module cache '
                        'now? (really recommended)'.format(self.proj_library)):
                    self.window.run_command('python_generate_modules_cache')
        else:
            sublime.error_message(
                'Could not create Qt Project files for template "{0}"'.format(
                    self.tplmanager.get_selected())
            )


# =============================================================================
# Classes
# =============================================================================
class Project(object):
    """
    Project class for Sublime Text 2 and SublimeRope Projects
    """

    def __init__(self, root, name, tplmanager):
        super(Project, self).__init__()

        self.root = root
        self.name = name
        self.tplmanager = tplmanager
        self.lib = None

    def generate_rope_project(self):
        """
        Create Rope project structure
        """

        if not ROPE_SUPPORT:
            return

        try:
            rope_project = rope.base.project.Project(projectroot=self.root)
            rope_project.close()
        except (ResourceNotFoundError, RopeError), error:
            msg = 'Could not create rope project folder at {0}\nException: {1}'
            sublime.status_message(msg.format(self.root, str(error)))

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
                except OSError, error:
                    sublime.error_message(error)
                continue

            with open(tpl, 'r') as fhandler:
                file_buffer = fhandler.read().replace(
                    '${APP_NAME}', self.name.encode('utf8')).replace(
                        '${QT_LIBRARY}', self.lib)

            with open(path, 'w') as fhandler:
                fhandler.write(file_buffer)
                sublime.status_message('Copying {0} file...'.format(tpl))


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
