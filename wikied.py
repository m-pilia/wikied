#!/usr/bin/env python3

# This file is part of wikied.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright (C) 2016 Martino Pilia <martino.pilia@gmail.com>

import sys

from PyQt5.QtCore import QSettings, Qt
from PyQt5.QtWidgets import (QApplication, QMainWindow, QAction, QLabel,
        QToolBar)
from PyQt5.QtGui import QIcon

from RegexSandbox import RegexSandbox
from Connection import Connection
from AccountDialog import AccountDialog
from FindAndReplace import FindAndReplace
from VoiceSelector import VoiceSelector
from VoiceEditor import VoiceEditor
from Diff import Diff

class MainWindow(QMainWindow):
    """ Main window of the program.
    """

    def __init__(self):
        super().__init__()
        # settings file
        self.settings = QSettings('martinopilia', 'wikied')
        # label for the permanent message in the status bar
        self.permanentMessage = QLabel('Disconnected')
        # window for the regex sandbox
        self.regexSandbox = RegexSandbox()
        # object for the connection to the site
        self.connection = Connection(self.settings)
        self.connection.statusMessage.connect(self.statusBar().showMessage)
        self.connection.permanentMessage.connect(self.permanentMessage.setText)
        # window for the account settings
        self.accountDialog = AccountDialog(self.settings)

        # add permanent widget to the status bar
        self.statusBar().addPermanentWidget(self.permanentMessage)

        # actions
        # quit
        exitAction = QAction(
                QIcon('icons/window-close'),
                'Exit', self)
        exitAction.setStatusTip('Quit the application (Ctrl+Q)')
        exitAction.setShortcut('Ctrl+Q')
        exitAction.triggered.connect(self.close)
        # open RegexSandbox
        sandboxAction = QAction(
                QIcon('icons/code-context'),
                'Regex sandbox', self)
        sandboxAction.setStatusTip(
                'Open the regex test environment (Ctrl+Shif+S)')
        sandboxAction.setShortcut('Ctrl+Shift+S')
        sandboxAction.triggered.connect(self.regexSandbox.show)
        # connect
        connectAction = QAction(
                QIcon('icons/network-connect'),
                'Connect', self)
        connectAction.setStatusTip('Connect to the project')
        connectAction.triggered.connect(self.connection.connect)
        # disconnect
        disconnectAction = QAction(
                QIcon('icons/network-disconnect'),
                'Disconnect', self)
        disconnectAction.setStatusTip('Disconnect from the project')
        disconnectAction.triggered.connect(self.connection.disconnect)
        # set account
        setAccountAction = QAction(
                QIcon('icons/user-identity'),
                'Set account', self)
        setAccountAction.setStatusTip('Manage the account settings')
        setAccountAction.triggered.connect(self.accountDialog.exec_)

        # central widget and docks
        diff = Diff()
        diff.setObjectName('Diff')
        diff.setVisible(False)
        self.addDockWidget(Qt.TopDockWidgetArea, diff)

        editorWidget = VoiceEditor(self.connection, diff)
        self.setCentralWidget(editorWidget)

        substWidget = FindAndReplace(editorWidget.pageContent)
        substWidget.setObjectName('Find and replace')
        substWidget.statusMessage.connect(self.statusBar().showMessage)
        self.addDockWidget(Qt.BottomDockWidgetArea, substWidget)

        voiceSelector = VoiceSelector(self.connection, editorWidget)
        voiceSelector.setObjectName('Select voices')
        voiceSelector.statusMessage.connect(self.statusBar().showMessage)
        self.addDockWidget(Qt.LeftDockWidgetArea, voiceSelector)

        # toolbars
        # Connection
        connectionToolbar = QToolBar('Connection')
        connectionToolbar.setObjectName('connectionToolbar')
        connectionToolbar.addActions(
                [connectAction, disconnectAction, setAccountAction])
        self.addToolBar(connectionToolbar)

        # menu bar
        # File
        fileMenu = self.menuBar().addMenu('File')
        fileMenu.addAction(connectAction)
        fileMenu.addAction(disconnectAction)
        fileMenu.addAction(setAccountAction)
        fileMenu.addSeparator()
        fileMenu.addAction(exitAction)
        # Tools
        toolsMenu = self.menuBar().addMenu('Tools')
        toolsMenu.addAction(sandboxAction)
        # View
        viewMenu = self.menuBar().addMenu('View')
        viewMenu.addAction(voiceSelector.toggleViewAction())
        viewMenu.addAction(substWidget.toggleViewAction())
        viewMenu.addAction(connectionToolbar.toggleViewAction())
        viewMenu.addAction(editorWidget.actionsToolbar.toggleViewAction())
        viewMenu.addAction(diff.toggleViewAction())
        viewMenu.addAction(editorWidget.editToolbar.toggleViewAction())

        # view details
        self.setGeometry(200, 200, 1000, 800)
        self.setWindowTitle('WikiEd')
        self.setWindowIcon(QIcon(''))
        editorWidget.pageContent.setFocus()

        # restore state and geometry (lazy initialization)
        if (not self.settings.value('window/geometry') or
            not self.settings.value('window/state')):
            self.saveWindow()
        self.restoreGeometry(self.settings.value('window/geometry'))
        self.restoreState(self.settings.value('window/state'))

        self.show()

    # overriding
    def closeEvent(self, e):
        """ Handle the closing of the main window.
        """

        # disconnect from server
        self.connection.disconnect()

        # close regex sandbox
        self.regexSandbox.done(0)

        # save state and geometry of the window
        self.saveWindow()

    def saveWindow(self):
        """ Save into the settings the geometry and state of the main window.
        """
        self.settings.setValue('window/geometry', self.saveGeometry())
        self.settings.setValue('window/state', self.saveState())

if __name__ == '__main__':

    app = QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())
