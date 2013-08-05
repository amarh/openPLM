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

    $("div.chzn-container>a").addClass("tb-btn");
    
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

    function () {
        make_combobox(); 

        $("#navigation_history li").hoverIntent({
            over: function() {
                $("#navigation_history").find("div.quick_link").hide();
                var top = $(this).offset().top - $("html").scrollTop() + $(this).height() + 5;
                $(this).find("div.quick_link").css({
                    "top" : top + "px",
                    "min-width" : $(this).width() + "px"
                }).show();
            },
            timeout: 600,
            out: function() {
                $(this).find("div.quick_link").hide();
            }
        });

        $("#SetLangForm select").change(function () {
            $("#SetLangForm").submit()
        });
        $("#SetLangForm input[type=submit]").hide();
        $(".timeline dd").hover(
            function () {
                $(this).prev().addClass("active");
            },
            function () {
                $(this).prev().removeClass("active");
            }
        );
    }
);
