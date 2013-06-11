jQuery.cachedScript = function(url, success, options) {
    // allow user to set any option except for dataType, cache, and url
    options = $.extend(options || {}, {
        dataType: "script",
        cache: true,
        success: success,
        url: url
    });
    // Use $.ajax() since it is more flexible than $.getScript
    // Return the jqXHR object so we can chain callbacks
    return jQuery.ajax(options);
};
// from http://api.jquery.com/jQuery.getScript/#comment-34269778
jQuery.getScripts = function(scripts, onComplete) {
    var i = 1;
    var ii = scripts.length;
    var onScriptLoaded = function(data, response) { if (i++ == ii) onComplete(); } ;
    for(var s in scripts) { $.cachedScript(scripts[s], onScriptLoaded); } ;
};
/**
* old AxisHelper
* @author sroucheray / http://sroucheray.org/
* @author mrdoob / http://mrdoob.com/
*/

THREE.AxisHelper = function () {

THREE.Object3D.call( this );

var lineGeometry = new THREE.Geometry();
lineGeometry.vertices.push( new THREE.Vector3() );
lineGeometry.vertices.push( new THREE.Vector3( 0, 100, 0 ) );

var coneGeometry = new THREE.CylinderGeometry( 0, 5, 25, 5, 1 );

var line, cone;

// x

line = new THREE.Line( lineGeometry, new THREE.LineBasicMaterial( { color : 0xff0000 } ) );
line.rotation.z = - Math.PI / 2;
this.add( line );

cone = new THREE.Mesh( coneGeometry, new THREE.MeshBasicMaterial( { color : 0xff0000 } ) );
cone.position.x = 100;
cone.rotation.z = - Math.PI / 2;
this.add( cone );

// y

line = new THREE.Line( lineGeometry, new THREE.LineBasicMaterial( { color : 0x00ff00 } ) );
this.add( line );

cone = new THREE.Mesh( coneGeometry, new THREE.MeshBasicMaterial( { color : 0x00ff00 } ) );
cone.position.y = 100;
this.add( cone );

// z

line = new THREE.Line( lineGeometry, new THREE.LineBasicMaterial( { color : 0x0000ff } ) );
line.rotation.x = Math.PI / 2;
this.add( line );

cone = new THREE.Mesh( coneGeometry, new THREE.MeshBasicMaterial( { color : 0x0000ff } ) );
cone.position.z = 100;
cone.rotation.x = Math.PI / 2;
this.add( cone );

};

THREE.AxisHelper.prototype = Object.create( THREE.Object3D.prototype );
$(function() {
    if ( !window.requestAnimationFrame ) {

        window.requestAnimationFrame = window.webkitRequestAnimationFrame ||
                                       window.mozRequestAnimationFrame ||
                                       window.oRequestAnimationFrame ||
                                       window.msRequestAnimationFrame ||
        function( /* function FrameRequestCallback */ callback, /* DOMElement Element */ element ) {

            window.setTimeout( callback, 1000 / 60 );

        };
    }  
});
View3D = function(has_menu, stl_file, js_files) {

    this.has_menu = has_menu;
    this.stl_file = stl_file;
    this.js_files = js_files;
    this.zoom_var=50;	
}


