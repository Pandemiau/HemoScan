import customtkinter as ctk
from tkinter import ttk
import matplotlib.pyplot as plt
import threading
import pyttsx3
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from fpdf import FPDF
import datetime
import cv2
import pathlib
import mysql.connector
import winsound
import time
import os
from dotenv import load_dotenv

class SystemNotifier:
    """Handles asynchronous background tasks like Voice Synthesis and Email delivery."""
    
    @staticmethod
    def speak(text):
        def _speak_thread():
            engine = pyttsx3.init()
            engine.setProperty('rate', 160)
            engine.say(text)
            engine.runAndWait()
        threading.Thread(target=_speak_thread, daemon=True).start()

    @staticmethod
    def send_email_async(target_email, pdf_path, patient_name):
        def _email_thread():
            load_dotenv() # Carga la caja fuerte invisible (.env)
            try:
                print(f"SYSTEM [NOTIFIER]: Initiating secure transmission to {target_email}...")
                sender = os.getenv("SENDER_EMAIL")  
                password = os.getenv("EMAIL_PASSWORD") 

                msg = MIMEMultipart()
                msg['From'] = sender
                msg['To'] = target_email
                msg['Subject'] = f"HemoScan Pro - Resultados: {patient_name}"

                html_body = f"""
                <html>
                  <body style="font-family: 'Segoe UI', sans-serif; color: #333;">
                    <div style="background-color: #0f4c5c; padding: 20px; text-align: center;">
                        <h2 style="color: white; margin: 0;">HemoScan Pro Telemetry</h2>
                    </div>
                    <div style="padding: 20px; border: 1px solid #ddd;">
                        <h3>Estimado Paciente {patient_name},</h3>
                        <p>El escaneo biométrico dual ha concluido exitosamente. Por favor, descargue el PDF adjunto.</p>
                    </div>
                  </body>
                </html>
                """
                msg.attach(MIMEText(html_body, 'html'))

                with open(pdf_path, "rb") as f:
                    attachment = MIMEApplication(f.read(), _subtype="pdf")
                    attachment.add_header('Content-Disposition', 'attachment', filename=pdf_path)
                    msg.attach(attachment)

                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login(sender, password)
                server.send_message(msg)
                server.quit()
                print("SYSTEM [NOTIFIER]: Email transmitted successfully.")
                winsound.Beep(2000, 100)
            except Exception as e:
                print(f"CRITICAL ERROR [NOTIFIER]: Transmission failed -> {e}")
                
        threading.Thread(target=_email_thread, daemon=True).start()


