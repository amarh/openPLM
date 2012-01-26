import os
import sys
import shutil
import json
import urllib
import webbrowser
import zipfile
import tempfile

# poster makes it possible to send http request with files
# sudo easy_install poster
from poster.encode import multipart_encode
import poster.streaminghttp as shttp


import urllib2

import traceback
import unohelper

from com.sun.star.beans import PropertyValue
from com.sun.star.task import XJobExecutor
from com.sun.star.awt import XActionListener, XItemListener, WindowDescriptor
from com.sun.star.awt.InvalidateStyle import UPDATE
from com.sun.star.awt.tree import XTreeExpansionListener
from com.sun.star.view import XSelectionChangeListener
from com.sun.star.view.SelectionType import SINGLE
from com.sun.star.util import CloseVetoException
from com.sun.star.frame.FrameSearchFlag import CREATE, ALL 

 
from com.sun.star.awt.WindowClass import MODALTOP
from com.sun.star.awt.VclWindowPeerAttribute import OK, OK_CANCEL, YES_NO, YES_NO_CANCEL, \
                                       RETRY_CANCEL, DEF_OK, DEF_CANCEL, DEF_RETRY, DEF_YES, DEF_NO

# Show a message box with the UNO based toolkit
def MessageBox(ParentWin, MsgText, MsgTitle, MsgType="messbox", MsgButtons=OK):
    MsgType = MsgType.lower()
    #available msg types
    MsgTypes = ("messbox", "infobox", "errorbox", "warningbox", "querybox")
    if MsgType not in MsgTypes:
        MsgType = "messbox"
    #describe window properties.
    aDescriptor = WindowDescriptor()
    aDescriptor.Type = MODALTOP
    aDescriptor.WindowServiceName = MsgType
    aDescriptor.ParentIndex = -1
    aDescriptor.Parent = ParentWin
    aDescriptor.WindowAttributes = MsgButtons
    tk = ParentWin.getToolkit()
    msgbox = tk.createWindow(aDescriptor)
    msgbox.setMessageText(MsgText)
    if MsgTitle :
        msgbox.setCaptionText(MsgTitle)
    return msgbox.execute()

def show_error(message, parent):
    MessageBox(parent, message, "Error", "errorbox")


def doc_to_type(doc):
    services = doc.SupportedServiceNames
    types = {'com.sun.star.text.TextDocument' : 'swriter',
             'com.sun.star.sheet.SpreadsheetDocument' : 'scalc',
             'com.sun.star.presentation.PresentationDocument' : 'simpress',
             'com.sun.star.drawing.DrawingDocument' : 'sdraw'}
    for key in types:
        if key in services:
            return types[key]
    return "swriter"


def close(gdoc, desktop):
    enum = desktop.getComponents().createEnumeration()
    cpt = 0
    while enum.hasMoreElements():
        cpt += 1
        enum.nextElement()
    gdoc.setModified(False)
    if cpt == 1:
        name = "_default"
        type = doc_to_type(gdoc)
        desktop.loadComponentFromURL("private:factory/" + type, name,
                                     CREATE | ALL, ())
    try:
        gdoc.close(True)
    except CloseVetoException:
        pass

