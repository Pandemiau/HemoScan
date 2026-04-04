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

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                continue
                
            frame = cv2.resize(frame, (800, 600))

            # 5. Process the frame through the Vision Engine
            (processed_frame, red_pct, yellow_pct, 
             anemia_diag, liver_diag, text_color, liver_color) = vision_engine.process_frame(frame)
            
            # Apply thermal mode if activated by the controller
            if hw_controller.thermal_mode:
                processed_frame = cv2.applyColorMap(processed_frame, cv2.COLORMAP_JET)
                cv2.putText(processed_frame, "FILTRO TERMICO ACTIVADO", (20, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            
            # Draw primary HUD
            cv2.putText(processed_frame, f"Porcentaje Rojo: {red_pct}%", (80, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, text_color, 1)
            cv2.putText(processed_frame, anemia_diag, (80, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, text_color, 1)
            cv2.putText(processed_frame, f"Nivel Ictericia: {yellow_pct}%", (10, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 1)
            cv2.putText(processed_frame, liver_diag, (10, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.7, liver_color, 1)

            cv2.imshow("HemoScan v2.0 - Telemetry Dashboard", processed_frame)
            
            # 6. Route keypresses to the Hardware Controller
            key = cv2.waitKey(5) & 0xFF
            if not hw_controller.check_controls(key, frame, red_pct, yellow_pct, anemia_diag, liver_diag):
                break # User pressed 'q'
                
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