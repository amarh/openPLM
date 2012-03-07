#! /usr/bin/env sh

# usage: extrator.sh FILE

# this simple script extracts some metadata or data (as plain text) and
# prints them to stdout
# errors are silently passed

filename=$1
ext=${filename##*.}
ext=`echo $ext | tr '[:upper:]' '[:lower:]'`

case "$ext" in 
    pdf)
        pdftotext -nopgbrk "$filename" - 2> /dev/null
        ;;
    
    html|xhtml|htm)
        html2text "$filename" 2> /dev/null
        ;;

    odt|ods|odp|odg)
        odt2txt "$filename" 2> /dev/null
        ;;

    docx|xlsx|pptx)
        openxmlinfo words "$filename" 2> /dev/null
        ;;
    
    doc)
        antiword "$filename" 2> /dev/null
        ;;

    xls)
        xls2csv "$filename" 2> /dev/null
        ;;
    ppt)
        catppt "$filename" 2> /dev/null
        ;;
    stp|step)
        grep -P -o "(?<=PRODUCT\(')([^']+)" $filename
        ;;
    *) ;;
esac

