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


global COMMANDE_LISTE
COMMANDE_LISTE={}
def updateGui():
    print("UPDATE GUI")
    ##import win32com.client
    ##SW = win32com.client.Dispatch("SldWorks.Application")
    ##SW.Visible = 1
    ##SW.ForceRebuild3(True)

    
def runCommand(chaine):
    print("RUN COMMAND ",chaine)
def addCommand(chaine,object):
    print("ADD COMMAND",chaine)
    COMMANDE_LISTE[chaine] = object
    
