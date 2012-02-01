$(
    function(){

        $("select[name=type]").each(
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
                                li.css("padding-left", "+=" +padding);
                            }
                        }
                        );
                }
            
        );
        $("select[multiple!=multiple]").each(
            function (){
                var size = 0;
                $(this).find("option").each(
                    function () {
                        var w = $.trim($(this).text()).length;
                        if (w > size){
                            size = w;
                        }
                    }
                    );
                $(this).css("width", (size*0.6+1) + "em");
                
            }
        );
        $("select").chosen({disable_search_threshold: 7});

        $("div.chzn-container").addClass("ui-widget ui-button ui-state-default ui-corner-all");
        $("div.chzn-container-single").addClass("selector");
      
        $("div.chzn-drop").css("width", "");
        $("div.chzn-drop").each(
            function (){
                var size = 0;
                var padding = 0;
                $(this).find("li").each(
                    function () {
                        var w = $.trim($(this).text()).length;
                        if (w > size){
                            size = w;
                        }
                        var p = $(this).css("padding-left");
                        if (p > padding) {
                            padding = p;
                        }
                    }
                    );
                size = size * 13 + padding;
                $(this).css("width", (size + 20));
                $(this).children("div.chzn-search:first")
                    .children("input:first").width(size -10);
                
            }
        );

        $("select.tiny").parent().addClass("tiny");

    }

 );
