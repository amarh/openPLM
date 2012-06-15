
//update the results block
function update_results(msg){
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
    
    //update link to search and create pages
    var req_type = $("#search_id_type").val();
    var req_q = $("#search_id_q").val();
    if (req_q==""){
        req_q="*";
    }
    var search_link = $("#DisplayBox").find("a[href^='/search']")[0];
    $(search_link).attr("href","/search/?type="+req_type+"&q="+req_q);
    if( req_type!="User"){
        var create_link = $("#DisplayBox").find("a[href^='/object/create']")[0];
        $(create_link).attr("href","/object/create/?type="+req_type);
    }
}

//launch the search request asynchronously
function perform_search(){
    var data ="navigate=" + $("div.Result").attr("navigate");
    data = data + "&type=" + $("#search_id_type").val();
    data = data +"&q=" + $("#search_id_q").val();
    $.ajax({
        type : "GET",
        url : "/perform_search/",
        data : data,
        success : function(msg){
            update_results(msg);
        } 
    });
}

$(function(){
    $("#SearchBox #search_button").click(function(e){
        if($("div.Result").attr("link_creation")!="true"){
            e.preventDefault();
            perform_search();
        }
    });
})