class OpenPLMPluginInstance(object):
    
    #: location of openPLM server
    SERVER = "http://localhost:8000/"
    #: OpenPLM main directory
    OPENPLM_DIR = os.path.join(os.path.expanduser("~"), ".openplm")
    #: directory where files are stored
    PLUGIN_DIR = os.path.join(OPENPLM_DIR, "openoffice")
    #: gedit plugin configuration file
    CONF_FILE = os.path.join(PLUGIN_DIR, "conf.json")

    def __init__(self):
        
        self.opener = urllib2.build_opener(shttp.StreamingHTTPHandler(),
                                           shttp.StreamingHTTPRedirectHandler(),
                                           shttp.StreamingHTTPSHandler(),
                                           urllib2.HTTPCookieProcessor())
        self.opener.addheaders = [('User-agent', 'openplm')]
        self.username = ""
        self.desktop = None
        self.documents = {}
        self.disable_menuitems()

        data = self.get_conf_data()
        if "server" in data:
            type(self).SERVER = data["server"]

        try:
            os.makedirs(self.PLUGIN_DIR, 0700)
        except os.error:
            pass

    def set_desktop(self, desktop):
        self.desktop = desktop
        self.window = desktop.getCurrentFrame().ContainerWindow

    def disable_menuitems(self):
        pass

    def enable_menuitems(self):
        pass

    def login(self, username, password):
        """
        Open a login dialog and connect the user
        """
        
        self.username = username
        self.password = password

        data = dict(username=self.username, password=self.password)
        res = self.get_data("api/login/", data)
        if res["result"] == "ok":
            #self._action_group2.set_sensitive(True)
            self.load_managed_files()
            self.enable_menuitems()
        else:
            self.disable_menuitems()
            raise ValueError(res["error"])

    def create(self, data, filename, unlock):
        res = self.get_data("api/create/", data)
        if not filename:
            return False, "Bad file name"
        if res["result"] != "ok":
            return False, res["error"]
        else:
            doc = res["object"]
            # create a new doc
            rep = os.path.join(self.PLUGIN_DIR, doc["type"], doc["reference"],
                               doc["revision"])
            try:
                os.makedirs(rep, 0700)
            except os.error:
                # directory already exists, just ignores the exception
                pass
            gdoc = self.desktop.getCurrentComponent()
            path = os.path.join(rep, filename)
            gdoc.storeAsURL(unohelper.systemPathToFileUrl(path), ())
            doc_file = self.upload_file(doc, path)
            self.add_managed_file(doc, doc_file, path)
            self.load_file(doc, doc_file["id"], path)
            if not unlock:
                self.get_data("api/object/%s/lock/%s/" % (doc["id"], doc_file["id"]))
            else:
                self.send_thumbnail(gdoc)
                self.forget(gdoc, False)
            return True, ""

    def get_data(self, url, data=None, show_errors=True, reraise=False):
        data_enc = urllib.urlencode(data) if data else None
        try:
            return json.load(self.opener.open(self.SERVER + url, data_enc)) 
        except urllib2.URLError as e:
            if show_errors:
                message = e.reason if hasattr(e, "reason") else ""
                if not isinstance(message, basestring):
                    message = str(e)
                show_error(u"Can not open '%s':>\n\t%s" % \
                           (url, unicode(message, "utf-8")), self.window)
            if reraise:
                raise
            else:
                return {"result" : "error", "error" : ""}

    def upload_file(self, doc, path):
        url = self.SERVER + "api/object/%s/add_file/" % doc["id"]
        datagen, headers = multipart_encode({"filename": open(path, "rb")})
        # Create the Request object
        request = urllib2.Request(url, datagen, headers)
        res = json.load(self.opener.open(request))
        return res["doc_file"]

    def download(self, doc, doc_file):
        f = self.opener.open(self.SERVER + "file/%s/" % doc_file["id"])
        rep = os.path.join(self.PLUGIN_DIR, doc["type"], doc["reference"],
                           doc["revision"])
        try:
            os.makedirs(rep, 0700)
        except os.error:
            # directory already exists, just ignores the exception
            pass
        dst_name = os.path.join(rep, doc_file["filename"])
        dst = open(dst_name, "wb")
        shutil.copyfileobj(f, dst)
        f.close()
        dst.close()
        self.add_managed_file(doc, doc_file, dst_name)
        self.load_file(doc, doc_file["id"], dst_name)

    def attach_to_part(self, doc, part_id):
        res = self.get_data("api/object/%s/attach_to_part/%s/" % (doc["id"], part_id))
        if res["result"] == "ok":
            url = self.SERVER + "object/%s/%s/%s/parts" % (doc["type"],
                    doc["reference"], doc["revision"])
            webbrowser.open_new_tab(url)
        else:
            show_error("Can not attach\n%s" % res.get('error', ''), self.window)

    def check_out(self, doc, doc_file):
        self.get_data("api/object/%s/checkout/%s/" % (doc["id"], doc_file["id"]))
        self.download(doc, doc_file)

    def add_managed_file(self, document, doc_file, path):
        data = self.get_conf_data()
        documents = data.get("documents", {})
        doc = documents.get(str(document["id"]), dict(document))
        files = doc.get("files", {})
        files[doc_file["id"]] = path
        doc["files"] = files
        documents[doc["id"]] = doc
        data["documents"] = documents
        self.save_conf(data)

    def save_conf(self, data):
        f = open(self.CONF_FILE, "w")
        json.dump(data, f)
        f.close()
    
    def get_conf_data(self):
        try:
            if not os.path.exists(self.PLUGIN_DIR):
                os.makedirs(self.PLUGIN_DIR, 0700)
            if not os.path.exists(self.CONF_FILE):
                return {}
            with open(self.CONF_FILE, "r") as f:
                try:
                    return json.load(f)
                except ValueError:
                    # empty/bad config file
                    return {}
        except IOError as e:
            # file does not exist
            show_error(e, self.window)
            return {}
    
    def set_server(self, url):
        data = self.get_conf_data()
        data["server"] = url
        type(self).SERVER = url
        self.save_conf(data)
        if self.username:
            try:
                self.login(self.username, self.password)
            except ValueError:
                pass

    def get_managed_files(self):
        data = self.get_conf_data()
        files = []
        for doc in data.get("documents", {}).itervalues():
            files.extend((d, doc) for d in doc.get("files", {}).items())
        return files
   
    def forget(self, gdoc=None, delete=True, close_doc=False):
        gdoc = gdoc or self.desktop.getCurrentComponent()
        if gdoc and gdoc.URL in self.documents:
            doc = self.documents[gdoc.URL]["openplm_doc"]
            doc_file_id = self.documents[gdoc.URL]["openplm_file_id"]
            path = self.documents[gdoc.URL]["openplm_path"]
            del self.documents[gdoc.URL]
            data = self.get_conf_data()
            del data["documents"][str(doc["id"])]["files"][str(doc_file_id)]
            if not data["documents"][str(doc["id"])]["files"]:
                del data["documents"][str(doc["id"])]
            self.save_conf(data)
            if close_doc:
                close(gdoc, self.desktop)
            if delete and os.path.exists(path):
                os.remove(path)

    def load_managed_files(self):
        for (doc_file_id, path), doc in self.get_managed_files():
            self.load_file(doc, doc_file_id, path)

    def load_file(self, doc, doc_file_id, path):
        document = self.desktop.loadComponentFromURL(unohelper.systemPathToFileUrl(path),
                                                     "_default", 0, ())
        if not document:
            # document may be a simple text file
            op1 = PropertyValue()
            op1.Name = 'InteractionHandler'
            op1.Value = self.smgr.createInstance("com.sun.star.task.InteractionHandler") 
            document = self.desktop.loadComponentFromURL(unohelper.systemPathToFileUrl(path),
                "_default", 0, (op1,))
        if not document:
            show_error("Can not load %s" % path, self.window)
            return
        self.documents[document.URL] = dict(openplm_doc=doc,
            openplm_file_id=doc_file_id, openplm_path=path)
        document.setTitle(document.getTitle() + " / %(name)s rev. %(revision)s" % doc)
        return document

    def check_in(self, gdoc, unlock, save=True):
        if gdoc and gdoc.URL in self.documents:
            doc = self.documents[gdoc.URL]["openplm_doc"]
            doc_file_id = self.documents[gdoc.URL]["openplm_file_id"]
            path = self.documents[gdoc.URL]["openplm_path"]
            def func():
                # headers contains the necessary Content-Type and Content-Length>
                # datagen is a generator object that yields the encoded parameters
                datagen, headers = multipart_encode({"filename": open(path, "rb")})
                # Create the Request object
                url = self.SERVER + "api/object/%s/checkin/%s/" % (doc["id"], doc_file_id)
                request = urllib2.Request(url, datagen, headers)
                res = self.opener.open(request)
                if not unlock:
                    self.get_data("api/object/%s/lock/%s/" % (doc["id"], doc_file_id))
                else:
                    self.send_thumbnail(gdoc)
                    self.forget(gdoc, False)
            if save:
                gdoc.store()
                func()
            else:
                func()
        else:
            show_error('Can not check in : file not in openPLM', self.window)

    def send_thumbnail(self, gdoc):
        doc = self.documents[gdoc.URL]["openplm_doc"]
        doc_file_id = self.documents[gdoc.URL]["openplm_file_id"]
        path = self.documents[gdoc.URL]["openplm_path"]
        try:
            zp = zipfile.ZipFile(path, 'r')
            image = zp.open("Thumbnails/thumbnail.png")
            f = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            f.write(image.read())
            f.close()
            datagen, headers = multipart_encode({"filename": open(f.name, "rb")})
            # Create the Request object
            url = self.SERVER + "api/object/%s/add_thumbnail/%s/" % (doc["id"], doc_file_id)
            request = urllib2.Request(url, datagen, headers)
            res = self.opener.open(request)
            image.close()
            os.remove(f.name)
            zp.close()
        except KeyError:
            zp.close()
        except (IOError, zipfile.BadZipfile):
            pass

    def revise(self, gdoc, revision, unlock):
        if gdoc and gdoc.URL in self.documents:
            doc = self.documents[gdoc.URL]["openplm_doc"]
            doc_file_id = self.documents[gdoc.URL]["openplm_file_id"]
            path = self.documents[gdoc.URL]["openplm_path"]
            res = self.get_data("api/object/%s/revise/" % doc["id"],
                                {"revision" : revision})
            new_doc = res["doc"]
            name = os.path.basename(gdoc.URL)
            doc_file = None
            for f in res["files"]:
                if f["filename"] == name:
                    doc_file = f
                    break
            # create a new doc
            rep = os.path.join(self.PLUGIN_DIR, doc["type"], doc["reference"],
                               revision)
            try:
                os.makedirs(rep, 0700)
            except os.error:
                # directory already exists, just ignores the exception
                pass
            
            gdoc.store()
            new_path = os.path.join(rep, name)
            shutil.copy(path, new_path)
            self.forget(gdoc, delete=False)
            gd = self.load_file(new_doc, doc_file["id"], new_path)
            self.add_managed_file(new_doc, doc_file, new_path)
            self.check_in(gd, unlock, False)
            self.get_data("api/object/%s/unlock/%s/" % (doc["id"], doc_file_id))
            return gd
        else:
            show_error("Can not revise : file not in openPLM", self.window)

    def check_is_locked(self, doc_id, file_id, error_dialog=True):
        """
        Return True if file which is is *file_id* is locked.

        If it is unlocked and *error_dialog* is True, an ErrorDialog is 
        displayed
        """
        locked = self.get_data("api/object/%s/islocked/%s/" % (doc_id, file_id))["locked"]
        if not locked and error_dialog:
            show_error("File is not locked, action not allowed", self.window)
        return locked


