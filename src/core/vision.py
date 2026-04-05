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

    def release_resources(self):
        self.face_mesh.close()

    # ==========================================
    # 🔌 MODULE 1: ANEMIA (CONJUNCTIVA)
    # ==========================================
    def _scan_anemia(self, frame, rgb_frame, landmarks, w, h):
        eye_x = int(landmarks.landmark[145].x * w)
        eye_y = int(landmarks.landmark[145].y * h)
        box_width, box_height, y_offset = 40, 15, 12
        pt1 = (eye_x - box_width//2, eye_y + y_offset)
        pt2 = (eye_x + box_width//2, eye_y + y_offset + box_height)
        
        cv2.rectangle(frame, pt1, pt2, (255, 255, 0), 2)
        
        stabilized_red = 0
        diagnosis = "SCANNING..."
        color = (255, 255, 255)

        if pt1[1] > 0 and pt2[1] < h and pt1[0] > 0 and pt2[0] < w:
            isolated_zone = rgb_frame[pt1[1]:pt2[1], pt1[0]:pt2[0]]
            hsv_zone = cv2.cvtColor(isolated_zone, cv2.COLOR_RGB2HSV)
            brightness_mask = cv2.inRange(hsv_zone, (0, 0, 40), (180, 255, 255))
            isolated_zone = cv2.bitwise_and(isolated_zone, isolated_zone, mask=brightness_mask)
            
            # PIP Minimap (Picture-in-Picture)
            minimap_bgr = cv2.cvtColor(isolated_zone, cv2.COLOR_RGB2BGR)
            minimap = cv2.resize(minimap_bgr, (200, 150))
            frame[h-150:h, 0:200] = minimap
            cv2.rectangle(frame, (0, h-150), (200, h), (0, 255, 0), 2)
            
            b, g, r = cv2.split(isolated_zone)
            sum_total = int(np.sum(r)) + int(np.sum(g)) + int(np.sum(b))
            raw_red = int((int(np.sum(r)) / sum_total) * 100) if sum_total > 0 else 0
            
            self.percentage_history.append(raw_red)
            if len(self.percentage_history) > 15: self.percentage_history.pop(0)
            stabilized_red = int(sum(self.percentage_history) / len(self.percentage_history))
            
            if stabilized_red >= 30:
                diagnosis, color = "HEALTHY", (0, 255, 0)
            else:
                diagnosis, color = "ALERT: POSSIBLE ANEMIA", (0, 0, 255)
                
        return stabilized_red, diagnosis, color

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
    # 🔌 MODULE 3: PUPILLARY RESPONSE (NEUROLOGY) -> PLACEHOLDER
    # ==========================================
    def _scan_pupil(self, frame, landmarks, w, h):
        # PUPIL LOGIC WILL BE IMPLEMENTED HERE LATER
        # MediaPipe Landmarks (Iris: 468, Estimated Pupil Center)
        pupil_status = "PUPIL: NORMAL"
        color = (0, 255, 0)
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
            cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (255, 255, 0), 2)
            
            box_height = y_max - y_min
            if box_height > 0:
                self.scanning_counter += 5
                if self.scanning_counter >= box_height: self.scanning_counter = 0
                laser_y = y_min + self.scanning_counter
                cv2.line(frame, (x_min, laser_y), (x_max, laser_y), (0, 255, 0), 2)
                
            # LIVE TELEMETRY GRAPH
            self.live_graph_history.append(red_pct)
            if len(self.live_graph_history) > 100: self.live_graph_history.pop(0)
            cv2.rectangle(frame, (w - 230, h - 130), (w - 20, h - 20), (0, 0, 0), cv2.FILLED)
            cv2.rectangle(frame, (w - 230, h - 130), (w - 20, h - 20), (0, 255, 255), 1)
            for i in range(1, len(self.live_graph_history)):
                cv2.line(frame, (w - 230 + (i - 1) * 2, h - 20 - int((self.live_graph_history[i-1] / 100) * 100)),
                         (w - 230 + i * 2, h - 20 - int((self.live_graph_history[i] / 100) * 100)), t_col, 2)

        # RETURN ALL DIAGNOSTICS INCLUDING PUPIL
        return frame, red_pct, yel_pct, anem_diag, liv_diag, t_col, l_col, pupil_diag, p_col