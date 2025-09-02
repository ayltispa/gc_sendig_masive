import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import threading  # Para ejecutar tareas en segundo plano

from django.conf import settings
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .models import Propietario, LoteDeEnvio, LogMensaje
from .serializers import PropietarioSerializer, LoteDeEnvioSerializer


class PropietarioViewSet(viewsets.ModelViewSet):
    queryset = Propietario.objects.all()
    serializer_class = PropietarioSerializer


def _ejecutar_envio_en_background(lote_id, data, files):
    """
    Esta función contiene la lógica de envío y se ejecutará en un hilo separado.
    """
    lote = LoteDeEnvio.objects.get(id=lote_id)
    lote.estado = "PROCESANDO"
    lote.save()

    def log(tipo, casa, mensaje):
        LogMensaje.objects.create(lote=lote, tipo=tipo, casa=str(casa), mensaje=mensaje)

    try:
        service = get_gmail_service()

        asunto = data.get("asunto", "Gastos Comunes del Mes")
        mensaje = data.get("mensaje", "Estimado(a) propietario(a),")
        casas_seleccionadas = data.getlist("casas_seleccionadas")
        casas_seleccionadas_int = [int(id_casa) for id_casa in casas_seleccionadas]
        propietarios = Propietario.objects.filter(
            numero_casa__in=casas_seleccionadas_int
        )

        for propietario in propietarios:
            log(
                "info",
                propietario.numero_casa,
                f"Procesando casa {propietario.numero_casa}...",
            )

            try:
                # (La lógica interna de creación y envío de cada correo se mantiene igual)
                # ...
                email_string = propietario.correo_electronico
                lista_correos = [
                    email.strip() for email in email_string.split(",") if email.strip()
                ]

                if not lista_correos:
                    log(
                        "error",
                        propietario.numero_casa,
                        "ERROR: No hay correos válidos.",
                    )
                    continue

                mime_message = MIMEMultipart()
                mime_message["to"] = ", ".join(lista_correos)
                mime_message["from"] = settings.EMAIL_OAUTH2_USER
                mime_message["subject"] = asunto

                body = f"Estimado(a) {propietario.nombre} {propietario.apellido},\n\n{mensaje}"
                mime_message.attach(MIMEText(body, "plain"))

                for f in files.getlist("archivos_comunes"):
                    f.seek(0)
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition", f'attachment; filename="{f.name}"'
                    )
                    mime_message.attach(part)

                nombre_archivo_esperado = f"{propietario.numero_casa}."
                archivo_individual_encontrado = next(
                    (
                        f
                        for f in files.getlist("archivos_individuales")
                        if f.name.startswith(nombre_archivo_esperado)
                    ),
                    None,
                )

                if archivo_individual_encontrado:
                    archivo_individual_encontrado.seek(0)
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(archivo_individual_encontrado.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition",
                        f'attachment; filename="{archivo_individual_encontrado.name}"',
                    )
                    mime_message.attach(part)
                    log(
                        "info",
                        propietario.numero_casa,
                        f"Adjunto individual '{archivo_individual_encontrado.name}' encontrado.",
                    )
                else:
                    log(
                        "error",
                        propietario.numero_casa,
                        "ERROR: No se encontró adjunto individual. Saltando.",
                    )
                    continue

                encoded_message = base64.urlsafe_b64encode(
                    mime_message.as_bytes()
                ).decode()
                create_message = {"raw": encoded_message}
                service.users().messages().send(
                    userId="me", body=create_message
                ).execute()

                destinatarios_str = ", ".join(lista_correos)
                log(
                    "success",
                    propietario.numero_casa,
                    f"ÉXITO: Correo enviado a {destinatarios_str}.",
                )

            except Exception as e:
                log("error", propietario.numero_casa, f"ERROR en envío: {str(e)}")

        lote.estado = "COMPLETADO"
        lote.save()

    except Exception as e:
        lote.estado = "ERROR"
        lote.save()
        log("error", "General", f"Error crítico en el lote: {str(e)}")


@api_view(["POST"])
def enviar_correos_gastos(request):
    """
    Inicia el proceso de envío de correos en segundo plano y responde inmediatamente.
    """
    casas_seleccionadas = request.data.getlist("casas_seleccionadas")
    if not casas_seleccionadas:
        return Response(
            {"error": "No se seleccionó ningún propietario."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # 1. Crear un nuevo lote de envío en la base de datos.
    nuevo_lote = LoteDeEnvio.objects.create()

    # 2. Iniciar la función de envío en un hilo separado.
    #    Le pasamos el ID del lote, los datos y los archivos.
    thread = threading.Thread(
        target=_ejecutar_envio_en_background,
        args=(nuevo_lote.id, request.data, request.FILES),
    )
    thread.start()

    # 3. Responder inmediatamente al frontend con el ID del lote.
    return Response({"lote_id": nuevo_lote.id}, status=status.HTTP_202_ACCEPTED)


@api_view(["GET"])
def obtener_estado_lote(request, lote_id):
    """
    Endpoint para que el frontend consulte el estado de un lote de envío.
    """
    try:
        lote = LoteDeEnvio.objects.get(id=lote_id)
        serializer = LoteDeEnvioSerializer(lote)
        return Response(serializer.data)
    except LoteDeEnvio.DoesNotExist:
        return Response(
            {"error": "Lote no encontrado"}, status=status.HTTP_404_NOT_FOUND
        )


def get_gmail_service():
    """Crea y retorna un servicio de la API de Gmail autenticado (sin cambios)."""
    creds = Credentials.from_authorized_user_info(
        info={
            "client_id": settings.EMAIL_OAUTH2_CLIENT_ID,
            "client_secret": settings.EMAIL_OAUTH2_CLIENT_SECRET,
            "refresh_token": settings.EMAIL_OAUTH2_REFRESH_TOKEN,
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    )
    service = build("gmail", "v1", credentials=creds)
    return service
