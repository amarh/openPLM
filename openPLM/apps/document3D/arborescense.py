from django.utils.html import escape

class JSGenerator(object):

    _header = """var object3D = new THREE.Object3D();
var part_to_object = {};
var part_to_parts = {};
var part0 = new THREE.Object3D();
"""
    _function_head = """
function change_part%(counter)s(attr) {
    if (attr == "click"){
        part%(counter)s.visible=!part%(counter)s.visible;
    }
    else{
        part%(counter)s.visible=attr;
    }
    var span = $("#li-part-%(counter)s");
    if (part%(counter)s.visible){
        span.removeClass("part_hidden");
    }
    else {
        span.addClass("part_hidden");
        var li = span.parent();
        li.addClass("expanded").removeClass("open");
        li.children("ul").hide();
    }
"""

    _function_change_part = """
    change_part%(child_counter)s(part%(counter)s.visible);
    """
    _function_change_object = """
    object%(object_counter)s.visible=part%(counter)s.visible;
    """

    _menu_tpl = """
function menu() {
    element = document.createElement("ul");
    element.id="tree";
    element.innerHTML ="%s</li></ul>";
    document.getElementById("menu_").appendChild(element);
}
"""
    def __init__(self, product):
        self.product = product
        self.menu_items = []
        self.js = []
        self.counter = 0
        self.locations = []

    def get_js(self):
        if not self.product:
            return ""
        self.menu_items.append(self._get_menu_item(0, self.product.name, self.product.geometry))
        self._process(self.product, [], self.counter)
        return self._header + self._get_menu() + "".join(self.js)

    def _process(self, product, locations, old_counter):
        self.counter += 1
        self.menu_items.append("<ul>")
        if product.geometry:
            self._add_object3d(old_counter, self.counter, product, locations)
        else:
            generated_parts = []
            for link in product.links:
                for i in range(link.quantity):
                    loc2 = locations[:]
                    loc2.append(link.locations[i])
                    generated_parts.append(self.counter)
                    self.menu_items.append(self._get_menu_item(self.counter, link.names[i],
                        link.product.geometry))
                    self._process(link.product, loc2, self.counter)
                    self.menu_items.append("</li>")
            self._add_parts(old_counter, generated_parts)
        self.menu_items.append("</ul>")

    def _get_menu(self):
        return self._menu_tpl % ("".join(self.menu_items))

    def _add_parts(self, counter, generated_parts):
        parts_definition = []
        function = [self._function_head % locals()]
        part_to_parts = ['part_to_parts["part%s"] = [' % counter]
        for child_counter in generated_parts:
            parts_definition.append("var part%s=new THREE.Object3D();\n" % child_counter)
            function.append(self._function_change_part % locals())
            part_to_parts.append('"part%s", ' % child_counter)
        part_to_parts.append("];\n")
        function.append("}\n")
        self.js.extend(parts_definition)
        self.js.extend(function)
        self.js.extend(part_to_parts)

    def _add_object3d(self, counter, object_counter, product, loc):
        reference = product.geometry
        part_id = str(product.doc_id)
        js = self.js
        function = ((self._function_head + self._function_change_object
                + "}\npart_to_object['part%(counter)s'] = object%(object_counter)s;\n"
                + "object%(object_counter)s.part = '%(counter)s';\n") % locals())

        counter = object_counter
        js.append("var object%s=new THREE.Mesh(_%s_%s,material_for_%s_%s );\n"%(counter, reference,
            part_id, reference, part_id))
        js.append("object%s.matrixAutoUpdate = false;\n" % counter)
        for l in loc:
            js.append("""
object%s.matrix.multiplySelf(new THREE.Matrix4(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,0,0,0,1));\n"""
                % (counter, l.x1, l.x2, l.x3, l.x4,
                            l.y1, l.y2, l.y3, l.y4,
                            l.z1, l.z2, l.z3, l.z4))
        js.append("object3D.add(object%s);\n" % counter)
        js.append(function)

    def _get_menu_item(self, counter, name, is_child):
        onclick = 'change_part%d(\\"click\\");' % counter
        name = escape(name)
        if is_child:
            li = ("<li><span class='part' id='li-part-{counter}' onClick='{onclick}'>{name}</span>&nbsp;"
            "<span id='color-{counter}'>&nbsp;&nbsp;</span>")
        else:
            li = ("<li class='open expander'><span class='expander'></span>"
                    "<span class='part' id='li-part-{counter}' onClick='{onclick}'>{name}</span>")
        return li.format(counter=counter, name=name, onclick=onclick)


