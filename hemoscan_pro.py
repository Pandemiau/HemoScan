import cv2
import mediapipe as mp
import datetime
import winsound
import time
import pathlib
import pyttsx3 # <-- NUEVO IMPORT
import threading
import math
import csv
import matplotlib.pyplot as plt
import customtkinter as ctk
import hashlib
import numpy as np
import mysql.connector
from fpdf import FPDF
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from tkinter import ttk
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_face_mesh = mp.solutions.face_mesh

# --- NUEVA FUNCIÓN: VOZ EN SEGUNDO PLANO (MULTIHILO) ---
def asistente_de_voz(texto):
    motor = pyttsx3.init()
    motor.setProperty('rate', 160)
    motor.say(texto)
   
    motor.runAndWait()
# ======================================================
# --- NUEVA INTERFAZ GRÁFICA DE INICIO (GUI) ---
# ======================================================

# =========================================================
# --- NUEVO: MOTOR DE ENVÍO DE CORREO EN SEGUNDO PLANO ---
# =========================================================
def enviar_correo_silencioso(correo_destino, archivo_pdf_adjunto):
    try:
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from email.mime.application import MIMEApplication

        print(f"🚀 Iniciando hilo secundario: Enviando correo a {correo_destino}...")
        
        # 1. Configurar credenciales
        remitente = "TU_CORREO_AQUI"  # <--- ¡OJO! Pon tu correo aquí
        password = "TU_CONTRASENA_AQUI" # <--- ¡OJO! Pon tu contraseña aquí

        # 2. Crear el mensaje
        msg = MIMEMultipart()
        msg['From'] = remitente
        msg['To'] = correo_destino
        msg['Subject'] = "HemoScan IA - Resultados de su Escáner Biométrico"

       # 3. Cuerpo del correo (Ahora en formato HTML Médico)
        cuerpo_html = """
        <html>
          <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #333; line-height: 1.6;">
            <div style="background-color: #0f4c5c; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;">
                <h2 style="color: white; margin: 0;">HemoScan Pro</h2>
                <p style="color: #ddd; margin: 5px 0 0 0;">Sistema de Alerta Médica Temprana</p>
            </div>
            
            <div style="padding: 20px; border: 1px solid #ddd; border-top: none; border-radius: 0 0 8px 8px; background-color: #f9f9f9;">
                <h3 style="color: #0f4c5c;">Estimado Paciente / Especialista,</h3>
                <p>El escaneo biométrico dual ha concluido exitosamente. El sistema de IA ha procesado los siguientes módulos:</p>
                
                <ul style="color: #444;">
                    <li>🩸 <b>Módulo Vascular:</b> Análisis de Pigmentación Conjuntival (Detección de Anemia)</li>
                    <li>🧪 <b>Módulo Hepático:</b> Análisis de Esclera Ocular (Detección de Ictericia)</li>
                </ul>
                
                <p style="background-color: #e36414; color: white; padding: 10px; border-radius: 5px; text-align: center; font-weight: bold;">
                    Por favor, descargue y abra el archivo PDF adjunto para revisar los porcentajes exactos, la evidencia fotográfica y el diagnóstico clínico.
                </p>
                
                <hr style="border: none; border-top: 1px solid #ccc; margin: 25px 0;">
                <p style="font-size: 11px; color: #888; text-align: justify;">
                    <b>AVISO LEGAL:</b> Este correo y su documento adjunto fueron generados automáticamente por HemoScan Pro v2.0. Los resultados mostrados son producto de un análisis de visión artificial y no sustituyen un análisis de sangre.
                </p>
            </div>
          </body>
        </html>
        """
        
        # Le decimos a Python que este texto ya no es 'plain', sino 'html'
        msg.attach(MIMEText(cuerpo_html, 'html'))

        # 4. Adjuntar el PDF
        with open(archivo_pdf_adjunto, "rb") as f:
            adjunto = MIMEApplication(f.read(), _subtype="pdf")
            adjunto.add_header('Content-Disposition', 'attachment', filename=archivo_pdf_adjunto)
            msg.attach(adjunto)

        # 5. Conectar y disparar
        servidor = smtplib.SMTP('smtp.gmail.com', 587)
        servidor.starttls()
        servidor.login(remitente, password)
        servidor.send_message(msg)
        servidor.quit()
        
        print("✅ [HILO SECUNDARIO]: ¡Correo enviado exitosamente sin congelar la pantalla!")
        import winsound
        winsound.Beep(2000, 100) # Un pitido agudo para avisar que el hilo terminó

    except Exception as e:
        print(f"⚠️ [HILO SECUNDARIO]: Error al enviar el correo: {e}")

ctk.set_appearance_mode("dark") # Tema oscuro profesional
ctk.set_default_color_theme("blue") 

ventana = ctk.CTk()
ventana.geometry("450x300")
ventana.title("HemoScan IA - Panel de Control")

# Título Principal
label_titulo = ctk.CTkLabel(ventana, text="HemoScan IA v2.0", font=("Segoe UI", 26, "bold"), text_color="#00d2ff")
label_titulo.pack(pady=(30, 10))

label_instruccion = ctk.CTkLabel(ventana, text="Ingrese el nombre del paciente para comenzar:", font=("Segoe UI", 14))
label_instruccion.pack(pady=(0, 20))

# Caja de texto para el nombre
entrada_nombre = ctk.CTkEntry(ventana, width=280, height=40, font=("Segoe UI", 14), placeholder_text="Ej. Jorge Rodríguez")
entrada_nombre.pack(pady=10)

# Caja de texto para el correo (NUEVO)
entrada_correo = ctk.CTkEntry(ventana, width=280, height=40, font=("Segoe UI", 14), placeholder_text="Correo Electrónico (Ej. jorge@gmail.com)")
entrada_correo.pack(pady=(0, 10))

