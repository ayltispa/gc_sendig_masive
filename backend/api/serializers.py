# ==============================================================================
# api/serializers.py
# ==============================================================================
from rest_framework import serializers
from .models import Propietario

class PropietarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Propietario
        fields = '__all__'