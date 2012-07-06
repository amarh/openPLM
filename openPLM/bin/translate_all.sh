#! /usr/bin/env sh

# run this script to compile translations of all installed apps

current=$(pwd)

if [ -d "apps" ] && [ -d "locale" ];then
    COMPILEMESSAGES="django-admin compilemessages"
    APPS=$(ls apps)
    
    $COMPILEMESSAGES
    for app in $APPS; do 
        path="apps/$app"

        # test if the locale directory for translations exists
        if [ -d "$path/locale" ]; then
            cd $path
            $COMPILEMESSAGES
        fi
    done
else
    echo "$current : this script should be run from openPLM directory"
fi
