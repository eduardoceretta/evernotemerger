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


VERSION = "0.1.0"
# USER_AGENT = {'User-Agent': 'SublimeEvernote/' + EVERNOTE_PLUGIN_VERSION}

# EVERNOTE_SETTINGS = "Evernote.sublime-settings"
# SUBLIME_EVERNOTE_COMMENT_BEG = "<!-- Sublime:"
# SUBLIME_EVERNOTE_COMMENT_END = "-->"


# class EvernoteDo():

#     _noteStore = None

#     _notebook_by_guid = None
#     _notebook_by_name = None
#     _notebooks_cache = None

#     _tag_name_cache = {}
#     _tag_guid_cache = {}

#     MD_EXTRAS = {
#         'footnotes'          : None,
#         'cuddled-lists'      : None,
#         'metadata'           : None,
#         'markdown-in-html'   : None,
#         'fenced-code-blocks' : {'noclasses': True, 'cssclass': "", 'style': "default"}
#     }

#     settings_token=None
#     settings_noteStoreUrl=None

#     def token(self):
#         return os.environ['EVERNOTE_DEV_TOKEN']

#     def get_shard_id(self, token=None):
#         token_parts = (token or self.token()).split(":")
#         id = token_parts[0][2:]
#         return id

#     def get_user_id(self, token=None):
#         token_parts = (token or self.token()).split(":")
#         id = token_parts[1][2:]
#         return int(id, 16)

#     def load_settings(self):
#         print ("NOOP load_settings")

#     def message(self, msg):
#         print ("message", msg)

#     def update_status_info(self, note, view=None):
#        print ("NOOP update_status_info")

#     def connect(self, callback, **kwargs):
#         self.message("initializing..., please wait...")

#         def __connect(token, noteStoreUrl):
#             if noteStoreUrl.startswith("https://") and not ssl:
#                 print("Not using SSL")
#                 noteStoreUrl = "http://" + noteStoreUrl[8:]
#             EvernoteDo.settings_noteStoreUrl = noteStoreUrl
#             if callback:
#                 callback(**kwargs)

#         def __derive_note_store_url(token):
#             id = self.get_shard_id(token)
#             url = "www.evernote.com/shard/" + id + "/notestore"
#             if ssl:
#                 url = "https://" + url
#             else:
#                 url = "http://" + url
#             return url

#         def on_token(token):
#             noteStoreUrl = EvernoteDo.settings_noteStoreUrl
#             if not noteStoreUrl:
#                 noteStoreUrl = __derive_note_store_url(token)
#                 __connect(token, os.environ['EVERNOTE_DEV_NOTESTORE_URL'])
#             else:
#                 __connect(token, noteStoreUrl)

#         token = self.token()
#         on_token(token)
#         noteStoreUrl = EvernoteDo.settings_noteStoreUrl
#         if not token or not noteStoreUrl:
#             print("go tohttps://www.evernote.com/api/DeveloperToken.action")

#     def get_note_store(self):
#         if EvernoteDo._noteStore:
#             return EvernoteDo._noteStore
#         noteStoreUrl = EvernoteDo.settings_noteStoreUrl
#         print (noteStoreUrl)
#         noteStoreHttpClient = THttpClient.THttpClient(noteStoreUrl)
#         noteStoreHttpClient.setCustomHeaders(USER_AGENT)
#         noteStoreProtocol = TBinaryProtocol.TBinaryProtocol(noteStoreHttpClient)
#         noteStore = NoteStore.Client(noteStoreProtocol)
#         EvernoteDo._noteStore = noteStore
#         return noteStore

