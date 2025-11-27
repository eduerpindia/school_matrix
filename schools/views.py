from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import School
from .serializers import SchoolSerializer

class SchoolListAPIView(APIView):
    def get(self, request):
        schools = School.objects.filter(is_active=True)
        serializer = SchoolSerializer(schools, many=True)
        return Response(serializer.data)

class SchoolCreateAPIView(APIView):
    def post(self, request):
        serializer = SchoolSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)