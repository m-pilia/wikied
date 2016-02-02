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

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QWidget, QAction, QComboBox, QPushButton,
        QLineEdit, QHBoxLayout, QVBoxLayout, QDockWidget)

from VoiceList import VoiceList

class VoiceSelector(QDockWidget):
    """ This class implements a dock widget which queries the wiki and
    adds the obtained page titles to a list of voices.

    The selector has a text input allowing the user to write a title, a
    dropdown menu allowing the user to chose the kind of query, and a buttton
    to fire the query. The resulting voices are added to the list. A voice in
    the list can be opened in a VoiceEditor attached to this object, or can be
    removed.
    """

    statusMessage = pyqtSignal('QString', name='statusMessage')

    def __init__(self, connection, editor):
        """ Object initialization.

        Parameters
        ----------
        self : QWidget
        connection : Connection
            Object managing the connection to the wiki.
        editor : VoiceEditor
            Editor widget in which open the voices from this list.
        """

        super().__init__('Select voices')

        self.editor = editor
        self.connection = connection
        self.pageContent = editor.pageContent
        self.pageTitle = editor.pageTitle

        self.connection.pageContentReceived.connect(self.receiveVoiceContent)
        self.connection.pageContentUnavailable.connect(self.skipVoice)
        self.editor.loadNextVoice.connect(self.loadNextVoice)

        # voice being currently loaded
        self.loadingVoice = None
        # voice adding modes
        self.titleModes = {
            'title': 'Add title',
            'backlinks': 'Links here',
            'links': 'Links',
            'embeddedin': 'Embedded in',
            'categorymembers': 'Category members'
        }
        # current voice index
        self.currentVoice = -1

        ## ACTIONS

        # load voice
        loadVoiceAction = QAction(
                QIcon('icons/document-edit-sign'),
                'Load', self)
        loadVoiceAction.setStatusTip('Load the voice in the editor')
        loadVoiceAction.triggered.connect(self.loadSelectedVoice)
        # remove voice
        removeVoiceAction = QAction(
                QIcon('icons/window-close'),
                'Remove', self)
        removeVoiceAction.setStatusTip('Remove the voice from the list')
        removeVoiceAction.triggered.connect(self.removeSelectedVoice)

        ## WIDGETS

        self.titleMode = QComboBox()
        self.titleMode.addItems(sorted(self.titleModes.values()))

        titleSubmit = QPushButton('Add')
        titleSubmit.setFixedWidth(40)
        titleSubmit.clicked.connect(self.addVoice)

        self.titleEdit = QLineEdit()
        self.titleEdit.returnPressed.connect(titleSubmit.click)

        titleTools = QHBoxLayout()
        titleTools.addWidget(self.titleMode)
        titleTools.addWidget(titleSubmit)

        self.voicesList = VoiceList(loadVoiceAction, removeVoiceAction)
        self.voicesList.setContextMenuPolicy(Qt.DefaultContextMenu)
        self.connection.voicesReceived.connect(self.voicesList.addItems)

        vbox = QVBoxLayout()
        vbox.addWidget(self.titleEdit)
        vbox.addLayout(titleTools)
        vbox.addWidget(self.voicesList)

        widget = QWidget()
        widget.setLayout(vbox)

        self.setWidget(widget)

    def addVoice(self):
        """ Add the queried voices.
        """
        title = self.titleEdit.text()
        if title == '':
            return
        if self.titleMode.currentText() == self.titleModes['title']:
            self.voicesList.addItem(title)
        elif self.titleMode.currentText() == self.titleModes['backlinks']:
            self.connection.getBacklinks(title)
        elif self.titleMode.currentText() == self.titleModes['links']:
            self.connection.getLinks(title)
        elif self.titleMode.currentText() == self.titleModes['embeddedin']:
            self.connection.getEmbeddedin(title)
        elif self.titleMode.currentText() == self.titleModes['categorymembers']:
            self.connection.getCategorymembers(title)

    def loadSelectedVoice(self):
        """ Load in the editor the page currently selected in the list.
        """
        selection = self.voicesList.selectedItems()
        if len(selection) != 1:
            return
        self.loadVoice(selection[0])

    def loadVoice(self, voice):
        """ Load a page in the editor.

        Parameters
        ----------
        self : QWidget
        voice : str
            Title of the page to be loaded.
        """

        if self.loadingVoice != None:
            return
        self.loadingVoice = voice
        self.connection.getPageContent(voice.text())

    def loadNextVoice(self):
        """ Load in the editor the page currently selected in the list, remove
        it from the list itself and select the following page.
        """
        # ensure there is a voice opened in the editor
        if self.currentVoice < 0 or self.loadingVoice:
            return
        # remove saved voice from the list
        self.removeVoice(self.voicesList.item(self.currentVoice))
        # check if there is any voice left
        voicesNo = self.voicesList.count()
        if voicesNo < 1:
            # no more voices in the list
            self.editor.clear()
            return
        # adjust index for current voice if needed
        if self.currentVoice > voicesNo - 1:
            self.currentVoice = voicesNo - 1
        # select next voice in the list
        self.voicesList.setCurrentRow(self.currentVoice)
        # load next voice
        self.loadVoice(self.voicesList.item(self.currentVoice))

    def skipVoice(self):
        """ Skip a page from the list.
        """
        self.loadingVoice = None
        self.loadNextVoice()

    def receiveVoiceContent(self, content):
        """ Receive the text content of a page and put it in the editor.

        Parameters
        ----------
        self : QWidget
        content : str
            Retrieved text content of the page.
        """
        self.currentVoice = self.voicesList.row(self.loadingVoice)
        self.pageContent.setPlainText(content)
        self.editor.originalContent = content
        self.pageTitle.setText(self.loadingVoice.text())

        self.loadingVoice = None

    def removeSelectedVoice(self):
        """ Remove from the voice list the currently selected entry.
        """
        selection = self.voicesList.selectedItems()
        if len(selection) != 1:
            return
        self.removeVoice(selection[0])

    def removeVoice(self, voice):
        """ Remove a page from the list.

        Parameters
        ----------
        self : QWidget
        voice : str
            Title of the page to be removed.
        """
        voicePos = self.voicesList.row(voice)
        if voicePos == None:
            return
        if voicePos < self.currentVoice:
            self.currentVoice = self.currentVoice - 1
        # workaround because removeItemWidget(QListWidgetItem) is not working
        self.voicesList.takeItem(voicePos)
