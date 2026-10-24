"""Headless Blender: connectivity stats of a mesh file (FBX/GLB): components, non-manifold edges, boundary edges.
Usage: python .omp/scripts/tool.py blender --script mesh_stats.py -- <in.fbx|in.glb>
Prints: STATS faces=.. components=.. top=[largest piece sizes] singles=.. boundaryEdges=.. nonManifoldEdges=..
"""
import bpy, bmesh, sys, os
argv = sys.argv[sys.argv.index("--") + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
p = os.path.abspath(argv[0])
(bpy.ops.import_scene.fbx if p.lower().endswith(".fbx") else bpy.ops.import_scene.gltf)(filepath=p)
ob = [o for o in bpy.context.scene.objects if o.type == "MESH"][0]
bm = bmesh.new(); bm.from_mesh(ob.data)
seen, sizes = set(), []
for f in bm.faces:
    if f.index in seen: continue
    stack, n = [f], 0; seen.add(f.index)
    while stack:
        x = stack.pop(); n += 1
        for e in x.edges:
            for g in e.link_faces:
                if g.index not in seen: seen.add(g.index); stack.append(g)
    sizes.append(n)
sizes.sort(reverse=True)
bnd = sum(1 for e in bm.edges if len(e.link_faces) == 1)
nm = sum(1 for e in bm.edges if len(e.link_faces) > 2)
tris = sum(len(f.verts) - 2 for f in bm.faces)
print(f"STATS faces={len(bm.faces)} tris={tris} components={len(sizes)} top={sizes[:12]} singles={sum(1 for s in sizes if s<=4)} boundaryEdges={bnd} nonManifoldEdges={nm}")
