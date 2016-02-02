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

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QListWidget, QMenu, QAction
from PyQt5.QtGui import QIcon

class VoiceList(QListWidget):
    """ This class implements a widget containing a list of page titles.
    """

    def __init__(self, load, remove):
        """ Object initialization.

        Parameters
        ----------
        self : QWidget
        load : QEvent
            Event triggered when the user loads a page from this list.
        remove : QEvent
            Event triggered when the user removes a page from this list.
        """

        super().__init__()
        self.load = load
        self.remove = remove

        # clear the list
        self.clearList= QAction(
                QIcon('icons/edit-clear'),
                'Clear list', self)
        self.clearList.setStatusTip('Remove all the voices from the list')
        self.clearList.triggered.connect(self.clear)

    def contextMenuEvent(self, e):
        """ Event handler.
        """
        menu = QMenu(self)
        menu.addActions([self.load, self.remove, self.clearList])
        # show the menu only if the mouse is pointing a list item
        if self.itemAt(e.pos()):
            menu.popup(e.globalPos())

    def keyPressEvent(self, e):
        """ Event handler.
        """
        if e.key() == Qt.Key_Delete:
            self.remove.trigger()
        elif e.key() == Qt.Key_Return:
            self.load.trigger()

    def mouseDoubleClickEvent(self, e):
        """ Event handler.
        """
        self.load.trigger()
