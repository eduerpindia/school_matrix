# students/id_card_service.py

from datetime import datetime, date, timedelta
from .id_card_config import ALL_AVAILABLE_FIELDS


class IDCardDataExtractor:
    """
    Extract data from Student and School models
    """
    
    def __init__(self, student, school, session, card_data=None):
        self.student = student
        self.school = school
        self.session = session
        self.card_data = card_data or {}
    
    def get_field_value(self, field_name):
        """
        Get value for a specific field
        """
        if field_name not in ALL_AVAILABLE_FIELDS:
            return None
        
        field_config = ALL_AVAILABLE_FIELDS[field_name]
        source = field_config.get('source')
        field_type = field_config.get('type')
        
        # Handle custom fields
        if source == 'custom':
            if field_name == 'class_section':
                if self.student.current_class and self.student.section:
                    return f"{self.student.current_class.display_name} - {self.student.section.name}"
                return ''
            elif field_name == 'instructions':
                return field_config.get('default', '')
        
        # Navigate source path
        try:
            parts = source.split('.')
            value = self
            
            for part in parts:
                if hasattr(value, part):
                    value = getattr(value, part)
                    if callable(value):
                        value = value()
                else:
                    return None
            
            # Format dates
            if field_type == 'date' and isinstance(value, date):
                date_format = field_config.get('format', 'DD/MM/YYYY')
                if date_format == 'DD/MM/YYYY':
                    return value.strftime('%d/%m/%Y')
                elif date_format == 'MM/DD/YYYY':
                    return value.strftime('%m/%d/%Y')
                else:
                    return value.strftime('%Y-%m-%d')
            
            # Handle image URLs
            if field_type == 'image':
                if hasattr(value, 'url'):
                    return value.url
                return value
            
            return str(value) if value else ''
        
        except Exception as e:
            return ''
    
    def extract_fields(self, field_names):
        """
        Extract multiple fields and return as dictionary
        """
        data = {}
        for field_name in field_names:
            value = self.get_field_value(field_name)
            data[field_name] = value
        return data
    
    def generate_card_number(self):
        """Generate unique card number"""
        year = datetime.now().year
        student_id = self.student.id
        return f"ID{year}{student_id:06d}"