PLUGIN = OpenPLMPluginInstance()

class Dialog(unohelper.Base, XActionListener):

    TITLE = "..."
    ACTION_NAME = "..."

    WIDTH = 200
    HEIGHT = 300
    PAD = 5
    ROW_HEIGHT = 15
    ROW_PAD = 2
    
    def __init__(self, ctx):
        self.ctx = ctx
        self.msg = None
        smgr = self.ctx.ServiceManager
        self.dialog = smgr.createInstanceWithContext(
            'com.sun.star.awt.UnoControlDialogModel', self.ctx)
        self.dialog.Width = self.WIDTH
        self.dialog.Height = self.HEIGHT
        self.dialog.Title = self.TITLE
   
    def addWidget(self, name, type, x, y, w, h, **kwargs):
        if "." in type:
            widget = self.dialog.createInstance('com.sun.star.awt.%s' % type)
        else:
            widget = self.dialog.createInstance('com.sun.star.awt.UnoControl%sModel' % type)
        widget.Name = name
        widget.PositionX = int(x)
        widget.PositionY = int(y)
        widget.Width = int(w)
        widget.Height = int(h)
        for k, w in kwargs.items():
            setattr(widget, k, w)
        self.dialog.insertByName(name, widget)
        return widget

    def get_value(self, entry, field):
        value = None
        if hasattr(entry, "Text"):
            value = entry.Text.encode("utf-8")
        elif hasattr(entry, 'SelectedItems'):
            if not field:
                value = entry.StringItemList[entry.SelectedItems[0]]
            else:
                value = field["choices"][entry.SelectedItems[0]][0]
        elif hasattr(entry, "State"):
            value = bool(entry.State)
        return value

    def set_value(self, entry, value, field=None):
        if hasattr(entry, "Text"):
            entry.Text = value or ''
        elif hasattr(entry, 'SelectedItems'):
            choices = [c[0] for c in field["choices"]]
            entry.SelectedItems = (choices.index(value or ''), )
        elif hasattr(entry, "State"):
            entry.State = int(value or 0)
    
    def field_to_widget(self, field, x, y, w, h):
        type = ""
        attributes = {}
        if field["type"] in ("text", "int", "decimal", "float"):
            type = "Edit"
        elif field["type"] == "boolean":
            type = "CheckBox"
        elif field["type"] == "choice":
            type = "ListBox"
            choices = field["choices"]
            if [u'', u'---------'] not in choices:
                choices = ([u'', u'---------'],) + tuple(choices)
            field["choices"] = choices
            values = []
            for _, c in choices:
                values.append(c)
            attributes['StringItemList'] = tuple(values)
            attributes['Dropdown'] = True
            attributes['MultiSelection'] = False
        if type == "":
            raise ValueError()
        widget = self.addWidget("%s_entry" % field["name"], type, x, y, w, h,
                                **attributes) 
        self.set_value(widget, field["initial"], field)
        return widget

    def run(self):
        pass

    def actionPerformed(self, actionEvent):
        pass

