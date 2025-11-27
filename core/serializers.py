# core/serializers.py
from rest_framework import serializers
from .models import AcademicYear

class AcademicYearSerializer(serializers.ModelSerializer):
    is_editable = serializers.SerializerMethodField()
    
    class Meta:
        model = AcademicYear
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
    
    def get_is_editable(self, obj):
        # Cannot edit current academic year if it has related data
        if obj.is_current:
            return False
        return True