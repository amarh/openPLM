#! /usr/bin/env sh

zip openplm.oxt Addons.xcu META-INF/manifest.xml openplm.py 
unopkg add -f -v openplm.oxt