class ClinicalDashboard:
    """Manages the CustomTkinter GUI for startup and Database visualization."""
    
    def __init__(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.session_data = None
        
    def launch_startup_menu(self):
        """Displays the startup window and returns the configuration dictionary."""
        window = ctk.CTk()
        window.geometry("450x350")
        window.title("HemoScan IA - Mission Control")

        ctk.CTkLabel(window, text="HemoScan IA v2.0", font=("Segoe UI", 26, "bold"), text_color="#00d2ff").pack(pady=(20, 10))
        
        name_entry = ctk.CTkEntry(window, width=280, placeholder_text="Nombre del Paciente")
        name_entry.pack(pady=10)
        
        email_entry = ctk.CTkEntry(window, width=280, placeholder_text="Correo (Opcional)")
        email_entry.pack(pady=10)

        cam_option = ctk.CTkComboBox(window, values=["Webcam Local (Laptop)", "Cámara IP (Celular)"], width=280)
        cam_option.pack(pady=10)
        
        ip_entry = ctk.CTkEntry(window, width=280, placeholder_text="URL IP (Si usa celular)")
        ip_entry.insert(0, "http://192.168.0.X:8080/video")
        ip_entry.pack(pady=10)

        def start_engine():
            source = 0 if cam_option.get() == "Webcam Local (Laptop)" else ip_entry.get()
            self.session_data = {
                "name": name_entry.get() if name_entry.get() else "Desconocido",
                "email": email_entry.get(),
                "camera_source": source
            }
            window.destroy()

        ctk.CTkButton(window, text="INICIAR SISTEMA", command=start_engine, fg_color="#2ecc71", hover_color="#27ae60").pack(pady=15)
        window.mainloop()
        return self.session_data


class HardwareController:
    """Handles keyboard telemtry interactions, PDF generation, and saving states."""
    
    def __init__(self, session_data, db_manager, authenticator):
        self.patient_name = session_data['name']
        self.patient_email = session_data['email']
        self.db = db_manager
        self.auth = authenticator
        
        self.healthy_threshold = 40
        self.thermal_mode = False

    def check_controls(self, key, current_frame, red_pct, yellow_pct, anemia_diag, liver_diag, pupil_diag):
        """Routes the hardware keypress to the correct sub-system."""
        if key == ord('q'):
            return False # Signal to break loop
            
        elif key == ord('t'):
            self.thermal_mode = not self.thermal_mode
            winsound.Beep(900, 150)
            
        elif key == ord('c'):
            self.healthy_threshold = red_pct - 5
            print(f"SYSTEM [HW_CONTROL]: Calibrated. New healthy threshold: {self.healthy_threshold}%")
            winsound.Beep(1000, 100)
            winsound.Beep(1500, 100)

        elif key == ord('b'):
            print("SYSTEM [HW_CONTROL]: Initiating Pupillary Baseline Calibration...")
            # Route signal to vision engine via main loop
            return "CALIBRATE_PUPIL" 
            
        elif key == 32: # SPACEBAR
            self.execute_capture_sequence(current_frame, red_pct, yellow_pct, anemia_diag, liver_diag, pupil_diag)
            
        return True # Continue loop

    def execute_capture_sequence(self, frame, red_pct, yellow_pct, anemia_diag, liver_diag, pupil_diag):
        """The master sequence: Hash -> DB -> PDF -> Email -> Voice."""
        winsound.Beep(2000, 200)
        timestamp_exact = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 1. Security Hash
        signature = self.auth.generate_biometric_signature(self.patient_name, red_pct, yellow_pct, anemia_diag)
        
        # 2. Database Persistence
        self.db.save_history(timestamp_exact, self.patient_name, red_pct, anemia_diag, signature, yellow_pct, liver_diag, pupil_diag)
        
        # 3. Save Evidence Image
        cv2.imwrite("foto_evidencia.jpg", frame)
        
        # 4. Generate PDF Report
        pdf_name = self.generate_medical_pdf(timestamp_exact, red_pct, yellow_pct, anemia_diag, liver_diag, pupil_diag, signature)
        # 5. Background Tasks (Email & Voice)
        if self.patient_email:
            SystemNotifier.send_email_async(self.patient_email, pdf_name, self.patient_name)
            
        SystemNotifier.speak(f"Reporte generado para {self.patient_name}. {anemia_diag.replace('ALERTA:', 'Alerta')}")

    def generate_medical_pdf(self, timestamp, red_pct, yellow_pct, anemia_diag, liver_diag, pupil_diag, signature):
        """Creates the formal FPDF report."""
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 18)
        pdf.cell(0, 10, txt="HEMOSCAN IA - REPORTE MEDICO OFICIAL", ln=True, align='C')
        pdf.set_font("Arial", '', 12)
        pdf.cell(0, 10, txt=f"Paciente: {self.patient_name}", ln=True)
        pdf.cell(0, 10, txt=f"Fecha: {timestamp}", ln=True)
        pdf.cell(0, 10, txt=f"Conjuntiva (Rojo): {red_pct}% -> {anemia_diag}", ln=True)
        pdf.cell(0, 10, txt=f"Esclera (Amarillo): {yellow_pct}% -> {liver_diag}", ln=True)
        pdf.cell(0, 10, txt=f"Neurologia (Pupila): {pupil_diag}", ln=True)
        pdf.image("foto_evidencia.jpg", x=60, w=90)
        pdf.ln(80)
        pdf.set_font("Arial", 'I', 8)
        pdf.cell(0, 10, txt=f"Firma SHA-256: {signature}", ln=True, align='C')
        
        filename = f"Reporte_{self.patient_name.replace(' ','_')}.pdf"
        pdf.output(filename)
        return filename