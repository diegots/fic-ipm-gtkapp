# -*- coding: utf-8 -*-

from gi.repository import Gtk, Gdk, GLib, GObject

import view.aboutWindow
import view.dialog
import locale
import gettext
import os
import threading

APP = "library"
DIR = "locale"

locale.setlocale(locale.LC_ALL, "")
LOCALE_DIR = os.path.join(os.path.dirname(__file__), DIR)
locale.bindtextdomain(APP, LOCALE_DIR)
gettext.bindtextdomain(APP, LOCALE_DIR)
gettext.textdomain(APP)
_ = gettext.gettext
N_ = gettext.ngettext
          
tag = "mainWindow.py  : "

#
# View is the main class that hosts all the main window widgets
#
class MainWindow:
    def __init__(self, controller):
        print(tag + "Constructor init")

        self.controller = controller
        
        self.builder = Gtk.Builder()
        #Translate the app
        self.builder.set_translation_domain(APP)  
        #load the view 
        self.builder.add_from_file("view/interface.glade")  # XXX fix path build
        # Connect to events
        self.builder.connect_signals(self)  # conectar eventos        

        self.cargar_elementos()
        self.asignar_eventos()

        self.prepareTreeView()
        self.loadListStore(self)
        self.progressBar.set_visible(False)        
        self.context_id = self.status_bar.get_context_id("Statusbar example")


        # Show main windows and enter Gtk events loop
        self.principal_window.show()
        Gtk.main()

    #
    # Init stuff
    #
        
    # Widget's association
    def cargar_elementos(self):
        print(tag + "cargar_elementos")
        self.principal_window = self.builder.get_object("window1")
        self.listStore = self.builder.get_object("liststore1")
        self.treeView = self.builder.get_object("treeview2")
        self.treeTitleCol = self.builder.get_object("treeviewcolumn1")
        self.treeTitleAuth = self.builder.get_object("treeviewcolumn2")
        self.uploadBtn = self.builder.get_object("button6")
        self.aboutBtn = self.builder.get_object("button5")
        self.comboBox = self.builder.get_object("comboboxtext1")
        self.exactCheckBox = self.builder.get_object("checkbutton1")
        self.caseCheckBox = self.builder.get_object("checkbutton2")
        self.selectCheckBox = self.builder.get_object("checkbutton3")
        self.searchEntry = self.builder.get_object("searchentry1")
        self.progressBar = self.builder.get_object("progressbar1")
        self.treeSelection = self.builder.get_object("treeview-selection10")
        self.status_bar = self.builder.get_object("statusbar1")

    # Link signals with handlers
    def asignar_eventos(self):
        print(tag + "asignar_eventos")

        self.principal_window.connect("delete-event", self.on_main_quit)
        self.uploadBtn.connect       ("clicked", self.on_upload)
        self.aboutBtn.connect        ("clicked", self.on_acercaDe)
        self.comboBox.connect        ("changed", self.on_search)
        self.exactCheckBox.connect   ("toggled", self.on_search)
        self.caseCheckBox.connect    ("toggled", self.on_search)
        self.selectCheckBox.connect  ("toggled", self.on_selectItems)
        self.searchEntry.connect     ("search-changed", self.on_search)
        self.treeView.connect        ("cursor-changed", self.on_cell_changed)


    #
    # Event handlers
    #

    def on_cell_changed(self, w):

        active = self.selectCheckBox.get_active()
        if active:
            self.selectCheckBox.set_active(False)
    
    def on_upload(self, w):
        print(tag + "on_upload")
        # Get selected items
        model, pathList = self.treeSelection.get_selected_rows()
        selected = self.treeSelection.count_selected_rows()
        
        if selected == 0:
            dialog = view.dialog.MessageDialog()
            message = _('You should select at least an item')
            titleDialog = _('Update')
            dialog.info_dialog(self.principal_window, message, titleDialog)
            return
            
        data = []

        columns = self.treeView.get_columns()
        colNames = []
        for col in columns:
            colNames.append(col.get_title())

        for path in pathList:
            treeIter = model.get_iter(path) 

            colValue0 = model.get_value(treeIter, 0) 
            colName0 = colNames[0]          
            colValue1 = model.get_value(treeIter, 1) 
            colName1 = colNames[1]          

            selectedDict = {}
            selectedDict.update({colNames[0]: colValue0})
            selectedDict.update({colNames[1]: colValue1})

            data.append(selectedDict)

        self.uploadBtn.set_sensitive(False)

        # Sends data to controller
        doUpload(data, self.controller, self).start()

        # Set timeout to update progressBar and make it visible
        self.timeout_id = GObject.timeout_add(100, self.on_timeout, None)
        self.progressBar.set_visible(True)

        # Show user some info in the status bar
        status = _('Status: uploaded')
        self.status_bar.push(self.context_id, status)            

    def on_acercaDe(self, w):
        print(tag + "on_acercaDe")
        self.status_bar.push(self.context_id, "")        
        view.aboutWindow.AboutWindow()
            
    def on_search(self, w):
        print(tag + "on_search")
        keywords = self.searchEntry.get_text()
        field = self.comboBox.get_active_text()
        case = self.caseCheckBox.get_active()
        exact = self.exactCheckBox.get_active()        
        self.controller.doSearch(self, keywords, exact, case, field)        

        # Show user some info in the status bar
        status = _('Status: search results')
        self.status_bar.push(self.context_id, status)                

    def on_main_quit(self, widget, event, donnees=None):
        print(tag + "on_main_quit: destroy signal occurred")
        dialog = view.dialog.MessageDialog()
        message = _('Are you sure to close the Library Managenment?')
        titleDialog = _('Close Library Managenment')
        respuesta = dialog.question_dialog(self.principal_window, message, titleDialog)
        if not respuesta:
            return True
        else:
            Gtk.main_quit()
            return False

    def on_selectItems(self, w):
        active = self.selectCheckBox.get_active()
        if active:
            self.treeSelection.select_all()
        else:
            self.treeSelection.unselect_all()
        
    # 
    # Private functions
    #

    def on_timeout(self, user_data):
        self.progressBar.pulse()
        return True

    def uploadDone(self): 
        print(tag + "uploadDone")
        GObject.source_remove(self.timeout_id)
        self.progressBar.set_visible(False)
        self.uploadBtn.set_sensitive(True)

    def loadListStore(self, w):
        print(tag + "loadListStore: requesting data from the controller")
        self.controller.requestData(self)
        
    # Prepare the treeView to host info
    def prepareTreeView(self):
        print(tag + "prepareTreeView")

        # Renderer for the title column
        rendererTitle = Gtk.CellRendererText()
        # This is the title column
        columnTitle = _('Title')
        treeTitleCol = Gtk.TreeViewColumn(columnTitle, rendererTitle, text=0)
        # Make the column sortable
        treeTitleCol.set_sort_column_id(0)
        # Make the column user resizable
        treeTitleCol.set_resizable(True)
        # Adding the column to the treeView
        self.treeView.append_column(treeTitleCol)

        # Renderer for the author column
        rendererAuthor = Gtk.CellRendererText()
        # This is the author column
        
        columnAuthor = _('Author')
        treeAuthorCol = Gtk.TreeViewColumn(columnAuthor, rendererAuthor, text=1)
        # Make the column sortable
        treeAuthorCol.set_sort_column_id(1)
        # Adding the column to the treeView
        self.treeView.append_column(treeAuthorCol)

    #
    # Services avaibable to the controller module
    #
    def populateDataWiget(self, data):
        print(tag + "populateDataWiget")

        # Make sure listStore is empty before adding new data
        self.listStore.clear()

        for v in data:
            self.listStore.append([v["title"], v["author"]])

class doUpload(threading.Thread):
    def __init__(self, data, controller, view):
        threading.Thread.__init__(self) 
        self.data = data
        self.controller = controller
        self.view = view

    def run(self):
        print(tag + "run")
        self.controller.doUpload(self.data) # Sends data to controller
        GObject.idle_add(self.view.uploadDone)
