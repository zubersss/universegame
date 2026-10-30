"""Material overrides, one per map (contract §3.3). Each pass rewires every material of the
rendered objects to an Emission shader carrying exactly the value that map needs, so the
render is the map with no lighting in it.

Source-material conventions (what artists build in the .blend):
  - a Principled BSDF supplies Base Color, Alpha, Metallic, Emission Color/Strength, Normal
  - optional material custom property `meridian_rim` (0..1) -> mask R (interactive props)
  - a bare Emission node (no Principled) counts as emission with black albedo
The .blend is reopened before every pass, so overrides never need undoing.
"""
import bpy

SOCKET_ALIASES = {
    "base": ("Base Color",),
    "alpha": ("Alpha",),
    "metal": ("Metallic",),
    "emit": ("Emission Color", "Emission"),
    "emit_strength": ("Emission Strength",),
    "normal": ("Normal",),
}


def _inp(node, role):
    for name in SOCKET_ALIASES[role]:
        s = node.inputs.get(name)
        if s is not None:
            return s
    return None


def _source(nt, socket, fallback):
    """Return an output socket carrying `socket`'s value (its link or a constant node)."""
    if socket is not None and socket.is_linked:
        return socket.links[0].from_socket
    val = fallback if socket is None else socket.default_value
    if isinstance(val, float) or (socket is not None and socket.type == "VALUE"):
        n = nt.nodes.new("ShaderNodeValue")
        n.outputs[0].default_value = float(val if not hasattr(val, "__len__") else val[0])
    else:
        n = nt.nodes.new("ShaderNodeRGB")
        v = list(val)[:3]
        n.outputs[0].default_value = (v[0], v[1], v[2], 1.0)
    return n.outputs[0]


def _output_node(nt):
    outs = [n for n in nt.nodes if n.bl_idname == "ShaderNodeOutputMaterial"]
    for n in outs:
        if n.is_active_output:
            return n
    return outs[0] if outs else nt.nodes.new("ShaderNodeOutputMaterial")


def _find(nt, idname):
    for n in nt.nodes:
        if n.bl_idname == idname:
            return n
    return None


def _value_node(nt, v):
    n = nt.nodes.new("ShaderNodeValue")
    n.outputs[0].default_value = v
    return n.outputs[0]


def _rewire(mat, pass_name):
    if not mat.use_nodes:
        mat.use_nodes = True
    nt = mat.node_tree
    L = nt.links
    out = _output_node(nt)
    for o in [n for n in nt.nodes if n.bl_idname == "ShaderNodeOutputMaterial" and n != out]:
        o.is_active_output = False
    out.target = "ALL"
    pr = _find(nt, "ShaderNodeBsdfPrincipled")
    em_src = _find(nt, "ShaderNodeEmission")

    emit = nt.nodes.new("ShaderNodeEmission")
    emit.inputs["Strength"].default_value = 1.0

    if pass_name == "color":
        src = _source(nt, _inp(pr, "base") if pr else None, (0.0, 0.0, 0.0, 1.0) if em_src else (0.8, 0.8, 0.8, 1.0))
        L.new(src, emit.inputs["Color"])
    elif pass_name == "emission":
        if pr:
            col = _source(nt, _inp(pr, "emit"), (0, 0, 0, 1))
            stren = _source(nt, _inp(pr, "emit_strength"), 0.0)
        elif em_src:
            col = _source(nt, em_src.inputs["Color"], (0, 0, 0, 1))
            stren = _source(nt, em_src.inputs["Strength"], 1.0)
        else:
            col, stren = _source(nt, None, (0, 0, 0, 1)), _value_node(nt, 0.0)
        L.new(col, emit.inputs["Color"])
        L.new(stren, emit.inputs["Strength"])
    elif pass_name == "normal":
        nsock = _inp(pr, "normal") if pr else None
        if nsock is not None and nsock.is_linked:
            nvec = nsock.links[0].from_socket
        else:
            geo = nt.nodes.new("ShaderNodeNewGeometry")
            nvec = geo.outputs["Normal"]
        vt = nt.nodes.new("ShaderNodeVectorTransform")
        vt.vector_type = "NORMAL"
        vt.convert_from = "WORLD"
        vt.convert_to = "CAMERA"
        L.new(nvec, vt.inputs[0])
        ma = nt.nodes.new("ShaderNodeVectorMath")
        ma.operation = "MULTIPLY_ADD"
        # Blender's "Camera" vector space is +Z forward (into the scene); the contract wants
        # +Z toward the camera (OpenGL), so Z is flipped here.
        ma.inputs[1].default_value = (0.5, 0.5, -0.5)
        ma.inputs[2].default_value = (0.5, 0.5, 0.5)
        L.new(vt.outputs[0], ma.inputs[0])
        L.new(ma.outputs[0], emit.inputs["Color"])
    elif pass_name == "mask":
        comb = nt.nodes.new("ShaderNodeCombineColor")
        comb.inputs[0].default_value = float(mat.get("meridian_rim", 0.0))
        ao = nt.nodes.new("ShaderNodeAmbientOcclusion")
        ao.inputs["Distance"].default_value = float(mat.get("meridian_ao_distance", 0.5))
        L.new(ao.outputs["AO"], comb.inputs[1])
        L.new(_source(nt, _inp(pr, "metal") if pr else None, 0.0), comb.inputs[2])
        L.new(comb.outputs[0], emit.inputs["Color"])
    else:
        raise ValueError(f"unknown pass {pass_name}")

    shader = emit.outputs[0]
    asock = _inp(pr, "alpha") if pr else None
    if asock is not None and (asock.is_linked or asock.default_value < 1.0):
        mix = nt.nodes.new("ShaderNodeMixShader")
        tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        L.new(_source(nt, asock, 1.0), mix.inputs["Fac"])
        L.new(tr.outputs[0], mix.inputs[1])
        L.new(shader, mix.inputs[2])
        shader = mix.outputs[0]
    for l in list(out.inputs["Surface"].links):
        L.remove(l)
    L.new(shader, out.inputs["Surface"])
    if out.inputs.get("Displacement") is not None:
        for l in list(out.inputs["Displacement"].links):
            L.remove(l)


def apply(objects, pass_name):
    default = None
    done = set()
    for ob in objects:
        if ob.type not in {"MESH", "CURVE", "SURFACE", "META", "FONT", "CURVES"}:
            continue
        if not ob.material_slots or all(s.material is None for s in ob.material_slots):
            if default is None:
                default = bpy.data.materials.new("meridian_default")
                default.use_nodes = True
            if ob.data is not None and hasattr(ob.data, "materials"):
                ob.data.materials.append(default)
        for slot in ob.material_slots:
            m = slot.material
            if m is not None and m.name not in done:
                _rewire(m, pass_name)
                done.add(m.name)
