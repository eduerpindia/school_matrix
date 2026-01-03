from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from schools.models import School
from .serializers import *



from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db import connection
from django.core.management import call_command
from django.utils import timezone
from schools.models import School, Domain
from django.contrib.auth import get_user_model
import re
from django_tenants.utils import schema_context


class AdminDashboardDetails(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            user = request.user
            school_id = user.school_id
            school_code = user.school_code
            
            if not school_id or not school_code:
                return Response({
                    'success': False,
                    'message': 'User is not associated with any school'
                }, status=status.HTTP_400_BAD_REQUEST)
            with schema_context('public'):
                try:
                    school = School.objects.get(
                        id=school_id,
                        school_code=school_code,
                        is_active=True
                    )
                    
                    school_details = {
                        'school_id': school.id,
                        'school_code': school.school_code,
                        'name': school.name,
                        'email': school.email,
                        'phone': school.phone,
                        'address': school.address,
                        'city': school.city,
                        'state': school.state,
                        'country': school.country,
                        'postal_code': school.postal_code,
                        'establishment_date': school.establishment_date,
                        'board': school.board,
                        'subscription_type': school.subscription_type,
                        'subscription_start': school.subscription_start,
                        'subscription_end': school.subscription_end,
                        'student_capacity': school.student_capacity,
                        'academic_year_start_month': school.academic_year_start_month,
                        'is_active': school.is_active,
                        'is_verified': school.is_verified
                    }
                except School.DoesNotExist:
                    return Response({
                        'success': False,
                        'message': 'School not found or is inactive'
                    }, status=status.HTTP_404_NOT_FOUND)
            
            # User details
            user_details = {
                'user_id': user.id,
                'email': user.email,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'user_type': user.user_type,
                'phone': user.phone,
                'date_of_birth': user.date_of_birth,
                'gender': user.gender,
                'address': user.address,
                'city': user.city,
                'state': user.state,
                'is_verified': user.is_verified,
                'profile_picture': request.build_absolute_uri(user.profile_picture.url) if user.profile_picture else None
            }
            
            return Response({
                'success': True,
                'message': 'School and user details fetched successfully',
                'school': school_details,
                'user': user_details
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error fetching details: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
class CurrentSessionView(APIView):
    """Get current active school session"""
    
    def get(self, request):
        try:
            # Current session fetch karo
            session = SchoolSession.objects.filter(is_current=True).first()
            
            if not session:
                return Response(
                    {'error': 'No active session found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            serializer = SchoolSessionSerializer(session)
            return Response({
                'success': True,
                'message': 'School current session fetched successfully',
                
                'data': serializer.data
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )