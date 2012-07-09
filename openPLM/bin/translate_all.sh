#! /usr/bin/env sh

# run this script to compile translations of all installed apps

MAKEMESSAGES="django-admin makemessages -e html,htm,xhtml,py,txt"
COMPILEMESSAGES="django-admin compilemessages"
current=$(pwd)


if [ -d "apps" ] && [ -d "locale" ];then
    case $1 in
    "compile")
        if [ $# -eq "2" ] ; then
            if [ $2 = "all" ];then
                $COMPILEMESSAGES
    
                APPS=$(ls apps)
                cd apps
                for app in $APPS; do 
                    if [ -d "$app/locale" ]; then
                        cd $app
                        $COMPILEMESSAGES
                        cd ".."
                    fi
                done
            else
                if [ -d "apps/$2" ]; then
                    cd "apps/$2"
                    $COMPILEMESSAGES
                else
                    echo "$2 : this is not an app repertory"
                fi
            fi
        else
            $COMPILEMESSAGES
        fi;;
    "make")
        if [ $# -eq "2" ]; then
            cd "apps/$2"
        else
            MAKEMESSAGES="$MAKEMESSAGES --ignore=apps/* "
        fi
        $MAKEMESSAGES -l fr 
        $MAKEMESSAGES -l es
        $MAKEMESSAGES -l ja
        $MAKEMESSAGES -l ru
        $MAKEMESSAGES -l zh_CN
    esac
else
    echo "$current : this script should be run from openPLM directory"
fi

