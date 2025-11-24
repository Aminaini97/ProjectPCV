"""dump_gltf_nodes.py
Utility to print node/mesh/skin/joint (bone) names from a .glb/.gltf file.

Usage:
    python dump_gltf_nodes.py path/to/model.glb

If no path given it defaults to ./model.glb

Requires: pygltflib
    pip install pygltflib

This script prints:
 - all nodes with index, name, mesh/skin info
 - all skins and their joint node names (bones)
 - a simple scene graph listing

Run this in your project (frontend) and paste the "Joints / Bones" output here.
"""
import sys
import os
try:
    from pygltflib import GLTF2
except Exception as e:
    print("Missing dependency: pygltflib. Install with: pip install pygltflib")
    raise


def get_node_name(gltf, idx):
    if not gltf.nodes or idx is None:
        return f"<no-node-{idx}>"
    try:
        node = gltf.nodes[idx]
        return node.name or f"<node-{idx}>"
    except Exception:
        return f"<node-{idx}>"


def print_nodes(gltf):
    print("== Nodes (index : name) ==")
    if not gltf.nodes:
        print("(no nodes)")
        return
    for i, node in enumerate(gltf.nodes):
        flags = []
        if node.mesh is not None:
            flags.append(f"mesh={node.mesh}")
        if node.skin is not None:
            flags.append(f"skin={node.skin}")
        if node.children:
            flags.append(f"children={len(node.children)}")
        name = node.name or f"<node-{i}>"
        print(f"{i:3d} : {name}    {', '.join(flags)}")


def print_skins(gltf):
    print("\n== Skins (joints/bones) ==")
    if not gltf.skins:
        print("(no skins found)")
        return
    for si, skin in enumerate(gltf.skins):
        joints = skin.joints or []
        skeleton_root = skin.skeleton
        print(f"Skin {si}: skeleton_root={skeleton_root}")
        for j in joints:
            print(f"    joint node {j}: {get_node_name(gltf, j)}")


def print_scenes(gltf):
    print("\n== Scenes / Graph ==")
    if not gltf.scenes:
        print("(no scenes)")
        return
    for si, scene in enumerate(gltf.scenes):
        print(f"Scene {si}")
        roots = scene.nodes or []
        for r in roots:
            print_node_tree(gltf, r, 1)


def print_node_tree(gltf, idx, depth=0):
    name = get_node_name(gltf, idx)
    indent = '  ' * depth
    print(f"{indent}- {idx}: {name}")
    node = gltf.nodes[idx]
    if node.children:
        for c in node.children:
            print_node_tree(gltf, c, depth+1)


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else 'model.glb'
    if not os.path.isabs(path):
        path = os.path.join(os.getcwd(), path)
    if not os.path.exists(path):
        print(f"File not found: {path}")
        sys.exit(1)

    gltf = GLTF2().load(path)
    print(f"Loaded: {path}")
    print_nodes(gltf)
    print_skins(gltf)
    print_scenes(gltf)

if __name__ == '__main__':
    main()
