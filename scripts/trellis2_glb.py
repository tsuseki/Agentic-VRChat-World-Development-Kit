#!/usr/bin/env python3
"""Image -> GLB with a local TRELLIS.2 install, for the kit's `image-to-3d` tool.

Run it with the TRELLIS.2 environment's Python from inside the cloned TRELLIS.2 repo (the
`command` backend's "python" and "cwd" fields), e.g. in `.omp/local/tools.json`:

    {"backend": "command", "name": "trellis2", "python": "<trellis2 env python>",
     "cwd": "<path to TRELLIS.2 clone>",
     "args": ["{kit}/scripts/trellis2_glb.py", "--image", "{image}", "--faces", "{faces}",
              "--output", "{output}"], "timeout": 1800}

Follows the repo's minimal example (README "Image to 3D Generation"): needs an NVIDIA GPU with
24 GB+ and the repo's setup.sh dependencies. Upstream tests on Linux only.
"""
import argparse
import os

os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--image", required=True)
    ap.add_argument("--output", required=True, help=".glb path")
    ap.add_argument("--faces", default="", help="decimation target (faces); empty = 200000")
    ap.add_argument("--texture-size", type=int, default=2048)
    ap.add_argument("--model", default="microsoft/TRELLIS.2-4B")
    a = ap.parse_args()

    from PIL import Image
    import o_voxel
    from trellis2.pipelines import Trellis2ImageTo3DPipeline

    pipeline = Trellis2ImageTo3DPipeline.from_pretrained(a.model)
    pipeline.cuda()
    mesh = pipeline.run(Image.open(a.image))[0]
    mesh.simplify(16777216)  # nvdiffrast limit, as in the upstream example
    glb = o_voxel.postprocess.to_glb(
        vertices=mesh.vertices, faces=mesh.faces, attr_volume=mesh.attrs, coords=mesh.coords,
        attr_layout=mesh.layout, voxel_size=mesh.voxel_size,
        aabb=[[-0.5, -0.5, -0.5], [0.5, 0.5, 0.5]],
        decimation_target=int(a.faces) if a.faces else 200000,
        texture_size=a.texture_size, remesh=True, remesh_band=1, remesh_project=0, verbose=True)
    os.makedirs(os.path.dirname(os.path.abspath(a.output)), exist_ok=True)
    glb.export(a.output)
    print(f"TRELLIS2_OK {a.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
