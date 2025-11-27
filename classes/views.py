from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Class, Section, Subject, ClassSubject, TimeTable
from .serializers import (
    ClassSerializer, SectionSerializer, SubjectSerializer, 
    ClassSubjectSerializer, TimeTableSerializer
)
from core.custom_permission import ClassesModulePermission

# Class Views
class ClassListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated, ClassesModulePermission]
    
    def get(self, request):
        classes = Class.objects.filter(is_active=True)
        serializer = ClassSerializer(classes, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = ClassSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ClassDetailAPIView(APIView):
    permission_classes = [IsAuthenticated, ClassesModulePermission]
    
    def get_object(self, pk):
        return get_object_or_404(Class, pk=pk, is_active=True)
    
    def get(self, request, pk):
        class_obj = self.get_object(pk)
        serializer = ClassSerializer(class_obj)
        return Response(serializer.data)
    
    def put(self, request, pk):
        class_obj = self.get_object(pk)
        serializer = ClassSerializer(class_obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        class_obj = self.get_object(pk)
        class_obj.is_active = False
        class_obj.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

# Section Views
class SectionListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated, ClassesModulePermission]
    
    def get(self, request):
        class_id = request.query_params.get('class_id')
        if class_id:
            sections = Section.objects.filter(class_name_id=class_id, is_active=True)
        else:
            sections = Section.objects.filter(is_active=True)
        serializer = SectionSerializer(sections, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = SectionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SectionDetailAPIView(APIView):
    permission_classes = [IsAuthenticated, ClassesModulePermission]
    
    def get_object(self, pk):
        return get_object_or_404(Section, pk=pk, is_active=True)
    
    def get(self, request, pk):
        section = self.get_object(pk)
        serializer = SectionSerializer(section)
        return Response(serializer.data)
    
    def put(self, request, pk):
        section = self.get_object(pk)
        serializer = SectionSerializer(section, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        section = self.get_object(pk)
        section.is_active = False
        section.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

# Subject Views
class SubjectListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated, ClassesModulePermission]
    
    def get(self, request):
        subjects = Subject.objects.filter(is_active=True)
        serializer = SubjectSerializer(subjects, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = SubjectSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SubjectDetailAPIView(APIView):
    permission_classes = [IsAuthenticated, ClassesModulePermission]
    
    def get_object(self, pk):
        return get_object_or_404(Subject, pk=pk, is_active=True)
    
    def get(self, request, pk):
        subject = self.get_object(pk)
        serializer = SubjectSerializer(subject)
        return Response(serializer.data)
    
    def put(self, request, pk):
        subject = self.get_object(pk)
        serializer = SubjectSerializer(subject, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        subject = self.get_object(pk)
        subject.is_active = False
        subject.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

# ClassSubject Views
class ClassSubjectListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated, ClassesModulePermission]
    
    def get(self, request):
        class_id = request.query_params.get('class_id')
        academic_year = request.query_params.get('academic_year')
        
        queryset = ClassSubject.objects.all()
        
        if class_id:
            queryset = queryset.filter(class_name_id=class_id)
        if academic_year:
            queryset = queryset.filter(academic_year=academic_year)
            
        serializer = ClassSubjectSerializer(queryset, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = ClassSubjectSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ClassSubjectDetailAPIView(APIView):
    permission_classes = [IsAuthenticated, ClassesModulePermission]
    
    def get_object(self, pk):
        return get_object_or_404(ClassSubject, pk=pk)
    
    def get(self, request, pk):
        class_subject = self.get_object(pk)
        serializer = ClassSubjectSerializer(class_subject)
        return Response(serializer.data)
    
    def put(self, request, pk):
        class_subject = self.get_object(pk)
        serializer = ClassSubjectSerializer(class_subject, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        class_subject = self.get_object(pk)
        class_subject.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

# TimeTable Views
class TimeTableListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated, ClassesModulePermission]
    
    def get(self, request):
        class_id = request.query_params.get('class_id')
        section_id = request.query_params.get('section_id')
        day = request.query_params.get('day')
        academic_year = request.query_params.get('academic_year')
        
        queryset = TimeTable.objects.filter(is_active=True)
        
        if class_id:
            queryset = queryset.filter(class_name_id=class_id)
        if section_id:
            queryset = queryset.filter(section_id=section_id)
        if day:
            queryset = queryset.filter(day=day)
        if academic_year:
            queryset = queryset.filter(academic_year=academic_year)
            
        serializer = TimeTableSerializer(queryset, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = TimeTableSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TimeTableDetailAPIView(APIView):
    permission_classes = [IsAuthenticated, ClassesModulePermission]
    
    def get_object(self, pk):
        return get_object_or_404(TimeTable, pk=pk, is_active=True)
    
    def get(self, request, pk):
        timetable = self.get_object(pk)
        serializer = TimeTableSerializer(timetable)
        return Response(serializer.data)
    
    def put(self, request, pk):
        timetable = self.get_object(pk)
        serializer = TimeTableSerializer(timetable, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        timetable = self.get_object(pk)
        timetable.is_active = False
        timetable.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

class ClassWithSectionsAPIView(APIView):
    permission_classes = [IsAuthenticated, ClassesModulePermission]
    
    def get(self, request):
        classes = Class.objects.filter(is_active=True)
        result = []
        
        for class_obj in classes:
            class_data = ClassSerializer(class_obj).data
            sections = Section.objects.filter(class_name=class_obj, is_active=True)
            class_data['sections'] = SectionSerializer(sections, many=True).data
            result.append(class_data)
        
        return Response(result)