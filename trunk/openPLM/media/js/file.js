/*****************************************************************
**		Add or delete files in queue			                **
*****************************************************************/

//count for files to upload
var nbr_files=0;
//count for input added
var num_file=0;

//create a new input file, called when a new file is added to the queue for upload
function new_input_file(){
    var table = $("#fileupload > table.Content");
    var num = num_file+1;
    var input = $("<input type='file' name='filename"+num+"' id='id_filename"+num+"'/ >");
    input.change(function(){
        if(at_least_one(this)){
            $(".up_fail").remove();
            add_file(this);
            if($("#_up").hasClass("hidden")){
                $("#_up").removeClass("hidden");
                $("#_delete").removeClass("hidden");
            }
        }else{
             $.each(this.files, function(id,file){
                var can_add=can_add_file(file.name,true);
                if (can_add==false){
                    can_add_native(file.name,true);
                }
            });
        }
        $("span.warning").remove();
    });
    if(($.browser.msie!=true)&&($.browser.opera!=true)){
        input.attr("multiple","multiple");
    }
    var td_input = $("<td></td>");
    td_input.append(input);
    var tr_input = $("<tr><th><label for='id_filename"+num+"'>Filename:</label></th></tr>");
    tr_input.append(td_input);
    table.prepend(tr_input);
    num_file++;
}

//add an input in the form which contains files to upload
function add_in_queue_form(input){
    hide(input);
    $('form.hidden').append(input);
}

//return size to display
function render_size(f_size){
    if (f_size<1000){
	    return f_size+" bytes";
    }
    if (f_size<=1024){
	    return "1 KB";
    }
    var ret="";
    var aux_size =f_size*1000/1024;
    var str_size = aux_size.toString().split(".")[0];
    var group = 3;
    if(str_size.length < 9){
        group = parseInt(str_size.length/3);
    }
    if (group*3 >= str_size.length){
        group = group-1;
    }
    var before_comma = str_size.length - group*3;
    ret+=str_size.substr(0,before_comma+1);
    if(group*3 < str_size.length){
        ret+="."+str_size.substr(before_comma+1,1);
    }
    aux_size = Math.round(parseFloat(ret));
    ret = aux_size.toString().substr(0,before_comma);
    ret+= "."+aux_size.toString().substr(before_comma,1);
    switch(group){
        case 1 :
            ret+=" KB";
            break;
        case 2 :
            ret+=" MB";
            break;
        case 3 :
            ret+=" GB";
            break;
    }
    return ret;
}

/*test if at least one file from the input can be added*/
function at_least_one(input){
    var ret=false;
    files = input.files;
    var nbr=0;
    $.each(files,function(ind,file){
        if((can_add_file(file.name,false))&&(can_add_native(file.name,false))){
            ret=true;
        }
    });
    return ret;
}

function can_add_native(file_name,display){
    var response;
    var ret=true;
    if((doc_type.toLowerCase()=="document3d")&&(xhr!=null)){
        var xhr_nat= getXHR();
        var url=location.href;
        url=url.replace("/files/","/files/add/?file_name="+file_name);
        xhr_nat.open("GET",url,false);
        xhr_nat.onreadystatechange=function(){
            if(xhr_nat.readyState == 4){
                response=xhr_nat.responseText.split(":");
                if(response[0]=="true"){
                    ret=false;
                }
                if((display==true)&&(response[0]=="true")){
                    //$(".up_fail").remove();
                    var warning_msg= $("<div class='up_fail'></div>");
                    $(warning_msg).text(response[1]);
                    $("#fileupload").after(warning_msg);
                }
            }
        }
        xhr_nat.send(null);
    }
    return ret;
}

function can_add_stp(){
    if((doc_type.toLowerCase()=="document3d")&&(has_stp_file())){
        return false;
    }
    return true;
}

function can_add_file(file_name,display){
    var msg_error="";
    if((file_linked(file_name)==false)&&(file_selected(file_name)==false)){
        if((is_stp_file(file_name)==false)||(can_add_stp())){
            return true;
        }else{
            msg_error=trans["A STEP file is already linked to this document."];
        }
    }else{
        if(file_linked(file_name)){
            msg_error=trans["A file named "]+file_name+" "+trans["is already linked to this document."];
        }else{
            msg_error=trans["You have already selected the file"]+" "+file_name+" "+trans["for upload"]+".";
        }
    }
    if(display==true){
        var div_error=$("<div class='up_fail'></div>");
        div_error.text(msg_error);
        $("#fileupload").after(div_error);
    }
    return false;
}

function add_f_file(input,f){
    //test if the file f can be added
    if(can_add_file(f.name,true)){
        //test if the file can be added even if it is a native file
        if((can_add_native(f.name,true))||(doc_type.toLowerCase()!="document3d")){

            var key = f.name.replace(".","_");
            key = key.replace(" ","_");
            var size=f.size;

            //create line for file progress
            var file_line = $("<div id='"+key+"' class='file_p'>"+f.name+"("+render_size(size)+") "+"</div>");
            var progress = $("<span class='progress'><span class='text'></span></span>");
            file_line.append(progress);

            //create link to delete this file from the queue for upload
            var link = $("<span class='del_link'> </span>");
            link.click(function(){
    	        del_file(file_line,input);
            });
            var del_img = "<img src='/media/img/trash_can1.png' alt='delete' title='"+trans["remove the file from the queue"]+"'>";
            link.append(del_img);
            file_line.append(link);

            //add the file in the list of files to upload
            $("#div_files").append(file_line);

            var f_id = gen_uuid();
            
            if(($.browser.opera!=true)&&($.browser.msie!=true)){
                /*var data_key = "filename";
                if(nbr_files!=0){
                    data_key+=nbr_files;
                }
                data.append(data_key,f);*/
                //create an object related to the file in the files_info array-like
                files_info[key]={"field_name":" ", "f_name":f.name, "p_id":f_id, "size":size, "uploaded":0, "status":"waiting"};
            }else{
                files_info[key]={"f_name":f.name, "p_id":f_id, "size":size, "uploaded":0, "status":"waiting"};
            }
            
            
            nbr_files+=1;
        }
    }
}
//add a file in the queue for uploading
function add_file(input){
    if (nbr_files==0){
        $("#div_files > div.file_p").remove();
    }
    $.each(input.files,function(ind,f){
        add_f_file(input,f);
    })
    if($("#fileupload").attr("action")=="."){
        add_in_queue_form(input);
        new_input_file();
    }
}

function check_in_file(input){
    var f = input.files[0];
    var key = f.name.replace(".","_");
    key = key.replace(" ","_");
    var size=f.size;

    //create line for file progress
    var file_line = $("<div id='"+key+"' class='file_p'>"+f.name+"("+render_size(size)+") "+"</div>");
    var progress = $("<span class='progress'><span class='text'></span></span>");
    file_line.append(progress);

    //create link to delete this file from the queue for upload
    var link = $("<span class='del_link'> </span>");
    link.click(function(){
        del_file(file_line,input);
    });
    var del_img = "<img src='/media/img/trash_can1.png' alt='delete' title='"+trans["remove the file from the queue"]+"'>";
    link.append(del_img);
    file_line.append(link);

    //add the file in the list of files to upload
    $("#div_files").append(file_line);

    var f_id = gen_uuid();
            
    if(($.browser.opera!=true)&&($.browser.msie!=true)){
    /*var data_key = "filename";
    if(nbr_files!=0){
        data_key+=nbr_files;
    }
    data.append(data_key,f);*/
     
        //create an object related to the file in the files_info array-like
        files_info[key]={"field_name":" ", "f_name":f.name, "p_id":f_id, "size":size, "uploaded":0, "status":"waiting"};
    }else{
        files_info[key]={"f_name":f.name, "p_id":f_id, "size":size, "uploaded":0, "status":"waiting"};
    }
                  
    nbr_files+=1;
    
}

