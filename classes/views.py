# classes/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from django.db.models import Sum

from .models import Class, Section, Subject, ClassSubject, TimeTable
from schools.models import SchoolSession
from .serializers import (
    ClassSerializer, SectionSerializer, SubjectSerializer,
    ClassSubjectSerializer, TimeTableSerializer
)


# ==================== CLASS VIEWS ====================
class ClassListAPIView(APIView):
    """GET: Returns list of all classes"""
    
    def get(self, request):
        is_active = request.query_params.get('is_active')
        session_id = request.query_params.get('session_id')
        
        classes = Class.objects.select_related('session', 'class_teacher').all()
        
        if is_active is not None:
            classes = classes.filter(is_active=is_active.lower() == 'true')
        
        # ✅ Filter by session
        if session_id:
            classes = classes.filter(session_id=session_id)
        else:
            # Default: current session
            current_session = SchoolSession.objects.filter(is_current=True).first()
            if current_session:
                classes = classes.filter(session=current_session)
            
        serializer = ClassSerializer(classes, many=True)
        return Response({
            'success': True,
            'count': classes.count(),
            'data': serializer.data
        }, status=status.HTTP_200_OK)


class ClassCreateAPIView(APIView):
    """POST: Create a new class"""
    
    def post(self, request):
        # ✅ Auto-assign current session if not provided
        if 'session' not in request.data:
            current_session = SchoolSession.objects.filter(is_current=True).first()
            if not current_session:
                return Response(
                    {"error": "No active session found. Please create a session first."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            request.data['session'] = current_session.id
        
        serializer = ClassSerializer(data=request.data)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response({
                    'success': True,
                    'message': 'Class created successfully',
                    'data': serializer.data
                }, status=status.HTTP_201_CREATED)
            except DjangoValidationError as e:
                return Response(
                    {"error": "Validation error", "details": e.message_dict if hasattr(e, 'message_dict') else str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
            except IntegrityError as e:
                return Response(
                    {"error": "Class already exists for this session", "details": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ClassRetrieveAPIView(APIView):
    """GET: Retrieve a single class by ID"""
    
    def get(self, request, pk):
        try:
            class_obj = Class.objects.select_related('session', 'class_teacher').get(pk=pk)
        except Class.DoesNotExist:
            return Response(
                {"error": "Class not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = ClassSerializer(class_obj)
        
        # ✅ Additional metadata
        sections = class_obj.sections.filter(is_active=True)
        total_section_capacity = sections.aggregate(total=Sum('capacity'))['total'] or 0
        
        return Response({
            'success': True,
            'data': serializer.data,
            'meta': {
                'sections_count': sections.count(),
                'total_section_capacity': total_section_capacity,
                'remaining_capacity': class_obj.capacity - total_section_capacity
            }
        }, status=status.HTTP_200_OK)


class ClassUpdateAPIView(APIView):
    """PUT: Update a class completely"""
    
    def put(self, request, pk):
        try:
            class_obj = Class.objects.get(pk=pk)
        except Class.DoesNotExist:
            return Response(
                {"error": "Class not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = ClassSerializer(class_obj, data=request.data, partial=False)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response({
                    'success': True,
                    'message': 'Class updated successfully',
                    'data': serializer.data
                }, status=status.HTTP_200_OK)
            except DjangoValidationError as e:
                return Response(
                    {"error": "Validation error", "details": e.message_dict if hasattr(e, 'message_dict') else str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ClassDeleteAPIView(APIView):
    """DELETE: Delete a class"""
    
    def delete(self, request, pk):
        try:
            class_obj = Class.objects.get(pk=pk)
        except Class.DoesNotExist:
            return Response(
                {"error": "Class not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # ✅ Check dependencies
        sections_count = class_obj.sections.count()
        subjects_count = class_obj.class_subjects.count()
        
        if sections_count > 0 or subjects_count > 0:
            return Response({
                "error": "Cannot delete class with existing sections or subject assignments",
                "details": {
                    "sections": sections_count,
                    "subjects": subjects_count
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        class_obj.delete()
        return Response(
            {"success": True, "message": "Class deleted successfully"},
            status=status.HTTP_200_OK
        )


# ==================== SECTION VIEWS ====================
class SectionListAPIView(APIView):
    """GET: Returns list of all sections"""
    
    def get(self, request):
        class_id = request.query_params.get('class_id')
        is_active = request.query_params.get('is_active')
        
        sections = Section.objects.select_related('class_obj', 'section_incharge').all()
        
        if class_id:
            sections = sections.filter(class_obj_id=class_id)
        
        if is_active is not None:
            sections = sections.filter(is_active=is_active.lower() == 'true')
            
        serializer = SectionSerializer(sections, many=True)
        return Response({
            'success': True,
            'count': sections.count(),
            'data': serializer.data
        }, status=status.HTTP_200_OK)


class SectionCreateAPIView(APIView):
    """POST: Create a new section"""
    
    def post(self, request):
        serializer = SectionSerializer(data=request.data)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response({
                    'success': True,
                    'message': 'Section created successfully',
                    'data': serializer.data
                }, status=status.HTTP_201_CREATED)
            except DjangoValidationError as e:
                return Response(
                    {"error": "Validation error", "details": e.message_dict if hasattr(e, 'message_dict') else str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
            except IntegrityError as e:
                return Response(
                    {"error": "Section already exists for this class", "details": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SectionRetrieveAPIView(APIView):
    """GET: Retrieve a single section by ID"""
    
    def get(self, request, pk):
        try:
            section = Section.objects.select_related('class_obj', 'section_incharge').get(pk=pk)
        except Section.DoesNotExist:
            return Response(
                {"error": "Section not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = SectionSerializer(section)
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)


class SectionUpdateAPIView(APIView):
    """PUT: Update a section completely"""
    
    def put(self, request, pk):
        try:
            section = Section.objects.get(pk=pk)
        except Section.DoesNotExist:
            return Response(
                {"error": "Section not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = SectionSerializer(section, data=request.data, partial=False)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response({
                    'success': True,
                    'message': 'Section updated successfully',
                    'data': serializer.data
                }, status=status.HTTP_200_OK)
            except DjangoValidationError as e:
                return Response(
                    {"error": "Validation error", "details": e.message_dict if hasattr(e, 'message_dict') else str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SectionDeleteAPIView(APIView):
    """DELETE: Delete a section"""
    
    def delete(self, request, pk):
        try:
            section = Section.objects.get(pk=pk)
        except Section.DoesNotExist:
            return Response(
                {"error": "Section not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # ✅ Check dependencies
        subjects_count = section.section_subjects.count()
        timetable_count = section.timetables.count()
        
        if subjects_count > 0 or timetable_count > 0:
            return Response({
                "error": "Cannot delete section with existing subject assignments or timetable entries",
                "details": {
                    "subjects": subjects_count,
                    "timetable": timetable_count
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        section.delete()
        return Response(
            {"success": True, "message": "Section deleted successfully"},
            status=status.HTTP_200_OK
        )


# ==================== SUBJECT VIEWS ====================
class SubjectListAPIView(APIView):
    """GET: Returns list of all subjects"""
    
    def get(self, request):
        is_active = request.query_params.get('is_active')
        is_core = request.query_params.get('is_core')
        
        subjects = Subject.objects.all()
        
        if is_active is not None:
            subjects = subjects.filter(is_active=is_active.lower() == 'true')
        
        # ✅ Filter by core/optional
        if is_core is not None:
            subjects = subjects.filter(is_core=is_core.lower() == 'true')
            
        serializer = SubjectSerializer(subjects, many=True)
        return Response({
            'success': True,
            'count': subjects.count(),
            'data': serializer.data
        }, status=status.HTTP_200_OK)


class SubjectCreateAPIView(APIView):
    """POST: Create a new subject"""
    
    def post(self, request):
        serializer = SubjectSerializer(data=request.data)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response({
                    'success': True,
                    'message': 'Subject created successfully',
                    'data': serializer.data
                }, status=status.HTTP_201_CREATED)
            except IntegrityError as e:
                return Response(
                    {"error": "Subject code already exists", "details": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SubjectRetrieveAPIView(APIView):
    """GET: Retrieve a single subject by ID"""
    
    def get(self, request, pk):
        try:
            subject = Subject.objects.get(pk=pk)
        except Subject.DoesNotExist:
            return Response(
                {"error": "Subject not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = SubjectSerializer(subject)
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)


class SubjectUpdateAPIView(APIView):
    """PUT: Update a subject completely"""
    
    def put(self, request, pk):
        try:
            subject = Subject.objects.get(pk=pk)
        except Subject.DoesNotExist:
            return Response(
                {"error": "Subject not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = SubjectSerializer(subject, data=request.data, partial=False)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response({
                    'success': True,
                    'message': 'Subject updated successfully',
                    'data': serializer.data
                }, status=status.HTTP_200_OK)
            except IntegrityError as e:
                return Response(
                    {"error": "Subject code already exists", "details": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SubjectDeleteAPIView(APIView):
    """DELETE: Delete a subject"""
    
    def delete(self, request, pk):
        try:
            subject = Subject.objects.get(pk=pk)
        except Subject.DoesNotExist:
            return Response(
                {"error": "Subject not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # ✅ Check if assigned
        assignments_count = ClassSubject.objects.filter(subject=subject).count()
        if assignments_count > 0:
            return Response({
                "error": f"Cannot delete subject. It is assigned to {assignments_count} class(es).",
                "suggestion": "Mark as inactive instead or remove all assignments first."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        subject.delete()
        return Response(
            {"success": True, "message": "Subject deleted successfully"},
            status=status.HTTP_200_OK
        )


# ==================== CLASS SUBJECT VIEWS ====================
class ClassSubjectListAPIView(APIView):
    """GET: Returns list of all class-subject mappings"""
    
    def get(self, request):
        class_id = request.query_params.get('class_id')
        section_id = request.query_params.get('section_id')
        session_id = request.query_params.get('session_id')
        teacher_id = request.query_params.get('teacher_id')
        
        class_subjects = ClassSubject.objects.select_related(
            'class_obj', 'section', 'subject', 'teacher', 'session'
        ).all()
        
        if class_id:
            class_subjects = class_subjects.filter(class_obj_id=class_id)
        if section_id:
            class_subjects = class_subjects.filter(section_id=section_id)
        
        # ✅ session_id filter
        if session_id:
            class_subjects = class_subjects.filter(session_id=session_id)
        else:
            current_session = SchoolSession.objects.filter(is_current=True).first()
            if current_session:
                class_subjects = class_subjects.filter(session=current_session)
        
        if teacher_id:
            class_subjects = class_subjects.filter(teacher_id=teacher_id)
            
        serializer = ClassSubjectSerializer(class_subjects, many=True)
        return Response({
            'success': True,
            'count': class_subjects.count(),
            'data': serializer.data
        }, status=status.HTTP_200_OK)


class ClassSubjectCreateAPIView(APIView):
    """POST: Create a new class-subject mapping"""
    
    def post(self, request):
        # ✅ Auto-assign session from class
        if 'class_obj' in request.data and 'session' not in request.data:
            try:
                class_obj = Class.objects.get(id=request.data['class_obj'])
                request.data['session'] = class_obj.session.id
            except Class.DoesNotExist:
                pass
        
        serializer = ClassSubjectSerializer(data=request.data)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response({
                    'success': True,
                    'message': 'Subject assigned successfully',
                    'data': serializer.data
                }, status=status.HTTP_201_CREATED)
            except DjangoValidationError as e:
                return Response(
                    {"error": "Validation error", "details": e.message_dict if hasattr(e, 'message_dict') else str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
            except IntegrityError as e:
                return Response(
                    {"error": "Subject already assigned to this class/section", "details": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ClassSubjectRetrieveAPIView(APIView):
    """GET: Retrieve a single class-subject mapping by ID"""
    
    def get(self, request, pk):
        try:
            class_subject = ClassSubject.objects.select_related(
                'class_obj', 'section', 'subject', 'teacher', 'session'
            ).get(pk=pk)
        except ClassSubject.DoesNotExist:
            return Response(
                {"error": "Class Subject mapping not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = ClassSubjectSerializer(class_subject)
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)


class ClassSubjectUpdateAPIView(APIView):
    """PUT: Update a class-subject mapping completely"""
    
    def put(self, request, pk):
        try:
            class_subject = ClassSubject.objects.get(pk=pk)
        except ClassSubject.DoesNotExist:
            return Response(
                {"error": "Class Subject mapping not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = ClassSubjectSerializer(class_subject, data=request.data, partial=False)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response({
                    'success': True,
                    'message': 'Subject assignment updated successfully',
                    'data': serializer.data
                }, status=status.HTTP_200_OK)
            except DjangoValidationError as e:
                return Response(
                    {"error": "Validation error", "details": e.message_dict if hasattr(e, 'message_dict') else str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ClassSubjectDeleteAPIView(APIView):
    """DELETE: Delete a class-subject mapping"""
    
    def delete(self, request, pk):
        try:
            class_subject = ClassSubject.objects.get(pk=pk)
        except ClassSubject.DoesNotExist:
            return Response(
                {"error": "Class Subject mapping not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        class_subject.delete()
        return Response(
            {"success": True, "message": "Subject assignment deleted successfully"},
            status=status.HTTP_200_OK
        )


# ==================== TIMETABLE VIEWS ====================
class TimeTableListAPIView(APIView):
    """GET: Returns list of all timetable entries"""
    
    def get(self, request):
        class_id = request.query_params.get('class_id')
        section_id = request.query_params.get('section_id')
        day = request.query_params.get('day')
        session_id = request.query_params.get('session_id')
        teacher_id = request.query_params.get('teacher_id')
        
        timetable = TimeTable.objects.select_related(
            'class_obj', 'section', 'subject', 'teacher', 'session'
        ).all()
        
        if class_id:
            timetable = timetable.filter(class_obj_id=class_id)
        if section_id:
            timetable = timetable.filter(section_id=section_id)
        if day:
            timetable = timetable.filter(day=day.upper())
        
        # ✅ session_id filter
        if session_id:
            timetable = timetable.filter(session_id=session_id)
        else:
            current_session = SchoolSession.objects.filter(is_current=True).first()
            if current_session:
                timetable = timetable.filter(session=current_session)
        
        if teacher_id:
            timetable = timetable.filter(teacher_id=teacher_id)
            
        serializer = TimeTableSerializer(timetable, many=True)
        return Response({
            'success': True,
            'count': timetable.count(),
            'data': serializer.data
        }, status=status.HTTP_200_OK)


class TimeTableCreateAPIView(APIView):
    """POST: Create a new timetable entry"""
    
    def post(self, request):
        # ✅ Auto-assign session from class
        if 'class_obj' in request.data and 'session' not in request.data:
            try:
                class_obj = Class.objects.get(id=request.data['class_obj'])
                request.data['session'] = class_obj.session.id
            except Class.DoesNotExist:
                pass
        
        serializer = TimeTableSerializer(data=request.data)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response({
                    'success': True,
                    'message': 'Timetable entry created successfully',
                    'data': serializer.data
                }, status=status.HTTP_201_CREATED)
            except DjangoValidationError as e:
                return Response(
                    {"error": "Validation error", "details": e.message_dict if hasattr(e, 'message_dict') else str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
            except IntegrityError as e:
                return Response(
                    {"error": "Timetable slot already occupied", "details": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TimeTableRetrieveAPIView(APIView):
    """GET: Retrieve a single timetable entry by ID"""
    
    def get(self, request, pk):
        try:
            timetable = TimeTable.objects.select_related(
                'class_obj', 'section', 'subject', 'teacher', 'session'
            ).get(pk=pk)
        except TimeTable.DoesNotExist:
            return Response(
                {"error": "Timetable entry not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = TimeTableSerializer(timetable)
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)


class TimeTableUpdateAPIView(APIView):
    """PUT: Update a timetable entry completely"""
    
    def put(self, request, pk):
        try:
            timetable = TimeTable.objects.get(pk=pk)
        except TimeTable.DoesNotExist:
            return Response(
                {"error": "Timetable entry not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = TimeTableSerializer(timetable, data=request.data, partial=False)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response({
                    'success': True,
                    'message': 'Timetable entry updated successfully',
                    'data': serializer.data
                }, status=status.HTTP_200_OK)
            except DjangoValidationError as e:
                return Response(
                    {"error": "Validation error", "details": e.message_dict if hasattr(e, 'message_dict') else str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TimeTableDeleteAPIView(APIView):
    """DELETE: Delete a timetable entry"""
    
    def delete(self, request, pk):
        try:
            timetable = TimeTable.objects.get(pk=pk)
        except TimeTable.DoesNotExist:
            return Response(
                {"error": "Timetable entry not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        timetable.delete()
        return Response(
            {"success": True, "message": "Timetable entry deleted successfully"},
            status=status.HTTP_200_OK
        )


# ==================== SPECIAL VIEWS ====================
class ClassSectionCheckAPIView(APIView):
    """GET: Check sections for a specific class"""
    
    def get(self, request, class_id):
        try:
            class_obj = Class.objects.select_related('session').get(id=class_id)
        except Class.DoesNotExist:
            return Response(
                {"error": "Class not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        sections = Section.objects.filter(class_obj=class_obj, is_active=True)
        serializer = SectionSerializer(sections, many=True)
        
        return Response({
            "success": True,
            "class": ClassSerializer(class_obj).data,
            "has_sections": sections.exists(),
            "sections_count": sections.count(),
            "sections": serializer.data
        }, status=status.HTTP_200_OK)


class BulkAssignSubjectsAPIView(APIView):
    """POST: Bulk assign subjects to a class/section"""
    
    def post(self, request):
        class_id = request.data.get('class_id')
        section_id = request.data.get('section_id')
        subject_ids = request.data.get('subject_ids', [])
        teacher_id = request.data.get('teacher_id')
        periods_per_week = request.data.get('periods_per_week', 5)

        if not class_id or not subject_ids:
            return Response(
                {"error": "class_id and subject_ids are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            class_obj = Class.objects.select_related('session').get(id=class_id)
        except Class.DoesNotExist:
            return Response(
                {"error": "Class not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # ✅ Auto-get session from class
        session = class_obj.session

        section_obj = None
        if section_id:
            try:
                section_obj = Section.objects.get(id=section_id)
                if section_obj.class_obj_id != class_obj.id:
                    return Response(
                        {"error": "Section does not belong to this class"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                if not section_obj.is_active:
                    return Response(
                        {"error": "Section is not active"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except Section.DoesNotExist:
                return Response(
                    {"error": "Section not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

        subjects = Subject.objects.filter(id__in=subject_ids, is_active=True)
        if subjects.count() != len(subject_ids):
            return Response(
                {"error": "One or more subjects not found or inactive"},
                status=status.HTTP_400_BAD_REQUEST
            )

        created_objects = []
        skipped_assignments = []
        validation_errors = []

        for subject in subjects:
            try:
                exists = ClassSubject.objects.filter(
                    class_obj=class_obj,
                    section=section_obj,
                    subject=subject,
                    session=session  # ✅ session check
                ).exists()
                
                if exists:
                    skipped_assignments.append({
                        'subject': subject.name,
                        'reason': 'Already assigned'
                    })
                    continue

                class_subject = ClassSubject(
                    class_obj=class_obj,
                    section=section_obj,
                    subject=subject,
                    teacher_id=teacher_id,
                    periods_per_week=periods_per_week,
                    session=session,  # ✅ session
                    is_optional=not subject.is_core
                )
                class_subject.save()
                created_objects.append(class_subject)

            except DjangoValidationError as e:
                validation_errors.append({
                    'subject': subject.name,
                    'errors': e.message_dict if hasattr(e, 'message_dict') else str(e)
                })
            except IntegrityError as e:
                validation_errors.append({
                    'subject': subject.name,
                    'errors': 'Database integrity error'
                })

        if validation_errors and not created_objects:
            return Response({
                "success": False,
                "error": "All assignments failed validation",
                "validation_errors": validation_errors
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "success": True,
            "message": f"{len(created_objects)} subject(s) assigned successfully",
            "created_count": len(created_objects),
            "skipped_count": len(skipped_assignments),
            "error_count": len(validation_errors),
            "skipped_assignments": skipped_assignments,
            "validation_errors": validation_errors,
            "assigned_subjects": ClassSubjectSerializer(created_objects, many=True).data
        }, status=status.HTTP_201_CREATED if created_objects else status.HTTP_200_OK)


class AssignedSubjectsAPIView(APIView):
    """GET: Returns all assigned subjects for a class/section"""
    
    def get(self, request):
        class_id = request.query_params.get('class_id')
        section_id = request.query_params.get('section_id')
        session_id = request.query_params.get('session_id')

        if not class_id:
            return Response(
                {"error": "class_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            class_obj = Class.objects.select_related('session').get(id=class_id)
        except Class.DoesNotExist:
            return Response(
                {"error": "Class not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        section_obj = None
        if section_id:
            try:
                section_obj = Section.objects.get(id=section_id)
                if section_obj.class_obj_id != class_obj.id:
                    return Response(
                        {"error": "Section does not belong to this class"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except Section.DoesNotExist:
                return Response(
                    {"error": "Section not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

        filters = {'class_obj_id': class_id}
        
        if section_id:
            filters['section_id'] = section_id
        
        # ✅ session filter
        if session_id:
            filters['session_id'] = session_id
        else:
            filters['session_id'] = class_obj.session.id

        assigned_subjects = ClassSubject.objects.filter(**filters).select_related(
            'class_obj', 'section', 'subject', 'teacher', 'session'
        )

        serializer = ClassSubjectSerializer(assigned_subjects, many=True)
        return Response({
            "success": True,
            "count": assigned_subjects.count(),
            "class": ClassSerializer(class_obj).data,
            "section": SectionSerializer(section_obj).data if section_obj else None,
            "assigned_subjects": serializer.data
        }, status=status.HTTP_200_OK)
