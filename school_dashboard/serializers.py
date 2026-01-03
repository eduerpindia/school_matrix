from rest_framework import serializers
from schools.models import *

class SchoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = School
        fields = [
            'id', 'name', 'school_code', 'email', 'phone', 
            'address', 'city', 'state', 'country', 'postal_code',
            'establishment_date', 'board', 'is_active', 'is_verified'
        ]
        read_only_fields = ['id', 'is_verified']
        
class SchoolSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolSession
        fields = ['id', 'name', 'start_date', 'end_date', 'is_current', 'created_at']
        read_only_fields = ['id', 'created_at']