/*****************************************************************
**		Add or delete files in queue			**
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
	var key=this.files[0].name.replace(".","_");
	if(files_info[key]==undefined){
	    add_file(this);
	}else{
	     alert("vous avez déjà selectionné ce fichier");
	}
    });
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
    $('form.form_queue').append(input);
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

//add a file in the queue for uploading
function add_file(input){
    if (nbr_files==0)
	$("#div_files > div").remove();

    //create line where the progress of the upload will be display for this input
    var f_name = input.value;
    var key= f_name.replace(".","_");
    var size = input.files[0].size;
    var file_line = $("<div id='"+key+"'>"+input.files[0].name+"("+render_size(size)+")"+": <span class='progress'><span class='text'></span></span></div>");

    //create link to delete this file from the queue for upload
    var link = $("<a class='del_link'></a>");
    link.click(function(){
	del_file(file_line,input);
    });
    var del_img = "<img src='/media/img/delete.png' alt='delete' title='remove the file from the queue'>";
    link.append(del_img);
    file_line.append(link);

    //add the file in the list of files to upload
    $("#div_files").append(file_line);
    add_in_queue_form(input);
    new_input_file();
    nbr_files+=1;
    var f_id = gen_uuid();
    //create an object related to the file in the files_info array-like
    files_info[key]={"f_name":f_name, "p_id":f_id, "size":size, "uploaded":0, "status":"waiting"};
}

//hide an input row in table content
function hide(input){
    $(input).parent().parent().remove();
}

//delete a file from list and form which contains files to upload
function del_file(item,input){
    var key = item.attr("id");
    files_info = files_info.remove(key);
    item.remove();
    $(input).remove();
    nbr_files--;
    $(".up_fail").remove();
}


/***********************************************************************/

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

//return an XMLHttpRequest
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
	//alert("Votre navigateur ne supporte pas l'objet XMLHTTPRequest...");
	return null;
    }

    return xhr;
}


//returns ids of the files to upload
function ids_to_data(){
    var ret="";
    var keys = files_info.key();
    $.each(keys,function(index,val){
	ret += files_info[val].f_name+"="+files_info[val].p_id+"&";
    });
    ret = ret.substr(0,ret.length-1);
    return ret;
}

//contains the value returns for the setTimeOut call on update_progress_info
var t;

//Array that contains path and size of eache files selected for upload
var files_info=new Array();
files_info.features=['features','size','key','remove'];

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

/*****************************************************************
**		Track and update progress info 			**
*****************************************************************/

//indicate wether or not the upload is complete for a given file name
function upload_end(key){
    var file_key = files_info[key];
    return (file_key.uploaded==file_key.size);
}

//get the progress for a given file name/key
function update_progress(key){
    var xhr2=getXHR();
    var action = location.href;
    action = action.split("?")[0];
    action=action.replace("/files/add","/files/_up");
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
		$("#"+key+" .progress .text").text(aux_per+"% ("+files_info[key].status+")");
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

//launch and track progress of upload file in the form f_form
function up_file(f_form){
    var new_action = location.href;
    new_action = new_action.replace("/files/add","/files/up");
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
	t=window.setTimeout(update_progress_info, 1000);
	if(go_to!=""){
	    location.href=go_to;
	}
    }
    t=window.setTimeout(update_progress_info, 1000);
    xhr.onreadystatechange = function() {
	if(xhr.readyState == 4){
	    if(xhr.status==200) {
	    	go_to = location.href;
	    	go_to = go_to.replace("/files/add","/files");
    	    }else{
	     	var fail_div = $("<div class='up_fail'></div>");
	     	var span_text="Your upload(s) failed!<br>Try again";
	     	if(nbr_files>1){
		    span_text+=" maybe with less files. ";
	     	}else{
		    span_text+=". ";
	     	}
		fail_div.append(span_text);
	     	$("#fileupload").after(fail_div);
		$(".progress .text").text(" ");
		$("progress").remove();
		$(".del_link").show();
		clearTimeout(t);
	    }
	}else{
	}
    }
    xhr.open("POST", new_action,true);
    data = new FormData(f_form);
    xhr.send(data);
}

var go_to ="";
var xhr = getXHR();
$(function(){
    if(xhr!=null){
    //if the browser has/supports xmlhttprequest object
    	$("input[type='file']").change(function (){
	    $(".up_fail").remove();
	    var key=this.files[0].name.replace(".","_");
	    if(files_info[key]==undefined){
	     	$("span.warning").remove();
	     	add_file(this);
	    }else{
	     	alert("vous avez déjà selectionner ce fichier");
	    }
    	});
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
		    $("#fileupload").find("input[type='file']").parent().append("<span class='warning'>Select at least one file</span>");
		}
		return;
	    }
	    $(".del_link").hide();
    	    $(".progress .text").text("0% (waiting)");
	    $(".progress").prepend("<progress max=100 value=0></progress>");
	    up_file($('form.form_queue')[0]);
    	});
    } else{
	//the browser does not have/support xmlhttprequest object
	//if javascript is disabled, noscript tag will handle that
	$("#fileupload").insertAfter("<span class='warning'>You can only upload one file</span>");
	$("#_up").click(function(){
	    if(nbr_files==0){
		$("#fileupload").find("input[type='file']").parent().append("<span class='warning'>Select at least one file</span>");
		return;
	    }
	    ("#fileupload").submit();
	});
    }
});
