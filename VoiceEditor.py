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

from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QWidget, QLineEdit, QHBoxLayout, QVBoxLayout,
        QPlainTextEdit, QLabel, QAction, QToolBar)

from EditToolbar import EditToolbar

class VoiceEditor(QWidget):
    """ This class implements an editor capable to load, edit and save pages.
    """

    # signal emitted when asking to load the next voice
    loadNextVoice = pyqtSignal(name='loadNextVoice')

    def __init__(self, connection, diff):
        """ Object initialization.

        Parameters
        ----------
        self : QWidget
        connection : Connection
            Object managing the connection to the wiki.
        diff : Diff
            Diff widget to be used by this editor.
        """

        super().__init__()

        self.connection = connection
        self.diff = diff
        self.originalContent = ''

        ## ACTIONS

        # save voice
        saveVoiceAction = QAction(
                QIcon('icons/document-save'),
                'Save voice', self)
        saveVoiceAction.setStatusTip('Save the voice content in the wiki')
        saveVoiceAction.triggered.connect(self.savePageContent)
        # save voice and load next one
        saveAndNextAction = QAction(
                QIcon('icons/save-and-next.svg'),
                'Save and next', self)
        saveAndNextAction.setStatusTip('Save the voice and load next one')
        saveAndNextAction.triggered.connect(self.saveAndNextVoice)
        # load next voice discarding changes
        nextVoiceAction = QAction(
                QIcon('icons/arrow-right'),
                'Next', self)
        nextVoiceAction.setStatusTip('Load the next voice discarding changes')
        nextVoiceAction.triggered.connect(self.loadNextVoice.emit)
        # clean editor discarding changes
        clearAction = QAction(
                QIcon('icons/window-close'),
                'Clear', self)
        clearAction.setStatusTip('Clean the editor discarding changes')
        clearAction.triggered.connect(self.clear)
        # show diff
        diffAction = QAction(
                QIcon('icons/sort-presence'),
                'Show changes', self)
        diffAction.setStatusTip('Show changes for the current the edit')
        diffAction.triggered.connect(self.showDiff)

        ## TOOLBARS

        # Actions
        self.actionsToolbar = QToolBar('Actions')
        self.actionsToolbar.addActions([
            diffAction,
            saveVoiceAction,
            saveAndNextAction,
            nextVoiceAction,
            clearAction])
        self.actionsToolbar.setOrientation(Qt.Vertical)

        ## WIDGETS

        self.pageTitle = QLineEdit()
        self.pageTitle.setDisabled(True)
        titleLayout = QHBoxLayout()
        titleLayout.addWidget(QLabel('Title:'))
        titleLayout.addWidget(self.pageTitle)
        titleWidget = QWidget()
        titleWidget.setLayout(titleLayout)

        self.pageContent = QPlainTextEdit()
        self.pageContent.setTabChangesFocus(True)

        summaryLabel = QLabel('Summary:')
        self.summary = QLineEdit()
        summaryHBox = QHBoxLayout()
        summaryHBox.addWidget(summaryLabel)
        summaryHBox.addWidget(self.summary)
        summaryWidget = QWidget()
        summaryWidget.setLayout(summaryHBox)

        self.editToolbar = EditToolbar(self, self.pageContent)

        vbox = QVBoxLayout()
        vbox.addWidget(titleWidget)
        vbox.addWidget(self.editToolbar)
        vbox.addWidget(self.pageContent)
        vbox.addWidget(summaryWidget)

        hbox = QHBoxLayout()
        hbox.addLayout(vbox)
        hbox.addWidget(self.actionsToolbar)

        self.setLayout(hbox)

    def savePageContent(self):
        """ Save the page content making an edit in the wiki.
        """
        # ensure there is an opened voice
        if self.pageTitle.text() == '':
            return

        self.connection.edit(
                self.pageTitle.text(),
                self.pageContent.toPlainText(),
                self.summary.text())

    def saveAndNextVoice(self):
        """ Save the page content and load the next voice in the list.
        """
        # save current voice
        self.savePageContent()
        # ask to load next voice
        self.loadNextVoice.emit()

    def clear(self):
        """ Clear the editor content.
        """
        self.pageContent.setPlainText('')
        self.pageTitle.setText('')
        self.originalContent = ''

    def showDiff(self):
        """ Show the diff between the original text and the current text in
        the editor.
        """

        # ensure there is an opened voice
        if self.pageTitle.text() == '':
            return

        # show diff widget if disabled
        if not self.diff.isVisible():
            self.diff.setVisible(True)

        self.diff.showDiff(self.originalContent, self.pageContent.toPlainText())
