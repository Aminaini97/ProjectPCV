// main.js
const MODEL_URL = "./model.glb"; 
const PLACEHOLDER_IMG = "/mnt/data/7d7feff8-b56e-4df4-8200-e0cafa94af81.png";

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

function loadPlaceholder() {
    const tex = new THREE.TextureLoader().load(PLACEHOLDER_IMG);
    const mat = new THREE.MeshBasicMaterial({ map: tex, transparent: true });
    const geo = new THREE.PlaneGeometry(1.6, 2.4);
    const mesh = new THREE.Mesh(geo, mat);
    mesh.position.y = 1.0;
    scene.add(mesh);
    avatar = mesh;
    document.getElementById('info').innerText = "Using placeholder. Replace MODEL_URL with your GLB.";
    cacheBones();
    debugListBonesWhenReady();
}

function loadGLB(url) {
    return new Promise((resolve, reject) => {
        const loader = new THREE.GLTFLoader();
        loader.load(url, (gltf) => {
            avatar = gltf.scene;
            avatar.position.set(0, 0, 0);
            scene.add(avatar);
            cacheBones();
            debugListBonesWhenReady();
            if (gltf.animations && gltf.animations.length) {
                mixer = new THREE.AnimationMixer(avatar);
            }
            resolve(gltf);
        }, undefined, (err) => reject(err));
    });
}

(async () => {
    try {
        await loadGLB(MODEL_URL);
        document.getElementById('info').innerText = "GLB loaded. Waiting for WebSocket data...";
    } catch (e) {
        console.warn("GLB not found or failed to load:", e);
        loadPlaceholder();
    }
})();

// WebSocket
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
        if (info) info.innerText = 'Connected. Receiving pose...';
    };

    socket.onmessage = (evt) => {
        try {
            const msg = JSON.parse(evt.data);
            if (msg.type === 'pose') handlePose(msg.payload);
        } catch (e) {
            console.warn('Invalid WS message', e);
        }
    };

    socket.onerror = (e) => { console.error('WebSocket error', e); };
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
    setTimeout(() => createSocket(), delay);
}
createSocket();

// --- BONE MAPPING ---
// Saya tambahkan Hip & Shoulder sesuai nama node yang kamu kasih
const boneMap = {
    // --- TAMBAHAN BARU ---
    "hip": "CC_Base_Waist_033",
    "left_shoulder": "CC_Base_L_Clavicle_049",  // Sesuai list kamu (Left -> L)
    "right_shoulder": "CC_Base_R_Clavicle_077", // Sesuai list kamu (Right -> R)
    // ---------------------
    "left_hand": "CC_Base_L_Hand_055",
    "left_upper_arm": "CC_Base_L_Upperarm_050",
    "left_lower_arm": "CC_Base_L_Forearm_051",
    "right_hand": "CC_Base_R_Hand_083",
    "right_upper_arm": "CC_Base_R_Upperarm_078",
    "right_lower_arm": "CC_Base_R_Forearm_079",
    "left_upper_leg": "CC_Base_L_Thigh_04",
    "left_lower_leg": "CC_Base_L_Calf_05",
    "right_upper_leg": "CC_Base_R_Thigh_018",
    "right_lower_leg": "CC_Base_R_Calf_019",
    "head": "CC_Base_Head_038",

    // Kita ambil Twist01 (biasanya induk dari twist lainnya)
    // Ingat Mirroring: Left Python -> Right Avatar
    "left_arm_twist": "CC_Base_R_ForearmTwist01_081", 
    "right_arm_twist": "CC_Base_L_ForearmTwist01_052",
};

let boneCache = {};
let skinnedMesh = null;

function findSkinnedMesh(root) {
    let found = null;
    root.traverse((obj) => { if (obj.isSkinnedMesh) found = obj; });
    return found;
}

function listAllBoneNames(root) {
    const names = [];
    root.traverse((obj) => { if (obj.isBone) names.push(obj.name); });
    console.log('Bones found in model:', names);
}

function cacheBones() {
    boneCache = {};
    if (!avatar) return;
    
    // Saya gunakan pencarian exact match agar tidak salah ambil tulang twist
    for (const key in boneMap) {
        const boneName = boneMap[key];
        // Cari object dengan nama persis
        const bone = avatar.getObjectByName(boneName);
        if(bone) {
            boneCache[key] = bone;
        } else {
            console.warn("Bone not found:", boneName);
        }
    }
}

const defaultAxis = new THREE.Vector3(0, 0, 1);
const boneAxisMap = {};

