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

from difflib import SequenceMatcher
import types

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QWidget, QDockWidget, QPlainTextEdit, QHBoxLayout
from PyQt5.QtGui import QTextCursor, QTextCharFormat, QBrush, QColor

class Diff(QDockWidget):
    """ A diff widget.

    This class defines a dock widget which shows the differences between
    the original page content retrieved in the last request and the current
    content in the voice editor.
    """

    def __init__(self):
        """ Widget initialization
        """

        super().__init__('Show changes')

        self.beforePTE = QPlainTextEdit()
        self.afterPTE = QPlainTextEdit()

        # widgets are read-only
        self.beforePTE.setReadOnly(True)
        self.afterPTE.setReadOnly(True)

        # bind the scroll position of the two widgets
        beforeScrollbar = self.beforePTE.verticalScrollBar()
        afterScrollbar = self.afterPTE.verticalScrollBar()
        beforeScrollbar.valueChanged.connect(afterScrollbar.setValue)
        afterScrollbar.valueChanged.connect(beforeScrollbar.setValue)

        hbox = QHBoxLayout()
        hbox.addWidget(self.beforePTE)
        hbox.addWidget(self.afterPTE)

        widget = QWidget()
        widget.setLayout(hbox)

#        # sizeHint for the widget
#        def sizeHint(self):
#            return QSize(self.width(), 150)
#        widget.sizeHint = types.MethodType(sizeHint, widget)

        self.setWidget(widget)

    def showDiff(self, before, after):
        """ Compute the diff and highlight changed parts.

        Parameters
        ----------
        self : QWidget
        before : str
            Original text.
        after : str
            Edited text.
        """

        beforeCursor = self.beforePTE.textCursor()
        afterCursor = self.afterPTE.textCursor()

        textFormat = QTextCharFormat()

        # delete any previous background
        textFormat.setBackground(QBrush(QColor('transparent')))
        beforeCursor.mergeCharFormat(textFormat)
        afterCursor.mergeCharFormat(textFormat)

        self.beforePTE.setPlainText(before)
        self.afterPTE.setPlainText(after)

        # get matching sequences
        sm = SequenceMatcher(a=before, b=after)
        i, j, k = 0, 0, 0

        # highlight mismatching sequences
        # NOTE: [ii:ii+kk] and [jj:jj+kk] are the matching sequences for the
        # first and second string, while [i+k:ii] and [j+k:jj] are the
        # mismatching ones
        for ii, jj, kk in sm.get_matching_blocks():

            # highlight with red the removed parts in the before text
            beforeCursor.setPosition(i + k)
            beforeCursor.movePosition(
                    QTextCursor.Right,
                    QTextCursor.KeepAnchor,
                    ii - i - k)
            textFormat.setBackground(QBrush(QColor('#F99')))
            beforeCursor.mergeCharFormat(textFormat)

            # highlight with green the added parts in the after text
            afterCursor.setPosition(j + k)
            afterCursor.movePosition(
                    QTextCursor.Right,
                    QTextCursor.KeepAnchor,
                    jj - j - k)
            textFormat.setBackground(QBrush(QColor('#CFC')))
            afterCursor.mergeCharFormat(textFormat)

            i, j, k = ii, jj, kk
