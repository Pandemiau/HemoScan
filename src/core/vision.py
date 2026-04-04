import cv2
import numpy as np
import mediapipe as mp
import math

class VisionEngine:
    """
    Core Computer Vision engine for HemoScan.
    Handles real-time biometric processing (Anemia & Jaundice detection)
    using MediaPipe Face Mesh, HSV color space analysis, and moving averages.
    """
    
    def __init__(self):
        """Initializes the optical sensors, neural networks, and telemetry stabilizers."""
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        
        # Telemetry Stabilizers (State variables)
        self.percentage_history = []
        self.scanning_counter = 0
        self.live_graph_history = [] # <--- NUEVA LÍNEA PARA EL COSITO
        
        print("SYSTEM [VISION_ENGINE]: Optical sensors and Face Mesh initialized.")

    def release_resources(self):
        """Safely shuts down the vision engine to prevent memory leaks."""
        self.face_mesh.close()
        print("SYSTEM [VISION_ENGINE]: Optical sensors safely powered down.")

    def process_frame(self, frame):
        """
        Main telemetry pipeline. Processes the ROI for HSV color analysis,
        draws the HUD (Laser, Bounding Boxes), and returns the biometric data.
        """
        h, w, channels = frame.shape
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)

        # Default telemetry values (Fail-safe state)
        stabilized_red = 0
        yellow_percentage = 0
        anemia_diagnosis = "SCANNING..."
        liver_diagnosis = "SCANNING..."
        text_color = (255, 255, 255)
        liver_color = (255, 255, 255)

        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                
                # ==========================================
                # 1. ANEMIA SCANNER (CONJUNCTIVA)
                # ==========================================
                eye_x = int(face_landmarks.landmark[145].x * w)
                eye_y = int(face_landmarks.landmark[145].y * h)
                
                box_width, box_height, y_offset = 40, 15, 12
                pt1 = (eye_x - box_width//2, eye_y + y_offset)
                pt2 = (eye_x + box_width//2, eye_y + y_offset + box_height)
                
                # Draw Targeting Box
                cv2.rectangle(frame, pt1, pt2, (255, 255, 0), 2)
                
                # Extract ROI & Filter Shadows
                if pt1[1] > 0 and pt2[1] < h and pt1[0] > 0 and pt2[0] < w:
                    isolated_zone = rgb_frame[pt1[1]:pt2[1], pt1[0]:pt2[0]]
                    hsv_zone = cv2.cvtColor(isolated_zone, cv2.COLOR_RGB2HSV)
                    brightness_mask = cv2.inRange(hsv_zone, (0, 0, 40), (180, 255, 255))
                    isolated_zone = cv2.bitwise_and(isolated_zone, isolated_zone, mask=brightness_mask)
                    
                    # PIP Minimap
                    minimap_bgr = cv2.cvtColor(isolated_zone, cv2.COLOR_RGB2BGR)
                    minimap = cv2.resize(minimap_bgr, (200, 150))
                    frame[h-150:h, 0:200] = minimap
                    cv2.rectangle(frame, (0, h-150), (200, h), (0, 255, 0), 2)
                    
                    # Vectorized Color Math
                    b, g, r = cv2.split(isolated_zone)
                    sum_red = int(np.sum(r))
                    sum_green = int(np.sum(g))
                    sum_blue = int(np.sum(b))
                    sum_total = sum_red + sum_green + sum_blue
                    
                    raw_red_percentage = int((sum_red / sum_total) * 100) if sum_total > 0 else 0
                    
                    # Telemetry Stabilizer (Moving Average)
                    self.percentage_history.append(raw_red_percentage)
                    if len(self.percentage_history) > 15:
                        self.percentage_history.pop(0)
                    stabilized_red = int(sum(self.percentage_history) / len(self.percentage_history))
                    
                    if stabilized_red >= 30: # Assuming 30 is your umbral_sano based on context
                        anemia_diagnosis = "HEALTHY"
                        text_color = (0, 255, 0)
                    else:
                        anemia_diagnosis = "ALERT: POSSIBLE ANEMIA"
                        text_color = (0, 0, 255)

                # ==========================================
                # 2. JAUNDICE SCANNER (SCLERA)
                # ==========================================
                sclera_x = int(face_landmarks.landmark[133].x * w)
                sclera_y = int(face_landmarks.landmark[133].y * h)
                
                s_box_width, s_box_height, s_x_offset, s_y_offset = 15, 10, -18, -12
                s_pt1 = (sclera_x + s_x_offset, sclera_y + s_y_offset)
                s_pt2 = (sclera_x + s_x_offset + s_box_width, sclera_y + s_y_offset + s_box_height)
                
                if s_pt1[1] > 0 and s_pt2[1] < h and s_pt1[0] > 0 and s_pt2[0] < w:
                    sclera_zone = frame.copy()[s_pt1[1]:s_pt2[1], s_pt1[0]:s_pt2[0]]
                    cv2.rectangle(frame, s_pt1, s_pt2, (0, 255, 255), 2)
                    
                    hsv_sclera = cv2.cvtColor(sclera_zone, cv2.COLOR_BGR2HSV)
                    yellow_low = np.array([15, 60, 60])
                    yellow_high = np.array([45, 255, 255])
                    yellow_mask = cv2.inRange(hsv_sclera, yellow_low, yellow_high)
                    
                    yellow_pixels = cv2.countNonZero(yellow_mask)
                    total_sclera_pixels = s_box_width * s_box_height
                    
                    if total_sclera_pixels > 0:
                        yellow_percentage = int((yellow_pixels / total_sclera_pixels) * 100)
                        
                    if yellow_percentage < 5:
                        liver_diagnosis = "LIVER: HEALTHY"
                        liver_color = (0, 255, 0)
                    else:
                        liver_diagnosis = "ALERT: POSSIBLE JAUNDICE"
                        liver_color = (0, 0, 255)

                # ==========================================
                # 3. LEVEL BAR HUD
                # ==========================================
                cv2.rectangle(frame, (20, 20), (60, 220), (255, 255, 255), 2)
                fill_height = int((min(stabilized_red, 100) / 100) * 200)
                cv2.rectangle(frame, (20, 220 - fill_height), (60, 220), text_color, cv2.FILLED)

                # ==========================================
                # 4. PROXIMITY RADAR & LASER ANIMATION
                # ==========================================
                left_eye_outer = face_landmarks.landmark[33]
                right_eye_outer = face_landmarks.landmark[263]
                eye_distance = math.hypot((right_eye_outer.x - left_eye_outer.x) * w, 
                                          (right_eye_outer.y - left_eye_outer.y) * h)
                
                hud_color = (255, 255, 0)
                if eye_distance < 120: hud_color = (0, 255, 255) # Too far
                elif eye_distance > 300: hud_color = (0, 165, 255) # Too close
                
                x_coords = [int(p.x * w) for p in face_landmarks.landmark]
                y_coords = [int(p.y * h) for p in face_landmarks.landmark]
                x_min, x_max = min(x_coords), max(x_coords)
                y_min, y_max = min(y_coords), max(y_coords)
                
                cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), hud_color, 2)
                
                box_height = y_max - y_min
                if box_height > 0:
                    self.scanning_counter += 5 # Laser speed
                    if self.scanning_counter >= box_height:
                        self.scanning_counter = 0
                    laser_y = y_min + self.scanning_counter
                    cv2.line(frame, (x_min, laser_y), (x_max, laser_y), (0, 255, 0), 2)

                    # ==========================================
                # 5. LIVE TELEMETRY MONITOR (El "Cosito")
                # ==========================================
                self.live_graph_history.append(stabilized_red)
                if len(self.live_graph_history) > 100:
                    self.live_graph_history.pop(0)
                
                # Fondo y borde del monitor
                cv2.rectangle(frame, (w - 230, h - 130), (w - 20, h - 20), (0, 0, 0), cv2.FILLED)
                cv2.rectangle(frame, (w - 230, h - 130), (w - 20, h - 20), (0, 255, 255), 1)
                cv2.putText(frame, 'TELEMETRIA EN VIVO', (w - 225, h - 135), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
                
                # Trazado de la gráfica
                for i in range(1, len(self.live_graph_history)):
                    x_prev = w - 230 + (i - 1) * 2
                    x_curr = w - 230 + i * 2
                    y_prev = h - 20 - int((self.live_graph_history[i-1] / 100) * 100)
                    y_curr = h - 20 - int((self.live_graph_history[i] / 100) * 100)
                    cv2.line(frame, (x_prev, y_prev), (x_curr, y_curr), text_color, 2)

        # Return the fully annotated frame and the pure biometric data
        return frame, stabilized_red, yellow_percentage, anemia_diagnosis, liver_diagnosis, text_color, liver_color