//hide an input row in table content
function hide(input){
    $(input).parent().parent().remove();
}

//delete a file from list and form which contains files to upload

function del_file(item,input){
    var key = item.attr("id");
    files_info=files_info.remove(key);
    item.remove();
    nbr_files--;
    $(".up_fail").remove();
    if(($.browser.opera)||($.browser.msie)){
        $(input).remove();
    }
    if(nbr_files==0){
        $("#_up").addClass("hidden");
        $("#_delete").addClass("hidden");
    }
}


/********************************************************************************************************************
**********      Handle files informations (linked and selected files : name, size (total and uploaded)     **********
********************************************************************************************************************/

//type of the current document
var doc_type = "";

//Array that contains path and size of eache files selected for upload
var files_info=new Array();
files_info.features=['features','size','key','remove','removeAll'];

files_info.key=function(){
    var ret=new Array();
    for(key in files_info){
	if($.inArray(key,files_info.features)==-1)
	    ret.push(key);
    }
    return ret;
}

files_info.size=function(){
    var ret = 0;
    for(key in files_info){
	if($.inArray(key,files_info.features)==-1)
	    ret++;
    }
    return ret;
}

files_info.remove=function(key){
   var keys = files_info.key();
   if($.inArray(key,keys)==-1){
	return;
   }else{
	var tmp_f_info=new Array();
	$.each(files_info.features, function (ind,fe){
	    tmp_f_info[fe]=files_info[fe];
	});
	$.each(keys, function(index,val){
	    if(val!==key)
		tmp_f_info[val]=files_info[val];
	});
	return tmp_f_info;
   }
}

files_info.removeAll=function(){
   var ret = new Array();
   $.each(files_info.features, function (ind,fe){
       ret[fe]=files_info[fe];
   });
   return ret;
}

function getSizeSelected(){
    var ret=0;
    var keys = files_info.key();
    $.each(keys, function(id, ke){
        ret+=files_info[ke].size;
    });
    return ret;
}

function getUpSize(){
    var ret = 0;
    var keys = files_info.key();
    $.each(keys, function(id, ke){
        ret+=files_info[ke].uploaded;
    });
    return ret;
}

function file_selected(file_name){
    var key= file_name.replace(".","_");
    return (files_info[key]!=undefined);
}
var files_linked= new Array();

function file_linked(file_name){
    return ($.inArray(file_name,files_linked)!=-1);
}

function is_stp_file(file_name){
    var ext = file_name.substr(-4).toLowerCase();
    return ($.inArray(ext, [".stp",".step"])!=-1);
}

function has_stp_file(){
    var ret = false;
    $.each(files_linked, function(ind,val){
	if(is_stp_file(val)){
	    ret = true;
	}
    });
    return ret;
};


/************************************************************************
**********      Handle and track progress for file upload      **********
************************************************************************/

//contains the value returns for the setTimeOut call on update_progress_info
var t;

var go_to ="";

var totalF_Size =0;

var totalUpSize =  0;
//xmlhttprequest use to launch the upload
var xhr = getXHR();

//generate random id to get the upload progress
function gen_uuid() {
    var uuid = "";
    for (var i=0; i < 32; i++) {
        uuid += Math.floor(Math.random() * 16).toString(16); 
    }
    return uuid;
}

//return percentage of the progress
function progress_bar(uploaded, total){
    var progress_w = uploaded * 100/total;
    return progress_w;
}


//returns ids of the files to upload in the form of sets of filename & ids
function ids_to_data(){
    var ret="";
    var keys = files_info.key();
    $.each(keys,function(index,val){
	ret += files_info[val].field_name+"="+files_info[val].p_id+"&";
    });
    ret = ret.substr(0,ret.length-1);
    return ret;
}