correo_paciente = "" # Variable global para guardar el correo

# --- NUEVO: SELECTOR DE CÁMARA ---
label_camara = ctk.CTkLabel(ventana, text="Seleccione la cámara a utilizar:", font=("Segoe UI", 14))
label_camara.pack(pady=(10, 0))

opcion_camara = ctk.CTkComboBox(ventana, values=["Cámara IP (Celular WiFi)", "Webcam Local (Laptop)"], width=280)
opcion_camara.pack(pady=5)

entrada_ip = ctk.CTkEntry(ventana, width=280, font=("Segoe UI", 12), placeholder_text="Dirección IP (Ej: http://192.168.1.5:8080/video)")
entrada_ip.pack(pady=5)
# Te dejo tu IP actual pre-escrita para que no la tengas que teclear siempre en tu casa:
entrada_ip.insert(0, "http://192.168.0.X:8080/video") # ¡OJO! Asegúrate de poner tus números reales aquí

# Variables globales que la IA usará
nombre_paciente = "Desconocido"
fuente_video = 0 

def ver_base_datos():

    # 1. Crear una ventana emergente
    ventana_db = ctk.CTkToplevel(ventana)
    ventana_db.title("Sistema de Gestión Hospitalaria - HemoScan")
    ventana_db.geometry("750x400")
    ventana_db.attributes("-topmost", True) # Mantener al frente
    
    # 2. Título interno
    label_titulo = ctk.CTkLabel(ventana_db, text="📋 Historial Clínico de Pacientes", font=("Segoe UI", 20, "bold"))
    label_titulo.pack(pady=15)
    
    # 3. Configurar la tabla (Estilo clásico integrado)
    columnas = ("ID", "Fecha", "Paciente", "Nivel Rojo", "Diagnóstico")
    tabla = ttk.Treeview(ventana_db, columns=columnas, show='headings', height=12)
    
    # Definir los encabezados y anchos de columna
    tabla.heading("ID", text="ID")
    tabla.column("ID", width=50, anchor='center')
    tabla.heading("Fecha", text="Fecha de Escaneo")
    tabla.column("Fecha", width=150, anchor='center')
    tabla.heading("Paciente", text="Nombre del Paciente")
    tabla.column("Paciente", width=200)
    tabla.heading("Nivel Rojo", text="Densidad Conjuntiva")
    tabla.column("Nivel Rojo", width=120, anchor='center')
    tabla.heading("Diagnóstico", text="Resultado IA")
    tabla.column("Diagnóstico", width=150, anchor='center')
# Definimos que la tabla tiene 7 columnas (usando los nombres originales de arriba)
    tabla["columns"] = ("ID", "Fecha", "Paciente", "Nivel Rojo", "Diagnóstico", "Ictericia", "Higado")
        
        # Agregamos los encabezados y anchos visuales para el hígado
    tabla.heading("Ictericia", text="Nivel Ictericia")
    tabla.column("Ictericia", width=120, anchor="center")
        
    tabla.heading("Higado", text="Estado Hepático")
    tabla.column("Higado", width=150, anchor="center")
        
        # 4. Extraer los datos de MySQL e insertarlos en la tabla
    try:
            import mysql.connector
            conexion_db = mysql.connector.connect(host="localhost", user="root", password="", database="hemoscan_db")
            cursor = conexion_db.cursor()
            
            # ¡CRÍTICO! Usamos SELECT * para que traiga TODAS las columnas (incluyendo el hígado)
            cursor.execute("SELECT * FROM historial_clinico")
            registros = cursor.fetchall()
            
            # Un solo ciclo FOR que ordena todo perfectamente
            for fila in registros:
                # f"{fila[3]}%" le pone el símbolo de porcentaje al rojo
                # f"{fila[-2]}%" le pone el símbolo de porcentaje al amarillo (penúltimo dato)
                # fila[-1] es el diagnóstico del hígado (último dato)
                tabla.insert("", "end", values=(fila[0], fila[1], fila[2], f"{fila[3]}%", fila[4], f"{fila[-2]}%", fila[-1]))    
            cursor.close()
            conexion_db.close()
        
    except Exception as e:
        tabla.insert("", "end", values=("-", "-", "Error de conexión a XAMPP", "-", "-"))
        print(f"Error al cargar DB: {e}")

        
    # ==========================================
        # --- NUEVO: EXPORTACIÓN SEGURA (AUDITORÍA PDF) ---
        # ==========================================
    def descargar_reporte_seguro():
            try:
                from fpdf import FPDF
                import datetime
                
                print("🔒 Generando reporte de auditoría inalterable...")
                pdf = FPDF()
                pdf.add_page()
                
                # Encabezado Oficial del Hospital
                pdf.set_font("Arial", 'B', 16)
                pdf.set_text_color(0, 51, 102)
                pdf.cell(0, 10, txt="HEMOSCAN - AUDITORIA GENERAL DE BASE DE DATOS", ln=True, align='C')
                
                pdf.set_font("Arial", 'I', 10)
                pdf.set_text_color(100, 100, 100)
                fecha_actual = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                pdf.cell(0, 10, txt=f"Fecha de emision del documento: {fecha_actual}", ln=True, align='C')
                pdf.line(10, 30, 200, 30)
                pdf.ln(10)
                
                # Dibujar los encabezados
                pdf.set_font("Arial", 'B', 10)
                pdf.set_text_color(0, 0, 0)
                pdf.cell(15, 10, "ID", border=1, align='C')
                pdf.cell(45, 10, "Fecha Escaneo", border=1, align='C')
                pdf.cell(65, 10, "Nombre del Paciente", border=1, align='C')
                pdf.cell(25, 10, "Rojo (%)", border=1, align='C')
                pdf.cell(40, 10, "Diagnostico", border=1, align='C')
                pdf.ln()
                
                # Extraer las filas de la tabla
                pdf.set_font("Arial", '', 9)
                for fila_id in tabla.get_children():
                    valores = tabla.item(fila_id)["values"]
                    pdf.cell(15, 10, str(valores[0]), border=1, align='C')
                    pdf.cell(45, 10, str(valores[1]), border=1, align='C')
                    pdf.cell(65, 10, str(valores[2])[:30], border=1) 
                    pdf.cell(25, 10, str(valores[3]), border=1, align='C')
                    pdf.cell(40, 10, str(valores[4]), border=1, align='C')
                    pdf.ln()
                    
                # Sello de inmutabilidad
                pdf.ln(10)
                pdf.set_font("Arial", 'I', 8)
                pdf.set_text_color(150, 150, 150)
                pdf.cell(0, 10, txt="Documento inalterable extraido directamente del servidor MySQL. Prohibida su modificacion.", ln=True, align='C')
                
                nombre_archivo = f"Auditoria_HemoScan_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
                pdf.output(nombre_archivo)
                
                print(f"✅ ¡Auditoría guardada exitosamente como {nombre_archivo}!")
                import winsound
                winsound.Beep(1200, 150)
                winsound.Beep(1600, 150)
                
            except Exception as e:
                print(f"⚠️ Error al crear auditoría: {e}")

        # =========================================================
        # --- ZONA DE DIBUJO (AFUERA DE LA FUNCIÓN DEL PDF) ---
        # =========================================================
        
