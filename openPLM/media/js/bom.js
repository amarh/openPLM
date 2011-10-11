function get_level(node){

    var cls = node.attr("class");
    var level = /level(\d+)/.exec(cls)[1];
    return Number(level);
}

function all(array) {
    var len = array.length;
    for (var i=0; i < len; i++) {
        if (! array[i]){
            return false;
        }
    }
    return true;
}

$(
function(){

    $("td.expander").click(function () {
        var row = $(this);
        var level = get_level(row);
        row.toggleClass("expanded open");
        var exps = new Array();
        exps.push(row.hasClass("open"));
        var nodes = row.parent().next().children('.expander');
        var is_child = nodes.size() != 0;
        var last_level = level;
        while (is_child){
            var node = nodes.first();
            var l = get_level(node);
            if (l > level){
                if (all(exps.slice(0, l-level))){
                    node.parent().show();
                }
                else {
                    node.parent().hide();
                }
                nodes = node.parent().next().children('.expander'); 
                is_child = nodes.size() != 0;
                if (l <= last_level){
                    exps = exps.slice(0, l-level);
                }
                exps.push(node.hasClass("open"));
                last_level = l;
            }
            else {
                is_child = false;
            }
        }

    });
}
);
