"""
This module can generate a thumbnail of a STEP file using POVRay.
"""

import os
import shutil
import subprocess


def generate_pov(product, loc, mesh_ids, output):

    if not product.geometry:
        for link in product.links:
            for i in range(link.quantity):
                loc2=loc[:]
                loc2.append(link.locations[i])
                generate_pov(link.product, loc2, mesh_ids, output)

    else:
        mesh_id = "_%s_%s" % (product.geometry, product.doc_id)
        if mesh_id in mesh_ids:
            generate_object(loc, mesh_id, output)


def generate_object(loc, mesh_id, output):

    output.write( """
object {
    m%s
""" % mesh_id)

    if loc:
        for l in reversed(loc):
            output.write( """
    matrix < %f, %f, %f,
            %f, %f,%f,
            %f, %f,%f,
            %f, %f, %f >
    """ % (
            l.x1, l.y1, l.z1,
            l.x2, l.y2, l.z2,
            l.x3, l.y3, l.z3,
            l.x4, l.y4, l.z4,
        )
    )
    output.write("""
    translate Trans
    scale Scale
    texture { t%s }

}
""" % mesh_id)

pov_tpl = """#include "math.inc"
#include "finish.inc"
#include "transforms.inc"


background {color rgb 1}

light_source {
        <-10,-45,200>
        rgb 1
        shadowless
}

global_settings {
  assumed_gamma 2
}

camera {
        orthographic
        location <0,200,0>
        rotate <23,0,-135>
        look_at <0,0,0>
}

sky_sphere
{
	pigment
	{
		gradient y
		color_map
		{
			[0.0 rgb <1.0,1.0,1.0>]		//153, 178.5, 255	//150, 240, 192
			[0.7 rgb <0.9,0.9,0.9>]		//  0,  25.5, 204	//155, 240, 96
		}
		scale 2
		translate 1
	}
}

"""


def create_thumbnail(product, step_importer, pov_dir, thumb_path):
    path = os.path.join(pov_dir, "step.pov")
    thumb = os.path.join(pov_dir, "step.png")

    with open(path, "w") as f:
        mesh_ids = set()
        for p, id_ in step_importer.povs:
            f.write('#include "%s"\n' % p)
            mesh_ids.add(id_)
        f.write(pov_tpl)
        f.write("#declare Scale = %f; \n" % step_importer.scale)
        f.write("#declare Trans = <%f, %f, %f>; \n" % step_importer.trans)
        generate_pov(product, [], mesh_ids, f)
        f.close()
    with open(os.devnull, "w") as null:
        args = ["povray", "-GA", "-I"+path, "-O"+thumb,
                "-H400", "-W400",
                "+A", "+AM2", "+Q9", "-d", "+WL0"]
        try:
            ret = subprocess.call(args, cwd=pov_dir, stdout=null, stderr=null)
        except OSError:
            # could not call povray
            ret = 1
    if ret == 0 and os.path.exists(thumb):
        shutil.copy2(thumb, thumb_path)
    shutil.rmtree(pov_dir, True)

