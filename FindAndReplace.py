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

import re
import traceback

from PyQt5.QtCore import pyqtSignal, QRegExp
from PyQt5.QtWidgets import (QDockWidget, QAction, QLineEdit, QToolBar,
        QGridLayout, QLabel, QWidget, QShortcut)
from PyQt5.QtGui import (QIcon, QTextCursor, QTextCharFormat, QColor, QBrush,
        QKeySequence)

class FindAndReplace(QDockWidget):
    """ This class defines a dock widget providing find and replace
    actions to a voice editor widget.
    """

    # signal emitted to set a status message
    statusMessage = pyqtSignal('QString', name='statusMessage')

    def __init__(self, pageContent):
        """ Object initialization.

        Parameters
        ----------
        self : QWidget
        pageContent : VoiceEditor
            Widget on which the actions should be performed.
        """

        super().__init__('Find and replace')

        self.pageContent = pageContent

        ## ACTIONS

        # find
        findAction = QAction(
                QIcon('icons/edit-find'),
                'Find', self)
        findAction.setStatusTip('Find the pattern')
        findAction.triggered.connect(self.find)
        # replace
        replaceAction = QAction(
                QIcon('icons/edit-find-replace'),
                'Replace', self)
        replaceAction.setStatusTip('Replace the pattern')
        replaceAction.triggered.connect(self.replace)
        # find all
        findAllAction = QAction(
                QIcon('icons/document-preview'),
                'Find all', self)
        findAllAction.setStatusTip(
                'Find all the occourrences of the pattern')
        findAllAction.triggered.connect(self.findAll)
        # replace all
        replaceAllAction = QAction(
                QIcon('icons/document-edit-decrypt-verify'),
                'Replace all', self)
        replaceAllAction.setStatusTip(
                'Replace all the occourrences of the pattern')
        replaceAllAction.triggered.connect(self.replaceAll)
        # clear search results
        clearAction = QAction(
                QIcon('icons/window-close'),
                'Clear', self)
        clearAction.setStatusTip('Clear the highlighted search results')
        clearAction.triggered.connect(self.removeHighlighting)

        ## WIDGETS

        self.regex = QLineEdit()
        self.regex.returnPressed.connect(self.find)
        QShortcut(QKeySequence('Ctrl+F'), self, self.selectFind)

        self.replacement = QLineEdit()
        self.replacement.returnPressed.connect(self.replace)
        QShortcut(QKeySequence('Ctrl+R'), self, self.selectReplace)

        QShortcut(QKeySequence('Esc'), self, self.pageContent.setFocus)

        findToolbar = QToolBar('Find')
        findToolbar.addActions([
            findAction,
            replaceAction])
        findAllToolbar = QToolBar('Find all')
        findAllToolbar.addActions([
            findAllAction,
            replaceAllAction,
            clearAction])

        layout = QGridLayout()
        layout.addWidget(QLabel('Regex'), 0, 0)
        layout.addWidget(self.regex, 0, 1)
        layout.addWidget(QLabel('Replacement'), 1, 0)
        layout.addWidget(self.replacement, 1, 1)
        layout.addWidget(findToolbar, 0, 3)
        layout.addWidget(findAllToolbar, 1, 3)

        widget = QWidget()
        widget.setLayout(layout)

        self.setWidget(widget)


    def textOperation(self,
            indices,
            lengths,
            color=None,
            replacements=[None],
            clear=False,
            selectNext=False):
        """ Perform replacement, selection and highlight operations in a single
        undo/redo commit inside the text area.

        Parameters
        ----------
        indices : list of int
            List of indices for the absolute position of each match's beginning.
        lengths : list of int
            A list containing the length of each match.
        replacements : list of str
            A list containing a replacement for each match. If absent, no
            replacement operation is done. If some replacement is None,
            then the corresponding match is not replaced.
        color : str optional
            If present, the match (or its replacement, when present) will be
            highlighted with it. Must be a valid Qt color string.
        clear : bool optional
            If True, any pre-existing highlighting will be removed.
        selectNext : bool optional
            If True, the match following the replaced one will be selected.
        """
        cursor = self.pageContent.textCursor()

        # begin a single edit commit
        cursor.beginEditBlock()

        if clear:
            # remove previous highlighting
            cursor.select(QTextCursor.Document)
            textFormat = QTextCharFormat()
            textFormat.setBackground(QBrush(QColor("transparent")))
            cursor.mergeCharFormat(textFormat)

        increment = 0
        for index, length, replacement in zip(indices, lengths, replacements):
            index = index + increment

            # select match
            cursor.setPosition(index)
            cursor.movePosition(
                    QTextCursor.Right,
                    QTextCursor.KeepAnchor,
                    length)

            if replacement == None:
                # do not block iterations when no replacement is present
                replacements.append(None)
            else:
                # replace selection
                cursor.insertText(replacement)
                # select after replacement
                cursor.setPosition(index)
                cursor.movePosition(
                        QTextCursor.Right,
                        QTextCursor.KeepAnchor,
                        len(replacement))

                # correction due to the variation of length after replacement
                increment = increment + len(replacement) - length

            # color or select the match/replacement
            if color == None:
                # select
                self.pageContent.setTextCursor(cursor)
            else:
                # highlight
                textFormat = QTextCharFormat()
                textFormat.setBackground(QBrush(QColor(color)))
                cursor.mergeCharFormat(textFormat)

        if selectNext:
            # select the match following the last replacement/highlighting
            index, length = self.findIndex(cursor.position())
            if index != None:
                # select match
                cursor.setPosition(index)
                cursor.movePosition(
                        QTextCursor.Right,
                        QTextCursor.KeepAnchor,
                        length)
                self.pageContent.setTextCursor(cursor)

        # end of the edit commit
        cursor.endEditBlock()

    def findIndex(self, position=0):
        """ Return the index and the length of the first match found after
        "position".

        When the end of the document is reached, the search continues from the
        beginning. Return [None, None] when no match is found.

        Parameters
        ----------
        self : QWidget
        position : int optional
            Position in the text used as start point for the search.
        """

        # avoid to search fpr an empty pattern
        if self.regex.text() == '':
            return None, None

        # create the regex object and the text cursor position object
        regex = QRegExp(self.regex.text())
        cursor = self.pageContent.textCursor()

        # find first occourrence after the cursor
        index = regex.indexIn(
                self.pageContent.toPlainText(),
                position)
        length = regex.matchedLength()

        if position != 0 and index < 0:
            # no match found, try from the document beginning
            index = regex.indexIn(
                    self.pageContent.toPlainText(),
                    0)
            length = regex.matchedLength()

            if index < 0:
                # no match: there is no occourrence
                return None, None

        return index, length

    def findAllIndices(self):
        """ Return three lists containing the absolute starting
        position, the length and the replacement text for each match in the
        whole text, starting from its beginning.
        """

        # avoid to search for an empty pattern
        if self.regex.text() == '':
            return None, None, None

        regex = QRegExp(self.regex.text())
        index = 0
        indices = []
        lengths = []
        replacements = []
        while True:
            # find next occourrence
            index = regex.indexIn(
                    self.pageContent.toPlainText(),
                    index)
            length = regex.matchedLength()

            if index < 0:
                return indices, lengths, replacements

            # get replacement text
            replacement = re.sub(
                        self.regex.text(),
                        self.replacement.text(),
                        self.pageContent.toPlainText()[index : index + length],
                        1)

            # append to result
            indices.append(index)
            lengths.append(length)
            replacements.append(replacement)

            # continue search after the match
            index = index + length

    def find(self):
        """ Select the first match for the pattern after the cursor position.
        If the end of the document is reached, the search is restarted from
        the beginning.
        """
        position = self.pageContent.textCursor().position()
        index, length = self.findIndex(position=position)

        if index and index >= 0:
            # select the match
            self.textOperation([index], [length], None)
        else:
            self.statusMessage.emit('Not found')

        return

    def replace(self):
        """ Substitute the first occourrence of the pattern, and highlight the
        following one.
        """
        try:
            # if the selection matches, use it, otherwise get next index
            cursor = self.pageContent.textCursor()
            if re.fullmatch(self.regex.text(), cursor.selectedText()):
                # selection matches, replace the selection
                index = cursor.selectionStart()
                length = cursor.selectionEnd() - cursor.selectionStart()
            else:
                # search a match forward
                index, length = self.findIndex(cursor.position())
                if index == None:
                    # not found
                    self.statusMessage.emit('Not found')
                    return

            # get replacing text for the first occourrence after the cursor
            replacement = re.sub(
                        self.regex.text(),
                        self.replacement.text(),
                        self.pageContent.toPlainText()[index : index + length],
                        1)
            # replace the match
            self.textOperation(
                    [index],
                    [length],
                    replacements=[replacement],
                    color='#9F9',
                    clear=True,
                    selectNext=True)

        except Exception:
            traceback.print_exc()

    def findAll(self):
        """ Highlight all the matches for the pattern in the page content.
        """
        indices, lengths, replacements = self.findAllIndices()

        if indices and len(indices) > 0:
            self.textOperation(
                    indices,
                    lengths,
                    color='#9F9',
                    clear=True)
        else:
            self.statusMessage.emit('Not found')

    def replaceAll(self):
        """ Replace all the occourrences.
        """
        indices, lengths, replacements = self.findAllIndices()

        if indices and len(indices) > 0:
            self.textOperation(
                    indices,
                    lengths,
                    replacements=replacements,
                    color='#9F9',
                    clear=True)
        else:
            self.statusMessage.emit('Not found')

    def removeHighlighting(self):
        """ Remove all the highlightings from the page content.
        """
        cursor = self.pageContent.textCursor()
        textFormat = QTextCharFormat()
        cursor.select(QTextCursor.Document)
        textFormat.setBackground(QBrush(QColor("transparent")))
        cursor.mergeCharFormat(textFormat)

    def selectFind(self):
        """ Select the content of the "find" text field.
        """
        self.regex.setFocus()
        self.regex.selectAll()

    def selectReplace(self):
        """ Select the content of the "replace" text field.
        """
        self.replacement.setFocus()
        self.regex.selectAll()
