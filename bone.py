from pygltflib import GLTF2

# Ganti path ke lokasi file kamu
file_path = r"D:\body-tracker-project\frontend\model.glb"

# Muat file .glb
gltf = GLTF2().load_binary(file_path)

# Tampilkan jumlah total node
print(f"Total node: {len(gltf.nodes)}\n")

# Tampilkan nama semua node
for i, node in enumerate(gltf.nodes):
    print(f"{i:03d} - {node.name}")