class LoginDialog(Dialog):
    HEIGHT = 105
    TITLE = 'Login'
    
    def run(self):
        smgr = self.ctx.ServiceManager
        label = self.addWidget('Username', 'FixedText', 5, 10, 60, 14,
                               Label='Username:')
        self.username = self.addWidget('UsernameEntry', 'Edit', 90, 10, 100, 14)
        label = self.addWidget('password', 'FixedText', 5, 30, 60, 14,
                               Label='Password:')
        self.password = self.addWidget('PasswordEntry', 'Edit', 90, 30, 100, 14,
                                       EchoChar=ord('*'))

        button = self.addWidget('login', 'Button', 55, 85, 50, 14,
                                Label='Login')
        self.container = smgr.createInstanceWithContext(
            'com.sun.star.awt.UnoControlDialog', self.ctx)
        self.container.setModel(self.dialog)
        self.container.getControl('login').addActionListener(self)
        toolkit = smgr.createInstanceWithContext(
            'com.sun.star.awt.ExtToolkit', self.ctx)
        self.container.setVisible(False)
        self.container.createPeer(toolkit, None)
        self.container.execute()

    def actionPerformed(self, actionEvent):
        try:
            username = self.username.Text
            password = self.password.Text
            try:
                PLUGIN.login(username, password)
                self.container.endExecute()
            except ValueError, e:
                show_error("Can not login: %s" % str(e), self.container.getPeer())
        except:
            traceback.print_exc()

class ConfigureDialog(Dialog):

    TITLE = "Conffigure"
    HEIGHT = 70

    def run(self):
        smgr = self.ctx.ServiceManager
        label = self.addWidget('url', 'FixedText', 5, 10, 80, 14,
                               Label="OpenPLM server's location:")
        self.url_entry = self.addWidget('UrlEntry', 'Edit', 90, 10, 100, 14)
        self.url_entry.Text = PLUGIN.SERVER

        button = self.addWidget('configure', 'Button', 85, 40, 50, 14,
                                Label='Configure')
        self.container = smgr.createInstanceWithContext(
            'com.sun.star.awt.UnoControlDialog', self.ctx)
        self.container.setModel(self.dialog)
        self.container.getControl('configure').addActionListener(self)
        toolkit = smgr.createInstanceWithContext(
            'com.sun.star.awt.ExtToolkit', self.ctx)
        self.container.setVisible(False)
        self.container.createPeer(toolkit, None)
        self.container.execute()

    def actionPerformed(self, actionEvent):
        try:
            url = self.url_entry.Text
            PLUGIN.set_server(url)
            self.container.endExecute()
        except:
            traceback.print_exc()

