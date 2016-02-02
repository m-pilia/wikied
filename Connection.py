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

import logging
import requests
import threading

from PyQt5.QtCore import QObject, pyqtSignal

class Connection(QObject):
    """ Manage the connection with the wiki.

    The requests are made in separate threads, allowing to wait without
    blocking the UI.
    """

    # signal emitted to change the temporary status message in a status bar
    statusMessage = pyqtSignal('QString', name='statusMessage')

    # signal emitted to change the permanent status message in a status bar
    permanentMessage = pyqtSignal('QString', name='permanentMessage')

    # signal emitted when the content of a page is available
    pageContentReceived = pyqtSignal('QString', name='pageContentReceived')

    # signal emitted when the content of a page is unavailable
    pageContentUnavailable = pyqtSignal(name='pageContentUnavailable')

    # signal emitted when a voice list is available
    voicesReceived = pyqtSignal(list, name='voicesReceived')

    def __init__(self, settings):
        """ Object initialization.

        Parameters
        ----------
        self : QWidget
        settings : QObject
            Settings object for the program.
        """
        super().__init__()
        self.setObjectName('Connection')

        # logging
        logging.basicConfig()
        logging.getLogger().setLevel(logging.DEBUG)
        requests_log = logging.getLogger("requests.packages.urllib3")
        requests_log.setLevel(logging.DEBUG)
        requests_log.propagate = True

        self.settings = settings
        self.isConnected = False
        self.session = requests.Session()

    def address(self):
        """ Return the address of the wiki in use.
        """
        return 'https://%s.%s.org/w/api.php' % (
            self.settings.value('connection/lang'),
            self.settings.value('connection/site'))

    def connect(self):
        """ Open a connection to the wiki.
        """
        if self.isConnected:
            return

        t = threading.Thread(target=self.connectFunction)
        t.start()

    def connectFunction(self):
        """ Implement the connection opening.

        See https://www.mediawiki.org/wiki/API:Login
        """

        data = {
            'action': 'login',
            'lgname': self.settings.value('connection/username'),
            'lgpassword': self.settings.value('connection/password'),
            'format': 'json'
        }
        res = self.session.post(self.address(), data=data)

        self.statusMessage.emit('Login: ' + res.json()['login']['result'])

        data = {
            'action': 'login',
            'lgname': self.settings.value('connection/username'),
            'lgpassword': self.settings.value('connection/password'),
            'lgtoken': res.json()['login']['token'],
            'format': 'json'
        }
        res = self.session.post(self.address(), data=data).json()

        self.statusMessage.emit('Login: ' + res['login']['result'])

        if res['login']['result'] == "Success":
            self.isConnected = True
            self.permanentMessage.emit(
                    '%s@%s.%s' % (
                        self.settings.value('connection/username'),
                        self.settings.value('connection/lang'),
                        self.settings.value('connection/site')))

    def disconnect(self):
        """ Close a connection to the wiki.
        """
        if not self.isConnected:
            return

        t = threading.Thread(target=self.disconnectFunction)
        t.start()

    def disconnectFunction(self):
        """ Implement the connection closure.

        See https://www.mediawiki.org/wiki/API:Logout
        """

        self.session.post(self.address(), data={'action': 'logout'})

        self.isConnected = False
        self.permanentMessage.emit('Disconnected')

    def getPageContent(self, page):
        """ Get the content of a page from the wiki.

        Parameters
        ----------
        self : QWidget
        page : str
            Name of the requested page.
        """

        if not self.isConnected:
            return

        t = threading.Thread(target=self.getPageContentFunction, args=[page])
        t.start()

    def getPageContentFunction(self, page):
        """ Implement the page request.
        """

        address = 'https://%s.%s.org/wiki/%s' % (
                self.settings.value('connection/lang'),
                self.settings.value('connection/site'),
                requests.utils.quote(page, safe=''))

        res = self.session.post(address, data={'action': 'raw'})

        if res.status_code != 200:
            self.statusMessage.emit('The selected voice cannot be loaded')
            self.pageContentUnavailable.emit()
        else:
            self.pageContentReceived.emit(res.text)

    def edit(self, page, content, summary=''):
        """ Edit a page in the wiki, using the providen content.

        Parameters
        ----------
        self : QWidget
        page : str
            Name of the requested page.
        content : str
            Content to be saved in the page.
        summary : str optional
            Summary for the edit.
        """

        if not self.isConnected:
            return

        t = threading.Thread(
                target=self.editFunction,
                args=[page, content, summary])
        t.start()

    def editFunction(self, page, content, summary=''):
        """ Implement the page edit.

        See https://www.mediawiki.org/wiki/API:Edit
        """

        # get edit token
        data = {
            'action': 'query',
            'format': 'json',
            'prop': 'info',
            'meta': 'tokens',
            'type': 'csrf',
            'indexpageids': '',
            'titles': page
        }

        res = self.session.post(self.address(), data=data).json()

        if 'error' in res:
            # TODO the query somehow failed
            self.statusMessage.emit('Some error')

        # get pageid
        pageid = str(res['query']['pageids'][0])
        if int(pageid) < 0:
            # TODO page not found
            self.statusMessage.emit('Wrong page title')
            return

        # query to submit changes
        # pass the token parameter last, so if the edit gets interrupted,
        # the token won't be passed and the edit will fail
        data = {
            'action': 'edit',
            'format': 'json',
            'assert': 'user',
            'title': page,
            'summary': summary,
            'text': content,
            'basetimestamp': res['query']['pages'][pageid]['touched'],
            'token': res['query']['tokens']['csrftoken']
        }

        res = self.session.post(self.address(), data=data).json()

        if 'error' in res:
            #TODO
            self.statusMessage.emit(res['error']['code'])
        else:
            self.statusMessage.emit(res['edit']['result'])

    def getLinks(self, title):
        """ Get the links contained in a page.

        Parameters
        ----------
        self : QWidget
        title : str
            Title of the page.
        """

        if not self.isConnected:
            return

        t = threading.Thread(target=self.getLinksFunction, args=[title])
        t.start()

    def getLinksFunction(self, title):
        """ Implement the request to obtain the links contained in a page.

        See https://www.mediawiki.org/wiki/API:Links

        Parameters
        ----------
        self : QWidget
        title : str
            Title of the page.
        """

        links = []

        data = {
            'action': 'query',
            'format': 'json',
            'assert': 'user',
            'prop': 'links',
            'titles': title,
            'pllimit': '500',
            'indexpageids': '',
            'continue': ''
        }

        continueToken = {}

        while True:
            data.update(continueToken)

            res = self.session.post(self.address(), data=data).json()

            if 'error' in res:
                #TODO
                self.voicesReceived.emit(links)
                return

            # get pageid
            pageid = str(res['query']['pageids'][0])
            if int(pageid) < 0:
                # TODO page not found
                self.statusMessage.emit('Wrong page title')
                return

            # get links
            for voice in res['query']['pages'][pageid]['links']:
                links.append(voice['title'])

            # manage continuation of the query
            if 'continue' in res:
                continueToken = res['continue']
            else:
                break

        self.voicesReceived.emit(links)

    def getBacklinks(self, title):
        """ Get the backlinks for a page.

        See https://www.mediawiki.org/wiki/API:Backlinks

        Parameters
        ----------
        self : QWidget
        title : str
            Title of the page.
        """

        if not self.isConnected:
            return

        data = {
            'list': 'backlinks',
            'blnamespace': '0',
            'bltitle': title,
            'bllimit': '500',
        }

        t = threading.Thread(
                target=self.getVoices,
                args=[title, 'backlinks', data])
        t.start()

    def getEmbeddedin(self, title):
        """ Get the list of pages embedding a page.

        See https://www.mediawiki.org/wiki/API:Embeddedin

        Parameters
        ----------
        self : QWidget
        title : str
            Title of the page.
        """

        if not self.isConnected:
            return

        data = {
            'list': 'embeddedin',
            'eititle': title,
            'einamespace': '0',
            'eilimit': '500',
            'continue': ''
        }

        t = threading.Thread(
                target=self.getVoices,
                args=[title, 'embeddedin', data])
        t.start()

    def getCategorymembers(self, title):
        """ Get the pages contained in a category.

        See https://www.mediawiki.org/wiki/API:Categorymembers

        Parameters
        ----------
        self : QWidget
        title : str
            Title of the category.
        """

        if not self.isConnected:
            return

        data = {
            'list': 'categorymembers',
            'cmtitle': title,
            'cmtype': 'page',
            'cmlimit': '500',
        }

        t = threading.Thread(
                target=self.getVoices,
                args=[title, 'categorymembers', data])
        t.start()

    def getVoices(self, title, query, params):
        """ Implement a query to the wiki to retrive a set of pages.

        See https://www.mediawiki.org/wiki/API:Query

        Parameters
        ----------
        self : QWidget
        title : str
            Title of the page.
        query : str
            MediaWiki query argument.
        params : dict
            Parameters for the query.
        """

        links = []
        data = {
            'action': 'query',
            'format': 'json',
            'assert': 'user',
        }
        data.update(params)

        continueToken = {}
        while True:
            data.update(continueToken)

            res = self.session.post(self.address(), data=data).json()

            if 'error' in res:
                #TODO
                print(res['error'])
                self.voicesReceived.emit(links)
                return

            # get links
            for voice in res['query'][query]:
                links.append(voice['title'])

            # manage continuation of the query
            if 'continue' in res:
                continueToken = res['continue']
            else:
                break

        self.voicesReceived.emit(links)
