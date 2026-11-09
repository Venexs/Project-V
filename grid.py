from ursina import *
from ursina.models.procedural.cylinder import Cylinder
from ursina.shaders import lit_with_shadows_shader, unlit_shader
from panda3d.core import SamplerState, CullFaceAttrib, TransparencyAttrib # Added TransparencyAttrib
from ursina.prefabs.first_person_controller import FirstPersonController
from PIL import Image
import threading, time, math, random
from collections import deque

# --- hand tracking
try:
    import cv2
    import mediapipe as mp
    import numpy as np
    MEDIA = True
    print("✓ MediaPipe and OpenCV imported successfully")
except Exception as e:
    MEDIA = False
    print(f"✗ Failed to import libraries: {e}")
    print("Install with: pip install opencv-python mediapipe")


# ------------------------ TRON WORLD ------------------------
app = Ursina()
window.color = color.black
camera.fov = 100

window.fog_color = color.rgb(0, 10, 20)
window.fog_density = 0.10

# Try to load HDR skybox
try:
    sky = Sky(texture='sky_sunset')
    sky.color = color.rgba(0, 5, 10, 255) 
    print("✓ HDR skybox loaded and darkened further")
except:
    print("✗ HDR not found, using default black sky")
    window.color = color.rgb(0, 0, 5) 

# Atmospheric glow
glow = Entity(
    model='quad', 
    scale=300, 
    color=color.rgba(0, 100, 150, 5), 
    z=50,
    rotation_x=-10
)

GRID_PATH = "files/grid_single.png"

# Enhanced ground with Tron grid
ground = Entity(
    model='plane',
    texture=GRID_PATH,
    scale=1000,
    texture_scale=(200, 200),
    color=color.rgb(0, 47, 74),
    collider='box',
    shader=unlit_shader # Unlit for consistent glow
)

try:
    gtex = ground.texture._texture
    gtex.setMinfilter(SamplerState.FT_linear_mipmap_linear)
    gtex.setMagfilter(SamplerState.FT_linear)
    gtex.setAnisotropicDegree(16)
except:
    pass

# Horizon glow - Tron Legacy style
horizon = Entity(
    model='quad',
    scale=(800, 100),
    position=(0, 30, 200),
    rotation_x=-15,
    color=color.rgba(0, 100, 200, 50)
)

# Grid pillars extending into distance - OPTIMIZED
for x in range(-150, 170, 50):  
    height = random.randint(25, 45)
    Entity(
        model='cube', 
        scale=(0.5, height, 0.5),
        position=(x, height/2, 140),
        color=color.rgba(0, 150, 255, 100),
        shader=unlit_shader # Unlit for consistent Tron glow
    )

for z in range(60, 180, 50):  
    height = random.randint(20, 40)
    Entity(
        model='cube',
        scale=(0.5, height, 0.5),
        position=(random.randint(-120, 120), height/2, z),
        color=color.rgba(0, 150, 255, 80),
        shader=unlit_shader # Unlit for consistent Tron glow
    )

player = FirstPersonController()
player.y = 3
player.gravity = 1
player.speed = 10

# Hand detection indicator
hand_indicator = Text(
    text='No hands detected',
    position=(-0.85, 0.45),
    scale=1.5,
    color=color.red,
    origin=(0, 0)
)

fps_text = Text(
    text='FPS: --',
    position=(0.7, 0.45),
    scale=1.2,
    color=color.cyan,
    origin=(0, 0)
)


# ------------------------ PROCEDURAL CLOUDS ------------------------
# --- MODIFICATION 1: Reverted to the stable, original LightningBolt class ---
class LightningBolt:
    def __init__(self, start_pos, end_pos):
        self.segments = []
        # Use the original, good, iterative logic
        self.create_bolt(start_pos, end_pos) 
        
    def create_bolt(self, start, end, depth=0, max_depth=2): # Reduced max_depth for performance
        direction = end - start
        distance = direction.length()
        
        if distance < 3: # Simplified check
            return
        
        # Fewer segments for performance
        num_segments = max(3, int(distance / 5))
        current_pos = start
        
        for i in range(num_segments):
            t = (i + 1) / num_segments
            next_pos = start + direction * t
            
            # Add jaggedness
            if i > 0 and i < num_segments - 1:
                offset = Vec3(
                    random.uniform(-3, 3),
                    random.uniform(-1, 1),
                    random.uniform(-3, 3)
                )
                next_pos += offset
            
            # Create the bolt segment
            segment = Entity(
                # Use Cylinder for a better look
                model=Cylinder(radius=0.15, height=1), 
                color=color.rgb(200, 240, 255),
                shader=unlit_shader, # Use unlit shader
                enabled=True
            )
            
            mid = (current_pos + next_pos) / 2
            # Cylinder height is set via scale_y
            length = (next_pos - current_pos).length()
            
            segment.world_position = mid
            segment.scale_y = length # Set height via scale
            segment.look_at(next_pos) # This is correct: call look_at on the Entity
            
            self.segments.append(segment)
            
            # Fewer branches for performance
            if depth < max_depth and i % 2 == 0 and random.random() < 0.3:
                branch_dir = Vec3(
                    random.uniform(-1, 1),
                    random.uniform(-1, 0), # Branches go down/out
                    random.uniform(-1, 1)
                ).normalized() * distance * 0.25 # Shorter branches
                branch_end = current_pos + branch_dir
                self.create_bolt(current_pos, branch_end, depth + 1, max_depth)
            
            current_pos = next_pos
    
    def destroy(self):
        for seg in self.segments:
            destroy(seg)
        self.segments.clear()
