# students/id_card_config.py

"""
ID Card Fields Configuration
Divided into Front Side and Back Side
"""

# ========== FRONT SIDE FIELDS ==========
FRONT_SIDE_FIELDS = {
    # Student Photo
    'photo_url': {
        'label': 'Student Photo',
        'source': 'student.photo.url',
        'type': 'image',
        'category': 'Student'
    },
    
    # Student Basic Info
    'name': {
        'label': 'Full Name',
        'source': 'student.user.get_full_name',
        'type': 'text',
        'category': 'Student'
    },
    'admission_no': {
        'label': 'Admission Number',
        'source': 'student.admission_number',
        'type': 'text',
        'category': 'Student'
    },
    'roll_number': {
        'label': 'Roll Number',
        'source': 'student.roll_number',
        'type': 'text',
        'category': 'Student'
    },
    'class': {
        'label': 'Class',
        'source': 'student.current_class.display_name',
        'type': 'text',
        'category': 'Student'
    },
    'section': {
        'label': 'Section',
        'source': 'student.section.name',
        'type': 'text',
        'category': 'Student'
    },
    'class_section': {
        'label': 'Class & Section',
        'source': 'custom',
        'type': 'text',
        'category': 'Student'
    },
    'dob': {
        'label': 'Date of Birth',
        'source': 'student.date_of_birth',
        'type': 'date',
        'format': 'DD/MM/YYYY',
        'category': 'Student'
    },
    'gender': {
        'label': 'Gender',
        'source': 'student.gender',
        'type': 'text',
        'category': 'Student'
    },
    'blood_group': {
        'label': 'Blood Group',
        'source': 'student.blood_group',
        'type': 'text',
        'category': 'Student'
    },
    'phone': {
        'label': 'Phone Number',
        'source': 'student.phone_number',
        'type': 'text',
        'category': 'Student'
    },
    
    # Card Info
    'card_number': {
        'label': 'Card Number',
        'source': 'card.card_number',
        'type': 'text',
        'category': 'Card'
    },
    'issue_date': {
        'label': 'Issue Date',
        'source': 'card.issue_date',
        'type': 'date',
        'format': 'DD/MM/YYYY',
        'category': 'Card'
    },
    'valid_till': {
        'label': 'Valid Till',
        'source': 'card.valid_till',
        'type': 'date',
        'format': 'DD/MM/YYYY',
        'category': 'Card'
    }
}

# ========== BACK SIDE FIELDS ==========
BACK_SIDE_FIELDS = {
    # School Info
    'school_name': {
        'label': 'School Name',
        'source': 'school.name',
        'type': 'text',
        'category': 'School'
    },
    'school_logo': {
        'label': 'School Logo',
        'source': 'school.logo.url',
        'type': 'image',
        'category': 'School'
    },
    'school_address': {
        'label': 'School Address',
        'source': 'school.address',
        'type': 'text',
        'category': 'School'
    },
    'school_city': {
        'label': 'City',
        'source': 'school.city',
        'type': 'text',
        'category': 'School'
    },
    'school_state': {
        'label': 'State',
        'source': 'school.state',
        'type': 'text',
        'category': 'School'
    },
    'school_pincode': {
        'label': 'Pin Code',
        'source': 'school.pincode',
        'type': 'text',
        'category': 'School'
    },
    'school_phone': {
        'label': 'School Phone',
        'source': 'school.phone',
        'type': 'text',
        'category': 'School'
    },
    'school_email': {
        'label': 'School Email',
        'source': 'school.email',
        'type': 'text',
        'category': 'School'
    },
    'school_website': {
        'label': 'Website',
        'source': 'school.website',
        'type': 'text',
        'category': 'School'
    },
    
    # Parent Info
    'father_name': {
        'label': "Father's Name",
        'source': 'student.father_name',
        'type': 'text',
        'category': 'Parent'
    },
    'mother_name': {
        'label': "Mother's Name",
        'source': 'student.mother_name',
        'type': 'text',
        'category': 'Parent'
    },
    'parent_phone': {
        'label': 'Parent Contact',
        'source': 'student.parent_phone',
        'type': 'text',
        'category': 'Parent'
    },
    'emergency_contact': {
        'label': 'Emergency Contact',
        'source': 'student.emergency_contact',
        'type': 'text',
        'category': 'Parent'
    },
    
    # Admin Signature
    'principal_signature': {
        'label': 'Principal Signature',
        'source': 'school.principal_signature.url',
        'type': 'image',
        'category': 'School'
    },
    'principal_name': {
        'label': 'Principal Name',
        'source': 'school.principal_name',
        'type': 'text',
        'category': 'School'
    },
    
    # Instructions/Notes
    'instructions': {
        'label': 'Instructions',
        'source': 'custom',
        'type': 'text',
        'category': 'School',
        'default': 'If found, please return to school address'
    }
}

# ========== TEMPLATE CONFIGURATIONS ==========
TEMPLATE_CONFIGS = {
    # Single Page Templates (Front side only)
    'template_1': {
        'name': 'Classic Blue - Single',
        'description': 'Single page classic design',
        'type': 'single',  # <-- Template Type
        'fields': [
            'photo_url', 'name', 'admission_no', 'class_section',
            'dob', 'blood_group', 'school_name', 'school_phone',
            'card_number', 'valid_till'
        ]
    },
    'template_2': {
        'name': 'Modern Red - Single',
        'description': 'Single page modern design',
        'type': 'single',
        'fields': [
            'photo_url', 'name', 'admission_no', 'class', 'section',
            'father_name', 'emergency_contact', 'school_name',
            'card_number'
        ]
    },
    
    # Front & Back Templates
    'template_3': {
        'name': 'Professional Green - Front & Back',
        'description': 'Professional design with front and back',
        'type': 'front_and_back',  # <-- Template Type
        'front_fields': [
            'photo_url', 'name', 'admission_no', 'class_section',
            'dob', 'blood_group', 'card_number', 'valid_till'
        ],
        'back_fields': [
            'school_name', 'school_logo', 'school_address',
            'school_city', 'school_phone', 'school_email',
            'principal_signature', 'principal_name', 'instructions'
        ]
    },
    'template_4': {
        'name': 'Elegant Purple - Front & Back',
        'description': 'Elegant design with detailed info',
        'type': 'front_and_back',
        'front_fields': [
            'photo_url', 'name', 'admission_no', 'roll_number',
            'class_section', 'dob', 'gender', 'blood_group',
            'card_number', 'issue_date', 'valid_till'
        ],
        'back_fields': [
            'school_name', 'school_logo', 'school_address',
            'school_phone', 'father_name', 'mother_name',
            'emergency_contact', 'principal_signature',
            'principal_name'
        ]
    },
    'template_5': {
        'name': 'Minimal Orange - Front & Back',
        'description': 'Minimalist design',
        'type': 'front_and_back',
        'front_fields': [
            'photo_url', 'name', 'admission_no', 'class_section',
            'card_number', 'valid_till'
        ],
        'back_fields': [
            'school_name', 'school_address', 'school_phone',
            'emergency_contact', 'principal_signature'
        ]
    }
}

# Combine all fields for reference
ALL_AVAILABLE_FIELDS = {**FRONT_SIDE_FIELDS, **BACK_SIDE_FIELDS}
