// Configuración básica de Three.js
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });

renderer.setSize(window.innerWidth, window.innerHeight);
document.getElementById('canvas-container').appendChild(renderer.domElement);

// Crear Geometría (Icosaedro - forma geométrica moderna)
const geometry = new THREE.IcosahedronGeometry(10, 1);
const material = new THREE.MeshBasicMaterial({ 
    color: 0xE31C25, // Rojo Bombero
    wireframe: true,
    transparent: true,
    opacity: 0.15
});

const sphere = new THREE.Mesh(geometry, material);
scene.add(sphere);

// Partículas flotantes
const particlesGeometry = new THREE.BufferGeometry();
const particlesCount = 700;
const posArray = new Float32Array(particlesCount * 3);

for(let i = 0; i < particlesCount * 3; i++) {
    posArray[i] = (Math.random() - 0.5) * 40; // Esparcir en el espacio
}

particlesGeometry.setAttribute('position', new THREE.BufferAttribute(posArray, 3));
const particlesMaterial = new THREE.PointsMaterial({
    size: 0.05,
    color: 0xffffff, // Blanco
    transparent: true,
    opacity: 0.8
});

const particlesMesh = new THREE.Points(particlesGeometry, particlesMaterial);
scene.add(particlesMesh);

camera.position.z = 15;

// Interacción con el Mouse
let mouseX = 0;
let mouseY = 0;

document.addEventListener('mousemove', (event) => {
    mouseX = event.clientX;
    mouseY = event.clientY;
});

// Animación Loop
const clock = new THREE.Clock();

function animate() {
    const elapsedTime = clock.getElapsedTime();

    // Rotación automática suave
    sphere.rotation.y = elapsedTime * 0.05;
    particlesMesh.rotation.y = -elapsedTime * 0.02;

    // Reacción al mouse (Parallax suave)
    sphere.rotation.x += 0.05 * (mouseY * 0.001 - sphere.rotation.x);
    sphere.rotation.y += 0.05 * (mouseX * 0.001 - sphere.rotation.y);

    renderer.render(scene, camera);
    window.requestAnimationFrame(animate);
}

// Responsive
window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});

animate();