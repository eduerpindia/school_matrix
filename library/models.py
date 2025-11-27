from django.db import models
from django.core.validators import MinValueValidator

class BookCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = "Book categories"
    
    def __str__(self):
        return self.name


class Book(models.Model):
    BOOK_STATUS = [
        ('AVAILABLE', 'Available'),
        ('ISSUED', 'Issued'),
        ('RESERVED', 'Reserved'),
        ('LOST', 'Lost'),
        ('DAMAGED', 'Damaged'),
        ('UNDER_MAINTENANCE', 'Under Maintenance'),
    ]
    
    isbn = models.CharField(max_length=20, unique=True, blank=True)
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=100)
    publisher = models.CharField(max_length=100, blank=True)
    publication_year = models.IntegerField(null=True, blank=True)
    category = models.ForeignKey(BookCategory, on_delete=models.SET_NULL, null=True)
    edition = models.CharField(max_length=50, blank=True)
    language = models.CharField(max_length=50, default='English')
    pages = models.IntegerField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    shelf_number = models.CharField(max_length=10)
    rack_number = models.CharField(max_length=10)
    total_copies = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    available_copies = models.IntegerField(default=1)
    status = models.CharField(max_length=20, choices=BOOK_STATUS, default='AVAILABLE')
    description = models.TextField(blank=True)
    acquired_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['title']
        indexes = [
            models.Index(fields=['isbn']),
            models.Index(fields=['title']),
            models.Index(fields=['author']),
        ]
    
    def __str__(self):
        return f"{self.title} by {self.author}"


class BookIssue(models.Model):
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='book_issues')
    teacher = models.ForeignKey('teachers.Teacher', on_delete=models.CASCADE, null=True, blank=True, 
                              related_name='book_issues')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='issues')
    issue_date = models.DateField()
    due_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)
    fine_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fine_paid = models.BooleanField(default=False)
    issued_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, 
                                related_name='issued_books')
    received_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='received_books')
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-issue_date']
        indexes = [
            models.Index(fields=['student', 'book']),
            models.Index(fields=['due_date']),
        ]
    
    def __str__(self):
        borrower = self.student if self.student else self.teacher
        return f"{self.book.title} issued to {borrower}"


class Fine(models.Model):
    book_issue = models.ForeignKey(BookIssue, on_delete=models.CASCADE, related_name='fines')
    days_overdue = models.IntegerField()
    fine_per_day = models.DecimalField(max_digits=8, decimal_places=2, default=5)
    total_fine = models.DecimalField(max_digits=10, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    paid_date = models.DateField(null=True, blank=True)
    is_waived = models.BooleanField(default=False)
    waiver_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Fine for {self.book_issue} - ₹{self.total_fine}"


class LibraryMember(models.Model):
    MEMBER_TYPES = [
        ('STUDENT', 'Student'),
        ('TEACHER', 'Teacher'),
        ('STAFF', 'Staff'),
    ]
    
    user = models.OneToOneField('users.User', on_delete=models.CASCADE, related_name='library_member')
    member_id = models.CharField(max_length=20, unique=True)
    member_type = models.CharField(max_length=10, choices=MEMBER_TYPES)
    max_books_allowed = models.IntegerField(default=2)
    current_books_issued = models.IntegerField(default=0)
    membership_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['member_id']
    
    def __str__(self):
        return f"{self.member_id} - {self.user.get_full_name()}"