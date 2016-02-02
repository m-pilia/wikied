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
import sys
import traceback

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QDialog, QHBoxLayout, QVBoxLayout, QLabel,
        QTextEdit, QPushButton)
from PyQt5.QtGui import QIcon

class RegexSandbox(QDialog):
    """ This class implements a window used to allow the user writing and
    testing regular expressions.
    """

    def __init__(self):
        """ Object initialization.
        """

        super().__init__()

        # boxes and labels for user input
        # regex
        self.regexBox = QTextEdit()
        self.regexBox.setTabChangesFocus(True)
        regexLabel = QLabel('Regex:')
        # replacement pattern
        self.replacementBox = QTextEdit()
        self.replacementBox.setTabChangesFocus(True)
        replacementLabel = QLabel('Replacement pattern:')
        # input text
        self.inputBox = QTextEdit()
        self.inputBox.setTabChangesFocus(True)
        inputLabel = QLabel('Input:')
        #output result
        self.outputBox = QTextEdit()
        self.outputBox.setFocusPolicy(Qt.NoFocus)
        self.outputBox.setReadOnly(True)
        outputLabel = QLabel('Output:')

        # buttons
        testButton = QPushButton('Test')
        testButton.clicked.connect(self.applyRegex)
        doneButton = QPushButton('Done')
        doneButton.clicked.connect(self.hideSandbox)

        # buttons' hbox row
        buttonsHbox = QHBoxLayout()
        buttonsHbox.addStretch(1)
        buttonsHbox.addWidget(testButton)
        buttonsHbox.addWidget(doneButton)

        # overall vbox layout
        vbox = QVBoxLayout()
        vbox.addStretch(1)
        vbox.addWidget(inputLabel)
        vbox.addWidget(self.inputBox)
        vbox.addWidget(regexLabel)
        vbox.addWidget(self.regexBox)
        vbox.addWidget(replacementLabel)
        vbox.addWidget(self.replacementBox)
        vbox.addWidget(outputLabel)
        vbox.addWidget(self.outputBox)
        vbox.addLayout(buttonsHbox)

        self.setLayout(vbox)

        self.setGeometry(300, 300, 400, 300)
        self.setWindowTitle('Regex Sandbox')
        self.setWindowIcon(QIcon.fromTheme('code-context'))

    def applyRegex(self):
        """ Apply the regex to the text in the input box.
        """
        try:
            self.outputBox.setPlainText(
                re.sub(self.regexBox.toPlainText(),       # regex
                       self.replacementBox.toPlainText(), # replacement pattern
                       self.inputBox.toPlainText()))      # input text
        except Exception:
            traceback.print_exc()

    def hideSandbox(self):
        """ Close the window.
        """
        self.done(0)
