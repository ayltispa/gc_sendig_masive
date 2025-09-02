from django.db import models
import uuid


# Create your models here.
class Propietario(models.Model):
    numero_casa = models.IntegerField(unique=True, primary_key=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    correo_electronico = models.TextField()

    class Meta:
        ordering = ["numero_casa"]

    def __str__(self):
        return f"Casa {self.numero_casa}:   {self.nombre} {self.apellido} |   {self.correo_electronico}"


# --- INICIO DE NUEVOS MODELOS ---
class LoteDeEnvio(models.Model):
    ESTADOS = [
        ("PENDIENTE", "Pendiente"),
        ("PROCESANDO", "Procesando"),
        ("COMPLETADO", "Completado"),
        ("ERROR", "Error"),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default="PENDIENTE")

    def __str__(self):
        return f"Lote {self.id} - {self.estado}"


class LogMensaje(models.Model):
    TIPOS = [
        ("info", "Info"),
        ("success", "Success"),
        ("error", "Error"),
    ]
    lote = models.ForeignKey(LoteDeEnvio, related_name="logs", on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    tipo = models.CharField(max_length=10, choices=TIPOS)
    casa = models.CharField(max_length=20, null=True, blank=True)
    mensaje = models.TextField()

    class Meta:
        ordering = ["timestamp"]


# --- FIN DE NUEVOS MODELOS ---
