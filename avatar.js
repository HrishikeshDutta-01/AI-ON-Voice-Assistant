const scene = new THREE.Scene()

const camera = new THREE.PerspectiveCamera(
75,
1,
0.1,
1000
)

const renderer = new THREE.WebGLRenderer({
canvas: document.getElementById("avatarCanvas"),
alpha:true
})

renderer.setSize(200,200)

const geometry = new THREE.SphereGeometry(1,32,32)

const material = new THREE.MeshBasicMaterial({
color:0x22d3ee,
wireframe:true
})

const avatar = new THREE.Mesh(geometry,material)

scene.add(avatar)

camera.position.z = 3

function animate(){

requestAnimationFrame(animate)

avatar.rotation.y += 0.01

renderer.render(scene,camera)

}

animate()