//indicate wether or not the upload is complete for a given file name
function upload_end(key){
    var file_key = files_info[key];
    return (file_key.uploaded==file_key.size);
}

//get the progress for a given file name/key
function update_progress(key){
    var xhr2=getXHR();
    var action = location.href;
    action = action.split("/files")[0];
    //action=action.replace("/files*","/files/_up");
    action+="/files/_up/";
    action+="?X-Progress-ID="+files_info[key].p_id;
    action+="&f_size="+files_info[key].size;
    xhr2.open("GET",action,true);
    xhr2.onreadystatechange = function() {
     	if((xhr2.readyState == 4)&&(xhr2.status==200)) {
	        var response=xhr2.responseText;
	        var uploaded = parseInt(response.split(":")[0]);
	        var totalsize = files_info[key].size;
    	    var f_status = response.split(":")[1];
    	    files_info[key].status= f_status;
    	    var percent = progress_bar(uploaded, totalsize);
    	    if(isNaN(percent)){
        		$("#"+key+" .progress .text").text("0% ("+files_info[key].status+")");
    	    }else{
        		var aux_per=""+percent;
        		if (aux_per.split(".").length>1){
        		    aux_per=aux_per.split(".")[0]+"."+aux_per.split(".")[1].substr(0,2);
        		}
        		$("#"+key+" .progress .text").text(aux_per+"%");
    	    }
    	    if(f_status=="linking"){
        		files_info[key].uploaded=files_info[key].size;
    	    }else{
        		if (f_status!="waiting"){
        		    files_info[key].uploaded=parseInt(response.split(":")[0]);
        		    $("#"+key).find("progress").attr("value",percent);
        		}
    	    }
    	}
    }
    xhr2.send(null);
}

function init_files_data(f_form){
    //initialize field_name for each file selected
    var keys = files_info.key();
    $.each(keys,function(id,key){
        files_info[key].field_name="filename";
        if(id>0){
            files_info[key].field_name+=id;
        }
    });
    var inputs_file = $(f_form).find("input[type='file']");
    if(($.browser.opera!=true)&&($.browser.msie!=true)){
        $.each(inputs_file, function(id, input){
            files = input.files;
            $.each(files,function(id, file){
                var f_key = file.name;
                f_key = f_key.replace(".","_");
                f_key = f_key.replace(" ","_");
                if(files_info[f_key]!=undefined){
                    data.append(files_info[f_key].field_name,file);
                }
            });
        });
    }else{
        opera_prepare_form(inputs_file);
    }
}

