
import os.path

# extensions from http://en.wikipedia.org/wiki/List_of_file_formats#Computer-aided_design_.28CAD.29
# + fc*, brep, stp, idv
#: a set of CAD file extensions, all values are in lowercase and starts with a dot.
CAD_FORMATS = set((
    ".3dmlw", ".3dxml",
    ".acp", ".amf", ".ar", ".art", ".asc", ".asm", ".bin", ".bim",
    ".ccc", ".ccm", ".ccs", ".cad", ".catdrawing", ".catpart",
    ".catproduct", ".catprocess", ".cel", ".cgr", ".co",
    ".drw", ".dwg", ".dft", ".dgn", ".dgk", ".dmt", ".dxf", ".dwb", ".dwf",
    ".emb", ".esw", ".excellon", ".exp", ".fm", ".fmz",
    ".g", ".gerber", ".grb", ".gtc",
    ".iam", ".icd", ".idv", ".idw", ".ifc", ".iges", ".ipn", ".ipt", ".jt",
    ".mcd", ".model", ".ocd",
    ".par", ".prt", ".pln", ".psm", ".psmodel", ".pwi", ".pyt",
    ".rlf", ".rvt", ".rfa",
    ".scdoc", ".skp", ".sldasm", ".slddrw", ".sldprt", ".step", ".stp", ".stl",
    ".tct", ".tcw", ".unv", ".vc6", ".vlm", ".vs", ".wrl", ".xe",
    ".fcstd", ".fmacro", ".fscript", ".brep", ".brp",
))

def is_cad_file(filename):
    """
    Returns True if *filename* is a CAD file.
    Only tests if its extension is in :const:`CAD_FORMATS`.
    """
    name, ext = os.path.splitext(filename)
    return ext.lower() in CAD_FORMATS

