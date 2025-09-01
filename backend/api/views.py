from django.shortcuts import render

# ==============================================================================
# api/views.py (ACTUALIZADO)
# ==============================================================================
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.utils import formataddr
from email import encoders

from django.conf import settings
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response

# Imports de Google API
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .models import Propietario
from .serializers import PropietarioSerializer


class PropietarioViewSet(viewsets.ModelViewSet):
    queryset = Propietario.objects.all()
    serializer_class = PropietarioSerializer


def get_gmail_service():
    """Crea y retorna un servicio de la API de Gmail autenticado."""
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


@api_view(["POST"])
def enviar_correos_gastos(request):
    """
    API endpoint para enviar correos usando la API de Gmail con OAuth2.
    """
    log_envio = []

    try:
        service = get_gmail_service()

        asunto = request.data.get("asunto", "Gastos Comunes del Mes")
        mensaje = request.data.get("mensaje", "Estimado(a) propietario(a),")
        archivos_comunes = request.FILES.getlist("archivos_comunes")
        archivos_individuales = request.FILES.getlist("archivos_individuales")
        casas_seleccionadas = request.data.getlist("casas_seleccionadas")

        if not casas_seleccionadas:
            return Response(
                {"error": "No se seleccionó ningún propietario."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        casas_seleccionadas_int = [int(id_casa) for id_casa in casas_seleccionadas]
        propietarios = Propietario.objects.filter(
            numero_casa__in=casas_seleccionadas_int
        )

        for propietario in propietarios:
            log_envio.append(
                {
                    "tipo": "info",
                    "casa": propietario.numero_casa,
                    "mensaje": f"Procesando casa {propietario.numero_casa}...",
                }
            )

            try:
                email_string = propietario.correo_electronico
                lista_correos = [
                    email.strip() for email in email_string.split(",") if email.strip()
                ]

                if not lista_correos:
                    log_envio.append(
                        {
                            "tipo": "error",
                            "casa": propietario.numero_casa,
                            "mensaje": f"ERROR: No hay correos válidos.",
                        }
                    )
                    continue

                # Crear el cuerpo del mensaje en formato MIME
                mime_message = MIMEMultipart()
                mime_message["to"] = ", ".join(lista_correos)
                nombre_remitente = "Alejandra Pangue"
                mime_message["From"] = formataddr(
                    (nombre_remitente, settings.EMAIL_OAUTH2_USER)
                )
                # mime_message["from"] = settings.EMAIL_OAUTH2_USER
                mime_message["subject"] = asunto

                body = f"Estimado(a) {propietario.nombre} {propietario.apellido},\n\n{mensaje}"
                mime_message.attach(MIMEText(body, "plain"))

                # Adjuntar archivos comunes
                for f in archivos_comunes:
                    f.seek(0)
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition", f'attachment; filename="{f.name}"'
                    )
                    mime_message.attach(part)

                # Adjuntar archivo individual
                nombre_archivo_esperado = f"{propietario.numero_casa}."
                archivo_individual_encontrado = next(
                    (
                        f
                        for f in archivos_individuales
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
                    log_envio.append(
                        {
                            "tipo": "info",
                            "casa": propietario.numero_casa,
                            "mensaje": f"Adjunto individual '{archivo_individual_encontrado.name}' encontrado.",
                        }
                    )
                else:
                    log_envio.append(
                        {
                            "tipo": "error",
                            "casa": propietario.numero_casa,
                            "mensaje": f"ERROR: No se encontró adjunto individual. Saltando.",
                        }
                    )
                    continue

                # Codificar el mensaje y enviarlo
                encoded_message = base64.urlsafe_b64encode(
                    mime_message.as_bytes()
                ).decode()
                create_message = {"raw": encoded_message}

                service.users().messages().send(
                    userId="me", body=create_message
                ).execute()

                destinatarios_str = ", ".join(lista_correos)
                log_envio.append(
                    {
                        "tipo": "success",
                        "casa": propietario.numero_casa,
                        "mensaje": f"ÉXITO: Correo enviado a {destinatarios_str}.",
                    }
                )

            except HttpError as error:
                log_envio.append(
                    {
                        "tipo": "error",
                        "casa": propietario.numero_casa,
                        "mensaje": f"ERROR en API de Gmail: {error}",
                    }
                )
            except Exception as e:
                log_envio.append(
                    {
                        "tipo": "error",
                        "casa": propietario.numero_casa,
                        "mensaje": f"ERROR en envío: {str(e)}",
                    }
                )

        return Response({"log": log_envio}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {"error": f"Error general en el proceso: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
