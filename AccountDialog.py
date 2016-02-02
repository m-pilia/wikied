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

from PyQt5.QtWidgets import (QDialog, QLineEdit, QFormLayout, QHBoxLayout,
        QVBoxLayout, QPushButton)
from PyQt5.QtGui import QIcon

class AccountDialog(QDialog):
    """ This class defines a dialog window for the account settings.
    """

    def __init__(self, settings):
        """ Object initialization

        Parameters
        ----------
        self : QWidget
        settings : QSettings
            Settings object for the program.
        """
        super().__init__()
        self.settings = settings
        self.langLineEdit = QLineEdit(settings.value('connection/lang'))
        self.siteLineEdit = QLineEdit(settings.value('connection/site'))
        self.usernameLineEdit = QLineEdit(settings.value('connection/username'))
        self.passwordLineEdit = QLineEdit(settings.value('connection/password'))

        self.passwordLineEdit.setEchoMode(QLineEdit.Password)

        formLayout = QFormLayout()
        formLayout.addRow('Lang:', self.langLineEdit)
        formLayout.addRow('Site:', self.siteLineEdit)
        formLayout.addRow('Username:', self.usernameLineEdit)
        formLayout.addRow('Password:', self.passwordLineEdit)

        doneButton = QPushButton('Done')
        doneButton.clicked.connect(self.close)

        hboxLayout = QHBoxLayout()
        hboxLayout.addStretch(1)
        hboxLayout.addWidget(doneButton)

        vboxLayout = QVBoxLayout()
        vboxLayout.addLayout(formLayout)
        vboxLayout.addLayout(hboxLayout)

        self.setLayout(vboxLayout)
        self.setWindowTitle('Account settings')
        self.setWindowIcon(QIcon.fromTheme('user-identity'))

    # overriding
    def closeEvent(self, e):
        """ Save the settings when the widget is closed.

        Parameters
        ----------
        self : QWidget
        e : QEvent
        """
        # save settings
        self.settings.setValue(
                'connection/lang',
                self.langLineEdit.text())
        self.settings.setValue(
                'connection/site',
                self.siteLineEdit.text())
        self.settings.setValue(
                'connection/username',
                self.usernameLineEdit.text())
        self.settings.setValue(
                'connection/password',
                self.passwordLineEdit.text())