# ==========================================
        # --- NUEVO: MOTOR ESTADÍSTICO MATPLOTLIB ---
        # ==========================================
    def mostrar_grafica():
            sanos = 0
            riesgo = 0
            
            # El programa lee la tabla en tiempo real
            for fila_id in tabla.get_children():
                diagnostico = str(tabla.item(fila_id)["values"][4]).upper()
                if "SALUDABLE" in diagnostico:
                    sanos += 1
                else:
                    riesgo += 1
                    
            # Si la base de datos está vacía, evitamos un error
            if sanos == 0 and riesgo == 0:
                print("⚠️ No hay datos suficientes para graficar.")
                return

            # Dibujamos la gráfica de pastel
            etiquetas = ['Saludables', 'En Riesgo / Anemia']
            valores = [sanos, riesgo]
            colores = ['#2ecc71', '#e74c3c'] # Verde y Rojo
            
            plt.figure(figsize=(6, 5))
            plt.pie(valores, labels=etiquetas, autopct='%1.1f%%', startangle=90, colors=colores, shadow=True)
            plt.title('HemoScan IA - Análisis Poblacional Histórico', fontweight='bold')
            plt.axis('equal') # Para que el pastel sea un círculo perfecto
            plt.show()

    # 1. Creamos y empacamos el botón rojo (pegado al fondo)
    boton_exportar = ctk.CTkButton(ventana_db, text="🔒 EXPORTAR AUDITORÍA (PDF)", command=descargar_reporte_seguro,
                                    fg_color="#c0392b", hover_color="#e74c3c", font=("Segoe UI", 12, "bold"))
    boton_exportar.pack(side="bottom", pady=15)

    # 2. Botón Analítico Azul (Agregado al fondo)
    boton_grafica = ctk.CTkButton(ventana_db, text="📊 VER ESTADÍSTICAS GLOBALES", command=mostrar_grafica,
                                    fg_color="#2980b9", hover_color="#3498db", font=("Segoe UI", 12, "bold"))
    boton_grafica.pack(side="bottom", pady=(0, 10))

    # 3. Empacamos la tabla
    tabla.pack(side="top", fill="both", expand=True, padx=20, pady=(0, 10))

# Función del botón actualizada
def arrancar_motor():

    global nombre_paciente, fuente_video, correo_paciente # Agregamos correo_paciente aquí
    
    # 1. Guardar el nombre
    texto_ingresado = entrada_nombre.get()
    if texto_ingresado.strip() != "":
        nombre_paciente = texto_ingresado
        
    # 2. Guardar el correo (NUEVO)
    correo_ingresado = entrada_correo.get()
    if correo_ingresado.strip() != "":
        correo_paciente = correo_ingresado
        
    # 3. Guardar qué cámara seleccionaste
    seleccion = opcion_camara.get()
    if seleccion == "Webcam Local (Laptop)":
        fuente_video = 0
    else:
        fuente_video = entrada_ip.get()
        
    ventana.destroy()

# Botón de Inicio Gigante
boton_iniciar = ctk.CTkButton(ventana, text="INICIAR ESCÁNER", command=arrancar_motor, 
                              width=200, height=45, font=("Segoe UI", 15, "bold"), 
                              fg_color="#2ecc71", hover_color="#27ae60")
boton_iniciar.pack(pady=15)

# Botón secundario para ver el historial
boton_historial = ctk.CTkButton(ventana, text="VER BASE DE DATOS", command=ver_base_datos,
                                width=200, height=35, font=("Segoe UI", 12, "bold"),
                                fg_color="#34495e", hover_color="#2c3e50")
boton_historial.pack(pady=(5, 10))

ventana.mainloop() 
# ======================================================
# ======================================================

# --- A PARTIR DE AQUÍ CONTINÚA TU CÓDIGO ORIGINAL (cap = cv2.VideoCapture...) ---

# 1. Configuración de la IA para encontrar la cara
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True)

# --- CONEXIÓN DE CÁMARA DINÁMICA ---
# La IA ahora leerá la 'fuente_video' que elegiste en el Panel de Control
cap = cv2.VideoCapture(fuente_video)

print("Presiona la tecla 'q' para cerrar la cámara")

# --- VARIABLES GLOBALES ---
scanning_counter = 0
tiempo_anterior = 0 
historial_porcentajes = [] 
historial_grafica = [] # <--- NUEVA MEMORIA PARA LA GRÁFICA
umbral_sano = 40 
modo_termico = False # El filtro empieza apagado