View3D.prototype = {

    constructor: View3D,

    menu: window.menu || null,
    part_to_object : window.part_to_object || {},
    part_to_parts : window.part_to_parts || {},
    object3D : window.object3D || null,

    render: function (){
        var self = this;
        $("#main_content").showLoading();
        if (this.stl_file !== null) {
            var xhr = new XMLHttpRequest();
            geometry = new THREE.Geometry();
            self.object3D = new THREE.Object3D();
            self.part_to_object = {};
            self.part_to_parts = {};
            self.part0=new THREE.Object3D();
            material_for_geometry = new THREE.MeshBasicMaterial({opacity:1,shading:THREE.SmoothShading});
            material_for_geometry.color.setRGB(0.4,0.3,0.3);
            self.object2=new THREE.Mesh(geometry, material_for_geometry );
            xhr.open('GET', this.stl_file, true);
            xhr.responseType = 'arraybuffer';

            xhr.onload = function(e) {
                var data = new Uint8Array(xhr.response);
                var t = Struct.Unpack("=80sI", data);
                var nbf = t[1];
                var is_text = String.fromCharCode.apply(null,data.subarray(0, 6)) == "solid ";
                is_text = is_text && (nbf*50+80 != data.length);
                if (is_text) {
                    var text = "";
                    for (var i=0; i<data.length; i+= 1000){
                        text += String.fromCharCode.apply(null, data.subarray(i, Math.min(i+1000, data.length)));
                    }
                    // strip out extraneous stuff
                    text = text.replace(/\r/, "\n");
                    text = text.replace(/^solid[^\n]*/, "");
                    text = text.replace(/\n/g, " ");
                    text = text.replace(/facet normal /g,"");
                    text = text.replace(/outer loop/g,"");
                    text = text.replace(/vertex /g,"");
                    text = text.replace(/endloop/g,"");
                    text = text.replace(/endfacet/g,"");
                    text = text.replace(/endsolid[^\n]*/, "");
                    text = text.replace(/\s+/g, " ");
                    text = text.replace(/^\s+/, "");
                    var points = text.split(" ");
                    var i,j,len= parseInt(points.length/ 12) * 12;
                    for (i=0, j=0; i<len; i+=12, j+=3){
                        for (var k= 0; k<3; k++){
                            var f1 = parseFloat(points[i + k * 3 + 3]);
                            var f2 = parseFloat(points[i + k * 3 + 4]);
                            var f3 = parseFloat(points[i + k * 3 + 5]);
                            geometry.vertices.push(new THREE.Vertex(new THREE.Vector3(f1, f2, f3)));
                        }
                        geometry.faces.push(new THREE.Face3(j, j+1, j+2));
                    }
                } else {
                    var i,j,len=data.length;
                    for (i=84, j=0; i<len; i+=50, j+=3){
                        var f = Struct.Unpack("<ffffffffffffxx", data, i);
                        geometry.vertices.push(new THREE.Vertex(new THREE.Vector3(f[3],f[4],f[5])));
                        geometry.vertices.push(new THREE.Vertex(new THREE.Vector3(f[6],f[7],f[8])));
                        geometry.vertices.push(new THREE.Vertex(new THREE.Vector3(f[9],f[10],f[11])));
                        geometry.faces.push(new THREE.Face3(j, j+1, j+2));
                    }
                }

                geometry.computeFaceNormals();

                self.object2.matrixAutoUpdate = false;
                self.object3D.add(self.object2);
                self.part_to_object['part2'] = self.object2;
                self.init();
                $("#main_content").hideLoading();
                self.animate();

            };

            xhr.send();
        }
        else {
            jQuery.getScripts(self.js_files, function (){
                build_tree();
                self.menu =  window.menu;
                self.part_to_object = window.part_to_object || {};
                self.part_to_parts = window.part_to_parts || {};
                self.object3D = window.object3D || null;
                self.init();
                $("#main_content").hideLoading();
                self.animate();
            });
        }

    },

    init: function () {

        if (!this.has_webgl()){
            document.getElementById("webgl_warning").style.display = 'block'; 
        }
        else{
            var self = this;
            this.container=document.getElementById('main_content');
            var container = this.container;

            this.scene = new THREE.Scene();
            var scene = this.scene;
            // init the lights

            this.ambient = new THREE.AmbientLight( 0xffffff, 1.1 );
            this.ambient.shadowDarkness = 0.001;
            scene.add(this.ambient );

            var light   = new THREE.DirectionalLight( 0xffffff, 1.2 );
            light.position.set(1, 1, 4 ).normalize();
            this.spot1 = light;
            light.shadowDarkness = 0.05;
            scene.add( light );

            var light   = new THREE.SpotLight( 0xffffff, 1.1 );
            this.spot2   = light;
            light.target.position.set( 0, 10, 0 ).normalize();
            light.shadowCameraNear = 0.01;     
            light.castShadow = true;
            light.shadowDarkness = 0.005;
                     

            light.shadowCameraRight     =  5;
            light.shadowCameraLeft     = -5;
            light.shadowCameraTop      =  5;
            light.shadowCameraBottom   = -5;

            scene.add( light );

            this.center_object(this.object3D);
            for (var i=0; i < this.object3D.children.length; i++) {
                var obj = this.object3D.children[i];
                var geo = THREE.GeometryUtils.clone(obj.geometry);
                obj.geometry.deallocate();
                delete obj.geometry;
                geo.computeBoundingSphere();
                geo.computeCentroids();
                geo.computeFaceNormals();
                obj.receiveShadow=true;
                obj.castShadow=true;
                var color = obj.material.color.getHex();
                obj.material.deallocate();
                obj.geometry = geo;

                obj.material = new THREE.MeshPhongMaterial({
                    ambient		: 0x000000, 
                    shininess	: 200, 
                    specular	: color,
                    shading		: THREE.FlatShading,
                    color: color,
                    side: THREE.DoubleSide,
                    depthTest: true,
                    opacity: 0.8
                });
                

                obj.material.original_step_color = obj.material.color.getHex(); 
                obj.material.original_color = obj.material.color.getHex(); 
                obj.material.original_opacity = obj.material.opacity; 
            }
            this.object3D.castShadow = true;
            this.object3D.receiveShadow = true;
            this.dummy = new THREE.Object3D();
            this.dummy.add( this.object3D);
            var axis = new THREE.AxisHelper();
            axis.position = this.object3D.position.clone().multiplyScalar(1.3);
            axis.scale.x = axis.scale.y = axis.scale.z = this.radius / 600;
            this.dummy.add(axis);
            scene.add(this.dummy);
            this.axis = axis;
            this.toggle_axis();

            camera = new THREE.PerspectiveCamera( 40, $(container).width() / $(container).height(),
                                                 this.radius/50, this.radius*200);
            camera.position.z = this.radius*1.5;
            this.camera = camera;

            renderer = new THREE.WebGLRenderer({
                antialias		: true,	// to get smoother output
                preserveDrawingBuffer	: true	// to allow screenshot
            });
            renderer.shadowMapCullFrontFaces = false;
            this.renderer = renderer;
            this.width = $(container).width();
            this.height = $(container).height();

            renderer.setSize(this.width , this.height);
            renderer.shadowMapEnabled	= true;
            renderer.shadowMapSoft		= true;
            container.appendChild( renderer.domElement );

            this.controls = new THREE.TrackballControls( camera, renderer.domElement );
            this.spot1_controls = new THREE.TrackballControls( this.spot1, renderer.domElement );
            this.spot2_controls = new THREE.TrackballControls( this.spot2, renderer.domElement );

            var ctrls = [this.controls, this.spot1_controls, this.spot2_controls ];
            for (var i = 0; i < ctrls.length; i++) {
                var ctrl = ctrls[i];
                ctrl.rotateSpeed = 1.0;
                ctrl.zoomSpeed = 1.2;
                ctrl.panSpeed = 0.2;
                ctrl.noZoom = true;
                ctrl.noPan = false;
                ctrl.staticMoving = false;
                ctrl.dynamicDampingFactor = 0.3;
                ctrl.minDistance = 0;
                ctrl.maxDistance = this.radius * 1000;
                ctrl.keys = [ 65, 83, 68 ]; // [ rotateKey, zoomKey, panKey ] [A,S,D]               
            }
            
            if (this.has_menu){ 
                this.menu();
                for (var i=0; i < this.object3D.children.length; i++) {
                    var obj = this.object3D.children[i];
                    $("#color-"+ obj.part).css("background-color", obj.material.color.getContextStyle());
                }
                $("span.expander").click(function () {
                    var row = $(this).parent();
                    row.toggleClass("expanded open");
                    var nodes = row.children('ul');
                    nodes.toggle();
                });

                $('.menu .part').hover(
                    function (){
                        var part = "part" + $(this).attr("id").replace("li-part-", "");
                        self.highlight_part(part);
                    },
                    function () {
                        var part = "part" +  $(this).attr("id").replace("li-part-", "");
                        self.unhighlight_part(part);
                    }
                );
            }

            container.focus();
            $('html, body').animate({scrollTop: $(container).offset().top}, 750);

            renderer.render(scene, camera); 

            $( "#zoom" ).slider({
                orientation: "vertical",
                min: 0,
                max: 100,
                value: 50,
                slide: function( event, ui ) {
                    total=self.zoom_var-ui.value;
                    self.zoom_var=ui.value;
                    camera.translateZ(1.5 *self.radius*(total/50));
                }

            });

            $("#zoom-fit-all").button().click(function() {
                self.set_scale(50);
            });
            $("#zoom-in").button().click(function () {
                if (self.zoom_var < 100){
                    self.set_scale(Math.min(self.zoom_var + 10, 100));
                }
            });
            $("#zoom-out").button().click(function () {
                if (self.zoom_var > 0){
                    self.set_scale(Math.max(self.zoom_var - 10, 0));
                }
            });

            s = function(f){
                return function(e){ return self[f](e);};
            }
            renderer.domElement.addEventListener( 'mousewheel', s("mousewheel"), false );
            renderer.domElement.addEventListener( 'DOMMouseScroll', s("mousewheel"), false );
            $("#colors-toolbar").buttonset();
            $("#random-color").button({text:false, icons:{primary:'random'}}).click(s("random_color"));
            $("#initial-color").button({text:false, icons:{primary:'axo'}}).click(s("reinit_color"));

            $("#views-toolbar").buttonset();
            $("#view-axo").button({text:false, icons:{primary:'axo'}}).click(s("view_axometric"));
            $("#view-top").button({text:false, icons:{primary:'top'}}).click(s("view_top"));
            $("#view-bottom").button({text:false, icons:{primary:'bottom'}}).click(s("view_bottom"));
            $("#view-left").button({text:false, icons:{primary:'left'}}).click(s("view_left"));
            $("#view-right").button({text:false, icons:{primary:'right'}}).click(s("view_right"));
            $("#view-front").button({text:false, icons:{primary:'front'}}).click(s("view_front"));
            $("#view-rear").button({text:false, icons:{primary:'rear'}}).click(s("view_rear"));

            $("#transparency").button({text:false, icons:{primary:'transparency'}}).click(s("toggle_transparency"));
            $("#axis").button({text:false, icons:{primary:'axis'}}).click(s("toggle_axis"));

            $("#toolbar, #zoom-toolbar").show();

            $("#full-screen").click(s("fullscreen"));
            screenfull.onchange = function() {
                var main = $(window);
                var w, h;
                if( screenfull.isFullscreen ) {
                    w = main.width() *0.95;
                    h = main.height() * 0.95;
                } else {
                    w = self.width;
                    h = self.height;
                }
                renderer.setSize(w, h);
                camera.aspect = w / h;
                camera.updateProjectionMatrix();
                self.center_object(self.object3D);
            };
        }
    },			

    fullscreen: function(){
        var main = document.getElementById("main_content");
         if (screenfull.enabled) {
             screenfull.toggle(main);
        }
    },
    set_scale : function (factor) {
        total=this.zoom_var-factor;
        this.zoom_var=factor;
        this.camera.translateZ(1.5 * this.radius*(total/50));
        $("#zoom").slider("value", factor);
    },

    mousewheel : function (event ) {
        event.preventDefault();
        event.stopPropagation();
        var delta = 0;

        if ( event.wheelDelta ) { // WebKit / Opera / Explorer 9
            delta = event.wheelDelta / 40;
        } else if ( event.detail ) { // Firefox
            delta = - event.detail * 1.5;
        }
        var factor = this.zoom_var + delta;
        if (factor >= 5 && factor <= 100){
            this.set_scale(factor);
        }
    },

    highlight_part : function (part_id) {

        var obj = this.part_to_object[part_id];
        if (obj != undefined){
            m = obj.material;
            m.color.setHex(0xff0000);
        }
        var self = this;
        $(this.part_to_parts[part_id]).each (
            function (i,p) {
                self.highlight_part(p);
            }
        );
    },

    unhighlight_part : function (part_id) {
        var obj = this.part_to_object[part_id];
        if (obj != undefined){
            m =  obj.material;
            m.color.setHex(m.original_color);
        }
        var self = this;
        $(this.part_to_parts[part_id]).each (
            function (i,p) {
                self.unhighlight_part(p);
            }
        );
    },

    has_webgl : function(){
        return !!window.WebGLRenderingContext;
    },

    center_object : function(object3D){ 	

        var boundingBox= this.computeGroupBoundingBox(object3D);

        width =Math.abs(boundingBox.x[ 1 ]-boundingBox.x[ 0 ]);
        height =Math.abs(boundingBox.y[ 1 ]-boundingBox.y[ 0 ]);
        deep =Math.abs(boundingBox.z[ 1 ]-boundingBox.z[ 0 ]);

        this.radius=Math.max(width,height,deep);

        object3D.position.x=-(boundingBox.x[ 0 ]+boundingBox.x[ 1 ])/2;
        object3D.position.y=-(boundingBox.y[ 0 ]+boundingBox.y[ 1 ])/2;  
        object3D.position.z=-(boundingBox.z[ 0 ]+boundingBox.z[ 1 ])/2; 

    },

    animate : function() {
        var self = this;
        var main = $("#main_content");
        anim = function (){
            requestAnimationFrame(anim);
            self.controls.update();
            self.spot1_controls.update();
            self.spot2_controls.update();
            self.renderer.render( self.scene, self.camera );
        }
        anim();
    },


    computeGroupBoundingBox : function(Object_Group) {   
        var boundingBox;
        for ( var v = 0 ;v  < Object_Group.children.length; v ++ ) {
            var geo=THREE.GeometryUtils.clone(Object_Group.children[v].geometry);
            geo.applyMatrix(Object_Group.children[v].matrix);
            geo.computeBoundingBox();
            BB=geo.boundingBox;
            if (BB){    
                if(!boundingBox){
                    boundingBox= { 
                        'x':[BB.min.x, BB.max.x],
                        'y':[BB.min.y, BB.max.y],
                        'z':[BB.min.z, BB.max.z]
                    }; 
                }
                else{
                    boundingBox.x[0]=Math.min(BB.min.x, boundingBox.x[0]);
                    boundingBox.y[0]=Math.min(BB.min.y, boundingBox.y[0]);
                    boundingBox.z[0]=Math.min(BB.min.z, boundingBox.z[0]);
                    boundingBox.x[1]=Math.max(BB.max.x, boundingBox.x[1]);
                    boundingBox.y[1]=Math.max(BB.max.y, boundingBox.y[1]);
                    boundingBox.z[1]=Math.max(BB.max.z, boundingBox.z[1]);
                }
            }   
            geo.deallocate();
        }
        return boundingBox;
    },

    random_color : function(){
        var object3D = this.object3D;
        for (var i=0; i < object3D.children.length; i++) {
            var obj = object3D.children[i];
            // avoid darkest colors
            obj.material.color.setHSV(Math.random(), Math.random() * 0.3+0.7, Math.random()*0.4+0.6);
            obj.material.original_color = obj.material.color.getHex();
            $("#color-"+ obj.part).css("background-color", obj.material.color.getContextStyle());
        }
    },

    reinit_color: function(){
        var object3D = this.object3D;
        for (var i=0; i < object3D.children.length; i++) {
            var obj = object3D.children[i];
            obj.material.color.setHex(obj.material.original_step_color);
            obj.material.original_color = obj.material.original_step_color;
            $("#color-"+ obj.part).css("background-color", obj.material.color.getContextStyle());
        }
    },

    toggle_transparency: function() {
        var object3D = this.object3D;
        if ($('#transparency').is(':checked')){
            for (var i=0; i < object3D.children.length; i++) {
                var obj = object3D.children[i];
                obj.material.opacity = obj.material.original_opacity;
            }
        } else {
            for (var i=0; i < object3D.children.length; i++) {
                var obj = object3D.children[i];
                obj.material.opacity = 1;
            }
        }
    },

    toggle_axis : function() {
        var visible = $('#axis').is(':checked');
        for (var i=0; i < this.axis.children.length; i++) {
            var obj = this.axis.children[i];
            obj.visible = visible;
        }
    },
    reinit_rotation : function() {
        this.dummy.rotation.set(0,0,0).addSelf(this.camera.rotation.clone());
        this.dummy.updateMatrix();
    },

    // rotateAroundObjectAxis
    // from http://stackoverflow.com/questions/11060734/how-to-rotate-a-3d-object-on-axis-three-js?rq=1
    // by Cory Gross, CC-BY-SA
    rotateAroundObjectAxis : function(object, axis, radians) {
        var rotObjectMatrix = new THREE.Matrix4();
        rotObjectMatrix.makeRotationAxis(axis.normalize(), radians);
        object.matrix.multiplySelf(rotObjectMatrix);      // post-multiply
        object.rotation.setEulerFromRotationMatrix(object.matrix);
    },

    view_rear : function (){
        this.view_front();
        this.rotateAroundObjectAxis(this.dummy, new THREE.Vector3(0,0,1), Math.PI);
    },

    view_top : function() {
        this.reinit_rotation();
    },

    view_front : function() {
        this.reinit_rotation();
        this.rotateAroundObjectAxis(this.dummy, new THREE.Vector3(1,0,0), -Math.PI/2);
        this.dummy.updateMatrix();
    },

    view_left : function() {
        this.view_front();
        this.rotateAroundObjectAxis(this.dummy, new THREE.Vector3(0,0,1), Math.PI/2);
    },

    view_right : function () {
        this.view_front();
        this.rotateAroundObjectAxis(this.dummy, new THREE.Vector3(0,0,1), -Math.PI/2);
    },

    view_bottom : function() {
        this.reinit_rotation();
        this.rotateAroundObjectAxis(this.dummy, new THREE.Vector3(1,0,0), Math.PI);
    },

    view_axometric : function() {
        this.view_front();
        this.rotateAroundObjectAxis(this.dummy, new THREE.Vector3(0,0,1), -Math.sqrt(2)/2);
        this.dummy.updateMatrix();
        this.rotateAroundObjectAxis(this.dummy,
            new THREE.Vector3(Math.sin(Math.sqrt(2)/2), Math.cos(Math.sqrt(2)/2),0), Math.PI/6);
    }
};