function upload_failed(){
    clearTimeout(t);
    var fail_div = $("<div class='up_fail'></div>");
    var span_text=trans["Your upload(s) failed"]+"!<br>"+trans["Try again"];
    if(nbr_files>1){
        span_text+=" "+trans["maybe with less files. "];
    }else{
        span_text+=". ";
    }
    fail_div.append(span_text);
    $("#fileupload").after(fail_div);
    $(".progress .text").empty();
    $("progress").remove();
    $(".del_link").show();
    $("#global").remove();
    $("#fileupload").find("input[type='file']").removeAttr("disabled");
    $("#_up").show();
    $("#_delete").show();
    var files_form = $(".archive_form").next();
    $(files_form[0]).find("a").removeAttr("target");
    $(files_form[0]).find("input[type='submit']").removeAttr("disabled");
    $("#up_message").hide();
}
//launch and track progress of upload file in the form f_form
function up_file(f_form){
    totalF_Size=getSizeSelected();
    totalUpSize=getUpSize();
    var new_action = location.href;
    var form_action="";
    if($(f_form).attr("action")!="."){
        form_action= $(f_form).attr("action");
        form_action=form_action.substr(2);
        new_action+="get_"+form_action;
    }else{
        //new_action = new_action.replace("/files*","/files/up");
        new_action = new_action.split("/files")[0]+"/files/up/";
    }
    init_files_data(f_form);
    var ids_list = ids_to_data();
    new_action +="?"+ids_list;
    function update_progress_info() {
        var keys = files_info.key();
        $.each(keys, function (index,key_val){
            if(upload_end(key_val)==false){
                update_progress(key_val);
            }else{
                $("#"+key_val).find("progress").attr("value",100);
            }
        });
        totalUpSize=getUpSize();
        var totalPercent = progress_bar(totalUpSize, totalF_Size);
        $("#global").find("progress").attr("value",totalPercent);
        var textTot = totalPercent.toString().split(".")[0];
        if(totalPercent.toString().split(".").length > 1){
            textTot+= "."+totalPercent.toString().split(".")[1].substr(0,2);
        }
        $("#global .progress .text").text(textTot+"%");
        t=window.setTimeout(update_progress_info, 1000)
        if(($.browser.opera)||($.browser.msie)){
            var x=document.getElementById("hidden_frame");
            var y=(x.contentWindow || x.contentDocument);
            if(y.document){
                y=y.document;
            }
            if($(y).find("body").text()!=""){
                if($(y).find("body").text()!="failed"){
                    go_to=location.href;
                }else{
                    upload_failed();
                }
            }
        }
        if(go_to!=""){
            location.href=go_to;
        }
    }
    t=window.setTimeout(update_progress_info, 1000);
    if(($.browser.opera!=true)&&($.browser.msie!=true)){
        xhr.onreadystatechange = function() {
            if(xhr.readyState == 4){
                if(xhr.status==200) {
                    go_to = location.href;
                    //go_to = go_to.replace("/files*","/files");
                    go_to = go_to.split("/files")[0]+"/files/";
                }else{
                    upload_failed();
                }
            }
        }
        xhr.open("POST", new_action,true);
        //var data = new FormData(f_form);
        xhr.send(data);
    }else{
        opera_up_file(f_form,new_action,go_to);
    }
}

/*reset the upload:
* - delete all files selected and hidden input files
*/
function reset_upload(){
    $(".del_link").click();
    nbr_files=0;
    num_file=0;
    //files_info = files_info.removeAll();
    var table = $("#fileupload > table.Content");
    $("#fileupload > table.Content tr:first").remove();
    var input = $("<input type='file' name='filename' id='id_filename'/ >");
    input.change(function(){
        var f_name = this.files[0].name;
        var up_f_name=$("#add_text").attr("checked-file");
         if(f_name!=up_f_name){
             if($(".up_fail").length==0){
                 var div_error=$("<div class='up_fail'></div>");
                 $("#fileupload").after(div_error);
             }
             $(".del_link").click();
             $(".up_fail").text(trans["You are checking-in for "]+up_f_name+".\n "+trans["You must add a file with this name."]);
         }else{
            $(".up_fail").remove();
            check_in_file(this);
            $("#_up").removeClass("hidden");
            $("#_delete").removeClass("hidden");
         }
    });
    var td_input = $("<td></td>");
    td_input.append(input);
    var tr_input = $("<tr><th><label for='id_filename'>Filename:</label></th></tr>");
    tr_input.append(td_input);
    table.prepend(tr_input);
}

//get the appropriate XmlHttpRequest object
function getXHR(){
    var xhr=null;
	
    if (window.XMLHttpRequest || window.ActiveXObject) {
	    if (window.ActiveXObject) {
	        try {
		        xhr = new ActiveXObject("Msxml2.XMLHTTP");
	        } catch(e) {
		        xhr = new ActiveXObject("Microsoft.XMLHTTP");
	        }
	    } else {
		    xhr = new XMLHttpRequest(); 
	    }
    } else {
	    return null;
    }
    
    return xhr;
}

var trans=[];
var data;
if(($.browser.opera!=true)&&($.browser.msie!=true)){
    data = new FormData($('form.hidden')[0]);
}