#     def get_notebooks(self):
#         if EvernoteDo._notebooks_cache:
#             print("Using cached notebooks list")
#             return EvernoteDo._notebooks_cache
#         notebooks = None
#         # try:
#         noteStore = self.get_note_store()
#         self.message("Fetching notebooks, please wait...")
#         notebooks = noteStore.listNotebooks(self.token())
#         self.message("Fetched all notebooks!")
#         # except Exception as e:
#         #     print("EXCEPTION", e)
#         #     return []
#         EvernoteDo._notebook_by_name = dict([(nb.name, nb) for nb in notebooks])
#         EvernoteDo._notebook_by_guid = dict([(nb.guid, nb) for nb in notebooks])
#         EvernoteDo._notebooks_cache = notebooks
#         return notebooks

    # def create_notebook(self, name):
    #     try:
    #         noteStore = self.get_note_store()
    #         notebook = Types.Notebook()
    #         notebook.name = name
    #         notebooks = noteStore.createNotebook(self.token(), notebook)
    #     except Exception as e:
    #         sublime.error_message(explain_error(e))
    #         LOG(e)
    #         return None
    #     EvernoteDo._notebooks_cache = None # To force notebook cache refresh
    #     return self.notebook_from_name(name)

    # def get_note_link(self, guid):
    #     linkformat = 'evernote:///view/{userid}/{shardid}/{noteguid}/{noteguid}/'
    #     return linkformat.format(userid=self.get_user_id(), shardid=self.get_shard_id(), noteguid=guid)

    # def notebook_from_guid(self, guid):
    #     self.get_notebooks()  # To trigger caching
    #     return EvernoteDo._notebook_by_guid[guid]

    # def notebook_from_name(self, name):
    #     self.get_notebooks()  # To trigger caching
    #     return EvernoteDo._notebook_by_name[name]

    # def tag_from_guid(self, guid):
    #     if guid not in EvernoteDo._tag_name_cache:
    #         name = self.get_note_store().getTag(self.token(), guid).name
    #         EvernoteDo._tag_name_cache[guid] = name
    #         EvernoteDo._tag_guid_cache[name] = guid
    #     return EvernoteDo._tag_name_cache[guid]

    # def tag_from_name(self, name):
    #     if name not in EvernoteDo._tag_guid_cache:
    #         # This requires downloading the full list
    #         self.cache_all_tags()
    #     return EvernoteDo._tag_guid_cache[name]

    # def cache_all_tags(self):
    #     tags = self.get_note_store().listTags(self.token())
    #     for tag in tags:
    #         EvernoteDo._tag_name_cache[tag.guid] = tag.name
    #         EvernoteDo._tag_guid_cache[tag.name] = tag.guid

    # @staticmethod
    # def clear_cache():
    #     EvernoteDo._noteStore = None
    #     EvernoteDo._notebook_by_name = None
    #     EvernoteDo._notebook_by_guid = None
    #     EvernoteDo._notebooks_cache = None
    #     EvernoteDo._tag_guid_cache = {}
    #     EvernoteDo._tag_name_cache = {}

    # def populate_note(self, note, contents):
    #     if isinstance(contents, sublime.View):
    #         contents = contents.substr(sublime.Region(0, contents.size()))
    #     body = markdown2.markdown(contents, extras=EvernoteDo.MD_EXTRAS)

    #     wrapper_style = ''
    #     if 'inline-css' in EvernoteDo.MD_EXTRAS:
    #         wrapper_style = EvernoteDo.MD_EXTRAS['inline-css'].get('body', "")
    #         if len(wrapper_style) > 0:
    #             wrapper_style = ' style="%s"' % wrapper_style

    #     meta = body.metadata or {}
    #     content = '<?xml version="1.0" encoding="UTF-8"?>'
    #     content += '<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">'
    #     content += '<en-note%s>' % wrapper_style
    #     hidden = ('\n%s%s%s\n' %
    #                 (SUBLIME_EVERNOTE_COMMENT_BEG,
    #                  b64encode(contents.encode('utf8')).decode('utf8'),
    #                  SUBLIME_EVERNOTE_COMMENT_END))
    #     content += hidden
    #     content += body
    #     LOG(body)
    #     content += '</en-note>'
    #     note.title = meta.get("title", note.title)
    #     tags = meta.get("tags", note.tagNames)
    #     if tags is not None:
    #         tags = extractTags(tags)
    #     LOG(tags)
    #     note.tagNames = tags
    #     note.content = content
    #     if "notebook" in meta:
    #         notebooks = self.get_notebooks()
    #         for nb in notebooks:
    #             if nb.name == meta["notebook"]:
    #                 note.notebookGuid = nb.guid
    #                 break
    #     return note



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



token = os.environ['EVERNOTE_DEV_TOKEN']
noteStoreUrl = os.environ['EVERNOTE_DEV_NOTESTORE_URL']

ev = Evernote(token, noteStoreUrl)
notebooks = ev.getNotebooks()
# noteStoreHttpClient = THttpClient.THttpClient(noteStoreUrl)
# noteStoreHttpClient.setCustomHeaders(USER_AGENT)
# noteStoreProtocol = TBinaryProtocol.TBinaryProtocol(noteStoreHttpClient)
# noteStore = NoteStore.Client(noteStoreProtocol)
# notebooks = noteStore.listNotebooks(token)
print(notebooks)

# ev = EvernoteDo()
# ev.connect(None)
# print(ev.get_notebooks())
print("oi")