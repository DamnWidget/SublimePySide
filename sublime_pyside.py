# -*- coding: utf8 -*-

# Copyright (C) 2012 - Oscar Campos <oscar.campos@member.fsf.org>
# This plugin is Free Software see LICENSE file for details

import sublime
import sublime_plugin

import os
import threading
from glob import glob

try:
    import rope
    rope_support = True
except ImportError:
    rope_support = False

from settings import cfg


class Project(object):
    """
    Project class for PySide Qt Projects
    """

    def __init__(self, projectroot, projectname, projecttpl):
        super(Project, self).__init__()

        self.root = projectroot
        self.name = projectname
        self.tpl = projecttpl

    def is_valid(self):
        """
        Checks if the project is valid
        """

        if self.tpl not in [tpl.split('::')[0] for tpl in get_template_list()]:
            return False

        return True

    def create_files(self):
        """
        Create the project files
        """

        path = self.tpl.replace(' ', '_').lower()

        for file in glob('{0}/{1}/*'.format(get_templates_dir(), path)):
            with open(file, 'r') as fh:
                buffer = fh.read().replace('${APP_NAME}', self.name)
            with open('{0}/{1}'.format(
                self.root, file.split('/')[-1]), 'w') as fh:
                fh.write(buffer)
                sublime.status_message('Copying {0} file...'.format(file))


class CreateQtProjectCommand(sublime_plugin.WindowCommand):
    """
    Creates a new PySide application from a template
    """
    def run(self):
        CreateQtProjectThread(self.window).start()


class CreateQtProjectThread(threading.Thread):
    """
    Worker that creates a new application from a template
    """
    def __init__(self, window):
        self.window = window
        threading.Thread.__init__(self)

    def run(self):
        """
        Starts the thread
        """
        self.template_list = list(get_template_list())

        def show_quick_pane():
            if not self.template_list:
                sublime.error_message(
                    "{0}: There are no templates to list.".format(__name__))
                return

            self.window.show_quick_panel(self.template_list, self.done)

        sublime.set_timeout(show_quick_pane, 10)

    def done(self, picked):
        """
        This method is called when user pickup a template from list
        """
        if picked == -1:
            return

        self.proj_tpl = self.template_list[picked].split('::')[0]

        folders = self.window.folders()
        suggestion = folders[0] if folders else os.path.expanduser('~')
        self.window.show_input_panel('Project root:', suggestion,
            self.entered_proj_dir, None, None
        )

    def entered_proj_dir(self, path):
        if not os.path.isdir(path):
            sublime.error_message("Is not a directory: {0}".format(path))
            return

        self.proj_dir = path

        self.window.show_input_panel(
            'Give me a project name :', 'MyProject', self.entered_proj_name,
            None, None
        )

    def entered_proj_name(self, name):
        if not name:
            sublime.error_message("You will use a project name")
            return

        self.proj_name = name

        # if rope_support:
        #     try:
        #         rope_project = rope.base.project.Project(
        #             projectroot=self.proj_dir)
        #         rope_project.close()
        #     except Exception, e:
        #         msg = 'Could not create rope project folder at {0}\n' \
        #               'Exception: {1}'.format(self.proj_dir, str(e))
        #         sublime.error_message(msg)

        project = Project(self.proj_dir, self.proj_name, self.proj_tpl)
        if project.is_valid():
            project.create_files()
        else:
            sublime.error_message(
                'Could not create Qt Project files for template "{0}"'.format(
                    self.proj_tpl)
            )


def get_template_list():
    """
    Generator for lazy templates list
    """

    with open("{0}/templates.lst".format(get_templates_dir(), "r")) as fh:
        for tpl in fh.read().split('\n'):
            if len(tpl):
                tpl_split = tpl.split(':')
                yield "{0}:: {1}".format(tpl_split[0], tpl_split[1])


def get_templates_dir():
    """
    Return the templates dir
    """

    return '{0}/{1}/{2}/templates'.format(
        sublime.packages_path(),
        cfg.get('package'),
        cfg.get('data_dir')
    )
