from rest_framework import serializers
from .models import School

class SchoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = School
        fields = [
            'id', 'name', 'school_code', 'email', 'phone', 
            'address', 'city', 'state', 'country', 'postal_code',
            'establishment_date', 'board', 'is_active', 'is_verified'
        ]
        read_only_fields = ['id', 'is_verified']