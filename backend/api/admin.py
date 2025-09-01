from django.contrib import admin

# Register your models here.
from .models import Propietario

#


class PropietarioAdmin(admin.ModelAdmin):
    list_display = ("numero_casa", "nombre", "apellido", "correo_electronico")
    search_fields = ("numero_casa", "nombre", "apellido", "correo_electronico")


admin.site.register(Propietario, PropietarioAdmin)