# ------------------------------------------------------------------


class TronCloud:
    def __init__(self, position, scale_range=(40, 40)):
        self.position = Vec3(*position)
        self.particles = []
        self.lightning_cooldown = random.uniform(3, 8) 
        self.time_since_lightning = 0
        self.active_bolts = []
        
        num_particles = random.randint(15, 25) 
        base_scale = random.uniform(*scale_range)
        
        for layer in range(2):
            layer_offset = Vec3(0, layer * base_scale * 0.2, 0)
            
            for i in range(num_particles // 2):
                offset = Vec3(
                    random.uniform(-base_scale*0.7, base_scale*0.7),
                    random.uniform(-base_scale*0.25, base_scale*0.25),
                    random.uniform(-base_scale*0.7, base_scale*0.7)
                )
                
                particle_scale = random.uniform(base_scale*0.5, base_scale*0.9)
                
                # --- Translucent Cloud Particles ---
                particle_fill = Entity(
                    model='sphere',
                    position=self.position + offset + layer_offset,
                    scale=particle_scale,
                    color=color.rgba(0, 60, 100, 150), # Translucent blue
                    shader=unlit_shader, 
                    render_queue=0 
                )
                particle_fill.transparency = TransparencyAttrib.M_alpha
                self.particles.append(particle_fill)
                
                # Outline (still parented)
                particle_outline = Entity(
                    parent=particle_fill, 
                    model='sphere',
                    scale=1.05, 
                    color=color.rgb(0, 150, 255), 
                    shader=unlit_shader,
                    render_queue=1 
                )
                particle_outline.setTwoSided(True)
                particle_outline.setAttrib(CullFaceAttrib.make(CullFaceAttrib.M_cull_clockwise))
                # ---------------------------------------------------

        
        self.glow = Entity(
            model='sphere',
            position=self.position,
            scale=base_scale * 2.5,
            color=color.rgba(150, 220, 255, 0),
            enabled=False,
            shader=unlit_shader
        )
        self.initial_particle_positions = [p.position for p in self.particles]
        self.initial_glow_position = self.glow.position
        self.movement_speed = random.uniform(0.1, 0.3)
        self.movement_range_x = random.uniform(50, 100)
        
    def update(self):
        self.time_since_lightning += time.dt
        
        # Trigger lightning between clouds
        if self.time_since_lightning > self.lightning_cooldown:
            # Pick another cloud to strike
            target_cloud = random.choice([c for c in clouds if c != self])
            self.trigger_lightning(target_cloud.position) # Pass target position
            self.time_since_lightning = 0
            self.lightning_cooldown = random.uniform(4, 10) # New cooldown
        
        # Clouds movement
        for i, particle in enumerate(self.particles):
            particle.x += self.movement_speed * time.dt
            if particle.x - self.position.x > self.movement_range_x / 2:
                particle.x -= self.movement_range_x
            if self.position.x - particle.x > self.movement_range_x / 2:
                particle.x += self.movement_range_x
        
        self.glow.x += self.movement_speed * time.dt
        if self.glow.x - self.position.x > self.movement_range_x / 2:
            self.glow.x -= self.movement_range_x
        if self.position.x - self.glow.x > self.movement_range_x / 2:
            self.glow.x += self.movement_range_x
            
    def trigger_lightning(self, target_pos):
        # Clear old bolts
        for bolt in self.active_bolts:
            bolt.destroy()
        self.active_bolts.clear()
        
        # Create 1-2 lightning bolts
        num_bolts = random.randint(1, 2)
        
        for i in range(num_bolts):
            # Start near this cloud's center
            start = self.position + Vec3(
                random.uniform(-10, 10),
                random.uniform(-3, 3),
                random.uniform(-10, 10)
            )
            
            # End near the target cloud's center
            end = target_pos + Vec3(
                random.uniform(-10, 10),
                random.uniform(-3, 3),
                random.uniform(-10, 10)
            )
            
            bolt = LightningBolt(start, end)
            self.active_bolts.append(bolt)   
            
            # Flash at start and end points
            impact_start = Entity(
                model='sphere',
                position=start,
                scale=6,
                color=color.rgba(200, 240, 255, 150),
                enabled=True,
                shader=unlit_shader
            )
            impact_start.animate_scale(0, duration=0.25)
            destroy(impact_start, delay=0.3)

            impact_end = Entity(
                model='sphere',
                position=end,
                scale=6,
                color=color.rgba(200, 240, 255, 150),
                enabled=True,
                shader=unlit_shader
            )
            impact_end.animate_scale(0, duration=0.25)
            destroy(impact_end, delay=0.3)
        
        # Flash the cloud itself
        self.glow.enabled = True
        self.glow.color = color.rgba(150, 220, 255, 120)
        invoke(self.fade_lightning, delay=0.08)
    
    def fade_lightning(self):
        self.glow.animate_color(color.rgba(150, 220, 255, 0), duration=0.2)
        invoke(self.remove_bolts, delay=0.35) # Clear bolts after fade for effect
    
    def flicker_bolt(self):
        pass 
    
    def show_bolts(self):
        pass 
    
    def remove_bolts(self):
        self.glow.enabled = False
        for bolt in self.active_bolts:
            bolt.destroy()
        self.active_bolts.clear()


clouds = []
for i in range(40): 
    x = random.uniform(-1000, 1000)
    y = random.uniform(70, 140)
    z = random.uniform(-1000, 1000)
    clouds.append(TronCloud((x, y, z), scale_range=(30, 45)))

print(f"✓ Created {len(clouds)} volumetric clouds with outline and lightning")


# ------------------------ AMBIENT PARTICLES ------------------------
particles = []
for i in range(30): 
    p = Entity(
        model='sphere',
        scale=random.uniform(0.15, 0.35),
        position=(
            random.uniform(-100, 100),
            random.uniform(5, 40),
            random.uniform(-50, 120)
        ),
        color=color.rgba(0, 200, 255, 120),
        shader=unlit_shader
    )
    particles.append({
        'entity': p,
        'speed': random.uniform(0.3, 1.5),
        'amplitude': random.uniform(1.5, 4)
    })


# ------------------------ SKELETON HANDS ------------------------
MAX_HANDS = 2
JOINT_SIZE = 0.15
BONE_RADIUS = 0.03
HAND_DISTANCE = 2.0
DEPTH_SCALE = 3.0
SMOOTH = 0.45

CONNECTIONS = (
    (0,1),(1,2),(2,3),(3,4),
    (0,5),(5,6),(6,7),(7,8),
    (0,9),(9,10),(10,11),(11,12),
    (0,13),(13,14),(14,15),(15,16),
    (0,17),(17,18),(18,19),(19,20)
)

latest = {
    "hands": None,
    "label": None
}


# ----------- CREATE HAND SKELETON MODELS -------------
hand_models = []
for h in range(MAX_HANDS):
    joints = []
    bones = []

    buffers = []
    group = Entity()

    for i in range(21):
        j = Entity(
            parent=group,
            model='sphere',
            scale=JOINT_SIZE,
            color=color.rgb(0, 255, 255),
            shader=unlit_shader, 
            enabled=False
        )
        joints.append(j)
        buffers.append(deque(maxlen=4))

    for a,b in CONNECTIONS:
        bone = Entity(
            parent=group,
            model=Cylinder(radius=BONE_RADIUS, height=0.001),
            color=color.rgb(0, 255, 255),
            shader=unlit_shader, 
            enabled=False
        )
        bones.append((a,b,bone))

    hand_models.append({"joints": joints, "bones": bones, "buffers": buffers})


# ------------------------ WEBCAM THREAD ------------------------
def webcam_thread():
    if not MEDIA:
        print("✗ MediaPipe not installed - hand tracking disabled")
        return

    print("Starting webcam initialization...")
    
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
        max_num_hands=MAX_HANDS,
        min_detection_confidence=0.6,
        min_tracking_confidence=0.6
    )
    print("✓ MediaPipe Hands initialized")

    cap = None
    for id in [0, 1, 2, 3]:
        print(f"Trying camera ID {id}...")
        cam = cv2.VideoCapture(id)
        time.sleep(0.5)
        
        if cam.isOpened():
            ret, test_frame = cam.read()
            if ret:
                print(f"✓ Successfully opened camera {id}")
                print(f"  Resolution: {test_frame.shape[1]}x{test_frame.shape[0]}")
                cap = cam
                break
            else:
                print(f"✗ Camera {id} opened but can't read frames")
                cam.release()
        else:
            print(f"✗ Camera {id} failed to open")

    if cap is None:
        print("✗ No working webcam found!")
        print("Possible issues:")
        print("  - Camera is being used by another application")
        print("  - Permission denied (check system settings)")
        print("  - No camera connected")
        return

    print("✓ Webcam thread running - move your hands in front of camera!")
    frame_count = 0
    
    while True:
        ok, frame = cap.read()
        if not ok:
            print("✗ Failed to read frame")
            time.sleep(0.1)
            continue

        frame_count += 1
        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = hands.process(rgb)

        latest["hands"] = res.multi_hand_landmarks
        latest["label"] = res.multi_handedness if res.multi_handedness else None


