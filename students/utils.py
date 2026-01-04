# students/utils.py

import random
import string
from django.contrib.auth import get_user_model
from students.models import Student

User = get_user_model()


def generate_admission_number(tenant_school):
    """
    Generate unique admission number based on tenant
    Format: TENANTCODE-ADM-0001, TENANTCODE-ADM-0002, etc.
    Example: BFA01-ADM-0001, BFA01-ADM-0002
    
    Args:
        tenant_school: School instance from request.tenant
        
    Returns:
        str: Generated admission number (e.g., "BFA01-ADM-0001")
    """
    tenant_code = tenant_school.school_code  # e.g., BFA01
    
    # Get last admission number for this tenant
    last_student = Student.objects.filter(
        admission_number__startswith=f"{tenant_code}-ADM-"
    ).order_by('-admission_number').first()
    
    if last_student:
        try:
            # Extract number from last admission number
            # Example: "BFA01-ADM-0005" -> "0005" -> 5
            last_number = int(last_student.admission_number.split('-ADM-')[1])
            next_number = last_number + 1
        except (ValueError, IndexError):
            # If parsing fails, start from 1
            next_number = 1
    else:
        # First student in this tenant
        next_number = 1
    
    # Format: BFA01-ADM-0001 (4 digits with leading zeros)
    admission_number = f"{tenant_code}-ADM-{next_number:04d}"
    
    return admission_number


def generate_college_email(first_name, admission_number, tenant_school):
    """
    Generate simple and clean college email
    Format: firstname.number@domain
    Example: rahul.0001@bfa.in, ankur.0002@bfa.in
    
    Args:
        first_name: Student's first name
        admission_number: Generated admission number (e.g., "BFA01-ADM-0001")
        tenant_school: School instance from request.tenant
        
    Returns:
        str: Generated college email (e.g., "rahul.0001@bfa.in")
    """
    # Get domain from school email
    domain = tenant_school.email.split('@')[1]  # Extract domain (e.g., bfa.in)
    
    # Extract only the number from admission number
    # BFA01-ADM-0001 -> 0001
    try:
        number = admission_number.split('-ADM-')[1]
    except IndexError:
        # Fallback: use last 4 characters
        number = admission_number[-4:].zfill(4)
    
    # Clean first name - remove spaces, dots, special chars
    first = first_name.lower().replace(' ', '').replace('.', '').replace('-', '')
    
    # Keep only alphabets
    first = ''.join(c for c in first if c.isalpha())
    
    # If name becomes empty after cleaning, use 'student'
    if not first:
        first = 'student'
    
    # Create email: firstname.number@domain
    base_email = f"{first}.{number}@{domain}"
    
    # Check for duplicates (rare case but handle it)
    counter = 1
    college_email = base_email
    
    while User.objects.filter(email=college_email).exists():
        college_email = f"{first}.{number}{counter}@{domain}"
        counter += 1
    
    return college_email


def generate_random_password(length=12):
    """
    Generate secure random password with mixed characters
    Format: Mix of Uppercase, Lowercase, Digits, Special chars
    Example: Ab12@#xY3zK9
    
    Args:
        length: Password length (default: 12)
        
    Returns:
        str: Generated random password
    """
    # Ensure password has required character types
    password_chars = [
        random.choice(string.ascii_uppercase),  # At least 2 uppercase
        random.choice(string.ascii_uppercase),
        random.choice(string.ascii_lowercase),  # At least 2 lowercase
        random.choice(string.ascii_lowercase),
        random.choice(string.digits),           # At least 2 digits
        random.choice(string.digits),
        random.choice('@#$%&*!'),               # At least 2 special chars
        random.choice('@#$%&*!'),
    ]
    
    # Fill remaining length with random characters
    all_chars = string.ascii_letters + string.digits + '@#$%&*!'
    remaining_length = length - len(password_chars)
    
    if remaining_length > 0:
        password_chars.extend(random.choice(all_chars) for _ in range(remaining_length))
    
    # Shuffle to randomize positions
    random.shuffle(password_chars)
    
    return ''.join(password_chars)


def create_student_credentials(first_name, admission_number, tenant_school):
    """
    Generate both college email and random password for student
    
    Args:
        first_name: Student's first name
        admission_number: Generated admission number
        tenant_school: School instance from request.tenant
        
    Returns:
        tuple: (college_email, plain_password)
        Example: ("rahul.0001@bfa.in", "Xy12@#aB3zK9")
    """
    college_email = generate_college_email(first_name, admission_number, tenant_school)
    plain_password = generate_random_password(12)
    
    return college_email, plain_password


# ========== OPTIONAL: Additional utility functions ==========

def validate_admission_number_format(admission_number):
    """
    Validate admission number format
    Expected: TENANT-ADM-XXXX (e.g., BFA01-ADM-0001)
    
    Returns:
        bool: True if valid format
    """
    import re
    pattern = r'^[A-Z0-9]+-ADM-\d{4}$'
    return bool(re.match(pattern, admission_number))


def get_next_roll_number(class_id, section_id):
    """
    Get next available roll number for a class-section
    
    Args:
        class_id: Class ID
        section_id: Section ID
        
    Returns:
        int: Next available roll number
    """
    last_student = Student.objects.filter(
        current_class_id=class_id,
        section_id=section_id,
        is_active=True
    ).order_by('-roll_number').first()
    
    if last_student:
        return last_student.roll_number + 1
    else:
        return 1


def bulk_generate_passwords(count=10, length=12):
    """
    Generate multiple random passwords (useful for bulk imports)
    
    Args:
        count: Number of passwords to generate
        length: Password length
        
    Returns:
        list: List of generated passwords
    """
    return [generate_random_password(length) for _ in range(count)]