class SearchDialog(Dialog, XItemListener,
                   XTreeExpansionListener, XSelectionChangeListener):

    TITLE = "Search"
    SEARCH_SUFFIX = ""
    ACTION_NAME = "..."
    TYPE = "Document"
    TYPES_URL = "api/docs/"
    ALL_FILES = False
    EXPAND_FILES = True

    WIDTH = 200
    HEIGHT = 300
    PAD = 5
    ROW_HEIGHT = 15
    ROW_PAD = 2

    def get_position(self, row, column):
        if column == 1:
            x = self.PAD
            w = (self.WIDTH - 3 * self.PAD) / 3
        else:
            x = self.PAD * 2 + (self.WIDTH-3*self.PAD) *1/3
            w = (self.WIDTH - 3 * self.PAD) * 2 / 3
        y = self.PAD + (self.ROW_HEIGHT + self.ROW_PAD) * row
        return x, y, w, self.ROW_HEIGHT

    def run(self):
        
        docs = PLUGIN.get_data(self.TYPES_URL)
        self.types = docs["types"]

        smgr = self.ctx.ServiceManager
        
        fields = [("type", 'ListBox'),
                 ]
        self.fields = []
        for i, (text, entry) in enumerate(fields): 
            x, y, w, h = self.get_position(i, 1)
            label = self.addWidget('%s_label' % text, 'FixedText', x, y, w, h,
                               Label = '%s:' % text.capitalize())
            x, y, w, h = self.get_position(i, 2)
            widget = self.addWidget('%s_entry' % text, entry, x, y, w, h)
            self.fields.append((text, widget))

        self.type_entry = self.fields[0][1]
        self.type_entry.StringItemList = tuple(self.types)
        self.type_entry.SelectedItems = (self.types.index(self.TYPE),)
        self.type_entry.Dropdown = True
        self.type_entry.MultiSelection = False
        
        self.advanced_fields = []
        self.display_fields(self.TYPE)
        
        x, y, w, h = self.get_position(len(self.fields)+len(self.advanced_fields)+1, 2)
        self.search_button = self.addWidget('search_button', 'Button', x, y, w, h,
                                Label = 'Search')
        
        self.tree = self.addWidget('tree', 'tree.TreeControlModel', 
                                   self.PAD, y + h +5, self.WIDTH-2*self.PAD, self.HEIGHT- (y+  2*h + 20))

        self.tree_model = self.createService("com.sun.star.awt.tree.MutableTreeDataModel")
        self.tree_root = self.tree_model.createNode("Results", True)
        self.tree_model.setRoot(self.tree_root)
        self.tree.DataModel = self.tree_model
        self.tree.SelectionType = SINGLE
        
        y = self.HEIGHT - self.PAD - h
        self.action_button = self.addWidget('action_button', 'Button', x, y, w, h,
                                Label = self.ACTION_NAME)

        self.container = smgr.createInstanceWithContext(
            'com.sun.star.awt.UnoControlDialog', self.ctx)
        self.container.setModel(self.dialog)
        self.container.getControl('search_button').addActionListener(self)
        self.container.getControl('action_button').addActionListener(self)
        self.container.getControl('type_entry').addItemListener(self)
        self.container.getControl('tree').addTreeExpansionListener(self)
        toolkit = smgr.createInstanceWithContext(
            'com.sun.star.awt.ExtToolkit', self.ctx)
        self.container.setVisible(False)
        self.container.createPeer(toolkit, None)
        self.container.execute()

    def createService(self, cClass):
        return self.ctx.ServiceManager.createInstanceWithContext(cClass, self.ctx)

    def display_fields(self, typename):
        fields = PLUGIN.get_data("api/search_fields/%s/" % typename)["fields"]
        temp = {}
        for field, entry in self.advanced_fields:
            name = field["name"]
            temp[name] = self.get_value(entry, field)
            self.container.getControl(entry.Name).setVisible(False)
            entry.dispose()
            self.dialog.removeByName(entry.Name)
            label = self.dialog.getByName("%s_label" % name)
            self.container.getControl(label.Name).setVisible(False)
            label.dispose()
            self.dialog.removeByName(label.Name)
        self.advanced_fields = []
        row = len(self.fields)
        for i, field in enumerate(fields):
            text, name = field["label"], field["name"]
            x, y, w, h = self.get_position(i + row, 1)
            label = self.addWidget('%s_label' % name, 'FixedText',
                                   x, y, w, h, Label='%s:' % text.capitalize())
            x, y, w, h = self.get_position(i + row, 2)
            widget = self.field_to_widget(field, x, y, w, h)
            if name in temp:
                self.set_value(widget, temp[name], field)
            self.advanced_fields.append((field, widget))
        if hasattr(self, 'container'):
            self.container.getPeer().invalidate(UPDATE|1)
            x, y, w, h = self.get_position(row + i + 2, 2)
            self.search_button.PositionX = x
            self.search_button.PositionY = y
            pos = self.tree.PositionY
            self.tree.PositionY = y + h + 5
            self.tree.Height -= self.tree.PositionY - pos

    def actionPerformed(self, actionEvent):
        try:
            if actionEvent.Source == self.container.getControl('search_button'):
                self.search()
            elif actionEvent.Source == self.container.getControl('action_button'):
                node =  self.container.getControl('tree').getSelection()
                doc = self.nodes[node.getParent().getDisplayValue()]
                doc_file = doc["files"][node.getParent().getIndex(node)]
                del doc["files"]
                self.do_action(doc, doc_file)
        except:
            traceback.print_exc()

    def itemStateChanged(self, itemEvent):
        try:
            typename = self.types[self.type_entry.SelectedItems[0]]
            self.display_fields(typename)
        except:
            traceback.print_exc()

    def requestChildNodes(self, event):
        res = self.nodes[event.Node.getDisplayValue()]
        suffix = "all/" if self.ALL_FILES else ""
        url = "api/object/%s/files/%s" % (res["id"], suffix)
        files = PLUGIN.get_data(url)["files"]
        if "files" in res:
            return
        res["files"] = files
        for f in files:
            node = self.tree_model.createNode(f["filename"], False)
            event.Node.appendChild(node)
        self.container.getPeer().invalidate(UPDATE|1)

    def display_results(self, results):
        self.nodes = {}
        while self.tree_root.getChildCount():
            self.tree_root.removeChildByIndex(0)
        for res in results:
            text = "%(reference)s|%(type)s|%(revision)s : %(name)s" % res
            node = self.tree_model.createNode(text, self.EXPAND_FILES)
            self.tree_root.appendChild(node)
            self.nodes[node.getDisplayValue()] = res
        self.container.getPeer().invalidate(UPDATE|1)

    def search(self, *args):
        data = {}
        for text, entry in self.fields:
            value = self.get_value(entry, None)
            if value:
                data[text] = value
        for field, entry in self.advanced_fields:
            value = self.get_value(entry, field)
            if value:
                data[field["name"]] = value
        get = urllib.urlencode(data)
        self.display_results(PLUGIN.get_data("api/search/%s?%s" % (self.SEARCH_SUFFIX, get))["objects"])

    def do_action(self, doc, doc_file):
        print doc, doc_file

