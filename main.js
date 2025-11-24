// main.js
// Adjust MODEL_URL to your GLB path. If you have a .glb file, put its path here.
// Developer note: using the uploaded file path as placeholder (image). Replace with your .glb
const MODEL_URL = "./model.glb"; // <-- REPLACE this with your GLB path
const PLACEHOLDER_IMG = "/mnt/data/7d7feff8-b56e-4df4-8200-e0cafa94af81.png"; // uploaded file (PNG)

// Basic Three.js setup
let scene = new THREE.Scene();
scene.background = new THREE.Color(0x333333);

let camera = new THREE.PerspectiveCamera(45, window.innerWidth/window.innerHeight, 0.1, 1000);
camera.position.set(0, 1.5, 4);

let renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);

const light = new THREE.DirectionalLight(0xffffff, 1);
light.position.set(0, 5, 5);
scene.add(light);

const amb = new THREE.AmbientLight(0xffffff, 0.4);
scene.add(amb);

let avatar = null;
let mixer = null;

// if you don't have a GLB yet, we will create a placeholder plane (2D) that shows uploaded PNG
function loadPlaceholder() {
    const tex = new THREE.TextureLoader().load(PLACEHOLDER_IMG);
    const mat = new THREE.MeshBasicMaterial({ map: tex, transparent: true });
    const geo = new THREE.PlaneGeometry(1.6, 2.4);
    const mesh = new THREE.Mesh(geo, mat);
    mesh.position.y = 1.0;
    scene.add(mesh);
    avatar = mesh;
    document.getElementById('info').innerText = "Using placeholder image. Replace MODEL_URL with your GLB.";
    cacheBones();
    debugListBonesWhenReady();
}

// Load GLB if exists
function loadGLB(url) {
    return new Promise((resolve, reject) => {
        const loader = new THREE.GLTFLoader();
        loader.load(url, (gltf) => {
            avatar = gltf.scene;
            avatar.position.set(0, 0, 0);
            scene.add(avatar);
            // cache bones and print available bone names for debugging
            cacheBones();
            debugListBonesWhenReady();
            // optionally find skeleton/mixer
            if (gltf.animations && gltf.animations.length) {
                mixer = new THREE.AnimationMixer(avatar);
            }
            resolve(gltf);
        }, undefined, (err) => reject(err));
    });
}

// Try to load GLB; if fail, load placeholder
(async () => {
    try {
        await loadGLB(MODEL_URL);
        document.getElementById('info').innerText = "GLB loaded. Waiting for WebSocket data...";
    } catch (e) {
        console.warn("GLB not found or failed to load:", e);
        loadPlaceholder();
    }
})();

// Socket: connect to python ws server with auto-detect host/protocol and reconnect
let socket = null;
let socketRetry = 0;
function createSocket() {
    const host = (location.hostname && location.hostname !== '') ? location.hostname : '127.0.0.1';
    const protocol = (location.protocol === 'https:') ? 'wss' : 'ws';
    const url = `${protocol}://${host}:8765`;
    console.log("Attempting WS connect to", url);

    try {
        socket = new WebSocket(url);
    } catch (err) {
        console.error('WebSocket constructor error:', err);
        scheduleReconnect();
        return;
    }

    socket.onopen = () => {
        console.log('WS connected', url);
        socketRetry = 0;
        const info = document.getElementById('info');
        if (info) info.innerText = 'Connected to WebSocket. Receiving pose...';
    };

    socket.onmessage = (evt) => {
        try {
            const msg = JSON.parse(evt.data);
            if (msg.type === 'pose') handlePose(msg.payload);
        } catch (e) {
            console.warn('Invalid WS message', e, evt.data);
        }
    };

    socket.onerror = (e) => {
        console.error('WebSocket error', e);
    };

    socket.onclose = (e) => {
        console.warn('WebSocket closed', e);
        const info = document.getElementById('info');
        if (info) info.innerText = 'WebSocket disconnected.';
        scheduleReconnect();
    };
}

function scheduleReconnect() {
    socketRetry = Math.min(10, socketRetry + 1);
    const delay = Math.min(5000, 500 * socketRetry);
    console.log(`Reconnecting in ${delay}ms (attempt ${socketRetry})`);
    setTimeout(() => createSocket(), delay);
}

// Start socket
createSocket();

// Note: local webcam preview removed to avoid camera device conflicts with Python/OpenCV server.

// Map MediaPipe "bone keys" to GLB bone names
// You must adapt these names to the actual bone names in your GLB.
// Example mapping (change to your model's bone names):
const boneMap = {
    // Mapped to node names found in your model (from dump_gltf_nodes.py)
    "left_upper_arm": "CC_Base_L_Upperarm_050", //tangan kanan user
    "left_lower_arm": "CC_Base_L_Forearm_051", //tangan kiri user
    "right_upper_arm": "CC_Base_R_Upperarm_078",
    "right_lower_arm": "CC_Base_R_Forearm_079",
    "left_upper_leg": "CC_Base_L_Thigh_04",
    "left_lower_leg": "CC_Base_L_Calf_05",
    "right_upper_leg": "CC_Base_R_Thigh_018",
    "right_lower_leg": "CC_Base_R_Calf_019",
    "head": "CC_Base_Head_038"
};

// Cache bones by name for fast access. Prefer skeleton bones from SkinnedMesh.
let boneCache = {};
let skinnedMesh = null;

function findSkinnedMesh(root) {
    let found = null;
    root.traverse((obj) => {
        if (obj.isSkinnedMesh) {
            found = obj;
        }
    });
    return found;
}

function listAllBoneNames(root) {
    const names = [];
    root.traverse((obj) => {
        if (obj.isBone) names.push(obj.name);
    });
    console.log('Bones found in model:', names);
}