if MEDIA:
    print("Starting webcam thread...")
    threading.Thread(target=webcam_thread, daemon=True).start()
else:
    print("Hand tracking disabled - MediaPipe not available")


# ------------------------ UTILITIES ------------------------
def mp_to_world(lm):
    x = -(lm.x - 0.5)  # FLIPPED: negative to reverse mirror effect
    y = 0.5 - lm.y
    z = HAND_DISTANCE + (-lm.z) * DEPTH_SCALE

    aspect = window.aspect_ratio
    sx = math.tan(math.radians(camera.fov/2)) * z * 2
    sy = sx / aspect

    return (
        camera.world_position
        + camera.forward * z
        + camera.right * (x * sx)
        + camera.up * (y * sy)
    )


def set_bone(bone, p1, p2):
    mid = (p1 + p2) / 2
    bone.world_position = mid
    # --- MODIFICATION 2: Fix bone length calculation ---
    # The original Cylinder model has a height of 1. 
    # We must set scale_y to the desired length.
    bone.scale_y = (p2 - p1).length()
    # -------------------------------------------------
    bone.look_at(p2)


# ------------------------ UPDATE LOOP ------------------------
def update():
    try:
        # Update clouds and lightning
        for cloud in clouds:
            cloud.update()
        
        # Animate floating particles
        for p in particles:
            t = time.time() * p['speed']
            p['entity'].y += math.sin(t) * 0.01
            p['entity'].x += math.cos(t * 0.7) * 0.005
            
        # Hand tracking
        data = latest["hands"]
        labels = latest["label"]

        # Update indicator
        if data and len(data) > 0:
            hand_indicator.text = f'{len(data)} hand(s) detected'
            hand_indicator.color = color.green
        else:
            hand_indicator.text = 'No hands detected'
            hand_indicator.color = color.red

        # Hide all
        for m in hand_models:
            for j in m["joints"]: 
                j.enabled = False
            for (_,_,b) in m["bones"]: 
                b.enabled = False

        if not data:
            return

        # For each detected hand
        for idx, landmarks in enumerate(data):
            if idx >= MAX_HANDS:
                break

            model = hand_models[idx]

            # PROCESS JOINTS
            positions = []
            for i, lm in enumerate(landmarks.landmark):
                pos = Vec3(*mp_to_world(lm))

                buf = model["buffers"][i]
                buf.append(pos)

                # Calculate average position
                avg = Vec3(0, 0, 0)
                for p in buf:
                    avg += p
                avg /= len(buf)
                
                # Initialize position on first frame
                if model["joints"][i].world_position == Vec3(0,0,0):
                    final = avg
                else:
                    final = lerp(model["joints"][i].world_position, avg, SMOOTH)

                model["joints"][i].world_position = final
                model["joints"][i].enabled = True
                positions.append(final)

            # PROCESS BONES
            for a, b, bone in model["bones"]:
                if a < len(positions) and b < len(positions):
                    set_bone(bone, positions[a], positions[b])
                    bone.enabled = True
                    
    except Exception as e:
        print(f"Update error: {e}")
        import traceback
        traceback.print_exc()


# Re-implement FPS counter on a delayed timer to reduce overhead
def update_fps_display():
    if time.dt != 0:
        fps_text.text = f'FPS: {round(1/time.dt)}'
    invoke(update_fps_display, delay=0.5) # Update only twice per second

invoke(update_fps_display, delay=0.5) 


def input(k):
    if k == "0":
        application.quit()


print("\n" + "="*50)
print("TRON LEGACY - HAND TRACKING")
print("="*50)
print("Controls:")
print("  WASD - Move")
print("  Mouse - Look around")
print("  0 - Quit")
print("="*50 + "\n")

app.run()