class CheckOutDialog(SearchDialog):
    TITLE = "Check-out..."
    ACTION_NAME = "Check-out"

    def do_action(self, doc, doc_file):
        PLUGIN.check_out(doc, doc_file)
        self.container.endExecute()

class DownloadDialog(SearchDialog):
    TITLE = "Download..."
    ACTION_NAME = "Download"
    ALL_FILES = True
    SEARCH_SUFFIX = "false/true/"

    def do_action(self, doc, doc_file):
        PLUGIN.download(doc, doc_file)
        self.container.endExecute()

class CheckInDialog(Dialog):

    TITLE = "Check-in..."
    ACTION_NAME = "Check-in"
    WIDTH = 200
    HEIGHT = 100

    def __init__(self, ctx, doc, name):
        Dialog.__init__(self, ctx)
        self.doc = doc
        self.name = name

    def run(self):
        smgr = self.ctx.ServiceManager
        
        text = "%s|%s|%s" % (self.doc["reference"], self.doc["revision"],
                                       self.doc["type"])

        label = self.addWidget('label', 'FixedText', 5, 10, 60, 14,
                               Label = text)
        self.unlock_button = self.addWidget('unlock_button', 'CheckBox',
                                            5, 30, 100, 14, Label='Unlock ?')

        button = self.addWidget('action', 'Button', 55, 85, 50, 14,
                                Label=self.ACTION_NAME)
        self.container = smgr.createInstanceWithContext(
            'com.sun.star.awt.UnoControlDialog', self.ctx)
        self.container.setModel(self.dialog)
        self.container.getControl('action').addActionListener(self)
        toolkit = smgr.createInstanceWithContext(
            'com.sun.star.awt.ExtToolkit', self.ctx)
        self.container.setVisible(False)
        self.container.createPeer(toolkit, None)
        self.container.execute()

    def actionPerformed(self, actionEvent):
        try:
            desktop = self.ctx.ServiceManager.createInstanceWithContext(
                'com.sun.star.frame.Desktop', self.ctx)
            doc = desktop.getCurrentComponent()
            unlock = self.get_value(self.unlock_button, None)
            PLUGIN.check_in(doc, unlock)
            self.container.endExecute()
        except:
            traceback.print_exc()

class ReviseDialog(Dialog):

    TITLE = "Revise..."
    ACTION_NAME = "Revise"
    WIDTH = 200
    HEIGHT = 100

    def __init__(self, ctx, doc, name, revision):
        Dialog.__init__(self, ctx)
        self.doc = doc
        self.name = name
        self.revision = revision
        self.gdoc = None

    def run(self):
        smgr = self.ctx.ServiceManager
        
        text = "%s|" % self.doc["reference"]
        label = self.addWidget('ref', 'FixedText', 5, 10, 60, 14,
                               Label = text)
        self.revision_entry = self.addWidget("rev_button", "Edit", 70, 10, 60, 14,
                                              Text=self.revision)
        text = "|%s" % self.doc["type"]
        label = self.addWidget('type', 'FixedText', 135, 10, 60, 14,
                               Label=text)
        self.unlock_button = self.addWidget('unlock_button', 'CheckBox',
                                            5, 30, 100, 14, Label='Unlock ?')

        button = self.addWidget('action', 'Button', 55, 85, 50, 14,
                                Label=self.ACTION_NAME)
        text = "Warning, old revision file will be automatically unlocked!"
        label = self.addWidget('warning', 'FixedText', 5, 45, 150, 14,
                               Label=text)
        self.container = smgr.createInstanceWithContext(
            'com.sun.star.awt.UnoControlDialog', self.ctx)
        self.container.setModel(self.dialog)
        self.container.getControl('action').addActionListener(self)
        toolkit = smgr.createInstanceWithContext(
            'com.sun.star.awt.ExtToolkit', self.ctx)
        self.container.setVisible(False)
        self.container.createPeer(toolkit, None)
        self.container.execute()

    def actionPerformed(self, actionEvent):
        try:
            desktop = self.ctx.ServiceManager.createInstanceWithContext(
                'com.sun.star.frame.Desktop', self.ctx)
            self.container.endExecute()
            self.gdoc = PLUGIN.revise(desktop.getCurrentComponent(),
                          self.get_value(self.revision_entry, None),
                          self.get_value(self.unlock_button, None))
        except:
            traceback.print_exc()

class AttachToPartDialog(SearchDialog):
    TITLE = "Attach to part"
    ACTION_NAME = "Attach"
    SEARCH_SUFFIX = "false/"
    TYPE = "Part"
    TYPES_URL = "api/parts/"
    EXPAND_FILES = False

    def __init__(self, ctx, doc):
        SearchDialog.__init__(self, ctx)
        self.doc = doc
    
    def do_action(self, part):
        PLUGIN.attach_to_part(self.doc, part["id"])
        self.container.endExecute()
    
    def actionPerformed(self, actionEvent):
        try:
            if actionEvent.Source == self.container.getControl('search_button'):
                self.search()
            elif actionEvent.Source == self.container.getControl('action_button'):
                node =  self.container.getControl('tree').getSelection()
                doc = self.nodes[node.getDisplayValue()]
                self.do_action(doc)
        except:
            traceback.print_exc()

