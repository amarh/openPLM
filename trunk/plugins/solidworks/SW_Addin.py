

#
# OpenPLM module
#

#***************************************************************************
#*   This file is part of the OpenPLM plugin for SWCAD.                  *
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU General Public License (GPL)            *
#*   as published by the Free Software Foundation; either version 2 of     *
#*   the License, or (at your option) any later version.                   *
#*   for detail see the LICENCE text file.                                 *
#*                                                                         *
#*   SWCAD is distributed in the hope that it will be useful,            *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#*   GNU Library General Public License for more details.                  *
#*                                                                         *
#*   You should have received a copy of the GNU Library General Public     *
#*   License along with this plugin; if not, write to the Free Software    *
#*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
#*   USA                                                                   *
#*                                                                         *
#***************************************************************************/

# Authors
# Baptiste M <baptistem@laposte.net>

#
# 18/5/2013 : Fonctionne en partie
# configure ( pour choisir le serveur )
# login
# le create document
# j'ai essayé de faire un truc generique pour les version de solidworks... mais je n'ai testé que sur ma version 2010
#
# un test et debugage sur les autres...
#

import pythoncom
import win32com.client
from win32com import universal
from win32com.client import gencache


import os
import shutil
import json

###on ouvre un solidworks COM pour obtenir la version....
import win32com.client

sw = win32com.client.Dispatch("SldWorks.Application")
sw.Visible = 1
rv = sw.RevisionNumber
sw.ExitApp

SW_VERSION = int(rv.split(".")[0])-8+2000


for type_library in ["SolidWorks %04d exposed type libraries for add-in use"%SW_VERSION]:
    print(type_library)
    from win32com.client import makepy
    ##a = makepy.GenerateFromTypeLibSpec(type_libray)
    resultat = makepy.selecttlb.FindTlbsWithDescription(type_library)
    for r in resultat:
        print("CLSID",r.clsid,"MAJOR",r.major,"MINOR",r.minor,"FLAGS",r.flags,"LCID",r.lcid)
        print("DESC",r.desc,"DLL",r.dll,"VER DESC",r.ver_desc)
        gencache.EnsureModule(r.clsid,int(r.lcid),int(r.major),int(r.minor))
        universal.RegisterInterfaces(r.clsid, 
                             int(r.lcid), int(r.major), int(r.minor),
                             ['ISwAddin','ISwPointInferenceBroker','ISwAddinBroker','ISwAddinLicenseManager','ISwAddinAdvancedOptionBroker','ISwCalloutHandler'])


##for type_library in ["SolidWorks %04d Constant type library"%SW_VERSION]:
##    print(type_library)
##    from win32com.client import makepy
##    ##a = makepy.GenerateFromTypeLibSpec(type_libray)
##    resultat = makepy.selecttlb.FindTlbsWithDescription(type_library)
##    for r in resultat:
##        print("CLSID",r.clsid,"MAJOR",r.major,"MINOR",r.minor,"FLAGS",r.flags,"LCID",r.lcid)
##        print("DESC",r.desc,"DLL",r.dll,"VER DESC",r.ver_desc)
        

global COMMANDE_LISTE
import SWCAD,SWCADGui
COMMANDE_LISTE={}
import openplm

