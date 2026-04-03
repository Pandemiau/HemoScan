import mysql.connector
from mysql.connector import Error

class DatabaseManager:
    """
    Gestor de base de datos para HemoScan.
    Aplica el principio de Responsabilidad Única (SRP). Este módulo
    no sabe nada de cámaras ni de Tkinter, solo se encarga de la persistencia de datos.
    """
    
    def __init__(self, host="localhost", user="root", password="", database="hemoscan_db"):
        # Inicializamos las credenciales. En un entorno real, esto vendría de variables de entorno (.env)
        self.host = host
        self.user = user
        self.password = password
        self.database = database

    def guardar_historial(self, fecha_mysql, nombre_paciente, porcentaje_rojo, diagnostico, firma_digital, porcentaje_amarillo, diagnostico_higado):
        """Abre conexión, guarda el registro biométrico dual y cierra la conexión de forma segura."""
        try:
            # 1. Establecer conexión aislada
            conexion = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            cursor = conexion.cursor()
            
            # 2. Preparar el comando SQL limpio (Previene inyecciones SQL)
            comando_sql = (
                "INSERT INTO historial_clinico "
                "(fecha_escaneo, nombre, porcentaje_rojo, diagnostico, firma_digital, porcentaje_amarillo, diagnostico_higado) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)"
            )
            
            # 3. Asignar los valores recibidos por el sensor
            valores = (fecha_mysql, nombre_paciente, porcentaje_rojo, diagnostico, firma_digital, porcentaje_amarillo, diagnostico_higado)
            
            # 4. Ejecutar y consolidar
            cursor.execute(comando_sql, valores)
            conexion.commit()
            print("INFO [DB_MANAGER]: Registro biométrico asegurado exitosamente en MySQL.")
            
        except Error as e:
            # Tolerancia a fallos: Registramos el error sin crashear todo el programa visual
            print(f"CRITICAL ERROR [DB_MANAGER]: Fallo de persistencia en MySQL -> {e}")
        finally:
            # Watchdog de limpieza: Garantiza que el puerto se cierre incluso si hay un fallo
            if 'conexion' in locals() and conexion.is_connected():
                cursor.close()
                conexion.close()