class CreateDialog(SearchDialog):

    TITLE = "Create a document..."
    ACTION_NAME = "Create"
    TYPE = "Document"
    TYPES_URL = "api/docs/"

    WIDTH = 200
    HEIGHT = 200
    PAD = 5
    ROW_HEIGHT = 15
    ROW_PAD = 2

    def run(self):
        self.doc_created = False
        docs = PLUGIN.get_data(self.TYPES_URL)
        self.types = docs["types"]

        smgr = self.ctx.ServiceManager
        
        fields = [("type", 'ListBox'),
                 ]
        self.fields = []
        for i, (text, entry) in enumerate(fields): 
            x, y, w, h = self.get_position(i, 1)
            label = self.addWidget('%s_label' % text, 'FixedText', x, y, w, h,
                               Label = '%s:' % text.capitalize())
            x, y, w, h = self.get_position(i, 2)
            widget = self.addWidget('%s_entry' % text, entry, x, y, w, h)
            self.fields.append((text, widget))

        self.type_entry = self.fields[0][1]
        self.type_entry.StringItemList = tuple(self.types)
        self.type_entry.SelectedItems = (self.types.index(self.TYPE),)
        self.type_entry.Dropdown = True
        self.type_entry.MultiSelection = False
        
        self.advanced_fields = []
        self.display_fields(self.TYPE)
       
        row = len(self.fields) + len(self.advanced_fields)
        x, y, w, h = self.get_position(row, 1)
        self.filename_label = self.addWidget('filenameLabel', 'FixedText',
                                             x, y, w, h, Label="Filename")
        x, y, w, h = self.get_position(row, 2)
        self.filename_entry = self.addWidget('filename', 'Edit', x, y, w, h)
        x, y, w, h = self.get_position(row + 1, 1)
        self.unlock_button = self.addWidget('unlock', 'CheckBox', x, y, w, h,
                                Label="Unlock ?")
        x, y, w, h = self.get_position(row + 2, 2)
        self.action_button = self.addWidget('action_button', 'Button', x, y, w, h,
                                Label=self.ACTION_NAME)

        self.container = smgr.createInstanceWithContext(
            'com.sun.star.awt.UnoControlDialog', self.ctx)
        self.container.setModel(self.dialog)
        self.container.getControl('action_button').addActionListener(self)
        self.container.getControl('type_entry').addItemListener(self)
        toolkit = smgr.createInstanceWithContext(
            'com.sun.star.awt.ExtToolkit', self.ctx)
        self.container.setVisible(False)
        self.container.createPeer(toolkit, None)
        self.container.execute()

    def display_fields(self, typename):
        fields = PLUGIN.get_data("api/creation_fields/%s/" % typename)["fields"]
        temp = {}
        for field, entry in self.advanced_fields:
            name = field["name"]
            temp[name] = self.get_value(entry, field)
            self.container.getControl(entry.Name).setVisible(False)
            entry.dispose()
            self.dialog.removeByName(entry.Name)
            label = self.dialog.getByName("%s_label" % name)
            self.container.getControl(label.Name).setVisible(False)
            label.dispose()
            self.dialog.removeByName(label.Name)
        self.advanced_fields = []
        row = len(self.fields)
        for i, field in enumerate(fields):
            text, name = field["label"], field["name"]
            x, y, w, h = self.get_position(i + row, 1)
            label = self.addWidget('%s_label' % name, 'FixedText',
                                   x, y, w, h, Label='%s:' % text.capitalize())
            x, y, w, h = self.get_position(i + row, 2)
            widget = self.field_to_widget(field, x, y, w, h)
            if name in temp:
                self.set_value(widget, temp[name], field)
            self.advanced_fields.append((field, widget))
        if hasattr(self, 'container'):
            self.container.getPeer().invalidate(UPDATE|1)
            x, y, w, h = self.get_position(row + i + 1, 1)
            self.filename_label.PositionY = y
            self.filename_entry.PositionY = y
            x, y, w, h = self.get_position(row + i + 2, 1)
            self.unlock_button.PositionY = y
            x, y, w, h = self.get_position(row + i + 3, 1)
            self.action_button.PositionY = y

    def actionPerformed(self, actionEvent):
        try:
            if actionEvent.Source == self.container.getControl('action_button'):
                b, error = PLUGIN.create(self.get_creation_data(),
                              self.get_value(self.filename_entry, None),
                              self.get_value(self.unlock_button, None))
                if b:
                    self.container.endExecute()
                else:
                    show_error(error, self.container.getPeer())
                self.doc_created = b
        except:
            traceback.print_exc()

    def get_creation_data(self):
        data = {}
        for field_name, widget in self.fields:
            data[field_name] = self.get_value(widget, None)
        for field, widget in self.advanced_fields:
            data[field["name"]] = self.get_value(widget, field)
        return data

    def itemStateChanged(self, itemEvent):
        try:
            typename = self.types[self.type_entry.SelectedItems[0]]
            self.display_fields(typename)
        except:
            traceback.print_exc()


class Job(unohelper.Base, XJobExecutor):
    def __init__(self, ctx):
        self.ctx = ctx
        self.desktop = self.ctx.ServiceManager.createInstanceWithContext(
                'com.sun.star.frame.Desktop', self.ctx)
        PLUGIN.set_desktop(self.desktop)
        PLUGIN.smgr = self.ctx.ServiceManager

