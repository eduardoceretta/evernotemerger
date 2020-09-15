#coding:utf-8
import sys
import os
import json
import re
import traceback

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
import markdown2
from base64 import b64encode, b64decode
from datetime import datetime


DEBUG = True

def LOG(*args):
    if DEBUG:
        print("Evernote:", *args)


VERSION = "0.1.0"

def datestr(d):
    d = datetime.fromtimestamp(d // 1000)
    n = datetime.now()
    delta = n - d
    if delta.days == 0:
        if delta.seconds <= 3600 == 0:
            if delta.seconds <= 60 == 0:
                return "just now"
            else:
                return "few minutes ago"
        else:
            return "few hours ago"
    elif delta.days == 1:
        return "yesterday"
    elif delta.days == 2:
        return "2 days ago"
    return d.strftime("on %d/%m/%y")


ecode = EDAMErrorCode
error_groups = {
        'server': ('Internal server error', [ecode.UNKNOWN, ecode.INTERNAL_ERROR, ecode.SHARD_UNAVAILABLE, ecode.UNSUPPORTED_OPERATION ]),
        'data': ('User supplied data is invalid or conflicting', [ecode.BAD_DATA_FORMAT, ecode.DATA_REQUIRED, ecode.DATA_CONFLICT, ecode.LEN_TOO_SHORT, ecode.LEN_TOO_LONG, ecode.TOO_FEW, ecode.TOO_MANY]),
        'permission': ('Action not allowed, permission denied or limits exceeded', [ecode.PERMISSION_DENIED, ecode.LIMIT_REACHED, ecode.QUOTA_REACHED, ecode.TAKEN_DOWN, ecode.RATE_LIMIT_REACHED]),
        'auth': ('Authorisation error, consider re-configuring the plugin', [ecode.INVALID_AUTH, ecode.AUTH_EXPIRED]),
        'contents': ('Illegal note contents', [ecode.ENML_VALIDATION])
    }


def errcode2name(err):
    name = ecode._VALUES_TO_NAMES.get(err.errorCode, "UNKNOWN")
    name = name.replace("_", " ").capitalize()
    return name


def err_reason(err):
    for reason, group in error_groups.values():
        if err.errorCode in group:
            return reason
    return "Unknown reason"

def printError(msg):
    print(msg)

def explain_error(err):
    if isinstance(err, EDAMUserException):
        printError("Evernote error: [%s]\n\t%s" % (errcode2name(err), err.parameter))
        if err.errorCode in error_groups["contents"][1]:
            explanation = "The contents of the note are not valid.\n"
            msg = err.parameter.split('"')
            what = msg[0].strip().lower()
            if what == "element type":
                return explanation +\
                    "The inline HTML tag '%s' is not allowed in Evernote notes." %\
                    msg[1]
            elif what == "attribute":
                if msg[1] == "class":
                    return explanation +\
                        "The note contains a '%s' HTML tag "\
                        "with a 'class' attribute; this is not allowed in a note.\n"\
                        "Please use inline 'style' attributes or customise "\
                        "the 'inline_css' setting." %\
                        msg[3]
                else:
                    return explanation +\
                        "The note contains a '%s' HTML tag"\
                        " with a '%s' attribute; this is not allowed in a note." %\
                        (msg[3], msg[1])
            return explanation + err.parameter
        else:
            return err_reason(err)
    elif isinstance(err, EDAMSystemException):
        printError("Evernote error: [%s]\n\t%s" % (errcode2name(err), err.message))
        return "Evernote cannot perform the requested action:\n" + err_reason(err)
    elif isinstance(err, EDAMNotFoundException):
        printError("Evernote error: [%s = %s]\n\tNot found" % (err.identifier, err.key))
        return "Cannot find %s" % err.identifier.split('.', 1)[0]
    elif isinstance(err, gaierror):
        printError("Evernote error: [socket]\n\t%s" % str(err))
        return 'The Evernote services seem unreachable.\n'\
               'Please check your connection and retry.'
    else:
        printError("Evernote plugin error: %s" % str(err))
        return 'Evernote plugin error, please see the console for more details.\nThen contact developer at\n'\
               'https://github.com/bordaigorl/sublime-evernote/issues'


class Evernote():
    USER_AGENT = {'User-Agent': 'EvernoteMerger:' + VERSION}

    MD_EXTRAS = {
        'footnotes'          : None,
        'cuddled-lists'      : None,
        'metadata'           : None,
        'markdown-in-html'   : None,
        'fenced-code-blocks' : {'noclasses': True, 'cssclass': "", 'style': "default"}
    }

    EVERNOTE_COMMENT_BEG = "<!-- EvernoteMerger:"
    EVERNOTE_COMMENT_END = "-->"

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

    def _convertContent(self, contents):
        body = markdown2.markdown(contents, extras=Evernote.MD_EXTRAS)

        wrapper_style = ''
        if 'inline-css' in Evernote.MD_EXTRAS:
            wrapper_style = Evernote.MD_EXTRAS['inline-css'].get('body', "")
            if len(wrapper_style) > 0:
                wrapper_style = ' style="%s"' % wrapper_style

        meta = body.metadata or {}
        content = '<?xml version="1.0" encoding="UTF-8"?>'
        content += '<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">'
        content += '<en-note%s>' % wrapper_style
        hidden = ('\n%s%s%s\n' %
                    (Evernote.EVERNOTE_COMMENT_BEG,
                     b64encode(contents.encode('utf8')).decode('utf8'),
                     Evernote.EVERNOTE_COMMENT_END))
        content += hidden
        content += body
        # LOG(body)
        content += '</en-note>'
        return content


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
            LOG(explain_error(e))
            LOG(e)
            track = traceback.format_exc()
            print(track)

            return None

    def createNote(self, notebook, title, tagNames, content, resources, isMarkdown=False):
        try:
            noteStore = self._getNoteStoreClient()
            note = Types.Note()
            note.title = title
            note.notebookGuid = notebook.guid
            note.tagNames = tagNames
            note.content = self._convertContent(content) if isMarkdown else content
            note.resources = resources
            cnote = noteStore.createNote(self.token, note)
            return cnote

        except Exception as e:
            LOG(explain_error(e))
            LOG(e)
            track = traceback.format_exc()
            print(track)

            return None

    def updateNote(self, noteMetadata, **kwargs):
        try:
            noteStore = self._getNoteStoreClient()
            note = Types.Note()
            note.guid = noteMetadata.guid
            note.title = noteMetadata.title

            if "title" in kwargs:
                note.title = kwargs["title"]
            if "notebook" in kwargs:
                note.notebookGuid = kwargs["notebook"].guid
            if "tagNames" in kwargs:
                note.tagNames = kwargs["tagNames"]
            if "content" in kwargs:
                note.content = self._convertContent(kwargs["content"])
            if "resources" in kwargs:
                note.resources = kwargs["resources"]
            cnote = noteStore.updateNote(self.token, note)
            return cnote

        except Exception as e:
            LOG(explain_error(e))
            LOG(e)
            track = traceback.format_exc()
            print(track)

            return None

    def moveNote(self, noteMetadata, notebook):
        try:
            noteStore = self._getNoteStoreClient()
            note = Types.Note()
            note.guid = noteMetadata.guid
            note.title = noteMetadata.title
            note.notebookGuid = notebook.guid

            cnote = noteStore.updateNote(self.token, note)
            return cnote

        except Exception as e:
            LOG(explain_error(e))
            LOG(e)
            track = traceback.format_exc()
            print(track)

            return None

    def getNotes(self, notebook):
        try:
            noteStore = self._getNoteStoreClient()
            return noteStore.findNotesMetadata(
                self.token,
                NoteStore.NoteFilter(notebookGuid=notebook.guid),
                None,
                1000,
                NoteStore.NotesMetadataResultSpec(includeTitle=True, includeNotebookGuid=True, includeContentLength=True, includeCreated=True)
            ).notes
        except Exception as e:
            LOG(explain_error(e))
            LOG(e)
            track = traceback.format_exc()
            print(track)

            return None

    def getNoteContent(self, note):
        try:
            noteStore = self._getNoteStoreClient()
            return noteStore.getNoteContent(
                self.token,
                note.guid,
            )
        except Exception as e:
            LOG(explain_error(e))
            LOG(e)
            track = traceback.format_exc()
            print(track)
            return None

    def getNoteResources(self, note):
        try:
            noteStore = self._getNoteStoreClient()

            return noteStore.getNote(
                self.token,
                note.guid,
                False,True,True,True
            ).resources or []
        except Exception as e:
            LOG(explain_error(e))
            LOG(e)
            track = traceback.format_exc()
            print(track)
            return None


token = os.environ['EVERNOTE_DEV_TOKEN']
noteStoreUrl = os.environ['EVERNOTE_DEV_NOTESTORE_URL']

ev = Evernote(token, noteStoreUrl)
notebooks = ev.getNotebooks()
####################################
# BACKUP ALL NOTES:
# for notebook in notebooks:
#     print (f"Notebook:{notebook.stack}.{notebook.name} - {notebook.guid}")
#     notes = ev.getNotes(notebook)
#     for note in notes:
#         print (f"  Title:{note.title}")
#         print (f"  GUID:{note.guid}")
#         print (f"  Length:{note.contentLength}")
#         content = ev.getNoteContent(note)
#         mdtxt = html2text.html2text(content)
#         print (mdtxt)
#         print ("=============================")
#     print ("++++++++++++++++++++++++++++++++++")
####################################################

MERGED_NOTE_TITLE = "EvernoteMerger_Merged"
INPUT_NOTEBOOK_TITLE = "Input"
ARCHIVE_NOTEBOOK_TITLE = "MergerArchive"

inputNotebook = next(filter(lambda x: x.stack is None and x.name == INPUT_NOTEBOOK_TITLE, notebooks))
notes = ev.getNotes(inputNotebook)

mergedNote = None

contents = ""
resources = []
notesToBeMoved = []
for note in notes:
    if note.title == MERGED_NOTE_TITLE:
        mergedNote = note
        continue
    content = ev.getNoteContent(note)
    mdtxt = html2text.html2text(content)

    resources.extend(ev.getNoteResources(note))

    createdTime = datetime.fromtimestamp(note.created // 1000).strftime("%Y-%m-%d %H:%M:%S")
    contents += f"# {note.title}\n\n{mdtxt}\n\n_CreatedAt: {createdTime}_\n\n"

    notesToBeMoved.append(note)


time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
contents += f"\n\n\n--------------------------\n_Merge generated at {time}_"

if len(notesToBeMoved) > 0:
    if mergedNote:
        print ("APPENDING")
        content = ev.getNoteContent(mergedNote)
        mdtxt = html2text.html2text(content)
        r = ev.getNoteResources(mergedNote)
        resources.extend(r)

        mergedNote = ev.updateNote(mergedNote, content=f"{mdtxt}\n\n\n---------------\n\n\n{contents}\n", resources=resources)
    else:
        print ("CREATING NEW NOTE")
        mergedNote = ev.createNote(inputNotebook, MERGED_NOTE_TITLE, [], contents, resources, True)


    archiveNotebook = next(filter(lambda x: x.stack is None and x.name == ARCHIVE_NOTEBOOK_TITLE, notebooks))
    for note in notesToBeMoved:
        print(f"Move {note.title} to {archiveNotebook.name}")
        ev.moveNote(note, archiveNotebook)



print("done")