# --- NUEVA FUNCIÓN: GENERADOR DE REPORTES HTML ---
def generar_reporte_html(nombre, fecha, porcentaje, diagnostico, porcentaje_amarillo, diagnostico_higado, imagen_path):
    # Creamos el nombre del archivo de reporte (ej. "reporte_Jorge_12_03_2026.html")
    fecha_limpia = fecha.replace("/", "_").replace(":", "_").replace(" ", "_")
    reporte_filename = f"reporte_{nombre.replace(' ', '_')}_{fecha_limpia}.html"
    
    # Obtenemos la ruta absoluta de la imagen para que el HTML la encuentre
    img_ruta_absoluta = pathlib.Path(imagen_path).absolute().as_uri()
    
    # Esta es la "plantilla" de nuestra página web con diseño CSS incluido
    plantilla_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Expediente Clínico Multibiométrico</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #333; line-height: 1.6; margin: 40px; }}
            .header {{ text-align: center; background-color: #0f4c5c; color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
            .paciente-box {{ background-color: #f4f4f9; padding: 15px; border-left: 5px solid #0f4c5c; margin-top: 20px; }}
            .diagnostico-container {{ display: flex; justify-content: space-between; margin-top: 20px; }}
            .card {{ width: 45%; padding: 15px; border: 1px solid #ddd; border-radius: 8px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }}
            .alerta {{ color: #d62828; font-weight: bold; }}
            .sano {{ color: #2a9d8f; font-weight: bold; }}
            .legal {{ font-size: 10px; color: #777; text-align: center; margin-top: 40px; border-top: 1px solid #eee; padding-top: 10px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2>HemoScan Pro - Análisis Biométrico por IA</h2>
            <p>Reporte Oficial de Escaneo</p>
        </div>
        
        <div class="paciente-box">
            <h3>Datos del Paciente: <b>{nombre}</b></h3>
            <p>Fecha y Hora del Escaneo: {fecha}</p>
        </div>

        <div class="diagnostico-container">
            <div class="card">
                <h3 style="color: #0f4c5c;">🩸 Análisis Vascular</h3>
                <p>Zona escaneada: Conjuntiva Palpebral</p>
                <p>Nivel de Pigmentación (Rojo): <b>{porcentaje}%</b></p>
                <p>Diagnóstico IA: <span class="{'alerta' if 'ALERTA' in diagnostico else 'sano'}">{diagnostico}</span></p>
            </div>

            <div class="card">
                <h3 style="color: #e36414;">🧪 Análisis Hepático</h3>
                <p>Zona escaneada: Esclera Ocular</p>
                <p>Nivel de Bilirrubina (Amarillo): <b>{porcentaje_amarillo}%</b></p>
                <p>Diagnóstico IA: <span class="{'alerta' if 'ALERTA' in diagnostico_higado else 'sano'}">{diagnostico_higado}</span></p>
            </div>
        </div>

        <h3 style="margin-top: 30px;">Evidencia Fotográfica:</h3>
        <img src="{imagen_path}" width="400" style="border: 2px solid #ccc; border-radius: 5px;">

        <div class="legal">
            <p>ESTE DOCUMENTO ES GENERADO AUTOMÁTICAMENTE POR INTELIGENCIA ARTIFICIAL.</p>
            <p><i>Aviso legal: HemoScan Pro es una herramienta de pre-diagnóstico asistido y NO sustituye un examen de sangre de laboratorio clínico ni el criterio de un médico profesional.</i></p>
        </div>
    </body>
    </html>
    """
    
    # Escribimos el archivo HTML
    with open(reporte_filename, 'w', encoding='utf-8') as archivo:
        archivo.write(plantilla_html)
        
    print(f"🌐 ¡BEEP-BEEP! Reporte web generado: {reporte_filename}")
    return reporte_filename

while cap.isOpened():
    
    success, image = cap.read()
    if not success:

        # Valores de seguridad por si la IA pierde el rostro
        porcentaje_rojo = 0
        porcentaje_amarillo = 0

        break

    # --- NUEVO: ESTANDARIZAR TAMAÑO PARA EVITAR LAG ---
    image = cv2.resize(image, (800, 600))

    # 2. Convertir la imagen para que la IA la entienda
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(image_rgb)

    # 3. Si la IA encuentra una cara, analiza los puntos
    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:

            # --- NUEVO: HUD MÉDICO LIMPIO ---
            #cv2.putText(image, "HemoScan IA - Sensor Biometrico Activo", (130, 150), 
                    #cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            #cv2.putText(image, ">>> Analizando micro-vasculatura...", (130, 180), 
                    #cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            # ==========================================
            puntos_parpado = [145, 153, 154, 155, 374, 380, 381, 382]

            # ==========================================
            # --- NUEVO: VISIÓN QUIRÚRGICA (MÁSCARAS) ---
            # ==========================================
            h, w, _ = image.shape # Extraemos las medidas exactas de tu cámara
            
            # 1. Crear un lienzo completamente negro
            mascara = np.zeros((h, w), dtype=np.uint8)

            # --- NUEVO SISTEMA DE CALIBRACIÓN CLÍNICA (HEMOSCAN PRO) ---
        # 1. Localizar el centro debajo del ojo izquierdo (Punto 145)
        ojo_x = int(face_landmarks.landmark[145].x * w)
        ojo_y = int(face_landmarks.landmark[145].y * h)
        
        # 2. Dibujar la "Mira Quirúrgica" (Targeting Box)
        box_ancho = 40
        box_alto = 15
        y_offset = 12 # Bajamos la mira para apuntar a la conjuntiva expuesta
        
        punto_1 = (ojo_x - box_ancho//2, ojo_y + y_offset)
        punto_2 = (ojo_x + box_ancho//2, ojo_y + y_offset + box_alto)
        
        # Dibujamos el cuadro guía en pantalla (Cian médico)
        cv2.rectangle(image, punto_1, punto_2, (255, 255, 0), 2)
        cv2.putText(image, "ALINEAR CONJUNTIVA AQUI", (punto_1[0] - 40, punto_1[1] - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 0), 1)

        # 3. Extraer SOLO el tejido dentro de la mira
        zona_aislada = np.zeros((10, 10, 3), dtype=np.uint8) # Respaldo por si falla
        
        if punto_1[1] > 0 and punto_2[1] < h and punto_1[0] > 0 and punto_2[0] < w:
            # Recorte exacto estilo francotirador
            zona_aislada = image_rgb[punto_1[1]:punto_2[1], punto_1[0]:punto_2[0]]
            
            # --- FILTRO DE LUZ Y SOMBRA (Nivel Pro) ---
            # Ignoramos los píxeles negros/oscuros que arruinan el porcentaje
            hsv_zona = cv2.cvtColor(zona_aislada, cv2.COLOR_RGB2HSV)
            mascara_brillo = cv2.inRange(hsv_zona, (0, 0, 40), (180, 255, 255))
            zona_aislada = cv2.bitwise_and(zona_aislada, zona_aislada, mask=mascara_brillo)
            
            # Devolvemos a BGR para que tu minimapa PIP lo muestre bien
            zona_aislada = cv2.cvtColor(zona_aislada, cv2.COLOR_RGB2BGR)
            # 5. Minimapa PIP (Picture-in-Picture)
            minimapa = cv2.resize(zona_aislada, (200, 150))
            image[h-150:h, 0:200] = minimapa
            cv2.rectangle(image, (0, h-150), (200, h), (0, 255, 0), 2)
            cv2.putText(image, "ZONA DE ANALISIS", (10, h-160), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
            # ==========================================
            
            # Variables para sumar todos los colores
            suma_rojo = 0
            suma_total_color = 0
            
            # --- NUEVO CÁLCULO VECTORIZADO (Numpy) ---
            # --- NUEVO CÁLCULO (Adaptado a la mini-zona de precisión) ---
            # Separamos los canales Azul, Verde y Rojo del pequeño recorte
            b, g, r = cv2.split(zona_aislada)

            # Como el recorte ya es exacto, sumamos los colores directamente
            # (Los píxeles oscuros valen 0 gracias a nuestro filtro de luz, así que no arruinan la suma)
            suma_rojo = int(np.sum(r))
            suma_verde = int(np.sum(g))
            suma_azul = int(np.sum(b))

            suma_total_color = suma_rojo + suma_verde + suma_azul
                    
            # --- NUEVA LÓGICA DE DIAGNÓSTICO (PORCENTAJE) ---
            if suma_total_color > 0:
                # Calculamos el porcentaje de rojo real
                porcentaje_rojo = int((suma_rojo / suma_total_color) * 100)
            else:
                porcentaje_rojo = 0
                
            # En la sangre humana sana, el rojo suele representar más del 40% del color en esa zona
# En la sangre humana sana, el rojo suele representar más del 40% del color en esa zona

            # ==========================================================
        # --- NUEVO: ESCÁNER HEPÁTICO (ICTERICIA / ESCLERA) ---
        # ==========================================================
        
        # 1. Localizar la esquina interior del ojo izquierdo (Punto 133)
        esclera_x = int(face_landmarks.landmark[133].x * w)
        esclera_y = int(face_landmarks.landmark[133].y * h)
        
        # 2. Definir las coordenadas de la "Mira"
        box_esc_ancho = 15 
        box_esc_alto = 10 
        x_offset = -18
        y_offset_esc = -12
        
        punto_esc_1 = (esclera_x + x_offset, esclera_y + y_offset_esc)
        punto_esc_2 = (esclera_x + x_offset + box_esc_ancho, esclera_y + y_offset_esc + box_esc_alto)
        
        # 3. Analizar el pigmento Amarillo
        porcentaje_amarillo = 0
        if punto_esc_1[1] > 0 and punto_esc_2[1] < h and punto_esc_1[0] > 0 and punto_esc_2[0] < w:
            
            # --- ¡EL TRUCO DE MAGIA! ---
            # PRIMERO cortamos la imagen LIMPIA (usando .copy() para no llevarnos la pintura)
            zona_esclera = image.copy()[punto_esc_1[1]:punto_esc_2[1], punto_esc_1[0]:punto_esc_2[0]]
            
            # SEGUNDO, ahora sí pintamos la mira amarilla en la pantalla
            cv2.rectangle(image, punto_esc_1, punto_esc_2, (0, 255, 255), 2)
            cv2.putText(image, "ESCLERA", (punto_esc_1[0] - 10, punto_esc_1[1] - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 255), 1)
            
            # TERCERO, analizamos el recorte que está limpio
            hsv_esclera = cv2.cvtColor(zona_esclera, cv2.COLOR_BGR2HSV)
            
            # Rango EQUILIBRADO: Acepta amarillos en cuartos con menos luz, pero rechaza la piel
            amarillo_bajo = np.array([15, 60, 60]) 
            amarillo_alto = np.array([45, 255, 255])
            
            mascara_amarilla = cv2.inRange(hsv_esclera, amarillo_bajo, amarillo_alto)
            
            pixeles_amarillos = cv2.countNonZero(mascara_amarilla)
            pixeles_totales_esclera = box_esc_ancho * box_esc_alto
            
            if pixeles_totales_esclera > 0:
                porcentaje_amarillo = int((pixeles_amarillos / pixeles_totales_esclera) * 100)
            
            
            # --- NUEVO: ESTABILIZADOR DE SENSOR (PROMEDIO MÓVIL) ---
            historial_porcentajes.append(porcentaje_rojo)
            if len(historial_porcentajes) > 15: # Mantiene solo los últimos 15 fotogramas
                historial_porcentajes.pop(0)
                
            # Calcula el promedio exacto para evitar que el número "tiemble"
            porcentaje_estabilizado = int(sum(historial_porcentajes) / len(historial_porcentajes))
            
            if porcentaje_estabilizado >= umbral_sano:
                diagnostico = "Estado: SALUDABLE"
                color_texto = (0, 255, 0) # Verde
            else:
                diagnostico = "ALERTA: POSIBLE ANEMIA"
                color_texto = (0, 0, 255) # Rojo
                
            # Textos en pantalla usando el valor estabilizado
            # Textos en pantalla usando el valor estabilizado (Grosor 1)
        cv2.putText(image, f"Porcentaje de Rojo: {porcentaje_estabilizado}%", (80, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_texto, 1)
        cv2.putText(image, diagnostico, (80, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_texto, 1)

        # ---------------------------------------------------------
        # --- NUEVO HUD: RESULTADO DE ICTERICIA ---
        # ---------------------------------------------------------

        # Lógica de diagnóstico rápido para el Hígado
        # En un ojo sano, el amarillo debe ser casi 0%. Damos un margen de 5% por las luces.
        if porcentaje_amarillo < 5:
            texto_higado = "Higado: SANO"
            color_higado = (0, 255, 0) # Verde
        else:
            texto_higado = "ALERTA: POSIBLE ICTERICIA"
            color_higado = (0, 0, 255) # Rojo de advertencia

        # Mostrar el porcentaje de color amarillo detectado
            cv2.putText(image, "ANALISIS HEPATICO (Ictericia)", (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 1)
            cv2.putText(image, f"Nivel Ictericia: {porcentaje_amarillo}%", (10, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 1)
            cv2.putText(image, texto_higado, (10, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_higado, 1)
        # ---------------------------------------------------------
            
            # --- NUEVO: BARRA GRÁFICA DE NIVEL ---
            # 1. Dibujar el contorno de la barra (vacío)
            cv2.rectangle(image, (20, 20), (60, 220), (255, 255, 255), 2)
            
            # 2. Calcular qué tan llena está la barra (máximo 200 píxeles de alto)
            porcentaje_grafico = min(porcentaje_estabilizado, 100) # Evita que se salga del 100%
            alto_relleno = int((porcentaje_grafico / 100) * 200)
            
            # 3. Rellenar la barra (Sube desde abajo hacia arriba)
            cv2.rectangle(image, (20, 220 - alto_relleno), (60, 220), color_texto, cv2.FILLED)
            
            # --- INTERFAZ GRÁFICA (HUD) ---
            h, w, canales = image.shape
            x_coords = [int(punto.x * w) for punto in face_landmarks.landmark]
            y_coords = [int(punto.y * h) for punto in face_landmarks.landmark]
            
            x_min, x_max = min(x_coords), max(x_coords)
            y_min, y_max = min(y_coords), max(y_coords)
            
            # --- NUEVO: SENSOR DE PROXIMIDAD (RADAR) ---
            # Calculamos la distancia en píxeles entre los extremos de los ojos (puntos 33 y 263)
            ojo_izq = face_landmarks.landmark[33]
            ojo_der = face_landmarks.landmark[263]
            distancia_ojos = math.hypot((ojo_der.x - ojo_izq.x) * w, (ojo_der.y - ojo_izq.y) * h)

            # Lógica de distancia para el color y texto del radar
            if distancia_ojos < 120: # El paciente está muy lejos
                color_hud = (0, 255, 255) # Amarillo
                texto_hud = "ALERTA: ACERQUESE A LA CAMARA"
            elif distancia_ojos > 300: # El paciente está demasiado cerca
                color_hud = (0, 165, 255) # Naranja
                texto_hud = "ALERTA: ALEJESE UN POCO"
            else: # Distancia perfecta para leer la sangre
                color_hud = (255, 255, 0) # Cyan original
                texto_hud = "RANGO OPTIMO - PACIENTE FIJADO"

            # Dibujamos el cuadro y el texto con el color dinámico
            cv2.rectangle(image, (x_min, y_min), (x_max, y_max), color_hud, 2)
            cv2.putText(image, texto_hud, (x_min, y_min - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color_hud, 2)
            
            # --- NUEVO: ANIMACIÓN DE LÁSER ---
            # Calculamos la altura de la caja de tu cara
            altura_caja = y_max - y_min
            if altura_caja > 0:
                # Velocidad de la línea (píxeles por fotograma)
                velocidad_frames = 5 
                
                # Incrementamos el contador en cada frame
                scanning_counter += velocidad_frames
                
                # Si la línea llega al final de la cara, la reiniciamos arriba
                if scanning_counter >= altura_caja:
                    scanning_counter = 0
                    
                # Coordenadas exactas del láser
                y_laser = y_min + scanning_counter
                
                # Dibujamos una línea verde horizontal que barre la cara
                cv2.line(image, (x_min, y_laser), (x_max, y_laser), (0, 255, 0), 2)

            # --- NUEVO: MONITOR DE TELEMETRÍA EN VIVO ---
            # 1. Guardar el dato actual en la memoria de la gráfica
            historial_grafica.append(porcentaje_estabilizado)
            if len(historial_grafica) > 100: # Mantener solo 100 puntos en pantalla
                historial_grafica.pop(0)
                
            # 2. Dibujar el fondo del monitor (Esquina inferior derecha)
            h, w, c = image.shape
            cv2.rectangle(image, (w - 230, h - 130), (w - 20, h - 20), (0, 0, 0), cv2.FILLED) # Fondo negro
            cv2.rectangle(image, (w - 230, h - 130), (w - 20, h - 20), (0, 255, 255), 1) # Borde amarillo
            cv2.putText(image, 'TELEMETRIA EN VIVO', (w - 225, h - 135), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
            
            # 3. Dibujar la línea de la gráfica conectando los puntos
            for i in range(1, len(historial_grafica)):
                # Calcular la posición X (avanza 2 píxeles por cada punto)
                x_prev = w - 230 + (i - 1) * 2
                x_curr = w - 230 + i * 2
                
                # Calcular la posición Y (convertimos el porcentaje a píxeles de altura)
                y_prev = h - 20 - int((historial_grafica[i-1] / 100) * 100)
                y_curr = h - 20 - int((historial_grafica[i] / 100) * 100)
                
                # Dibujar un segmento de la línea
                cv2.line(image, (x_prev, y_prev), (x_curr, y_curr), color_texto, 2)

   # --- NUEVO: MEDIDOR DE FPS ---
            tiempo_actual = time.time()
            if (tiempo_actual - tiempo_anterior) > 0:
                fps = int(1 / (tiempo_actual - tiempo_anterior))
            else:
                fps = 0
            tiempo_anterior = tiempo_actual
            
            # Dibujar los FPS en la esquina superior derecha
            h, w, c = image.shape
            cv2.putText(image, f'FPS: {fps}', (w - 120, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    # --- NUEVO: APLICAR MAPA DE CALOR ---
    if modo_termico:
        # Transforma los colores normales a un espectro térmico
        image = cv2.applyColorMap(image, cv2.COLORMAP_JET)
        # Aviso en pantalla para que el profesor sepa qué está viendo
        cv2.putText(image, "FILTRO TERMICO ACTIVADO", (20, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

    # 4. Mostrar la ventana con el video
    cv2.imshow('HemoScan IA', image)
    
# --- CONTROLES DEL TECLADO Y BASE DE DATOS ---
    tecla = cv2.waitKey(5) & 0xFF
    
    if tecla == ord('g'): # --- ACTUALIZADO: MÓDULO DE ANALÍTICA (MySQL) ---
        winsound.Beep(1200, 100)
        print("📊 Generando gráfica de población desde MySQL...")
        try:
            # 1. Conectar a la base de datos XAMPP
            conexion_db = mysql.connector.connect(
                host="localhost",
                user="root",
                password="",
                database="hemoscan_db"
            )
            cursor = conexion_db.cursor()
            
            # 2. Extraer los nombres y porcentajes directamente de la tabla
            cursor.execute("SELECT nombre, porcentaje_rojo FROM historial_clinico")
            registros = cursor.fetchall()
            
            if not registros:
                print("❌ La base de datos está vacía. Escanea a un paciente primero.")
            else:
                nombres = []
                porcentajes = []
                colores = []
                
                # 3. Procesar los datos para Matplotlib
                for fila in registros:
                    nombres.append(fila[0]) # El nombre es la primera columna del SELECT
                    val = int(fila[1])      # El porcentaje es la segunda
                    porcentajes.append(val)
                    colores.append('green' if val >= umbral_sano else 'red')
                
                # 4. Dibujar el Dashboard
                plt.figure(figsize=(10, 5))
                plt.bar(nombres, porcentajes, color=colores)
                plt.axhline(y=umbral_sano, color='blue', linestyle='--', label=f'Umbral Sano ({umbral_sano}%)')
                
                plt.title('Análisis de Población Médica - Servidor MySQL')
                plt.xlabel('Pacientes Escaneados')
                plt.ylabel('Nivel de Irrigación Sanguínea (%)')
                plt.legend()
                plt.xticks(rotation=45)
                plt.tight_layout()
                
                # 5. Mostrar la ventana con la gráfica
                plt.show()
                
            cursor.close()
            conexion_db.close()
            
        except mysql.connector.Error as error:
            print(f"⚠️ Error al conectar con MySQL para la gráfica: {error}")

    elif tecla == ord('t'): # --- NUEVO: INTERRUPTOR TÉRMICO ---
        modo_termico = not modo_termico # Enciende o apaga el filtro
        winsound.Beep(900, 150)
        
    elif tecla == ord('q'):
        break
    
    if tecla == ord('q'):
        break
        
    elif tecla == ord('c'): # --- NUEVO: BOTÓN DE CALIBRACIÓN ---
        umbral_sano = porcentaje_estabilizado - 5
        print(f"⚙️ ¡CALIBRADO! Nuevo umbral sano fijado en: {umbral_sano}%")
        winsound.Beep(1000, 100) # Sonido rápido de configuración
        winsound.Beep(1500, 100)
        
    elif tecla == 32: # Barra espaciadora
        winsound.Beep(2000, 200) 
        fecha_hora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        cv2.imwrite('expediente_hemoscan.png', image)

        # 2. Generar Firma Digital Anti-Fraude (Hash SHA-256)
        datos_en_bruto = f"{fecha_hora}{nombre_paciente}{porcentaje_estabilizado}{diagnostico}"
        firma_digital = hashlib.sha256(datos_en_bruto.encode('utf-8')).hexdigest()[:12] # Tomamos los primeros 12 caracteres
        
        # 3. Guardar los datos en el historial clínico con su sello inalterable
        with open('historial_medico.csv', 'a', encoding='utf-8') as archivo:
            # Agregamos la firma al final de la línea
            archivo.write(f"{fecha_hora}, {nombre_paciente}, {porcentaje_estabilizado}%, {diagnostico}, FIRMA:{firma_digital}\n")
            
            # ==========================================
        # --- NUEVO: CONEXIÓN A BASE DE DATOS MYSQL ---
        # ==========================================
        try:
            # MySQL necesita un formato de fecha específico (Año-Mes-Día)
            fecha_mysql = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 1. Abrir la conexión con XAMPP
            conexion_db = mysql.connector.connect(
                host="localhost",
                user="root",      # Usuario por defecto en XAMPP
                password="",      # Sin contraseña por defecto
                database="hemoscan_db"
            )
            
            cursor = conexion_db.cursor()
            
            # 2. Preparar el comando SQL en una sola línea limpia
            comando_sql = "INSERT INTO historial_clinico (fecha_escaneo, nombre, porcentaje_rojo, diagnostico, firma_digital, porcentaje_amarillo, diagnostico_higado) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        
            # Las 7 variables exactas
            valores_sql = (fecha_mysql, nombre_paciente, porcentaje_estabilizado, diagnostico, firma_digital, porcentaje_amarillo, texto_higado)
            
            # 3. Ejecutar y guardar (Commit)
            cursor.execute(comando_sql, valores_sql)
            conexion_db.commit()
            
            print("💾 ¡Datos guardados exitosamente en el servidor MySQL!")
            
            # 4. Cerrar la conexión
            cursor.close()
            conexion_db.close()
            
        except mysql.connector.Error as error:
            print(f"⚠️ Error de servidor: {error}")
            print("Los datos se guardaron en el Excel de respaldo local.")

            # ==========================================
        # --- NUEVO: GENERADOR DE PDF MÉDICO ---
        # ==========================================
        # --- NUEVO: CAPTURAR EVIDENCIA CLÍNICA ---
        cv2.imwrite("foto_evidencia.jpg", image)
        
        try:
            print("📄 Generando expediente médico en PDF...")
            pdf = FPDF()
            pdf.add_page()
            
            # Encabezado Oficial
            pdf.set_font("Arial", 'B', 18)
            pdf.set_text_color(0, 51, 102) # Color azul oscuro
            pdf.cell(0, 10, txt="HEMOSCAN IA - REPORTE MEDICO OFICIAL", ln=True, align='C')
            pdf.line(10, 25, 200, 25) # Línea divisoria
            pdf.ln(10)
            
            # Datos del Paciente
            pdf.set_font("Arial", 'B', 12)
            pdf.set_text_color(0, 0, 0) # Letra negra
            pdf.cell(50, 10, txt="Nombre del Paciente:", border=0)
            pdf.set_font("Arial", '', 12)
            pdf.cell(0, 10, txt=nombre_paciente, ln=True)
            
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(50, 10, txt="Fecha de Escaneo:")
            pdf.set_font("Arial", '', 12)
            # Usamos la fecha_mysql que ya habíamos creado arriba
            pdf.cell(0, 10, txt=fecha_mysql, ln=True)
            
            # Resultados Biomédicos
            pdf.ln(5)
            pdf.set_font("Arial", 'B', 14)
            pdf.set_text_color(153, 0, 0) # Rojo oscuro
            pdf.cell(0, 10, txt="RESULTADOS BIOMETRICOS", ln=True)
            
            pdf.set_font("Arial", 'B', 12)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(60, 10, txt="Densidad de Conjuntiva:")
            pdf.set_font("Arial", '', 12)
            pdf.cell(0, 10, txt=f"{porcentaje_estabilizado}%", ln=True)
            
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(60, 10, txt="Diagnostico IA:")
            pdf.set_font("Arial", 'B', 12)
            # Cambiar color si es alerta o saludable
            if porcentaje_estabilizado >= umbral_sano:
                pdf.set_text_color(0, 128, 0) # Verde
            else:
                pdf.set_text_color(255, 0, 0) # Rojo
            pdf.cell(0, 10, txt=diagnostico, ln=True)
            
            # ... (aquí terminan los textos de diagnóstico) ...
            
            # Insertar la fotografía del paciente
            pdf.ln(10) # Damos un pequeño salto de línea
            # Ponemos la foto centrada (x=60) y con un ancho de 90 mm
            pdf.image("foto_evidencia.jpg", x=60, w=90) 
            
            # Sello de Seguridad
            pdf.ln(100) # Saltamos el espacio que ocupa la foto
            pdf.set_font("Arial", 'I', 8)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(0, 10, txt=f"Firma Criptografica (SHA-256): {firma_digital}", ln=True, align='C')
            pdf.cell(0, 5, txt="Documento generado automaticamente por HemoScan IA v2.0", ln=True, align='C')
            
            # Guardar el PDF con un nombre único
            nombre_archivo_pdf = f"Reporte_{nombre_paciente.replace(' ', '_')}_{fecha_mysql.replace(':', '').replace('-', '').replace(' ', '_')}.pdf"
            pdf.output(nombre_archivo_pdf)
            print(f"✅ ¡PDF Guardado exitosamente como {nombre_archivo_pdf}!")
            
            # --- NUEVO: DISPARAR EL HILO DE CORREO ---
            if correo_paciente.strip() != "":
                # Creamos el clon (hilo) y lo mandamos a trabajar en el fondo
                hilo_correo = threading.Thread(target=enviar_correo_silencioso, args=(correo_paciente, nombre_archivo_pdf))
                hilo_correo.start() 
            else:
                print("ℹ️ El paciente no proporcionó correo. Se guardó solo de forma local.")       
            
        except Exception as e:
            print(f"⚠️ Error al crear el PDF: {e}")
        # ==========================================
        # ==========================================
        
       # --- NUEVO: GENERAR REPORTE HTML ---
        generar_reporte_html(nombre_paciente, fecha_mysql, porcentaje_estabilizado, diagnostico, porcentaje_amarillo, texto_higado, "foto_evidencia.jpg")
        
        print("🗂️ ¡Datos guardados exitosamente!")
        
# --- NUEVO: SÍNTESIS DE VOZ SIN CONGELAR (MULTIHILO) ---
        texto_hablar = f"Reporte generado. Paciente {nombre_paciente}. {diagnostico.replace('Estado:', '').replace('ALERTA:', 'Alerta,')}"
        
        # Llamamos a la voz directamente para evitar crasheos de memoria
        asistente_de_voz(texto_hablar)

cap.release()
cv2.destroyAllWindows()