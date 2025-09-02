from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PropietarioViewSet, enviar_correos_gastos, obtener_estado_lote

router = DefaultRouter()
router.register(r"propietarios", PropietarioViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("enviar-gastos/", enviar_correos_gastos, name="enviar_gastos"),
    # --- NUEVA RUTA PARA CONSULTAR ESTADO ---
    path("estado-lote/<uuid:lote_id>/", obtener_estado_lote, name="estado_lote"),
]
