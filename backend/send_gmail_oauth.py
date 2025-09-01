import smtplib
import base64
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# Datos de tu app
CLIENT_ID = "49649377583-1ie040pjnmpnhcnb6tp6scjnjuckvoj1.apps.googleusercontent.com"
CLIENT_SECRET = "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"
REFRESH_TOKEN = "1//0hkAgAHDgDNH3CgYIARAAGBESNwF-L9IrYoy9FcQhvVCJ-GWMJMCIHJzRpE3GKG9rrDtceu0q9OQFx4EDBsebJTOK665xYUcXt-o"
EMAIL = "ayl.ti.spa@gmail.com"

# Construir credenciales
creds = Credentials(
    None,
    refresh_token=REFRESH_TOKEN,
    token_uri="https://oauth2.googleapis.com/token",
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    scopes=["https://mail.google.com/"],
)

# Refrescar token (obtener access_token nuevo)
creds.refresh(Request())
access_token = creds.token

# Crear mensaje
msg = MIMEText("¡Hola! Este correo fue enviado con Gmail y OAuth2 en Python.")
msg["Subject"] = "Prueba Gmail OAuth2"
msg["From"] = EMAIL
msg["To"] = EMAIL

# Preparar string de autenticación XOAUTH2
auth_string = f"user={EMAIL}\1auth=Bearer {access_token}\1\1"
auth_bytes = base64.b64encode(auth_string.encode("utf-8"))

# Conectar a Gmail SMTP
server = smtplib.SMTP("smtp.gmail.com", 587)
server.ehlo()
server.starttls()
server.ehlo()
server.docmd("AUTH", "XOAUTH2 " + auth_bytes.decode())

server.sendmail(EMAIL, [EMAIL], msg.as_string())
server.quit()

print("✅ Correo enviado correctamente")
