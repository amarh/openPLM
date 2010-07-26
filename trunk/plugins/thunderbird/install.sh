#! /usr/bin/env sh

cd openplm
cp -r * ~/.mozilla-thunderbird/*.default/extensions/openplm@example.com/
zip -r ../openplm.xpi .
cd ..


