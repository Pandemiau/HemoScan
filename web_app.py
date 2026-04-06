import cv2
import av
import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase
from src.core.vision import VisionEngine

# --- CLOUD UI & PATIENT DATA CONFIGURATION ---
st.set_page_config(page_title="HemoScan Telemetry", layout="wide")
st.title("HemoScan Cloud Node v2.0")

# Sidebar for Patient Registration
st.sidebar.header("Patient Registration")
patient_name = st.sidebar.text_input("Full Name")
patient_id = st.sidebar.text_input("Patient ID / Passport")
patient_email = st.sidebar.text_input("Contact Email")

if not patient_name or not patient_email:
    st.warning("Please enter Patient Name and Email to activate telemetry.")
else:
    st.success(f"System ready for: {patient_name}")

st.markdown("---")

class HemoScanProcessor(VideoProcessorBase):
    def __init__(self):
        # Initialize the core biometric engine in the cloud thread
        self.vision_engine = VisionEngine()

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        # Convert WebRTC incoming stream to OpenCV standard BGR format
        img = frame.to_ndarray(format="bgr24")

        # Execute Vision Engine diagnostics
        processed_img, red_pct, yel_pct, anem_diag, liv_diag, t_col, l_col, pupil_diag, p_col = self.vision_engine.process_frame(img)

        # Render Cloud HUD directly onto the video stream
        cv2.putText(processed_img, f"RED SATURATION: {red_pct}%", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, t_col, 2)
        cv2.putText(processed_img, anem_diag, (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, t_col, 2)
        
        cv2.putText(processed_img, f"JAUNDICE LEVEL: {yel_pct}%", (20, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, l_col, 2)
        cv2.putText(processed_img, liv_diag, (20, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.7, l_col, 2)

        # Convert back to WebRTC standard and return to the client browser
        return av.VideoFrame.from_ndarray(processed_img, format="bgr24")

# --- WEBRTC CONNECTION HANDLER ---
# Uses Google's STUN servers to bypass NAT/Firewalls during deployment
webrtc_streamer(
    key="hemoscan-stream",
    video_processor_factory=HemoScanProcessor,
    rtc_configuration={
        "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
    }
)