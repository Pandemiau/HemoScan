import cv2
from src.core.vision import VisionEngine
from src.database.db_manager import DatabaseManager
from src.core.security import DataAuthenticator
from src.ui.dashboard import ClinicalDashboard, HardwareController

def main():
    print("SYSTEM [MAIN]: Initializing HemoScan Telemetry System...")
    
    # 1. Start the CustomTkinter GUI to get patient data
    dashboard = ClinicalDashboard()
    session_config = dashboard.launch_startup_menu()
    
    # If user closed the window without clicking start
    if not session_config:
        print("SYSTEM [MAIN]: Boot sequence aborted by user.")
        return

    # 2. Initialize all Core Modules
    db_manager = DatabaseManager()
    authenticator = DataAuthenticator()
    vision_engine = VisionEngine()
    
    # 3. Initialize the Hardware Controller with the session data
    hw_controller = HardwareController(session_config, db_manager, authenticator)
    
    # 4. Connect to the Optical Sensor (Camera)
    cap = cv2.VideoCapture(session_config['camera_source']) 
    
    if not cap.isOpened():
        print("CRITICAL ERROR [MAIN]: Failed to connect to the optical sensor.")
        return

    print("SYSTEM [MAIN]: Video feed established. Press SPACE to capture, 'q' to abort.")

    # --- UI STATE CONTROLLER ---
    # 0 = Debug (All), 1 = Vascular, 2 = Hepatic, 3 = Neurological
    current_view_mode = 0 

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                continue
                
            frame = cv2.resize(frame, (800, 600))

            # 5. Process the frame through the Vision Engine
            (processed_frame, red_pct, yellow_pct,
            anemia_diag, liver_diag, text_color, liver_color, 
            pupil_diag, p_col) = vision_engine.process_frame(frame)
            
            # Apply thermal mode if activated by the controller
            if hw_controller.thermal_mode:
                processed_frame = cv2.applyColorMap(processed_frame, cv2.COLORMAP_JET)
                cv2.putText(processed_frame, "FILTRO TERMICO ACTIVADO", (20, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            
            # --- DYNAMIC UI RENDERER (VIEW SELECTOR) ---
            # Global HUD (Always visible)
            cv2.putText(processed_frame, f"Porcentaje Rojo: {red_pct}%", (80, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, text_color, 1)
            cv2.putText(processed_frame, anemia_diag, (80, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, text_color, 1)
            cv2.putText(processed_frame, f"Nivel Ictericia: {yellow_pct}%", (10, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 1)
            cv2.putText(processed_frame, liver_diag, (10, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.7, liver_color, 1)
            cv2.putText(processed_frame, pupil_diag, (10, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.7, p_col, 2)

            # Neurological View (Mode 3) or Master View (Mode 0)
            if current_view_mode in [3, 0] and len(vision_engine.live_graph_history) > 1:
                gx, gy, gw, gh = 580, 480, 200, 100
                
                cv2.rectangle(processed_frame, (gx, gy), (gx + gw, gy + gh), (20, 20, 20), -1) 
                cv2.rectangle(processed_frame, (gx, gy), (gx + gw, gy + gh), (255, 255, 255), 1) 
                
                max_val = max(vision_engine.live_graph_history) or 1
                min_val = min(vision_engine.live_graph_history) or 0
                data_range = max_val - min_val if max_val != min_val else 1
                
                plot_points = []
                for i, val in enumerate(vision_engine.live_graph_history):
                    px = int(gx + (i / 100) * gw)
                    py = int(gy + gh - ((val - min_val) / data_range) * gh) 
                    plot_points.append((px, py))
                    
                for i in range(1, len(plot_points)):
                    cv2.line(processed_frame, plot_points[i-1], plot_points[i], (0, 255, 0), 2)
            
            cv2.imshow("HemoScan v2.0 - Telemetry Dashboard", processed_frame)
            
            # 6. Route keypresses to the Hardware Controller
            key = cv2.waitKey(5) & 0xFF
            
            # BULLETPROOF EXIT: Abort on 'q', 'Q', or closing the window
            if key in [ord('q'), ord('Q')] or cv2.getWindowProperty("HemoScan v2.0 - Telemetry Dashboard", cv2.WND_PROP_VISIBLE) < 1:
                print("SYSTEM [MAIN]: Emergency abort triggered.")
                break 

            control_signal = hw_controller.check_controls(key, frame, red_pct, yellow_pct, anemia_diag, liver_diag, pupil_diag)
            
            if control_signal == "CALIBRATE_PUPIL":
                vision_engine.start_pupil_calibration()
                
            # --- UI MODE SWITCHES ---
            if key == ord('1'): current_view_mode = 1
            elif key == ord('2'): current_view_mode = 2
            elif key == ord('3'): current_view_mode = 3
            elif key == ord('0'): current_view_mode = 0
                    
    except Exception as e:
        print(f"CRITICAL ERROR [MAIN]: System crash -> {e}")
        
    finally:
        # Safe Shutdown
        vision_engine.release_resources()
        cap.release()
        cv2.destroyAllWindows()
        print("SYSTEM [MAIN]: Telemetry connection terminated cleanly.")

if __name__ == "__main__":
    main()