#!/usr/bin/env python
"""
    Sample App to illustrate table functionality.
    Created January 2014
    Copyright (C) Damien Farrell

    This program is free software; you can redistribute it and/or
    modify it under the terms of the GNU General Public License
    as published by the Free Software Foundation; either version 3
    of the License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
"""

import tkinter
from tkinter import *
from tkinter.ttk import *
from tkinter import filedialog, messagebox, simpledialog
import matplotlib
matplotlib.use('TkAgg')
import re, os, platform
import time
import pickle
from core import Table
from data import TableModel
from prefs import Preferences
import images

class TablesApp(Frame):
    """Tables app"""
    def __init__(self,parent=None,data=None,datafile=None):
        "Initialize the application."

        self.parent=parent
        if not self.parent:
            Frame.__init__(self)
            self.main=self.master
        else:
            self.main=Toplevel()
            self.master=self.main

        # Get platform into a variable
        self.currplatform=platform.system()
        if not hasattr(self,'defaultsavedir'):
            self.defaultsavedir = os.getcwd()

        self.preferences=Preferences('TablesApp',{'check_for_update':1})
        self.loadprefs()
        self.style = Style()
        available_themes = self.style.theme_names()
        self.style.theme_use('clam')

        self.main.title('Pandas Table Viewer')
        self.createMenuBar()
        self.setupGUI()

        if data != None:
            self.data = data
            self.new_project(data)
        elif datafile != None:
            self.openProject(datafile)
        else:
            self.newProject()
        
        self.main.protocol('WM_DELETE_WINDOW',self.quit)
        return

    def setupGUI(self):
        
        #self.notebook.pack(fill=BOTH, expand=1)
        self.m = PanedWindow(self.main, orient=HORIZONTAL)
        self.m.pack(fill=BOTH,expand=1)
        self.notebook = Notebook(self.main)
        self.m.add(self.notebook)
        #self.createSidePane()        
        self.setGeometry()
        return

    def createSidePane(self, width=200):
        """Side panel for various dialogs is tabbed notebook"""
        self.closeSidePane() 
        self.sidepane = Frame(self.m)  
        self.m.add(self.sidepane, weight=3)
        return self.sidepane

    def closeSidePane(self):
        """Destroy sidepine"""
        if hasattr(self, 'sidepane'):
            self.m.forget(self.sidepane)
            self.sidepane.destroy()
        return

    def addChildFrame(self, cframe, width=200):
        """Create a child frame in sidepane """
                    
        #self.sidepane.add(cframe, text=name)
        cframe.pack()
        self.__dict__[name] = cframe
        #bind frame close
        def func(evt):
            if hasattr(self, name):
                del self.__dict__[name]
   
        cframe.bind("<Destroy>", func)
        return cframe

    def createMenuBar(self):
        """Create the menu bar for the application. """
        self.menu=Menu(self.main)
        self.proj_menu={'01New':{'cmd':self.newProject},
                        '02Open':{'cmd':self.openProject},
                        '03Close':{'cmd':self.closeProject},
                        '04Save':{'cmd':self.saveProject},
                        '05Save As':{'cmd':self.saveasProject},          
                        '08Quit':{'cmd':self.quit}}
        if self.parent:
            self.proj_menu['08Return to Database']={'cmd':self.return_data}
        self.proj_menu=self.createPulldown(self.menu,self.proj_menu)
        self.menu.add_cascade(label='Project',menu=self.proj_menu['var'])

        self.sheet_menu={'01Add Sheet':{'cmd':self.addSheet},
                         '02Remove Sheet':{'cmd':self.deleteSheet},
                         '03Copy Sheet':{'cmd':self.copySheet},
                         '04Rename Sheet':{'cmd':self.renameSheet},
                         }
        self.sheet_menu=self.createPulldown(self.menu,self.sheet_menu)
        self.menu.add_cascade(label='Sheet',menu=self.sheet_menu['var'])

        self.IO_menu={'01Import from csv file':{'cmd':self.doImport},
                      '02Export to csv file':{'cmd':self.doExport},
                      }

        self.IO_menu=self.createPulldown(self.menu,self.IO_menu)
        self.menu.add_cascade(label='Import/Export',menu=self.IO_menu['var'])

        self.help_menu={'01Online Help':{'cmd':self.online_documentation},
                        '02About':{'cmd':self.about_Tables}}
        self.help_menu=self.createPulldown(self.menu,self.help_menu)
        self.menu.add_cascade(label='Help',menu=self.help_menu['var'])

        self.main.config(menu=self.menu)
        return

    def getBestGeometry(self):
        """Calculate optimal geometry from screen size"""
        ws = self.main.winfo_screenwidth()
        hs = self.main.winfo_screenheight()
        self.w=w=ws/1.4; h=hs*0.7
        x = (ws/2)-(w/2); y = (hs/2)-(h/2)
        g = '%dx%d+%d+%d' % (w,h,x,y)
        return g

    def setGeometry(self):
        self.winsize = self.getBestGeometry()
        self.main.geometry(self.winsize)
        return

    def createPulldown(self,menu,dict):
        var=Menu(menu,tearoff=0)
        items=list(dict.keys())
        items.sort()
        for item in items:
            if item[-3:]=='sep':
                var.add_separator()
            else:
                command=None
                if 'cmd' in dict[item]:
                    command=dict[item]['cmd']

                if 'sc' in dict[item]:
                    var.add_command(label='%-25s %9s' %(item[2:],dict[item]['sc']),command=command)
                else:
                    var.add_command(label='%-25s' %(item[2:]),command=command)
        dict['var']=var
        return dict

    def loadprefs(self):
        """Setup default prefs file if any of the keys are not present"""
        defaultprefs = {'textsize':14,
                         'windowwidth': 800 ,'windowheight':600}
        for prop in list(defaultprefs.keys()):
            try:
                self.preferences.get(prop)
            except:
                self.preferences.set(prop, defaultprefs[prop])

        return

    def newProject(self, data=None):
        """Create a new project"""

        #if hasattr(self,'currenttable'):
            #self.notebook.destroy()
            #self.currenttable.destroy()
        for n in self.notebook.tabs():
            self.notebook.forget(n)
        self.sheets = {}
        if data !=None:
            for s in list(data.keys()):
                sdata = data[s]          
                self.addSheet(s ,sdata)                
        else:
            #do the table adding stuff for the initial sheet
            self.addSheet('sheet1')
     
        return

    def openProject(self, filename=None):
        if filename == None:
            filename = filedialog.askopenfilename(defaultextension='.tbleprj"',
                                                      initialdir=os.getcwd(),
                                                      filetypes=[("Pickle file","*.tbleprj"),
                                                                 ("All files","*.*")],
                                                      parent=self.main)
        if os.path.isfile(filename):
            fd = open(filename)
            data = pickle.load(fd)
            fd.close()
        self.new_project(data)
        self.filename=filename
        return

    def saveProject(self):
        if not hasattr(self, 'filename'):
            self.save_as_project()
        elif self.filename == None:
            self.save_as_project()
        else:
            self.do_save_project(self.filename)

        return

    def saveasProject(self):
        """Save as a new filename"""
        filename = filedialog.asksaveasfilename(parent=self.main,
                                                defaultextension='.mpk',
                                                initialdir=self.defaultsavedir,
                                                filetypes=[("msgpk","*.mpk"),
                                                           ("All files","*.*")])
        if not filename:
            print('Returning')
            return
        self.filename=filename
        self.do_save_project(self.filename)
        return

    def closeProject(self):
        if hasattr(self,'currenttable'):         
            self.currenttable.destroy()
        return

    def addSheet(self, sheetname=None):
        """Add a new sheet"""
        def checksheet_name(name):
            if name == '':
                messagebox.showwarning("Whoops", "Name should not be blank.")
                return 0
            if name in self.sheets:
                messagebox.showwarning("Name exists", "Sheet name already exists!")
                return 0
        noshts = len(self.notebook.tabs())
        if sheetname == None:
            sheetname = simpledialog.askstring("New sheet name?", "Enter sheet name:",
                                                initialvalue='sheet'+str(noshts+1))
        checksheet_name(sheetname)        
        #Create the table
        main = PanedWindow(orient=HORIZONTAL)
        self.notebook.add(main, text=sheetname)
        f1 = Frame(main)
        main.add(f1)
        #f1.pack(side=LEFT)
        table = Table(f1)
        table.loadPrefs(self.preferences)
        table.createTableFrame()    
        f2 = Frame(main)
        main.add(f2, weight=3)            
        pf = table.showPlotFrame(f2)

        #add the table to the sheet dict
        self.sheets[sheetname] = table
        self.saved = 0
        self.currenttable = table        
   
        return sheetname

    def deleteSheet(self):
        """Delete a sheet"""
        s = self.notebook.getcurselection()
        self.notebook.delete(s)
        del self.sheets[s]
        return

    def copySheet(self, newname=None):
        """Copy a sheet"""
        newdata = self.currenttable.getModel().getData().copy()
        if newname==None:
            self.add_Sheet(None, newdata)
        else:
            self.add_Sheet(newname, newdata)
        return

    def renameSheet(self):
        """Rename a sheet"""
        s = self.notebook.getcurselection()
        newname = simpledialog.askstring("New sheet name?", 
                                          "Enter new sheet name:",
                                          initialvalue=s)
        if newname == None:
            return
        self.copy_Sheet(newname)
        self.delete_Sheet()
        return

    def setcurrenttable(self, event):
        """Set the currenttable so that menu items work with visible sheet"""
        try:
            s = self.notebook.getcurselection()
            self.currenttable = self.sheets[s]
        except:
            pass
        return

    def addRow(self):
        """Add a new row"""
        self.currenttable.addRow()
        self.saved = 0
        return

    def deleteRow(self):
        """Delete currently selected row"""
        self.currenttable.deleteRow()
        self.saved = 0
        return

    def addColumn(self):
        """Add a new column"""
        self.currenttable.addColumn()
        self.saved = 0
        return

    def deleteColumn(self):
        """Delete currently selected column in table"""
        self.currenttable.delete_Column()
        self.saved = 0
        return

    def autoAddRows(self):
        """Auto add x rows"""
        self.currenttable.autoAdd_Rows()
        self.saved = 0
        return

    def autoAddColumns(self):
        """Auto add x rows"""
        self.currenttable.autoAdd_Columns()
        self.saved = 0
        return

    def findValue(self):
        self.currenttable.findValue()
        return

    def doImport(self):
        importer = TableImporter()
  
        #just use the dialog to load and import the file
        #importdialog = importer.import_Dialog(self.main)
        self.main.wait_window(importdialog)
        model = TableModel()
        model.importDict(importer.data)
        return

    def doExport(self):

        return

    def plot(self, event=None):
        self.currenttable.plotSelected()
        return

    def about_Tables(self):
        self.ab_win=Toplevel()
        self.ab_win.geometry('+100+350')
        self.ab_win.title('About')

        logo = images.tableapp_logo()
        label = Label(self.ab_win,image=logo)
        label.image = logo
        label.grid(row=0,column=0,sticky='news',padx=4,pady=4)

        text=['Table Viewer for Pandas',
                'Copyright (C) Damien Farrell 2014-', 
                'This program is free software; you can redistribute it and/or',
                'modify it under the terms of the GNU General Public License',
                'as published by the Free Software Foundation; either version 3',
                'of the License, or (at your option) any later version.']
        row=1
        for line in text:
            tmp=Label(self.ab_win,text=line)
            tmp.grid(row=row,column=0,sticky='news',padx=4)
            row=row+1
        return

    def online_documentation(self,event=None):
        """Open the online documentation"""
        import webbrowser
        link='http://sourceforge.net/projects/tkintertable/'
        webbrowser.open(link,autoraise=1)
        return

    def quit(self):
        self.main.destroy()
        return

def main():
    "Run the application"
    import sys, os
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-f", "--file", dest="tablefile",
                        help="Open a table file", metavar="FILE")
    opts, remainder = parser.parse_args()
    if opts.tablefile != None:
        app=TablesApp(datafile=opts.tablefile)
    else:
        app=TablesApp()
    app.mainloop()
    return

if __name__ == '__main__':
    main()
