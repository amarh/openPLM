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


print("Import SWCAD")

class Convertisseur:
    def __init__(self):
        pass
    def saveImage(self,nom):
        print(nom)
        G = open(nom,"w+")
        G.write(nom)
        G.close()
       
class Document:
    def __init__(self):
        self.FileName = "BMA.sldrt"
        self.Objects = []
        self.Label = ""
    def ActiveView(self):
        return Convertisseur()
def ActiveDocument():
    print("Active Document")
    import win32com.client
    SW = win32com.client.Dispatch("SldWorks.Application")
    swModel = SW.ActiveDoc
    if ( swModel is None):
        nom_fichier=""
        print("Pas de fichier selectionne")
    else:
        nom_fichier=swModel.GetPathName
    print(nom_fichier)
    D = Document()
    D.FileName = nom_fichier
    return D
def openDocument(chemin):
    print("OPEN DOCUMENT",chemin)
    import win32com.client
    SW = win32com.client.Dispatch("SldWorks.Application")
    SW.Visible = 1
    a=0
    b=0
    if ( str(chemin).lower()[:-5] == "sldprt"):
        swModel = SW.OpenDoc(chemin,1)
    if ( str(chemin).lower()[:-5] == "sldasm"):
        swModel = SW.OpenDoc(chemin,2)
    D = Document()
    D.FileName = chemin
    return D
def closeDocument(chemin):
    print("Close Document",chemin)
    import win32com.client
    SW = win32com.client.Dispatch("SldWorks.Application")
    SW.Visible = 1
    swModel = SW.ActiveDoc
    if ( swModel is None):
        nom_fichier=""
        print("Pas de fichier selectionne")
    else:
        nom_fichier=swModel.GetPathName
        print(nom_fichier,chemin)
        swModel.Close
    
