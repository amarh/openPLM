    function Serialize (txt)
        {
        /*auteur : XoraX
        info : http://www.xorax.info/blog/programmatio ... e-php.html  ... script légèrement modifié*/
        switch(typeof(txt))
            {
            case 'string':
                return 's:'+txt.length+':"'+txt+'";';
            case 'number':
                if(txt>=0 && String(txt).indexOf('.') == -1 && txt < 65536) return 'i:'+txt+';';
                return 'd:'+txt+';';
            case 'boolean':
                return 'b:'+( (txt)?'1':'0' )+';';
            case 'object':
                var i=0,k,ret='';
                for(k in txt)
                    {
                    //alert(isNaN(k));
                    if(!isNaN(k)) k = Number(k);
                    ret += Serialize(k)+Serialize(txt[k]);
                    i++;
                    }
                return 'a:'+i+':{'+ret+'}';
            default:
                return 'N;';
                //alert('var undefined: '+typeof(txt));return undefined;
            }
        }
    function Unserialize(txt)
        {
        /*auteur : XoraX
        info : http://www.xorax.info/blog/programmatio ... e-php.html  ... script légèrement modifié*/
        var level=0,arrlen=new Array(),del=0,final=new Array(),key=new Array(),save=txt;
        while(1)
            {
            switch(txt.substr(0,1))
                {
                case 'N':
                    del = 2;
                    ret = null;
                    break;
                case 'b':
                    del = txt.indexOf(';')+1;
                    ret = (txt.substring(2,del-1) == '1')?true:false;
                    break;
                case 'i':
                    del = txt.indexOf(';')+1;
                    ret = Number(txt.substring(2,del-1));
                    break;
                case 'd':
                    del = txt.indexOf(';')+1;
                    ret = Number(txt.substring(2,del-1));
                    break;
                case 's':
                    del = txt.substr(2,txt.substr(2).indexOf(':'));
                    ret = txt.substr( 1+txt.indexOf('"'),del);
                    del = txt.indexOf('"')+ 1 + ret.length + 2;
                    break;
                case 'a':
                    del = txt.indexOf(':{')+2;
                    ret = new Array();
                    arrlen[level+1] = Number(txt.substring(txt.indexOf(':')+1, del-2))*2;
                    break;
                case 'O':
                    txt = txt.substr(2);
                    var tmp = txt.indexOf(':"')+2;
                    var nlen = Number(txt.substring(0, txt.indexOf(':')));
                    name = txt.substring(tmp, tmp+nlen );
                    //alert(name);
                    txt = txt.substring(tmp+nlen+2);
                    del = txt.indexOf(':{')+2;
                    ret = new Object();
                    arrlen[level+1] = Number(txt.substring(0, del-2))*2;
                    break;
                case '}':
                    txt = txt.substr(1);
                    if(arrlen[level] != 0)
                        {
                                //alert('var missed : '+save);
                                return undefined;
                        }
                    //alert(arrlen[level]);
                    level--;
                    continue;
                default:
                    if(level==0) return final;
                    //alert('syntax invalid(1) : '+save+"\nat\n"+txt+"level is at "+level);
                    return undefined;
                }
            if(arrlen[level]%2 == 0)
                {
                if(typeof(ret) == 'object')
                    {
                    //alert('array index object no accepted : '+save);
                    return undefined;
                    }
                if(ret == undefined)
                    {
                    //alert('syntax invalid(2) : '+save);
                    return undefined;
                    }
                key[level] = ret;
                }
            else
                {
                var ev = '';
                for(var i=1;i<=level;i++)
                    {
                    if(typeof(key[i]) == 'number')
                        {
                        ev += '['+key[i]+']';
                        }
                    else
                        {
                        ev += '["'+key[i]+'"]';
                        }
                    }
                eval('final'+ev+'= ret;');
                }
            
            arrlen[level]--;//alert(arrlen[level]-1);
            if(typeof(ret) == 'object') level++;
            txt = txt.substr(del);
            continue;
            }
        }
    function showHide (button, id1, id2, id3, picture)
        {
        //recuperation de l'etat actuel de l'element et affectation de son opposé
        var showHide = (document.getElementById(id1).style.display == 'block' ) ? 'none' : 'block';
        var widthDiv = (document.getElementById(id1).style.display == 'block' && document.getElementById(id2).style.display != 'block') ? '1172px' : '768px';
        var buttonBorder = (document.getElementById(id1).style.display == 'block' ) ? '2px outset' : '2px inset';
        var buttonBackground = (document.getElementById(id1).style.display == 'block' ) ? '#CCCCCC' : '#777777';
        //nouvelle valeur pour l'element id
        document.getElementById(id1).style.display = showHide;
        //document.getElementById(id3).style.width = widthDiv;
        document.getElementById(button).style.border = buttonBorder;
        document.getElementById(button).style.background = buttonBackground;
        var toMoveImg = document.getElementById(picture);
        if (toMoveImg)
            {
            var currentLeftImg = Number(toMoveImg.style.left.substr(0, toMoveImg.style.left.indexOf('px')));
            if (document.getElementById(id2).style.display != 'block')
                {
                var newLeftImg = (document.getElementById(id1).style.display == 'block') ?
                                    String(currentLeftImg-1172+768)+"px" : String(currentLeftImg+1172-768)+"px";
                //alert("newLeftImg : "+newLeftImg);
                }
            toMoveImg.style.left = newLeftImg;
            }
        var tab_cook_showDiv;
        // Cherche le cookie affecté à cette page et s'il existe le désérialise
        //tab_cook_showDiv = (tab_cook_showDiv = GetCookie(SetNomCookie())) ? Unserialize(tab_cook_showDiv) : null;
        tab_cook_showDiv = (tab_cook_showDiv = GetCookie('sessionid2')) ? Unserialize(tab_cook_showDiv) : null;
        // Vérifie que le résultat tab_cook_showDiv est un tableau sinon initialise cette variable en tableau
        tab_cook_showDiv = (typeof tab_cook_showDiv == 'object' && tab_cook_showDiv instanceof Array) ? tab_cook_showDiv : new Array();
        // Enregistre l'état de la div avec l'id comme index de l'élément dans le tableau (crée l'élément ou le remplace)
        tab_cook_showDiv[id1+'_display'] = showHide;
        tab_cook_showDiv[id3+'_width'] = widthDiv;
        tab_cook_showDiv[button+'_border'] = buttonBorder;
        tab_cook_showDiv[button+'_background'] = buttonBackground;
//        if (newLeftImg)
//            {
//            tab_cook_showDiv[picture+'_left'] = newLeftImg;
//            }
//        else
//            {
//            tab_cook_showDiv[picture+'_left'] = null;
//            }
        // Envoi le tableau sérialisé dans un cookie dont le nom est "SetNomCookie()"
        //SetCoockie (SetNomCookie(), Serialize(tab_cook_showDiv));
        SetCoockie ('sessionid2', Serialize(tab_cook_showDiv));
        }
    function ToggleDisplay(element, picture)
        {
        var showHide = (document.getElementById(element).style.display == 'block' ) ? 'none' : 'block';
        var pictureSrc = (document.getElementById(element).style.display == 'block' ) ? "/media/img/plier.png" : "/media/img/deplier.png";
        document.getElementById(element).style.display = showHide;
        document.getElementById(picture).src = pictureSrc;
        var tab_cook_showDiv;
        // Cherche le cookie affecté à cette page et s'il existe le désérialise
        tab_cook_showDiv = (tab_cook_showDiv = GetCookie('sessionid2')) ? Unserialize(tab_cook_showDiv) : null;
        // Vérifie que le résultat tab_cook_showDiv est un tableau sinon initialise cette variable en tableau
        tab_cook_showDiv = (typeof tab_cook_showDiv == 'object' && tab_cook_showDiv instanceof Array) ? tab_cook_showDiv : new Array();
        // Enregistre l'état de la div avec l'id comme index de l'élément dans le tableau (crée l'élément ou le remplace)
        tab_cook_showDiv[element+'_display'] = showHide;
        tab_cook_showDiv[picture+'_src'] = pictureSrc;
        // Envoi le tableau sérialisé dans un cookie dont le nom est "SetNomCookie()"
        //SetCoockie (SetNomCookie(), Serialize(tab_cook_showDiv));
        SetCoockie ('sessionid2', Serialize(tab_cook_showDiv));
        }
    function SetNomCookie()
        {
        var fich = window.location.pathname;
        if (fich != '/')
            {
            //Enlève tout ce qu'il y a après de dernier point
            fich = fich.substr(0,fich.lastIndexOf('/'));
            //Si fich = "/index" on est sur la page d'accueil et l'on renvoie le nom de domaine
            var name = (fich == '/index')?  window.location.host : fich;
            }
        else
            {
            //si fich == '/' on est sur la page d'accueil et l'on renvoie le nom de domaine
            var name = window.location.host;
            }
        return (name);
        }
    function GetCookie(nom)
        {
        //http://www.asp-php.net/tutorial/scripting/cookies.php ... script légèrement modifié
        var deb,fin;
        deb = document.cookie.indexOf(nom + "=");
        if (deb >= 0)
            {
            deb += nom.length + 1;             
            fin = document.cookie.indexOf(";",deb);
            if (fin < 0) fin = document.cookie.length;         
            return unescape(document.cookie.substring(deb,fin));
            }
        else return false;
        }
    function SetCoockie (nom, valeur)
        {
        //http://fr.selfhtml.org/javascript/exemples/visites_pages.htm ... script légèrement modifié
        var peremption = 1000*60*60*24*365;//durée de validité : 1an
        var maintenant = new Date();
        var temps = new Date(maintenant.getTime() + peremption);
        document.cookie = nom+"="+escape(valeur)+"; expires="+temps.toGMTString()+"; path=/;";
        }
    function InitShowDiv ()
        {
        var cookie_showDiv;
        // Cherche le cookie affecté à cette page (ayant pour nom SetNomCookie()) et s'il existe ...
        //if (cookie_showDiv = GetCookie(SetNomCookie()))
        if (cookie_showDiv = GetCookie('sessionid2'))
            {
            // Désérialise le tableau enregistré dans le cookie
            var tab_cook_showDiv = Unserialize(cookie_showDiv);
                // Si tab_cook_showDiv est un objet et un tableau
                if(typeof tab_cook_showDiv == 'object' && tab_cook_showDiv instanceof Array)
                    {
                    // Affiche les div suivant leur état "block" ou "none" enregistrés dans le tableau du cookie de la page
                    // Liste le tableau associatif
                    //alert('est un objet et un tableau');
                    for (var index in tab_cook_showDiv)
                         {
                         //alert('index : '+index);
                         var id = index.substr(0,index.lastIndexOf('_'));
                         //alert('id : '+id);
                         var property = index.substr(index.lastIndexOf('_')+1,index.length);
                         //alert(property);
                         var affiche_id = document.getElementById(id);
                             if (affiche_id)
                                {
                                switch(property)
                                    {
                                    case 'display':
                                        affiche_id.style.display = tab_cook_showDiv[index];
                                        break;
                                    case 'width':
                                        //affiche_id.style.width = tab_cook_showDiv[index];
                                        break;
                                    case 'border':
                                        affiche_id.style.border = tab_cook_showDiv[index];
                                        break;
                                    case 'background':
                                        affiche_id.style.background = tab_cook_showDiv[index];
                                        break;
                                    case 'src':
                                        affiche_id.src = tab_cook_showDiv[index];
                                        break;
//                                    case 'left':
//                                        if (tab_cook_showDiv[index] != null)
//                                            {
//                                            affiche_id.style.left = tab_cook_showDiv[index];
//                                            }
//                                        break;
                                    }
                                
                                }
                            else
                                {
                                //alert('gros pb : '+id);
                                if (id.substr(0,12) == 'NavigateBox4') alert('detecte : '+id.substr(0,12));
                                }
                         }
                    if (document.getElementById('DivNav') && document.getElementById('NavigateBox').style.width == '768px')
                        {
                        var divNavElement = document.getElementById('DivNav')
                        var currentLeftPosition = Number(divNavElement.style.left.substr(0, divNavElement.style.left.indexOf('px')));
                        var newLeftPosition = String(currentLeftPosition-1172+768)+"px";
                        // alert('currentLeftPosition : '+currentLeftPosition+' newLeftPosition : '+newLeftPosition);
                        divNavElement.style.left = newLeftPosition;
                        }
                        // Et renvoie le même cookie pour prolongation de sa durée de vie dès le chargement de la page
                    //:SetCoockie (SetNomCookie(), cookie_showDiv);
                    SetCoockie ('sessionid2', cookie_showDiv);
                    }
            };
//        var block;
//        if (block = document.getElementById(conteneur)) block.style.visibility = 'visible';
        var mySelect = document.getElementById("id_type");
//        alert(mySelect);
        for (var loop = 0; loop <mySelect.options.length; loop++)
                {
//                alert(mySelect.options[loop].innerHTML.lastIndexOf('&gt;'));
                switch(mySelect.options[loop].innerHTML.lastIndexOf('&gt;'))
                                    {
                                    case -1:
                                        mySelect.options[loop].className="option_-1";
                                        break;
                                    case 0:
                                        mySelect.options[loop].className="option_0";
                                        break;
                                    case 1:
                                        mySelect.options[loop].className="option_1";
                                        break;
                                    case 2:
                                        mySelect.options[loop].className="option_2";
                                        break;
                                    }
                }
        }


