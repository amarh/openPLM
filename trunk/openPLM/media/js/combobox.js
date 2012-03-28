var make_combobox = function () {
/* 
     * Convert the ===> items to indented items
     */
    $("select[name=type], select[name$=type_part]").each(
        function (index) {
            $(this).find("option").each(
                function(i) {
                    var li = $(this);
                    var padding = 0;
                    var text = $.trim(li.text());

                    var result = /^([=>]*)(.*)/.exec(text);
                    li.text(result[2]);
                    padding = 20 * result[1].length;
                    if (padding > 0) {
                        li.addClass("indented");
                        li.text(result[2]);
                        li.css("padding-left", "+=" + padding);
                    }
                }
                );
            }
        
    );
    /* recompute the width of select elements */
    $("select[multiple!=multiple]").each(
        function (){
            var width = 0;
            $(this).find("option").each(
                function () {
                    width = Math.max($.trim($(this).text()).length, width);
                }
                );
            $(this).css("width", (width*0.6+1) + "em");
        }
    );
    $("select").chosen({disable_search_threshold: 7});

    $("div.chzn-container").addClass("ui-widget ui-button ui-state-default ui-corner-all");
    
    /* set the width of the drop-down menu */
    $("div.chzn-drop").each(
        function (){
            var width = 0;
            var div = $(this);
            div.find("li").each(
                function () {
                    width = Math.max($.trim($(this).text()).length, width);
                }
            );
            width *= 13;
            div.css("width", (width + 10));
            div.children("div.chzn-search:first")
                .children("input:first").width(width - 30);
            
        }
    );



}

$(
  make_combobox 

 );
