# ==============================================================================
# api/serializers.py
# ==============================================================================
from rest_framework import serializers
from .models import Propietario, LoteDeEnvio, LogMensaje


class PropietarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Propietario
        fields = "__all__"


# --- INICIO DE NUEVOS SERIALIZERS ---
class LogMensajeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LogMensaje
        fields = ["timestamp", "tipo", "casa", "mensaje"]


class LoteDeEnvioSerializer(serializers.ModelSerializer):
    logs = LogMensajeSerializer(many=True, read_only=True)

    class Meta:
        model = LoteDeEnvio
        fields = ["id", "fecha_creacion", "estado", "logs"]


# --- FIN DE NUEVOS SERIALIZERS ---
