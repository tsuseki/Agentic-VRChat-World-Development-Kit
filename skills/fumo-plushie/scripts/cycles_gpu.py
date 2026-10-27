"""Cycles on the GPU for headless Blender scripts: OptiX, else CUDA/HIP/Metal/oneAPI, else CPU (printed).
Use: sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from cycles_gpu import use_gpu; use_gpu(scene)
(not "gpu": that name is Blender's built-in module)"""
import bpy


def use_gpu(sc):
    sc.render.engine = "CYCLES"
    pr = bpy.context.preferences.addons["cycles"].preferences
    for kind in ("OPTIX", "CUDA", "HIP", "METAL", "ONEAPI"):
        try:
            pr.compute_device_type = kind
        except TypeError:
            continue
        pr.get_devices()
        devs = [d for d in pr.devices if d.type == kind]
        if devs:
            for d in pr.devices:
                d.use = d.type == kind
            sc.cycles.device = "GPU"
            print(f"CYCLES_DEVICE {kind} {[d.name for d in devs]}", flush=True)
            return kind
    sc.cycles.device = "CPU"
    print("CYCLES_DEVICE CPU (no GPU backend found)", flush=True)
    return "CPU"