class OpenPLMLogin(Job):

    def trigger(self, args):
        try:
            dialog = LoginDialog(self.ctx)
            dialog.run()
        except:
            traceback.print_exc()

class OpenPLMConfigure(Job):

    def trigger(self, args):
        try:
            dialog = ConfigureDialog(self.ctx)
            dialog.run()
        except:
            traceback.print_exc()

class OpenPLMCheckOut(Job):

    def trigger(self, args):
        try:
            dialog = CheckOutDialog(self.ctx)
            dialog.run()
        except:
            traceback.print_exc()

class OpenPLMDownload(Job):
    
    def trigger(self, args):
        try:
            dialog = DownloadDialog(self.ctx)
            dialog.run()
        except:
            traceback.print_exc()

class OpenPLMForget(Job):

    def trigger(self, args):
        try:
            PLUGIN.forget(close_doc=True)
        except:
            traceback.print_exc()

class OpenPLMCheckIn(Job):
    
    def trigger(self, args):
        try:
            gdoc = self.desktop.getCurrentComponent()
            if gdoc and gdoc.URL in PLUGIN.documents:
                doc = PLUGIN.documents[gdoc.URL]["openplm_doc"]
                doc_file_id = PLUGIN.documents[gdoc.URL]["openplm_file_id"]
                path = PLUGIN.documents[gdoc.URL]["openplm_path"]
                if not doc or not PLUGIN.check_is_locked(doc["id"], doc_file_id):
                    return
                name = os.path.basename(path)
                dialog = CheckInDialog(self.ctx, doc, name)
                dialog.run() 
                if gdoc.URL not in PLUGIN.documents:
                    close(gdoc, self.desktop)
                    try:
                        os.remove(path)
                    except os.error:
                        pass
            else:
                win = gdoc.CurrentController.Frame.ContainerWindow
                show_error("Document not stored in OpenPLM", win)
        except:
            traceback.print_exc()

class OpenPLMRevise(Job):

    def trigger(self, args):
        try:
            gdoc = self.desktop.getCurrentComponent()
            if gdoc and gdoc.URL in PLUGIN.documents:
                doc = PLUGIN.documents[gdoc.URL]["openplm_doc"]
                doc_file_id = PLUGIN.documents[gdoc.URL]["openplm_file_id"]
                path = PLUGIN.documents[gdoc.URL]["openplm_path"]
                if not doc or not PLUGIN.check_is_locked(doc["id"], doc_file_id):
                    return
                revisable = PLUGIN.get_data("api/object/%s/isrevisable/" % doc["id"])["revisable"]
                if not revisable:
                    win = gdoc.CurrentController.Frame.ContainerWindow
                    show_error("Document can not be revised", win)
                    return
                res = PLUGIN.get_data("api/object/%s/nextrevision/" % doc["id"])
                revision = res["revision"]
                name = os.path.basename(path)
                dialog = ReviseDialog(self.ctx, doc, name, revision)
                dialog.run()
                if gdoc.URL not in PLUGIN.documents:
                    path = unohelper.fileUrlToSystemPath(gdoc.URL)
                    close(gdoc, self.desktop)
                    try:
                        os.remove(path)
                    except os.error:
                        pass
                if dialog.gdoc and dialog.gdoc.URL not in PLUGIN.documents:
                    path = unohelper.fileUrlToSystemPath(dialog.gdoc.URL)
                    close(dialog.gdoc, self.desktop)
                    try:
                        os.remove(path)
                    except os.error:
                        pass
            else:
                win = gdoc.CurrentController.Frame.ContainerWindow
                show_error("Document not stored in OpenPLM", win)
        except:
            traceback.print_exc()

class OpenPLMAttach(Job):

    def trigger(self, args):
        try:
            gdoc = self.desktop.getCurrentComponent()
            if gdoc and gdoc.URL in PLUGIN.documents:
                doc = PLUGIN.documents[gdoc.URL]["openplm_doc"]
                dialog = AttachToPartDialog(self.ctx, doc)
                dialog.run()
            else:
                win = gdoc.CurrentController.Frame.ContainerWindow
                show_error("Document not stored in OpenPLM", win)
        except:
            traceback.print_exc()

class OpenPLMCreate(Job):
    
    def trigger(self, args):
        try:
            gdoc = self.desktop.getCurrentComponent()
            win = gdoc.CurrentController.Frame.ContainerWindow
            if not gdoc:
                show_error("Need an opened file to create a document", win)
                return
            if gdoc.URL in PLUGIN.documents:
                show_error("Current file already attached to a document", win)
                return
            dialog = CreateDialog(self.ctx)
            resp = dialog.run()
            if dialog.doc_created and gdoc.URL not in PLUGIN.documents:
                path = unohelper.fileUrlToSystemPath(gdoc.URL)
                close(gdoc, self.desktop)
                try:
                    os.remove(path)
                except os.error:
                    pass
        except:
            traceback.print_exc()


g_ImplementationHelper = unohelper.ImplementationHelper()

for cls in (OpenPLMLogin, OpenPLMCheckOut, OpenPLMDownload, OpenPLMForget,
            OpenPLMCheckIn, OpenPLMRevise, OpenPLMAttach, OpenPLMConfigure,
            OpenPLMCreate):
    g_ImplementationHelper.addImplementation(cls,
                                         'org.example.%s' % cls.__name__,
                                         ('com.sun.star.task.Job',))

