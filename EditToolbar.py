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

from PyQt5.QtWidgets import QToolBar, QAction
from PyQt5.QtGui import QIcon, QTextCursor

class EditToolbar(QToolBar):
    """ This class defines a toolbar containing some buttons for text format.
    """

    def __init__(self, parent, editor):
        """ Object initialization.

        Parameters
        ----------
        self : QWidget
        parent : QWidget
        editor : QPlainTextEdit
            Widget containing the text to be edited with the toolbar.
        """
        super().__init__('Edit actions')
        self.editor = editor

        # ACTIONS

        # bold
        boldAction = QAction(QIcon('icons/format-text-bold'),
                'Bold', parent)
        boldAction.setStatusTip('Toggle bold format for the selection')
        boldAction.triggered.connect(lambda x: self.toggleTag("'''", "'''"))

        # italic
        italicAction = QAction(QIcon('icons/format-text-italic'),
                'Italic', parent)
        italicAction.setStatusTip('Toggle italic format for the selection')
        italicAction.triggered.connect(lambda x: self.toggleTag("''", "''"))

        # TOOLBAR

        self.addActions([
            boldAction,
            italicAction])

    def toggleTag(self, opening, closing):
        """ Add or remove a couple of tags around the currently selected text.

        This function receives a couple of opening and closing tags as
        parameters, and it searches if the selected word is enclosed between
        them yet.
        A word is considered enclosed if the selection begins at the
        beginning of the opening tag and ends at the end of the closing one
        (i.e. if the tags are included in the selection) or if the selection
        begins just after the end of the opening tag and it ends just before
        the beginning of the closing one (i.e., if only the content of the tags
        is selected).
        If the selected word is enclosed yet, then the tags are removed,
        otherwise they are added. After the operation, the word is selected
        (excluding the tags).
        All the operations performed by this funcion are done in a single
        undo/redo commit.

        Parameters
        ----------
        opening : str
            String for the opening tag.
        closing : str
            String for the closing tag.
        """
        regex = re.compile(
                "^%s(.*)%s$" % (
                re.escape(opening),
                re.escape(closing)))
        cursor = self.editor.textCursor()

        # do all the operations in a single undo/redo commit
        cursor.beginEditBlock()

        # get selected text
        selection = cursor.selectedText()
        selectionLen = len(selection)

        # check if the tags are inside the selection
        match = regex.match(selection)

        # check if the tags are just outside the selection
        start = cursor.selectionStart() - len(opening)
        start = start if start >= 0 else 0
        outLen = selectionLen + len(opening) + len(closing)
        end = start + outLen
        length = cursor.document().characterCount()
        end = end if end < length else length - 1
        outMatch = regex.match(self.editor.toPlainText()[start:end])

        if outMatch:
            # if there are tags outside, extend the selection to cover them
            cursor.setPosition(start)
            cursor.movePosition(
                    QTextCursor.Right,
                    QTextCursor.KeepAnchor,
                    outLen)

        if match or outMatch:
            # index of the word beginning after tag removal
            beginning = cursor.selectionStart()
            # remove tags
            text = match.group(1) if match else outMatch.group(1)
            cursor.insertText(text)
            outputLen = len(text)

        else:
            # index of the word beginning after tag addition
            beginning = cursor.selectionStart() + len(opening)
            # add tags
            cursor.insertText("%s%s%s" % (opening, selection, closing))
            outputLen = len(selection)

        # select the word after the operation (tags excluded)
        cursor.setPosition(beginning)
        cursor.movePosition(
                QTextCursor.Right,
                QTextCursor.KeepAnchor,
                outputLen)
        self.editor.setTextCursor(cursor)

        # end undo/redo commit
        cursor.endEditBlock()
