"""
Core views - Public endpoints for landing page
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.db import connection


@api_view(['GET'])
@permission_classes([AllowAny])  # Không cần authentication
def public_stats(request):
    """
    GET /api/public/stats/
    
    Trả về số liệu thống kê công khai cho landing page.
    Không cần authentication.
    """
    with connection.cursor() as cursor:
        # Đếm số lớp học
        cursor.execute("SELECT COUNT(*) FROM classes")
        classes_count = cursor.fetchone()[0]
        
        # Đếm số học viên
        cursor.execute("SELECT COUNT(*) FROM students")
        students_count = cursor.fetchone()[0]
        
        # Đếm số giáo viên
        cursor.execute("SELECT COUNT(*) FROM teachers")
        teachers_count = cursor.fetchone()[0]
        
        # Đếm số khóa học
        cursor.execute("SELECT COUNT(*) FROM courses")
        courses_count = cursor.fetchone()[0]
    
    return Response({
        'classes': classes_count,
        'students': students_count,
        'teachers': teachers_count,
        'courses': courses_count,
        'satisfaction_rate': 98  # Fixed value
    })


@api_view(['GET'])
@permission_classes([AllowAny])  # Không cần authentication
def public_courses(request):
    """
    GET /api/public/courses/
    
    Trả về danh sách khóa học công khai cho landing page.
    Không cần authentication.
    """
    # Get limit from query params (default 6)
    limit = int(request.GET.get('limit', 6))
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                id,
                name,
                description,
                level,
                total_sessions,
                fee,
                min_entry_score
            FROM courses
            ORDER BY name ASC
            LIMIT %s
        """, [limit])
        
        columns = [col[0] for col in cursor.description]
        courses = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
    
    return Response({
        'count': len(courses),
        'results': courses
    })


@api_view(['GET'])
@permission_classes([AllowAny])  # Không cần authentication
def public_classes(request):
    """
    GET /api/public/classes/
    
    Trả về danh sách lớp học CÔNG KHAI (is_public=true) cho landing page.
    Không cần authentication.
    """
    limit = int(request.GET.get('limit', 10))
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                c.id,
                c.name,
                c.start_date,
                c.end_date,
                c.time_slot,
                c.weekday,
                c.limit_slot,
                c.status,
                co.name as course_name,
                ca.name as campus_name
            FROM classes c
            LEFT JOIN courses co ON c.course_id = co.id
            LEFT JOIN campuses ca ON c.campus_id = ca.id
            WHERE c.is_public = true
            ORDER BY c.start_date DESC
            LIMIT %s
        """, [limit])
        
        columns = [col[0] for col in cursor.description]
        classes = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
    
    return Response({
        'count': len(classes),
        'results': classes
    })


@api_view(['GET'])
@permission_classes([AllowAny])  # Không cần authentication
def public_campuses(request):
    """
    GET /api/public/campuses/
    
    Trả về danh sách cơ sở công khai (cho dropdown trong form).
    Không cần authentication.
    """
    try:
        # Import Campus model
        from campus.models import Campus
        
        # Get all active campuses using ORM (correct field names: hotline not phone)
        campuses = Campus.objects.filter(status='active').values(
            'id', 'name', 'address', 'hotline', 'email'
        ).order_by('name')
        
        # Convert QuerySet to list
        campuses_list = list(campuses)
        
        # Convert UUID to string for JSON serialization
        for campus in campuses_list:
            campus['id'] = str(campus['id'])
        
        return Response({
            'count': len(campuses_list),
            'results': campuses_list
        })
    except Exception as e:
        # Log error and return empty list
        print(f"❌ Error in public_campuses: {e}")
        import traceback
        traceback.print_exc()
        
        return Response({
            'count': 0,
            'results': [],
            'error': str(e)
        })
