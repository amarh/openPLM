#! /bin/bash

if [ ! -e ~/.gnome2/gedit ]; then
    mkdir ~/.gnome2/gedit
fi

if [ ! -e ~/.gnome2/gedit/plugins ]; then
    mkdir ~/.gnome2/gedit/plugins
fi
cp -f openplm.py openplm.gedit-plugin ~/.gnome2/gedit/plugins
