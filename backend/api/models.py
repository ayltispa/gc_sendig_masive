from django.db import models


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
