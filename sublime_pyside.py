"""
Sublime PySide adds support for Nokia's PySide and Riberbancks PyQt libraries
"""

# -*- coding: utf8 -*-

# Copyright (C) 2012 - Oscar Campos <oscar.campos@member.fsf.org>
# This plugin is Free Software see LICENSE file for details


import sublime
import sublime_plugin

import os
import sys
import shutil
import functools
import threading
import subprocess
from glob import glob

try:
    import rope
    from rope.base.exceptions import RopeError, ResourceNotFoundError
    ROPE_SUPPORT = True
except ImportError:
    ROPE_SUPPORT = False


class Project(object):
    """
    Project class for PySide Qt Projects
    """

    def __init__(self, projectroot, projectname, projecttpl, templates):
        super(Project, self).__init__()

        self.templates = templates
        self.root = projectroot
        self.name = projectname
        self.tpl = projecttpl

    def is_valid(self):
        """
        Checks if the project is valid
        """

        if self.tpl not in [tpl.split('::')[0] for tpl in self.templates]:
            return False

        return True

    def create_files(self):
        """
        Create the project files
        """

        path = self.tpl.replace(' ', '_').lower()

        for tpl_file in glob('{0}/{1}/*'.format(get_templates_dir(), path)):
            if os.path.isdir(tpl_file):
                sublime.status_message('Copying {0} tree...'.format(tpl_file))
                try:
                    shutil.copytree(tpl_file, '{0}/{1}'.format(self.root,
                        os.path.basename(tpl_file)))
                except OSError, error:
                    sublime.error_message(error)
                continue
            with open(tpl_file, 'r') as file_handler:
                file_buffer = file_handler.read().replace('${APP_NAME}',
                    self.name.encode('utf8'))
            with open('{0}/{1}'.format(
                self.root, os.path.basename(tpl_file)), 'w') as file_handler:
                file_handler.write(file_buffer)
                sublime.status_message('Copying {0} file...'.format(tpl_file))

    def create_rope_files(self):
        """
        Create the Rope project files
        """

        try:
            rope_project = rope.base.project.Project(
                projectroot=self.root)
            rope_project.close()
        except (ResourceNotFoundError, RopeError), error:
            msg = 'Could not create rope project folder at {0}\n' \
                  'Exception: {1}'.format(self.root, str(error))
            sublime.error_message(msg)

    def create_st2_project_files(self):
        """
        Create the Sublime Text 2 project file
        """

        with open(
            '%s/%s.sublime-project' % (self.root, self.name), 'w') as fdesc:
            with open('%s/template.sublime-project' %
                (get_templates_dir()), 'r') as fhandler:
                file_buffer = fhandler.read().replace(
                    '${PATH}', self.root).replace('${QT_LIBRARY}', 'PySide')
            fdesc.write(file_buffer)


class CreateQtProjectCommand(sublime_plugin.WindowCommand):
    """
    Creates a new PySide application from a template
    """

    def run(self):
        """WindowCommand entry point"""
        CreateQtProjectThread(self.window).start()


class CreateQtProjectThread(threading.Thread):
    """
    Worker that creates a new application from a template
    """
    def __init__(self, window):
        self.window = window
        self.folders = self.window.folders()
        self.templates = list(get_template_list())
        self.proj_tpl = None
        self.proj_dir = None
        self.proj_name = None

        threading.Thread.__init__(self)

    def run(self):
        """
        Starts the thread
        """

        def show_quick_pane():
            """Just a wrapper to get set_timeout on OSX and Windows"""
            if not self.templates:
                sublime.error_message(
                    "{0}: There are no templates to list.".format(__name__))
                return

            self.window.show_quick_panel(self.templates, self.done)

        sublime.set_timeout(show_quick_pane, 10)

    def done(self, picked):
        """
        This method is called when user pickup a template from list
        """
        if picked == -1:
            return

        self.proj_tpl = self.templates[picked].split('::')[0]

        suggest = self.folders[0] if self.folders else os.path.expanduser('~')
        self.window.show_input_panel('Project root:', suggest,
            self.entered_proj_dir, None, None
        )

    def entered_proj_dir(self, path):
        """Called when user select an option in the quick panel"""
        if not os.path.exists(path):
            if sublime.ok_cancel_dialog('{path} does not exists.\n'
                            'Do you want to create it now?'.format(path=path)):
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
            sublime.error_message("You will use a project name")
            return

        self.proj_name = name

        project = Project(
                self.proj_dir, self.proj_name, self.proj_tpl, self.templates)

        if project.is_valid():
            project.create_files()
            if ROPE_SUPPORT:
                project.create_rope_files()
            project.create_st2_project_files()

            subprocess.Popen(
                [
                    sublime_executable_path(),
                    '--project',
                    '%s/%s.sublime-project' % (self.proj_dir, self.proj_name)
                ]
            )

            if ROPE_SUPPORT:
                if sublime.ok_cancel_dialog('Do you want to regenerate the '
                    'PySide/PyQt module cache now? (really recommended)'):
                    self.window.run_command('python_generate_modules_cache')
        else:
            sublime.error_message(
                'Could not create Qt Project files for template "{0}"'.format(
                    self.proj_tpl)
            )


def sublime_executable_path():
    """
    Return the Sublime Text 2 installation path for each platform
    """
    platform = sublime.platform()
    error = sublime.set_timeout(
        functools.partial(get_settings, 'osx_st2_path'), 0)
    if platform == 'osx':
        if not error:
            return '/Applications/Sublime Text 2.app' \
                                            '/Contents/SharedSupport/bin/subl'
        else:
            return error

    if platform == 'linux':
        if os.path.exists('/proc/self/cmdline'):
            return open('/proc/self/cmdline').read().split(chr(0))[0]

    return sys.executable


def get_template_list():
    """
    Generator for lazy templates list
    """

    with open("{0}/templates.lst".format(get_templates_dir(), "r")) as fhandle:
        for tpl in fhandle.read().split('\n'):
            if len(tpl):
                tpl_split = tpl.split(':')
                yield "{0}:: {1}".format(tpl_split[0], tpl_split[1])


def get_templates_dir():
    """
    Return the templates dir
    """

    return '{0}/{1}/{2}/templates'.format(
        sublime.packages_path(),
        get_settings('sublimepyside_package'),
        get_settings('sublimepyside_data_dir')
    )


def get_settings(name, typeof=str):
    """Get settings"""
    settings = sublime.load_settings('SublimePySide.sublime-settings')
    setting = settings.get(name)
    if setting:
        if typeof == str:
            return setting
        elif typeof == bool:
            return setting == True
        elif typeof == int:
            return int(settings.get(name, 500))
    else:
        if typeof == str:
            return ''
        else:
            return None