$(function(){
    $("#up_message").hide();
    $("input[type='submit'][name='_validate']").hide();
    if(($.browser.msie!=true)&&($.browser.opera!=true)){
        $("input[type='file']").attr('multiple','multiple');
    }
    $("#add_file_container").toggleClass("hidden");
    if(files_linked.length!=0){
        $("#add_form_file").toggleClass("hidden");
    }
    var add_text= $("#add_text").text();
    $("#add_text").text(add_text.split(" / ")[0]);
    $("#add_text").attr("title",trans["Show/Hide the upload form"]);

    $.each($(".check-in"),function(ind,val){
        var ref =$(val).parent().attr("href");
        $(val).parent().removeAttr("href");
        $(val).attr("action",ref);
    });

    $("#add_text").click(function(){
        $("#add_form_file").toggleClass("hidden");
    });

    $(".check-in").click(function(){
        if($("#fileupload").find("input[type='file']").attr("disabled")!="disabled"){
            $("#fileupload").attr("action",$(this).attr("action"));
            reset_upload();
            $("#add_form_file").removeClass("hidden");
            var line= $(this).parent().parent().parent();
            var f_name = line.find("td a:first").text();
            $("#add_text").text(trans["Check-in for file "]+f_name+":");
            $("#add_text").attr("checked-file",f_name);
        }
    });

    $("input[type='file']").change(function (){
        if(at_least_one(this)){
            $(".up_fail").remove();
            add_file(this);
            $("#_up").removeClass("hidden");
            $("#_delete").removeClass("hidden");
        }else{
            $.each(this.files, function(id,file){
                var can_add=can_add_file(file.name,true);
                if (can_add==false){
                    can_add_native(file.name,true);
                }
            });
        }
        $("span.warning").remove();
    });

    $("#_delete").click(function(){
        $(".del_link").click();
        $("#_up").addClass("hidden");
        $("#_delete").addClass("hidden");
    });

    if(xhr!=null){
    //if the browser supports xmlhttprequest object
        $("input[name='_undo']").click(function(){
            if(xhr.readyState!=0){
                xhr.onreadystatechange = function() {}
                xhr.abort();
            }
        });
        $("#_up").click(function(){
            $(".up_fail").remove();
            if(nbr_files==0){
                if($("#fileupload").find("span.warning").length==0){
                    $("#fileupload").find("input[type='file']").parent().append("<span class='warning'>"+trans["Select at least one file"]+"</span>");
                }
                return;
            }
            var global_prog = $("<div style='margin-top:1%' id='global'>Total: </div>");
            global_prog.append("<span class='progress'><span class='text'></span></span>");
            $("#up_message").after(global_prog);
            $(".del_link").hide();
            $(".progress .text").text("0% (waiting)");
            $(".progress").prepend("<progress max=100 value=0></progress>");
            if($("#fileupload").attr("action")=="."){
                $('form.hidden')[0].action=".";
                up_file($('form.hidden')[0]);
            }else{
                up_file($("#fileupload")[0]);
            }
            $("#fileupload").find("input[type='file']").attr("disabled","disabled");
            $("#_delete").hide();
            $("#_up").hide();
            var files_form = $(".archive_form").next();
            $(files_form[0]).find("a").attr("target","_blank");
            $(files_form[0]).find("input[type='submit']").attr("disabled","disabled");
            $("#up_message").show();
        });
    }else{
        //the browser does not support xmlhttprequest object
        //if javascript is disabled, noscript tag will handle that
        $("#fileupload").insertAfter("<span class='warning'>"+trans["You can only upload files, but you wont get progress of this upload"]+"</span>");
        $("#_up").click(function(){
            if(nbr_files==0){
                $("#fileupload").find("input[type='file']").parent().append("<span class='warning'>"+trans["Select at least one file"]+"</span>");
                return;
            }
            $('form.hidden')[0].action=location.href+"add/";
            $('form.hidden')[0].method="post";
            $('form.hidden')[0].submit();
	    });
    }
});
