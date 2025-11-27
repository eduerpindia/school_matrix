from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
# Create your views here.
class LoginView(APIView):
    def post(self, request):
        # Login logic here
        return Response({'message': 'Login successful'}, status=status.HTTP_200_OK)