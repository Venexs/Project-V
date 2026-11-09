"""Audio and video capture, face recognition, and user identification"""
import cv2
import face_recognition
import numpy as np
import sounddevice as sd
import soundfile as sf
import time
import os
import json
from typing import Tuple, Optional

def capture_audio_video(duration=5, audio_file="temp_audio.wav", video_file="temp_video.avi") -> Tuple[Optional[np.ndarray], str, str]:
    """
    Capture short video + audio from user.
    Returns face encoding and audio/video file paths.
    """
    print(f"[Recording] Capturing {duration} seconds of video and audio...")
    
    face_encoding = None
    audio_file_path = None
    video_file_path = None
    
    # --- Video Capture ---
    cap = None
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("[WARN] Camera not available")
            cap = None
    except Exception as e:
        print(f"[WARN] Could not initialize camera: {e}")
        cap = None
    
    frames = []
    if cap is not None:
        start_time = time.time()
        frame_count = 0
        
        try:
            while time.time() - start_time < duration:
                ret, frame = cap.read()
                if not ret:
                    continue
                frames.append(frame)
                frame_count += 1
                
                # Show window only every 5 frames to reduce overhead
                if frame_count % 5 == 0:
                    try:
                        cv2.imshow("Recording (Press 'q' to stop)", frame)
                        if cv2.waitKey(1) & 0xFF == ord("q"):
                            break
                    except:
                        # If display fails, continue without showing
                        pass
        except Exception as e:
            print(f"[WARN] Video capture error: {e}")
        finally:
            cap.release()
            try:
                cv2.destroyAllWindows()
            except:
                pass

        # Save video
        if frames:
            try:
                height, width, _ = frames[0].shape
                out = cv2.VideoWriter(video_file, cv2.VideoWriter_fourcc(*'XVID'), 10, (width, height))
                for f in frames:
                    out.write(f)
                out.release()
                video_file_path = video_file
                print(f"[Recording] Video saved: {video_file}")
            except Exception as e:
                print(f"[WARN] Could not save video: {e}")

            # Extract face encoding from first frame
            try:
                # Convert BGR to RGB for face_recognition
                rgb_frame = cv2.cvtColor(frames[0], cv2.COLOR_BGR2RGB)
                face_encodings = face_recognition.face_encodings(rgb_frame)
                if face_encodings:
                    face_encoding = face_encodings[0]
                    print("[Recording] Face detected and encoded")
                else:
                    print("[Recording] No face detected in video")
            except Exception as e:
                print(f"[WARN] Face encoding failed: {e}")

    # --- Audio Capture ---
    fs = 44100
    print("Recording audio...")
    try:
        # Check if audio device is available
        devices = sd.query_devices()
        if devices:
            # Record audio with timeout protection
            audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, blocking=False)
            
            # Wait for recording to complete with timeout.
            # NOTE: sd.wait() is the correct way to wait for a non-blocking
            # recording to finish. The old loop used audio.all(), which
            # returned False as long as ANY sample was still zero -- causing a
            # hard 12-second freeze on every single capture.
            try:
                sd.wait()
            except Exception as wait_err:
                print(f"[WARN] Audio wait error: {wait_err}")
            
            # Stop recording if still going
            try:
                sd.stop()
            except Exception as stop_err:
                print(f"[WARN] Error stopping audio: {stop_err}")
            
            # Wait a moment before saving
            time.sleep(0.2)
            
            # Save audio file
            try:
                sf.write(audio_file, audio, fs)
                audio_file_path = audio_file
                print(f"[Recording] Audio saved: {audio_file}")
            except Exception as save_err:
                print(f"[WARN] Could not save audio: {save_err}")
                audio_file_path = None
    except Exception as e:
        print(f"[WARN] Audio capture failed: {e}")
        audio_file_path = None
    finally:
        # Ensure audio stream is properly closed
        try:
            sd.stop()
            # Give it a moment to fully close
            time.sleep(0.1)
        except Exception as e:
            # Ignore handle errors on Windows
            if "handle" not in str(e).lower() and "invalid" not in str(e).lower():
                print(f"[WARN] Audio cleanup warning: {e}")

    print("[Recording] Capture complete")
    return face_encoding, audio_file_path, video_file_path

def recognize_user(face_encoding, memory_index, threshold=0.5) -> Tuple[Optional[str], Optional[str]]:
    """
    Check if face matches existing memory.
    Returns (memory_id, user_name) or (None, None)
    """
    if face_encoding is None:
        return None, None
    
    for mem_id, meta in memory_index.items():
        if meta.get("face_encoding") is not None:
            try:
                stored_face = np.array(meta["face_encoding"])
                # Ensure both arrays are the same shape
                if stored_face.shape != face_encoding.shape:
                    continue
                dist = np.linalg.norm(stored_face - face_encoding)
                if dist < threshold:
                    return mem_id, meta.get("title", "Unknown")
            except Exception as e:
                print(f"[WARN] Error comparing face encoding: {e}")
                continue
    return None, None