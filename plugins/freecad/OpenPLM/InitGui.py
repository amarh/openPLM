
#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2009 Yorik van Havre <yorik@gmx.fr>                     * 
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU General Public License (GPL)            *
#*   as published by the Free Software Foundation; either version 2 of     *
#*   the License, or (at your option) any later version.                   *
#*   for detail see the LICENCE text file.                                 *
#*                                                                         *
#*   This program is distributed in the hope that it will be useful,       *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#*   GNU Library General Public License for more details.                  *
#*                                                                         *
#*   You should have received a copy of the GNU Library General Public     *
#*   License along with this program; if not, write to the Free Software   *
#*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
#*   USA                                                                   *
#*                                                                         *
#***************************************************************************

__title__="FreeCAD OpenPLM Workbench - Init file"
__author__ = "Yorik van Havre <yorik@gmx.fr>"
__url__ = ["http://yorik.orgfree.com","http://free-cad.sourceforge.net"]

# adding the OpenPLM module scripts to FreeCAD
import os
path1 = FreeCAD.ConfigGet("AppHomePath") + "Mod/OpenPLM/"
path2 = FreeCAD.ConfigGet("UserAppData") + "Mod/OpenPLM/"
if os.path.exists(path2): draftpath = path2
else: draftpath =  path1
Gui.addIconPath(draftpath)

class OpenPLMWorkbench (Workbench):
    "the OpenPLM Workbench"
    Icon = "logo_small.png"
    MenuText = "OpenPLM"
    ToolTip = "The OpenPLM module"

    def Initialize(self):
        self.initialized = False
        Log ('Loading OpenPLM GUI...\n')
        import openplm
        openplm.PLUGIN.workbench = self
        self.cmdList = ["OpenPLM_Login", "Separator"]
        self.appendMenu("OpenPLM", self.cmdList)

        self.cmdList2 = ["OpenPLM_CheckOut", "OpenPLM_Download", "OpenPLM_Forget",
                         "OpenPLM_CheckIn", "OpenPLM_Revise",
                         "OpenPLM_AttachToPart", "OpenPLM_Create"]
        self.appendMenu("OpenPLM", self.cmdList2)
        self.cmdList3 = ["Separator", "OpenPLM_Configure"]
        self.appendMenu("OpenPLM", self.cmdList3)
        self.initialized = True
 
    def Activated(self):
        pass

    def Deactivated(self):
        pass

    def GetClassName(self): 
        return "Gui::PythonWorkbench"


Gui.addWorkbench(OpenPLMWorkbench)
Gui.activateWorkbench("OpenPLMWorkbench")