// --- SIGN MAP ---
// Tambahkan arah putar untuk Hip & Shoulder
const boneSignMap = {
    // Tambahan Baru
    "hip": -1, 
    // "left_shoulder": -1, 
    // "right_shoulder": 1,

    // 
    // --- TAMBAHKAN INI ---
    "left_hand": -1,
    "right_hand": -1,
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

// --- OFFSET MAP ---
// Tambahkan posisi awal untuk Hip & Shoulder
const boneOffsetMap = {
    // Tambahan Baru (Posisi diam)
    "hip": new THREE.Euler(0, 0, - Math.PI / 2), // Pinggang biasanya butuh 90 derajat agar tegak
    "left_shoulder": new THREE.Euler(0, 0, - Math.PI / 2),
    "right_shoulder": new THREE.Euler(0, 0, - Math.PI / 2),

    // Yang sudah ada (tidak saya ubah)
    "head": new THREE.Euler(0, 0, Math.PI),
    "left_upper_leg": new THREE.Euler(0, 0, -Math.PI / 2),
    "right_upper_leg": new THREE.Euler(0, 0, -Math.PI / 2),
    "left_lower_leg": new THREE.Euler(0, 0, Math.PI / 2),
    "right_lower_leg": new THREE.Euler(0, 0, Math.PI / 2),
    "left_upper_arm": new THREE.Euler(0, 0, 0),
    "right_upper_arm": new THREE.Euler(0, 0, Math.PI),
    "left_lower_arm": new THREE.Euler(0, 0, 0),
    "right_lower_arm": new THREE.Euler(0, 0, Math.PI),
    // 1. TWIST BONE (DAGING LENGAN) -> PINDAH KE SUMBU Y (Tengah)
    // Jangan di X (angka pertama), tapi di Y (angka kedua) biar ga patah.
    "left_arm_twist": new THREE.Euler(0, Math.PI / 2, 0),
    "right_arm_twist": new THREE.Euler(0, -Math.PI / 2, 0),

    // 2. HAND (PERGELANGAN) -> BIARKAN DI X (Depan)
    // Kalau telapak sudah menghadap layar, biarkan ini di X.
    // Tapi jika sambungannya masih aneh, coba pindah ke Y juga: new THREE.Euler(0, -Math.PI / 2, 0)
    "left_hand": new THREE.Euler(0, -Math.PI / 2, 0),
    "right_hand": new THREE.Euler(0, Math.PI / 2, 0),
};

function applyAngleToBone(key, degAngle) {
    const bone = boneCache[key];
    if (!bone) return;
    const axis = boneAxisMap[key] || defaultAxis;
    const sign = boneSignMap[key] || 1;
    const rad = (degAngle * sign) * Math.PI / 180;

    const targetQAxis = new THREE.Quaternion();
    targetQAxis.setFromAxisAngle(axis, rad);

    const offsetEuler = boneOffsetMap[key];
    let targetQ = targetQAxis;
    if (offsetEuler) {
        const offsetQ = new THREE.Quaternion().setFromEuler(offsetEuler);
        targetQ = offsetQ.multiply(targetQAxis);
    }
    bone.quaternion.slerp(targetQ, 0.6);
}

function debugListBonesWhenReady() {
    if (!avatar) return;
    setTimeout(() => { listAllBoneNames(avatar); }, 500);
}

let lastPose = null;
function handlePose(pose) {
    lastPose = pose;
    if (!Object.keys(boneCache).length) cacheBones();

    if (pose.root_position) {
        // 1. Ambil posisi X dari Python
        // Angka 0.5 adalah tengah layar.
        // Kita kurangi 0.5 agar: Kiri = negatif, Tengah = 0, Kanan = positif
        let moveX = (pose.root_position.x - 0.5);

        // 2. Skala Sensitivitas (Biar geraknya kerasa)
        // Semakin besar angka 5, semakin jauh avatar bergeser.
        // Pakai MINUS (-5) karena mode Mirror (Kiri layar = Kanan Avatar)
        const sensitivity = 5.0;

        // 3. Terapkan ke Avatar
        if (avatar) {
            // Kita geser sumbu X (Kiri-Kanan)
            // Gunakan teknik 'Lerp' (Linear Interpolation) biar geraknya mulus/tidak patah-patah
            let targetX = moveX * sensitivity;
            
            // Rumus: Posisi Sekarang + (Target - Sekarang) * Kecepatan (0.1)
            avatar.position.x += (targetX - avatar.position.x) * 0.1;
            
            // Opsi Tambahan: Geser Naik-Turun (Jongkok)
            // Kalau mau avatar bisa jongkok/naik turun, aktifkan baris bawah ini:
            /*
            let moveY = (pose.root_position.y - 0.5) * -5.0;
            // -1.0 adalah posisi lantai dasar avatar kamu
            avatar.position.y += ((-1.0 + moveY) - avatar.position.y) * 0.1;
            */
        }

    }
    // -------------------------------------------
    
    for (const key in boneMap) {
        if (key === "left_hand" || key === "right_hand") continue;

        if (pose[key] && boneCache[key]) {
            applyAngleToBone(key, pose[key].angle || 0);
        }
    }

    applyAngleToBone("left_arm_twist", 0);
    applyAngleToBone("right_arm_twist", 0);

    applyAngleToBone("left_hand", 0);
    applyAngleToBone("right_hand", 0);
}

function animate() {
    requestAnimationFrame(animate);
    if (mixer) mixer.update(0.016);
    renderer.render(scene, camera);
}
animate();

window.addEventListener('resize', () => {
    renderer.setSize(window.innerWidth, window.innerHeight);
    camera.aspect = window.innerWidth/window.innerHeight;
    camera.updateProjectionMatrix();
});