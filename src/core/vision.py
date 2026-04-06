import cv2
import numpy as np
import mediapipe as mp
import math

class VisionEngine:
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )

        self.percentage_history = []
        self.scanning_counter = 0
        self.live_graph_history = []
        self.pupil_baseline = None
        self.calibration_buffer = []
        self.is_calibrating = False

    def start_pupil_calibration(self):
        """Initiates patient baseline pupillary capture sequence"""
        self.is_calibrating = True
        self.calibration_buffer = []
        self.pupil_baseline = None

    def release_resources(self):
        self.face_mesh.close()

    def _calculate_distance(self, pt1, pt2):
        """Calcula la Distancia Euclidiana bidimensional entre dos puntos"""
        return math.sqrt((pt2[0] - pt1[0])**2 + (pt2[1] - pt1[1])**2)    

    # ==========================================
    # 🔌 MODULE 1: ANEMIA (CONJUNCTIVA)
    # ==========================================
    def _scan_anemia(self, frame, rgb_frame, landmarks, w, h):
        eye_x = int(landmarks.landmark[145].x * w)
        eye_y = int(landmarks.landmark[145].y * h)
        box_width, box_height, y_offset = 50, 15, 5
        pt1 = (eye_x - box_width//2, eye_y + y_offset)
        pt2 = (eye_x + box_width//2, eye_y + y_offset + box_height)
        
        cv2.rectangle(frame, pt1, pt2, (255, 255, 0), 2)
        
        stabilized_red = 0
        diagnosis = "SCANNING..."
        color = (255, 255, 255)

        if pt1[1] > 0 and pt2[1] < h and pt1[0] > 0 and pt2[0] < w:
            isolated_zone = rgb_frame[pt1[1]:pt2[1], pt1[0]:pt2[0]]

            # --- DYNAMIC ILLUMINATION NORMALIZATION ---
            # 1. Convert to HSV to isolate the luminance (Value) channel
            hsv_zone = cv2.cvtColor(isolated_zone, cv2.COLOR_RGB2HSV)
            h_chan, s_chan, v_chan = cv2.split(hsv_zone)

            # 2. Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
            # This mathematically balances shadows and bright spots in real-time
            clahe_engine = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(2, 2))
            v_equalized = clahe_engine.apply(v_chan)

            # 3. Reconstruct the ocular ROI with normalized lighting
            hsv_equalized = cv2.merge((h_chan, s_chan, v_equalized))

            # --- CLINICAL COLOR EXTRACTION ---
            # Using the equalized matrix, we can now safely lower thresholds
            # without triggering false positives from ambient shadows.
            
            # Lower Red Spectrum
            lower_red1 = np.array([0, 130, 50])
            upper_red1 = np.array([10, 255, 255])
            mask1 = cv2.inRange(hsv_equalized, lower_red1, upper_red1)

            # Upper Red Spectrum
            lower_red2 = np.array([160, 130, 50])
            upper_red2 = np.array([179, 255, 255])
            mask2 = cv2.inRange(hsv_equalized, lower_red2, upper_red2)

            vascular_mask = cv2.bitwise_or(mask1, mask2)

            # Calculate clinical percentage of vascular saturation
            total_pixels = isolated_zone.shape[0] * isolated_zone.shape[1]
            red_pixels = cv2.countNonZero(vascular_mask)
            stabilized_red = int((red_pixels / total_pixels) * 100) if total_pixels > 0 else 0

            # --- VISUAL DEBUGGING (X-RAY MODE) ---
            # Renders the binary mask in a separate window to verify pixel detection
            
            
            # --- DYNAMIC DIAGNOSIS ---
            if stabilized_red > 15:
                diagnosis = f"ANEMIA: HEALTHY ({stabilized_red}%)"
                color = (0, 255, 0)
            elif stabilized_red > 5:
                diagnosis = f"ANEMIA: WARNING ({stabilized_red}%)"
                color = (0, 255, 255)
            else:
                diagnosis = f"ANEMIA: CRITICAL ({stabilized_red}%)"
                color = (0, 0, 255)
                
            return stabilized_red, diagnosis, color
            
        return 0, "ANEMIA: NO EYES DETECTED", (100, 100, 100)

    # ==========================================
    # 🔌 MODULE 2: JAUNDICE (SCLERA)
    # ==========================================
    def _scan_jaundice(self, frame, landmarks, w, h):
        sclera_x = int(landmarks.landmark[133].x * w)
        sclera_y = int(landmarks.landmark[133].y * h)
        s_box_width, s_box_height, s_x_offset, s_y_offset = 15, 10, -18, -12
        pt1 = (sclera_x + s_x_offset, sclera_y + s_y_offset)
        pt2 = (sclera_x + s_x_offset + s_box_width, sclera_y + s_y_offset + s_box_height)
        
        yellow_percentage = 0
        diagnosis = "SCANNING..."
        color = (255, 255, 255)

        if pt1[1] > 0 and pt2[1] < h and pt1[0] > 0 and pt2[0] < w:
            sclera_zone = frame.copy()[pt1[1]:pt2[1], pt1[0]:pt2[0]]
            cv2.rectangle(frame, pt1, pt2, (0, 255, 255), 2)
            
            hsv_sclera = cv2.cvtColor(sclera_zone, cv2.COLOR_BGR2HSV)
            yellow_mask = cv2.inRange(hsv_sclera, np.array([15, 60, 60]), np.array([45, 255, 255]))
            
            pixels = cv2.countNonZero(yellow_mask)
            total = s_box_width * s_box_height
            if total > 0: yellow_percentage = int((pixels / total) * 100)
                
            if yellow_percentage < 5:
                diagnosis, color = "LIVER: HEALTHY", (0, 255, 0)
            else:
                diagnosis, color = "ALERT: POSSIBLE JAUNDICE", (0, 0, 255)
                
        return yellow_percentage, diagnosis, color

    # ==========================================
    # 🔌 MODULE 3: PUPILLARY RESPONSE (NEUROLOGY)
    # ==========================================
    def _scan_pupil(self, frame, landmarks, w, h):
        # Puntos del ojo izquierdo en MediaPipe
        # Horizontal: 33 (afuera), 133 (adentro)
        # Vertical: 159 (arriba), 145 (abajo)
        
        # 1. Extraer coordenadas espaciales (x, y)
        left_eye_left = (int(landmarks.landmark[33].x * w), int(landmarks.landmark[33].y * h))
        left_eye_right = (int(landmarks.landmark[133].x * w), int(landmarks.landmark[133].y * h))
        left_eye_top = (int(landmarks.landmark[159].x * w), int(landmarks.landmark[159].y * h))
        left_eye_bottom = (int(landmarks.landmark[145].x * w), int(landmarks.landmark[145].y * h))
        
        # 2. Dibujar guías visuales en pantalla para el HUD
        cv2.line(frame, left_eye_top, left_eye_bottom, (0, 255, 0), 1)
        cv2.line(frame, left_eye_left, left_eye_right, (255, 0, 0), 1)
        
        # 3. Calcular Distancia Euclidiana
        eye_width = self._calculate_distance(left_eye_left, left_eye_right)
        eye_height = self._calculate_distance(left_eye_top, left_eye_bottom)
        
        # 4. Calcular Ratio Biométrico
        pupil_ratio = 0
        if eye_width > 0:
            pupil_ratio = eye_height / eye_width

        # Store telemetry history for live oscilloscope
        self.live_graph_history.append(pupil_ratio)
        if len(self.live_graph_history) > 100:
            self.live_graph_history.pop(0) # Prevent memory overflow
            
        # 5. Lógica de Auto-Calibración
        if self.is_calibrating:
            self.calibration_buffer.append(pupil_ratio)
            if len(self.calibration_buffer) >= 30:  # Captures ~1 second of high-frequency telemetry
                self.pupil_baseline = sum(self.calibration_buffer) / len(self.calibration_buffer)
                self.is_calibrating = False
                self.calibration_buffer.clear()
            return f"CALIBRATING ({len(self.calibration_buffer)}/30)...", (0, 165, 255) # Naranja
            
        # Request calibration if baseline is undefined
        if self.pupil_baseline is None:
            return "PUPIL: UNCALIBRATED (PRESS 'B')", (200, 200, 200) # Gris

        # 6.  Dynamic Clinical Diagnosis (Baseline Deviation)
        # Miosis = -15% of normal size | Mydriasis = +25% of normal size
        miosis_threshold = self.pupil_baseline * 0.85
        mydriasis_threshold = self.pupil_baseline * 1.25

        if pupil_ratio < miosis_threshold:
            pupil_status = f"PUPIL: MIOSIS ({pupil_ratio:.2f} | B: {self.pupil_baseline:.2f})"
            color = (0, 255, 255) # Amarillo alerta
        elif pupil_ratio > mydriasis_threshold:
            pupil_status = f"PUPIL: MYDRIASIS ({pupil_ratio:.2f} | B: {self.pupil_baseline:.2f})"
            color = (0, 0, 255) # Rojo peligro
        else:
            pupil_status = f"PUPIL: NORMAL ({pupil_ratio:.2f} | B: {self.pupil_baseline:.2f})"
            color = (0, 255, 0) # Verde saludable
            
        return pupil_status, color

    def process_frame(self, frame):
        h, w, _ = frame.shape
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)

        red_pct, yel_pct = 0, 0
        anem_diag, liv_diag = "SCANNING...", "SCANNING..."
        t_col, l_col = (255, 255, 255), (255, 255, 255)
        pupil_diag, p_col = "SCANNING...", (255, 255, 255)

        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0]
            
            # Execute pluggable modules
            red_pct, anem_diag, t_col = self._scan_anemia(frame, rgb_frame, landmarks, w, h)
            yel_pct, liv_diag, l_col = self._scan_jaundice(frame, landmarks, w, h)
            pupil_diag, p_col = self._scan_pupil(frame, landmarks, w, h)

            # DRAW RADAR AND LASER SCANNER
            x_coords = [int(p.x * w) for p in landmarks.landmark]
            y_coords = [int(p.y * h) for p in landmarks.landmark]
            x_min, x_max = min(x_coords), max(x_coords)
            y_min, y_max = min(y_coords), max(y_coords)
            #cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (255, 255, 0), 2)
            
            box_height = y_max - y_min
            if box_height > 0:
                self.scanning_counter += 5
                if self.scanning_counter >= box_height: self.scanning_counter = 0
                laser_y = y_min + self.scanning_counter
                #cv2.line(frame, (x_min, laser_y), (x_max, laser_y), (0, 255, 0), 2)
                
            # LIVE TELEMETRY GRAPH
            self.live_graph_history.append(red_pct)
            if len(self.live_graph_history) > 100: self.live_graph_history.pop(0)
            #cv2.rectangle(frame, (w - 230, h - 130), (w - 20, h - 20), (0, 0, 0), cv2.FILLED)
            #cv2.rectangle(frame, (w - 230, h - 130), (w - 20, h - 20), (0, 255, 255), 1)
            #for i in range(1, len(self.live_graph_history)):
            #    cv2.line(frame, (w - 230 + (i - 1) * 2, h - 20 - int((self.live_graph_history[i-1] / 100) * 100)),
            #             (w - 230 + i * 2, h - 20 - int((self.live_graph_history[i] / 100) * 100)), t_col, 2)

        # RETURN ALL DIAGNOSTICS INCLUDING PUPIL
        return frame, red_pct, yel_pct, anem_diag, liv_diag, t_col, l_col, pupil_diag, p_col