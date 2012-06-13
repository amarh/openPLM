
function update_results(msg){
    var response = $(msg);
    var hr_element = response.find("hr")[0];
    var res_div = response.find("div.Result")[0];
    $.each($(res_div).find("div.reference"), function(i,v){
        var link =$(v).find("a")[0];
        var span_link = $(link).next("span");
        $(link).append(span_link);
    });
    var searchBox=$(res_div).parent()[0];
    var searchBox_class = $(searchBox).attr("class");
    $("#SearchBox").attr("class",searchBox_class);
    $("#SearchBox > div.Result").replaceWith(res_div);
    $("#SearchBox hr").replaceWith(hr_element);
    init();

}

function perform_search(){
    var url = location.href;
    url = url.split("navigate")[0];
    url = url+"navigate/perform_search/";
    var data = "type=" + $("#search_id_type").val();
    data = data +"&q=" + $("#search_id_q").val();
    $.ajax({
        type : "GET",
        url : url,
        data : data,
        success : function(msg){
            update_results(msg);
        } 
    })
}

$(function(){
    $("#search_button").click(function(e){
        e.preventDefault();
        perform_search();
    });
})
