"""Virtual world and camera control for the AI's vision"""
import threading
import time
import queue
import numpy as np
from typing import Optional, Tuple, Dict
from PIL import Image
import io

# Try to import Ursina
try:
    from ursina import *
    from ursina.prefabs.first_person_controller import FirstPersonController
    URSINA_AVAILABLE = True
except ImportError:
    URSINA_AVAILABLE = False
    print("[WARN] Ursina not available - virtual world disabled")

class VirtualWorld:
    """Virtual 3D world that the AI can see through and control"""
    
    def __init__(self):
        self.app = None
        self.camera_controller = None
        self.world_initialized = False
        self.vision_queue = queue.Queue(maxsize=10)
        self.control_queue = queue.Queue()
        self.is_running = False
        self.current_position = (0, 3, 0)
        self.current_rotation = (0, 0, 0)
        self.thread = None
        self.init_failed = False
        
        if URSINA_AVAILABLE:
            self._init_world()
        else:
            print("[Virtual World] Ursina not available - using placeholder")
    
    def _init_world(self):
        """Initialize the 3D world in a separate thread"""
        def world_thread():
            try:
                # Monkey-patch signal to prevent threading errors
                import signal as signal_module
                original_signal = signal_module.signal
                
                def safe_signal(signalnum, handler):
                    """Wrapper that ignores signal errors in threads"""
                    try:
                        return original_signal(signalnum, handler)
                    except ValueError as e:
                        if "signal only works in main thread" in str(e):
                            # Ignore this error - we're in a thread
                            return None
                        raise
                
                # Replace signal.signal temporarily
                signal_module.signal = safe_signal
                
                # Initialize Ursina app with minimal settings
                # DO NOT use signal handlers - they don't work in threads
                self.app = Ursina(
                    title="Vashrak Vision",
                    borderless=False,
                    fullscreen=False,
                    size=(864, 486),
                    show_ursina_splash=False,
                    development_mode=False,
                    vsync=False  # Disable vsync for better performance
                )
                
                # Restore original signal function
                signal_module.signal = original_signal
                
                # Set window properties
                try:
                    window.color = color.black
                    window.exit_button.visible = False
                    camera.fov = 100
                except:
                    pass
                
                # Create ground
                try:
                    from ursina.shaders import unlit_shader
                    ground = Entity(
                        model='plane',
                        scale=1000,
                        color=color.rgb(0, 47, 74),
                        collider='box',
                        shader=unlit_shader
                    )
                except:
                    ground = Entity(
                        model='plane',
                        scale=1000,
                        color=color.rgb(0, 47, 74),
                        collider='box'
                    )
                
                # Create grid pillars
                import random
                for x in range(-150, 170, 50):
                    height = random.randint(25, 45)
                    Entity(
                        model='cube',
                        scale=(0.5, height, 0.5),
                        position=(x, height/2, 140),
                        color=color.rgba(0, 150, 255, 100)
                    )
                
                # Create camera controller (AI's "body")
                self.camera_controller = FirstPersonController()
                self.camera_controller.y = 3
                self.camera_controller.gravity = 0  # No gravity for AI control
                self.camera_controller.speed = 5
                
                # Disable mouse and keyboard input - AI will control it
                self.camera_controller.mouse_sensitivity = Vec2(0, 0)
                self.camera_controller.enabled = True
                
                self.world_initialized = True
                print("[Virtual World] World initialized")
                
                # Update loop for camera control
                vision_capture_timer = [0]  # Use list to modify in closure
                
                def update():
                    if not self.is_running:
                        return
                    
                    # Process movement commands
                    try:
                        while not self.control_queue.empty():
                            command = self.control_queue.get_nowait()
                            self._process_command(command)
                    except:
                        pass
                    
                    # Update position tracking
                    if self.camera_controller:
                        try:
                            self.current_position = (
                                self.camera_controller.x,
                                self.camera_controller.y,
                                self.camera_controller.z
                            )
                            self.current_rotation = (
                                self.camera_controller.rotation_x,
                                self.camera_controller.rotation_y,
                                self.camera_controller.rotation_z
                            )
                        except:
                            pass
                    
                    # Capture vision periodically (every 0.5 seconds = 2 FPS to reduce overhead)
                    vision_capture_timer[0] += time.dt
                    if vision_capture_timer[0] >= 0.5:
                        vision_capture_timer[0] = 0
                        try:
                            # Use Ursina's screenshot function - saves to file
                            import os
                            temp_path = 'temp_vision.jpg'
                            
                            # Take screenshot
                            from ursina import screenshot
                            screenshot(name=temp_path, path='', file_type='')
                            
                            # Load and add to queue
                            if os.path.exists(temp_path):
                                from PIL import Image
                                img = Image.open(temp_path)
                                img_array = np.array(img)
                                
                                if not self.vision_queue.full():
                                    self.vision_queue.put(img_array)
                                
                                # Clean up temp file
                                try:
                                    os.remove(temp_path)
                                except:
                                    pass
                        except Exception as e:
                            # Silently fail - vision capture is not critical
                            pass
                
                # Assign the update function to Ursina
                self.app.update = update
                
                # Run the app (this blocks until window is closed)
                # Use try-except to catch SystemExit and signal errors
                try:
                    self.app.run()
                except (SystemExit, KeyboardInterrupt):
                    print("[Virtual World] Closed by user")
                except ValueError as e:
                    if "signal only works in main thread" in str(e):
                        print("[Virtual World] Signal error caught - continuing anyway")
                        # World is still initialized and working
                    else:
                        raise
                except Exception as e:
                    print(f"[Virtual World] Run error: {e}")
                    
            except Exception as e:
                print(f"[Virtual World Error] {e}")
                import traceback
                traceback.print_exc()
                self.init_failed = True
        
        # Start world in separate daemon thread
        self.thread = threading.Thread(target=world_thread, daemon=True)
        self.thread.start()
        
        # Wait for initialization with timeout
        timeout = 15  # Increased timeout
        start = time.time()
        while not self.world_initialized and not self.init_failed and (time.time() - start) < timeout:
            time.sleep(0.1)
        
        if self.init_failed:
            print("[Virtual World] Initialization failed")
        elif not self.world_initialized:
            print("[Virtual World] Initialization timed out")
    
    def _process_command(self, command: Dict):
        """Process a movement command"""
        if not self.camera_controller or not self.world_initialized:
            return
        
        cmd_type = command.get("type")
        
        try:
            if cmd_type == "move":
                direction = command.get("direction", "forward")
                amount = command.get("amount", 1.0)
                
                # Get forward/right vectors from camera
                try:
                    from ursina import Vec3
                    forward = self.camera_controller.forward
                    right = self.camera_controller.right
                    
                    if direction == "forward":
                        self.camera_controller.position += forward * amount
                    elif direction == "backward":
                        self.camera_controller.position -= forward * amount
                    elif direction == "left":
                        self.camera_controller.position -= right * amount
                    elif direction == "right":
                        self.camera_controller.position += right * amount
                    elif direction == "up":
                        self.camera_controller.y += amount
                    elif direction == "down":
                        self.camera_controller.y -= amount
                except Exception as e:
                    print(f"[Virtual World Move Error] {e}")
            
            elif cmd_type == "rotate":
                yaw = command.get("yaw", 0)  # Left/right
                pitch = command.get("pitch", 0)  # Up/down
                
                try:
                    self.camera_controller.rotation_y += yaw
                    self.camera_controller.rotation_x += pitch
                    
                    # Clamp pitch
                    self.camera_controller.rotation_x = max(-90, min(90, self.camera_controller.rotation_x))
                except Exception as e:
                    print(f"[Virtual World Rotate Error] {e}")
            
            elif cmd_type == "look_at":
                try:
                    from ursina import Vec3
                    target = command.get("target", (0, 0, 0))
                    self.camera_controller.look_at(Vec3(*target))
                except Exception as e:
                    print(f"[Virtual World Look Error] {e}")
        except Exception as e:
            print(f"[Virtual World Command Error] {e}")
    
    def start(self):
        """Start the virtual world"""
        self.is_running = True
        print("[Virtual World] Started")
    
    def stop(self):
        """Stop the virtual world"""
        self.is_running = False
        if self.app:
            try:
                # Try to quit the app gracefully
                self.app.userExit()
            except:
                pass
    
    def move(self, direction: str, amount: float = 1.0):
        """Move the camera in a direction"""
        if not URSINA_AVAILABLE or not self.world_initialized:
            return
        try:
            self.control_queue.put({
                "type": "move",
                "direction": direction,
                "amount": amount
            })
        except:
            pass
    
    def rotate(self, yaw: float = 0, pitch: float = 0):
        """Rotate the camera"""
        if not URSINA_AVAILABLE or not self.world_initialized:
            return
        try:
            self.control_queue.put({
                "type": "rotate",
                "yaw": yaw,
                "pitch": pitch
            })
        except:
            pass
    
    def look_at(self, target: Tuple[float, float, float]):
        """Look at a specific point"""
        if not URSINA_AVAILABLE or not self.world_initialized:
            return
        try:
            self.control_queue.put({
                "type": "look_at",
                "target": target
            })
        except:
            pass
    
    def get_vision(self) -> Optional[np.ndarray]:
        """Get the current vision frame"""
        try:
            return self.vision_queue.get_nowait()
        except:
            return None
    
    def get_position(self) -> Tuple[float, float, float]:
        """Get current camera position"""
        return self.current_position
    
    def get_rotation(self) -> Tuple[float, float, float]:
        """Get current camera rotation"""
        return self.current_rotation

# Global instance
_virtual_world = None

def get_virtual_world() -> VirtualWorld:
    """Get or create global virtual world instance"""
    global _virtual_world
    if _virtual_world is None:
        _virtual_world = VirtualWorld()
    return _virtual_world