#! /bin/bash

if [ ! -e ~/.FreeCAD ]; then
    mkdir ~/.FreeCAD
fi

if [ ! -e ~/.FreeCAD/Mod ]; then
    mkdir ~/.FreeCAD/Mod
fi
cp -rf OpenPLM ~/.FreeCAD/Mod/
