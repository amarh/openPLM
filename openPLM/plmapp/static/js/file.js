/******************************************************
Author : Zahariri ALI
Contact : zahariri.ali@gmail.com
******************************************************/





/*****************************************************************
**		Add or delete files in queue			                **
*****************************************************************/
//count for input added
var num_input=0;

//create a new input file
//function called when a new file is added to the queue for upload
function new_input_file(){
    var table = $("#fileupload > table.Content");
    var num = num_input+1;
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
    //if(($.browser.msie!=true)&&($.browser.opera!=true)&&(xhr!=null)){
        input.attr("multiple","multiple");
    //}
    var td_input = $("<td></td>");
    td_input.append(input);
    var tr_input = $("<tr><th><label for='id_filename"+num+"'>Filename:</label></th></tr>");
    tr_input.append(td_input);
    table.prepend(tr_input);
    num_input++;
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
        url +="add/?file_name="+file_name;
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

//add the file f from the input to the queue
function add_f_file(input,f){

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
        var del_img = "<img src='/static/img/trash_can1.png' alt='delete' title='"+trans["remove the file from the queue"]+"'>";
        link.append(del_img);
        file_line.append(link);

        //add the file in the list of files to upload
        $("#div_files").append(file_line);

        //create an object related to the file in the files_info array-like
        var f_id = gen_uuid();
        if(FD_SUPPORTED){
            files_info[key]={"field_name":" ", "f_name":f.name, "p_id":f_id, "size":size, "uploaded":0, "status":"waiting"};
        }else{
            files_info[key]={"f_name":f.name, "p_id":f_id, "size":size, "uploaded":0, "status":"waiting"};
        }
}

//add an input and the files selected in the queue for uploading
function add_file(input){
    if (files_info.size()==0){
        $("#div_files > div.file_p").remove();
    }
    
    $.each(input.files,function(ind,f){
        //test if the file f can be added
        if((can_add_file(f.name,true))&&(can_add_native(f.name,true))){
            add_f_file(input,f);
        }
    });
    
    //the file is not added in the queue form when
    // checking in for a given file
    if($("#fileupload").attr("action")=="."){
        add_in_queue_form(input);
        new_input_file();
    }
}

//add the file selected for check-in to the upload queue
function check_in_file(input){

    //check-in consider only the first file selected
    var f = input.files[0];
    add_f_file(input,f);
    
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
    $(".up_fail").remove();
    
    //input file's multiple selection is not enable for opera and IE
    if(input.files.length==1){
        $(input).remove();
    }
    if(files_info.size()==0){
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
var files_info=[];
files_info.features=['features','size','key','remove'];

//returns all the key except those in files_info.features
files_info.key=function(){
    var ret=[];
    for(key in files_info){
	if($.inArray(key,files_info.features)==-1)
	    ret.push(key);
    }
    return ret;
}

//returns the number of file in files_info
files_info.size=function(){
    var ret = 0;
    for(key in files_info){
	if($.inArray(key,files_info.features)==-1)
	    ret++;
    }
    return ret;
}

//remove an element identified by key from files_info
files_info.remove=function(key){
    var keys = files_info.key();
   
    if($.inArray(key,keys)==-1){
        return;
    }else{
    
        var tmp_f_info=[];
        
	    $.each(files_info.features, function (ind,fe){
	        tmp_f_info[fe]=files_info[fe];
	    });
	    $.each(keys, function(index,val){
	        if(val!==key){
	            tmp_f_info[val]=files_info[val];
	        }
	    });
	    return tmp_f_info;
    }
}

//return the total size of all selected files
function getSizeSelected(){
    var ret=0;
    var keys = files_info.key();
    $.each(keys, function(id, ke){
        ret+=files_info[ke].size;
    });
    return ret;
}

//return the uploaded size for all selected files
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

//list of files linked to the document
var files_linked= [];

function file_linked(file_name){
    return ($.inArray(file_name,files_linked)!=-1);
}

function is_stp_file(file_name){
    var ext = file_name.substr(-4).toLowerCase();
    return ($.inArray(ext, [".stp",".step"])!=-1);
}

//test if the document has step file linked
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

//size of all files selected for upload
var totalF_Size =0;

//size of files uploaded
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
    var progress_w = uploaded/total;
    progress_w=Math.round(progress_w*10000)/100;
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


//indicate wether or not the upload is complete for a given file name/key
function upload_end(key){
    var file_key = files_info[key];
    return (file_key.uploaded==file_key.size);
}

//get the progress for a given file name/key
function update_progress(key){
    var xhr2=getXHR();
    
    var action = location.href;
    action+="_up/";
    action+="?X-Progress-ID="+files_info[key].p_id;
    action+="&f_size="+files_info[key].size;
    
    xhr2.open("GET",action,true);
    
    xhr2.onreadystatechange = function() {
     	if((xhr2.readyState == 4)&&(xhr2.status==200)) {

	        var response = xhr2.responseText;
	        var uploaded = parseInt(response.split(":")[0]);
	        var f_status = response.split(":")[1];
	        
    	    if(files_info[key].status != f_status){
    	        files_info[key].status = f_status;
    	    }
    	    if(f_status=="linking"){
        		files_info[key].uploaded=files_info[key].size;
    	    }else{
        		if (f_status!="waiting"){
        		    files_info[key].uploaded=parseInt(response.split(":")[0]);
        		}
    	    }
    	    
    	    var percent = progress_bar(uploaded, files_info[key].size);
    	    if(!isNaN(percent)){
                var div = $(document.getElementById(key));
        	    div.find(" .progress .text").text(percent+"%");
        		div.find("progress").attr("value",percent);
    	    }
    	    
    	}
    }
    
    xhr2.send(null);
}

//intialize data before the upload is sent
//data : formData object or form element (opera, IE)
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
    if(FD_SUPPORTED){
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

//Handle the failure of upload
function upload_failed(){
    clearTimeout(t);
    
    //display a message
    var fail_div = $("<div class='up_fail'></div>");
    var span_text=trans["Your upload(s) failed"]+"!<br>"+trans["Try again"];
    if(files_info.size() > 1){
        span_text+=" "+trans["maybe with less files. "];
    }else{
        span_text+=". ";
    }
    fail_div.append(span_text);
    $("#fileupload").after(fail_div);
    
    //remove all the progress info
    $(".progress .text").empty();
    $("progress").remove();
    $(".del_link").show();
    $("#global").remove();
    
    //reset the file upload form
    $("#fileupload").find("input[type='file']").removeAttr("disabled");
    $("#_up").show();
    $("#_delete").show();
    var files_form = $(".archive_form").next();
    $(files_form[0]).find("a").removeAttr("target");
    $(files_form[0]).find("input[type='submit']").removeAttr("disabled");
    $(files_form[0]).next("div").find("a").removeAttr("target");
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
        if (form_action[0] == "."){
            form_action=form_action.substr(2);
            new_action+="get_"+form_action;
        } else {
            new_action = form_action.replace("/checkin/", "/get_checkin/");
        }

    }else{
        new_action+="up/";
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
        $("#global .progress .text").text(totalPercent+"%");
        
        t=window.setTimeout(update_progress_info, 1000);
        
        if(!FD_SUPPORTED){
            var x=document.getElementById("hidden_frame");
            var y=(x.contentWindow || x.contentDocument);
            if(y.document){
                y=y.document;
            }
            var resp = $(y).find("body").text();
            if (resp != ""){
                if(resp != "failed"){
                    go_to= resp;
                }else{
                    upload_failed();
                }
            }
        }
        
        if(go_to!=""){
            if (go_to.substring(0, 8) != "/object/") {
                go_to = ".";
            }
            location.href=go_to;
        }
    }
    
    t=window.setTimeout(update_progress_info, 1000);
    
    if(FD_SUPPORTED){
        xhr.onreadystatechange = function() {
            if(xhr.readyState == 4){
                if(xhr.status==200 && xhr.responseText != "failed") {
                    go_to = xhr.responseText;
                }else{
                    upload_failed();
                }
            }
        }
        
        xhr.open("POST", new_action,true);
        
        xhr.send(data);
    }else{
        //opera and IE do not support FormData object
        opera_up_file(f_form,new_action,go_to);
    }
}

/*reset the upload:
* - delete all files selected and hidden input files
* - set the upload form to check-in for a given file
*/
function reset_upload(){
    $(".del_link").click();
    num_input=0;
    
    $(".up_fail").remove();
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
             $('html, body').animate({
                 scrollTop: $("#add_file_container").offset().top
             }, 500);
         }else{
            $(".up_fail").remove();
            check_in_file(this);
            $("#_up").removeClass("hidden");
            $("#_delete").removeClass("hidden");
            $("#_up").click();
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
    return new XMLHttpRequest;

}

//contains translation needed for different message/text
var trans=[];

//sets data according to the browser used
var data;
var FD_SUPPORTED = FormData !== undefined;
if(FD_SUPPORTED){
    data = new FormData($('form.hidden')[0]);
}


$(function(){
    //sets the message that will be displayed while uploading files
    var up_msg = $("<div style='margin:1%;' id='up_message'></div>");
    up_msg.text(trans["Do not leave the current page until the upload ends"]);
    $("form.hidden:first").after(up_msg);
    $("#up_message").hide();
    
    $("input[type='submit'][name='_validate']").hide();
    
    $("#add_file_container:not(.ci)").toggleClass("hidden");
    if(files_linked.length!=0){
        $("#add_form_file").toggleClass("hidden");
    }
    var add_text= $("#add_text").text();
    $("#add_text").text(add_text.split(" / ")[0]);
    $("#add_text").attr("title",trans["Show/Hide the upload form"]);

    $("#add_text").click(function(){
        $(this).toggleClass("tb-active");
        $("#add_form_file").toggleClass("hidden");
        if (!$("#add_form_file").hasClass("hidden")){
            $("#id_filename").click();
        }
    });

    $(".check-in").click(function(e){
        e.preventDefault();
        if($("#fileupload").find("input[type='file']").attr("disabled")!="disabled"){
            $("#fileupload").attr("action",$(this).parent().attr("href"));
            reset_upload();
            $("#add_form_file, #add_file_container").removeClass("hidden");
            var f_name = $(this).attr("data-file");
            $("#add_text").text(trans["Check-in for file "]+f_name+":");
            $("#add_text").attr("checked-file",f_name);
            $("#id_filename").click();
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

    //remove all the selected files and hidden inputs files
    $("#_delete").click(function(){
        $(".del_link").click();
        $("form.hidden > input[type='file']").remove();
        $("#_up").addClass("hidden");
        $("#_delete").addClass("hidden");
    });

    if(xhr!=null){
    //if the browser supports xmlhttprequest object
    
        if(FD_SUPPORTED){
            $("input[type='file']").attr('multiple','multiple');
        }
        
        $("input[name='_undo']").click(function(){
            if(xhr.readyState!=0){
                xhr.onreadystatechange = function() {}
                xhr.abort();
            }
        });
        $("#_up").click(function(){
            $(".up_fail").remove();
            if(files_info.size()==0){
                if($("#fileupload").find("span.warning").length==0){
                    $("#fileupload").find("input[type='file']").parent().append("<span class='warning'>"+trans["Select at least one file"]+"</span>");
                }
                return;
            }
            var global_prog = $("<div style='margin-top:1%' id='global'>"+trans["Total"]+": </div>");
            global_prog.append("<span class='progress'><span class='text'></span></span>");
            $("#up_message").after(global_prog);
            $(".del_link").hide();
            $(".progress .text").text("0% ("+trans["waiting"]+")");
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
            
            //disable actions in the file display form
            $(files_form[0]).find("input[type!='hidden']").attr("disabled","disabled");
            
            //set all links so a new tab is opened when they are clicked on
            $(files_form[0]).find("a").attr("target","_blank");
            $(files_form[0]).next("div").find("a").attr("target","_blank");
            
            $("#up_message").show();
        });
    }else{
        //the browser does not support xmlhttprequest object but has javascript enabled
        //if javascript is disabled, noscript tag will handle that
        $("#fileupload").insertAfter("<span class='warning'>"+trans["You can only upload files, but you wont get progress of this upload"]+"</span>");
        $("#_up").click(function(){
            if(files_info.size()==0){
                $("#fileupload").find("input[type='file']").parent().append("<span class='warning'>"+trans["Select at least one file"]+"</span>");
                return;
            }
            
            opera_prepare_form($("form.hidden:first > input[type='file']"));
            $('form.hidden')[0].action=location.href+"add/";
            $('form.hidden')[0].method="post";
            $('form.hidden')[0].submit();
	    });
    }
});
$(document).ready(function () {
    $("#dialog_check-out").dialog({
    modal: true,
    autoOpen: false
    });
    $("a.check-out").click(function(e) {
        e.preventDefault();
        var url = $(this).attr("href");
        $("#dialog_check-out").dialog('option', 'buttons', {
            "CANCEL": function() {
                $(this).dialog("close");
                },
                "CHECK-OUT": function() {
                $(location).attr('href',url); 
                $(this).dialog("close");
                }
            });
            $("#dialog_check-out").dialog();
            $("#dialog_check-out").dialog("open");
            return false;
    });

    $("#s_all").click(function(){
        $("td.Content > input:checkbox").attr("checked",true);
        $("#s_all").addClass("hidden");
        $("#des_all").removeClass("hidden");
    });
    $("#des_all").click(function(){
        $("td.Content > input:checkbox").attr("checked",false);
        $("#s_all").removeClass("hidden");
        $("#des_all").addClass("hidden");
    });
    $("a.check-out-link").click(function(){
        var a=$(this);
        setTimeout(function(){
            var tr = a.parents(".file");
            tr.find(".status, .checkin").toggle();
            tr.toggleClass("locked unlocked");
            a.hide();
        }, 500);
    });

});