function cacheBones() {
    boneCache = {};
    if (!avatar) return;

    // Find a SkinnedMesh and use its skeleton if available
    skinnedMesh = findSkinnedMesh(avatar);
    if (skinnedMesh && skinnedMesh.skeleton) {
        console.log('Using SkinnedMesh skeleton for bones');
        const bones = skinnedMesh.skeleton.bones;
        for (const key in boneMap) {
            const name = boneMap[key];
            const bone = bones.find(b => b.name === name) || avatar.getObjectByName(name) || null;
            boneCache[key] = bone;
            if (!bone) console.warn('Bone not found in skeleton:', name, '(map key:', key, ')');
        }
        return;
    }

    // Fallback: try to find bone objects by name anywhere in the scene
    console.log('SkinnedMesh not found, falling back to node-based bone lookup');
    for (const key in boneMap) {
        const name = boneMap[key];
        const bone = avatar.getObjectByName(name) || avatar.getObjectByName(name, true) || null;
        boneCache[key] = bone;
        if (!bone) console.warn('Bone not found in GLB scene:', name, '(map key:', key, ')');
    }
}

// Convert degrees (from Python) to radians and apply to bone rotation using quaternion slerp
// Default rotate axis is Z to approximate 2D image-plane rotation; you can override per-bone if needed.
const defaultAxis = new THREE.Vector3(0, 0, 1);
const boneAxisMap = {
    // per-bone overrides, e.g. 'left_upper_arm': new THREE.Vector3(1,0,0)
};
// Per-bone sign multipliers to flip direction if needed
const boneSignMap = {
    // Try these sign flips if a side rotates in the opposite direction.
    // These are conservative defaults based on typical CC rig orientation.
    "left_upper_arm": -1,
    "left_lower_arm": -1,
    "right_upper_arm": -1,
    "right_lower_arm": -1,
    "left_upper_leg": -1,
    "left_lower_leg": -1,
    "right_upper_leg": -1,
    "right_lower_leg": -1,
    "head": -1
};

// Per-bone Euler offset (radians) to correct bind/orientation differences.
// Example: flip head 180deg around X -> new THREE.Euler(Math.PI, 0, 0)
const boneOffsetMap = {
    // default no offset
    // "Math.PI" artinya putar 180 derajat pada sumbu X
    "head": new THREE.Euler(0, 0, Math.PI),
    // Paha Kiri: Dikurangi 90 derajat (-Math.PI/2) agar turun ke bawah
    "left_upper_leg": new THREE.Euler(0, 0, -Math.PI / 2), 

    // Paha Kanan: Ditambah 90 derajat (Math.PI/2) karena sumbunya biasanya berlawanan
    "right_upper_leg": new THREE.Euler(0, 0, -Math.PI / 2),
    
    // (Opsional) Jika betis juga aneh, bisa tambahkan koreksi serupa:
    "left_lower_leg": new THREE.Euler(0, 0, Math.PI / 2), //kanan user
    "right_lower_leg": new THREE.Euler(0, 0, Math.PI / 2), //kiri user

    // "left_upper_arm": new THREE.Euler(0, 0, Math.PI / 2),
    "left_upper_arm": new THREE.Euler(0, 0, 0),
    "right_upper_arm": new THREE.Euler(0, 0, Math.PI),
    "left_lower_arm": new THREE.Euler(0, 0, 0),
    "right_lower_arm": new THREE.Euler(0, 0, Math.PI),
};

function applyAngleToBone(key, degAngle) {
    const bone = boneCache[key];
    if (!bone) return;
    const axis = boneAxisMap[key] || defaultAxis;
    const sign = boneSignMap[key] || 1;
    const rad = (degAngle * sign) * Math.PI / 180;

    // target quaternion rotates from identity around axis by rad
    const targetQAxis = new THREE.Quaternion();
    targetQAxis.setFromAxisAngle(axis, rad);

    // apply optional per-bone Euler offset (bind-pose correction)
    const offsetEuler = boneOffsetMap[key];
    let targetQ = targetQAxis;
    if (offsetEuler) {
        const offsetQ = new THREE.Quaternion().setFromEuler(offsetEuler);
        // apply offset before the axis rotation
        targetQ = offsetQ.multiply(targetQAxis);
    }

    // Smoothly interpolate from current quaternion to target
    bone.quaternion.slerp(targetQ, 0.6);
}

// Useful: after loading GLB, list bone names to help create correct boneMap
function debugListBonesWhenReady() {
    if (!avatar) return;
    // small delay to allow GLTF scene graph to settle
    setTimeout(() => {
        listAllBoneNames(avatar);
    }, 500);
}

let lastPose = null;
function handlePose(pose) {
    lastPose = pose;
    // Ensure bones cached
    if (!Object.keys(boneCache).length) cacheBones();

    // overlay drawing removed (webcam preview disabled to avoid device conflict)

    // For every mapped bone, apply rotation (using 2D angle)
    for (const key in boneMap) {
        if (pose[key] && boneCache[key]) {
            applyAngleToBone(key, pose[key].angle || 0);
        }
    }

    // Example: head tilt -> rotate head
    if (pose.head && boneCache["head"]) {
        // pose.head.angle approximates shoulder line; invert sign if needed
        const headAngle = pose.head.angle;
        applyAngleToBone("head", headAngle);
    }
}

// render loop
function animate() {
    requestAnimationFrame(animate);
    if (mixer) mixer.update(0.016);
    renderer.render(scene, camera);
}
animate();

// handle resize
window.addEventListener('resize', () => {
    renderer.setSize(window.innerWidth, window.innerHeight);
    camera.aspect = window.innerWidth/window.innerHeight;
    camera.updateProjectionMatrix();
});