class OpenPlm_Addin(openplm.OpenPLMPluginInstance):
    _com_interfaces_ = ["ISwAddin", 'ISwPointInferenceBroker','ISwAddinBroker','ISwAddinLicenseManager','ISwAddinAdvancedOptionBroker','ISwCalloutHandler']
    _public_methods_ = ['ConnectToSW','DisconnectFromSW',
                        'login_cmd','login_enable',
                        'checkin_cmd','checkin_enable',
                        'checkout_cmd','checkout_enable',
                        'revise_cmd','revise_enable',
                        'download_cmd','download_enable',
                        'create_cmd','create_enable',
                        'forget_cmd','forget_enable',
                        'attachtopart_cmd','attachtopart_enable',
                        'configure_cmd','configure_enable']
    _public_attrs_ = ['data','sw']
    ### Cette ligne est a changer avec pythoncom.CreateGuid()
    _reg_clsid_ = "{45F7003E-4BF0-41B5-B440-9A8AA4A31350}"
    _reg_desc_ = "OPENPLM CONNECTOR"
    _typelib_version_ = 0, 0
    _reg_progid_ = "OpenPLM"
    key_rep = """SOFTWARE\\SolidWorks\\SolidWorks %04d\\AddIns\\"""%SW_VERSION
    data = {}
    def __init__(self):
        openplm.OpenPLMPluginInstance.__init__(self)

    def ConnectToSW(self,sw,cookie):
        print("CONNECT")
        self.sw1 = sw
        self.sw = win32com.client.Dispatch(sw)
        print(dir(self.sw))
        self.sw.SetAddinCallbackInfo(0, sw, cookie)
        self.sw.SetAddinCallbackInfo(0, win32com.client.Dispatch(str(self._reg_progid_)),cookie)
        self.cookie = cookie
        self.sw.AddMenu(1,str(self._reg_progid_),10)
        i=10
        for c in SWCADGui.COMMANDE_LISTE:
            res = SWCADGui.COMMANDE_LISTE[c].GetResources()
            self.sw.AddMenuItem4(1,self.cookie,res['MenuText']+"@"+self._reg_progid_,i,c.split("_")[-1].lower()+"_cmd",c.split("_")[-1].lower()+"_enable",res['ToolTip'],"B")
            i=i+1            

        ## ne pas oublie de mettre les "callback" dans les publics methods en haut !!!
        return True
    def DisconnectFromSW(self):
        print("DISCONNECT")
        self.sw.RemoveMenu(1,self._reg_progid_,10)
        return True
    def login_enable(self):
        c="OpenPLM_Login"
        return 1
    def login_cmd(self):
        c="OpenPLM_Login"
        import PyQt4.QtGui as qt
        import sys
        app = qt.QApplication(sys.argv)
        SWCADGui.COMMANDE_LISTE[c].Activated()
        app.exec_()
        app.quit()
    def configure_enable(self):
        c="OpenPLM_Configure"
        return 1
    def configure_cmd(self):
        c="OpenPLM_Configure"
        import PyQt4.QtGui as qt
        import sys
        app = qt.QApplication(sys.argv)
        SWCADGui.COMMANDE_LISTE[c].Activated()
        app.exec_()
        app.quit()
    def checkin_enable(self):
        c="OpenPLM_CheckIn"
        return SWCADGui.COMMANDE_LISTE[c].IsActive()
    def checkin_cmd(self):
        c="OpenPLM_CheckIn"
        import PyQt4.QtGui as qt
        import sys
        app = qt.QApplication(sys.argv)
        SWCADGui.COMMANDE_LISTE[c].Activated()
        app.exec_()
        app.quit()
    def checkout_enable(self):
        c="OpenPLM_CheckOut"
        return SWCADGui.COMMANDE_LISTE[c].IsActive()
    def checkout_cmd(self):
        c="OpenPLM_CheckOut"
        import PyQt4.QtGui as qt
        import sys
        app = qt.QApplication(sys.argv)
        SWCADGui.COMMANDE_LISTE[c].Activated()
        app.exec_()
        app.quit()
    def revise_enable(self):
        c="OpenPLM_Revise"
        return SWCADGui.COMMANDE_LISTE[c].IsActive()
    def revise_cmd(self):
        c="OpenPLM_Revise"
        import PyQt4.QtGui as qt
        import sys
        app = qt.QApplication(sys.argv)
        SWCADGui.COMMANDE_LISTE[c].Activated()
        app.exec_()
        app.quit()
    def download_enable(self):
        c="OpenPLM_Download"
        return SWCADGui.COMMANDE_LISTE[c].IsActive()
    def download_cmd(self):
        c="OpenPLM_Download"
        import PyQt4.QtGui as qt
        import sys
        app = qt.QApplication(sys.argv)
        SWCADGui.COMMANDE_LISTE[c].Activated()
        app.exec_()
        app.quit()
    def create_enable(self):
        c="OpenPLM_Create"
        return SWCADGui.COMMANDE_LISTE[c].IsActive()
    def create_cmd(self):
        c="OpenPLM_Create"
        import PyQt4.QtGui as qt
        import sys
        app = qt.QApplication(sys.argv)
        SWCADGui.COMMANDE_LISTE[c].Activated()
        app.exec_()
        app.quit()
    def forget_enable(self):
        c="OpenPLM_Forget"
        return SWCADGui.COMMANDE_LISTE[c].IsActive()
    def forget_cmd(self):
        c="OpenPLM_Forget"
        import PyQt4.QtGui as qt
        import sys
        app = qt.QApplication(sys.argv)
        SWCADGui.COMMANDE_LISTE[c].Activated()
        app.exec_()
        app.quit()
    def attachtopart_enable(self):
        c="OpenPLM_AttachToPart"
        return SWCADGui.COMMANDE_LISTE[c].IsActive()
    def attachetopart_cmd(self):
        c="OpenPLM_AttachToPart"
        import PyQt4.QtGui as qt
        import sys
        app = qt.QApplication(sys.argv)
        SWCADGui.COMMANDE_LISTE[c].Activated()
        app.exec_()
        app.quit()
    def register(self):
        import sys
        import win32com.server.register
        sys.argv.append('--debug')
        win32com.server.register.UseCommandLine(self.__class__)
    def create_key(self):
        print("CREATE KEY")
        import datetime
        import pythoncom
        import _winreg

        with _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, self.key_rep) as key:
            k = _winreg.CreateKey(key,self._reg_clsid_)
            _winreg.SetValueEx(k,"default",0,_winreg.REG_DWORD,1)
            _winreg.SetValueEx(k,"Title",0,_winreg.REG_SZ,self._reg_progid_)
            _winreg.SetValueEx(k,"Description",0,_winreg.REG_SZ,self._reg_desc_)
            _winreg.FlushKey(key)
    def delete_key(self):
        print("TODO")


import sys
if (__name__ == "__main__"):
    b = OpenPlm_Addin()
    b.register()
    if ( "--install" in sys.argv):
        b.create_key()
    if ( "--uninstall" in sys.argv):
        b.delete_key()

