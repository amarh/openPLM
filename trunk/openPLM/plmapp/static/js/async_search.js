
function get_search_query(data) {
    return "?type="+data.type+"&q="+data.q+ "&search_official="+data.search_official;
}

//update the results block
function update_results(msg, data){
    var response = $(msg);
    
    // get the results block
    var res_div = response.find("div.Result")[0];
    $.each($(res_div).find("div.reference"), function(i,v){
        var link =$(v).find("a")[0];
        var span_link = $(link).next("span");
        $(link).append(span_link);
    });
    
    /*var searchBox=$(res_div).parent()[0];
    var searchBox_class = $(searchBox).attr("class");
    $("#SearchBox").attr("class",searchBox_class);*/
    $("#SearchBox > div.Result").replaceWith(res_div);
    if($(res_div).attr("navigate")=="true"){
        init();
    }
    
    data.q = encodeURIComponent(data.q);
    //update link to search and create pages
    var search_link = $("#DisplayBox").find("a[href^='/search']");
    $(search_link).attr("href","/search/" + get_search_query(data));
    if( data.type != "User" && data.type != "all"){
        var create_link = $("#DisplayBox").find("a[href^='/object/create']");
        $(create_link).attr("href","/object/create/?type="+data.type);
    }
    
    //update link on ADD button for bom and doccad pages
    if (typeof(window.update_add_param)=='function'){
        update_add_param(data);
    }
}

//launch the search request asynchronously
function perform_search(){
    var data = {
        navigate : $("div.Result").attr("navigate"),
        type :  $("#search_id_type").val(),
        q : $("#search_id_q").val(),
        search_official: ($("#search_id_search_official").is(':checked')? "on" : "") 
    }
    $.get("/perform_search/", data, function (r) {update_results(r, data);});
}

$(function(){
    $("#SearchBox #search_button").click(function(e){
        if($("div.Result").attr("link_creation")!="true"){
            e.preventDefault();
            perform_search();
        }
    });
})
