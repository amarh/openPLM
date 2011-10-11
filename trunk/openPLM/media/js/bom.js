$(
function(){
    $(".expander").click(
        function() {
            var cls = $(this).attr("class");
            var level = /level\d+/.exec(cls)[0];
        }
    );
    

    }
);
