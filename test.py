#coding:utf-8
import sys
import os
import json
import re

try:
    import ssl
except:
    ssl = None

if sys.version_info < (3, 3):
    raise RuntimeError('The requires python 3')

# NOTE: OAuth was not implemented, because the Python 3 that is built into Sublime Text 3 was
# built without SSL. So, among other things, this means no http.client.HTTPSRemoteConnection

package_file = os.path.normpath(os.path.abspath(__file__))
package_path = os.path.dirname(package_file)
lib_path = os.path.join(package_path, "lib")

if lib_path not in sys.path:
    sys.path.append(lib_path)

import evernote.edam.type.ttypes as Types
from evernote.edam.error.ttypes import EDAMErrorCode, EDAMUserException, EDAMSystemException, EDAMNotFoundException

# import evernote.edam.userstore.UserStore as UserStore
import evernote.edam.notestore.NoteStore as NoteStore
import thrift.protocol.TBinaryProtocol as TBinaryProtocol
import thrift.transport.THttpClient as THttpClient
# from socket import gaierror
import html2text


DEBUG = True

def LOG(*args):
    if DEBUG:
        print("Evernote:", *args)


VERSION = "0.1.0"

class Evernote():
    USER_AGENT = {'User-Agent': 'EvernoteMerger:' + VERSION}

    def __init__(self, token, noteStoreUrl):
        if not token :
            raise ValueError("Token is invalid" + token)
        if not noteStoreUrl :
            raise ValueError("NoteStoreUrl is invalid" + noteStoreUrl)
        self.token = token
        self.noteStoreUrl = noteStoreUrl
        self.noteStoreClient = None

    def _getNoteStoreClient(self):
        if not self.noteStoreClient:
            noteStoreHttpClient = THttpClient.THttpClient(self.noteStoreUrl)
            noteStoreHttpClient.setCustomHeaders(Evernote.USER_AGENT)
            noteStoreProtocol = TBinaryProtocol.TBinaryProtocol(noteStoreHttpClient)
            self.noteStoreClient = NoteStore.Client(noteStoreProtocol)
        return self.noteStoreClient

    def getNotebooks(self):
        noteStore = self._getNoteStoreClient()
        return noteStore.listNotebooks(self.token)

    def createNotebook(self, name):
        try:
            noteStore = self._getNoteStoreClient()
            notebook = Types.Notebook()
            notebook.name = name
            notebooks = noteStore.createNotebook(self.token, notebook)
        except Exception as e:
            LOG(e)
            return None

    def getNotes(self, notebook):
        try:
            noteStore = self._getNoteStoreClient()
            return noteStore.findNotesMetadata(
                self.token,
                NoteStore.NoteFilter(
                    # {
                      notebookGuid=notebook.guid
                    # }
                ),
                None,
                1000,
                NoteStore.NotesMetadataResultSpec(includeTitle=True, includeNotebookGuid=True, includeContentLength=True, includeCreated=True)
            ).notes
        except Exception as e:
            LOG(e)
            return None

    def getNoteContent(self, note):
        try:
            noteStore = self._getNoteStoreClient()
            return noteStore.getNoteContent(
                self.token,
                note.guid,
            )
        except Exception as e:
            LOG(e)
            return None



token = os.environ['EVERNOTE_DEV_TOKEN']
noteStoreUrl = os.environ['EVERNOTE_DEV_NOTESTORE_URL']

ev = Evernote(token, noteStoreUrl)
notebooks = ev.getNotebooks()
print("notebooks")
# print(['%s.%s (%s)' % (x.stack, x.name, x.guid) for x in notebooks])
nb = next(filter(lambda x: x.stack is None and x.name == "Input", notebooks))
print("notebook")
print(nb)
notes = ev.getNotes(nb)
print("notes")
print(['%s %s %s %s' % (x.title, x.guid, x.contentLength, x.created) for x in notes])
for note in notes:
    print (f"Title:{note.title}")
    print (f"  GUID:{note.guid}")
    print (f"  Length:{note.contentLength}")
    content = ev.getNoteContent(note)
    mdtxt = html2text.html2text(content)
    print (mdtxt)
    print ("=============================")


print("done")