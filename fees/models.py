from django.db import models
from django.core.validators import MinValueValidator

class FeeStructure(models.Model):
    FEE_TYPES = [
        ('TUITION', 'Tuition Fee'),
        ('ADMISSION', 'Admission Fee'),
        ('EXAM', 'Examination Fee'),
        ('LIBRARY', 'Library Fee'),
        ('LAB', 'Laboratory Fee'),
        ('SPORTS', 'Sports Fee'),
        ('TRANSPORT', 'Transport Fee'),
        ('HOSTEL', 'Hostel Fee'),
        ('MISCELLANEOUS', 'Miscellaneous Fee'),
    ]
    
    class_name = models.ForeignKey('classes.Class', on_delete=models.CASCADE, related_name='fee_structures')
    fee_type = models.CharField(max_length=15, choices=FEE_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    frequency = models.CharField(max_length=15, choices=[
            ('MONTHLY', 'Monthly'),
            ('QUARTERLY', 'Quarterly'),
            ('HALF_YEARLY', 'Half Yearly'),
            ('YEARLY', 'Yearly'),
            ('ONE_TIME', 'One Time'),
        ])
    due_date = models.DateField(null=True, blank=True)
    academic_year = models.CharField(max_length=9)  # Format: 2024-2025
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['class_name', 'fee_type', 'academic_year']
        ordering = ['class_name', 'fee_type']
    
    def __str__(self):
        return f"{self.class_name.display_name} - {self.get_fee_type_display()} - ₹{self.amount}"


class FeeInvoice(models.Model):
    INVOICE_STATUS = [
        ('PENDING', 'Pending'),
        ('PARTIAL', 'Partially Paid'),
        ('PAID', 'Paid'),
        ('OVERDUE', 'Overdue'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='fee_invoices')
    invoice_number = models.CharField(max_length=20, unique=True)
    invoice_date = models.DateField()
    due_date = models.DateField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    balance_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=INVOICE_STATUS, default='PENDING')
    academic_year = models.CharField(max_length=9)  # Format: 2024-2025
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-invoice_date']
        indexes = [
            models.Index(fields=['invoice_number']),
            models.Index(fields=['student', 'status']),
        ]
    
    def __str__(self):
        return f"Invoice #{self.invoice_number} - {self.student.admission_number}"


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(FeeInvoice, on_delete=models.CASCADE, related_name='items')
    fee_type = models.CharField(max_length=15, choices=FeeStructure.FEE_TYPES)
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        ordering = ['fee_type']
    
    def __str__(self):
        return f"{self.invoice.invoice_number} - {self.get_fee_type_display()}"


class FeePayment(models.Model):
    PAYMENT_MODES = [
        ('CASH', 'Cash'),
        ('CHEQUE', 'Cheque'),
        ('DD', 'Demand Draft'),
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('UPI', 'UPI'),
        ('CARD', 'Credit/Debit Card'),
        ('ONLINE', 'Online Payment'),
    ]
    
    PAYMENT_STATUS = [
        ('SUCCESS', 'Success'),
        ('PENDING', 'Pending'),
        ('FAILED', 'Failed'),
        ('REFUNDED', 'Refunded'),
    ]
    
    invoice = models.ForeignKey(FeeInvoice, on_delete=models.CASCADE, related_name='payments')
    payment_date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    payment_mode = models.CharField(max_length=15, choices=PAYMENT_MODES)
    transaction_id = models.CharField(max_length=100, blank=True)
    bank_name = models.CharField(max_length=100, blank=True)
    cheque_dd_number = models.CharField(max_length=50, blank=True)
    cheque_dd_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=PAYMENT_STATUS, default='SUCCESS')
    remarks = models.TextField(blank=True)
    received_by = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-payment_date']
        indexes = [
            models.Index(fields=['transaction_id']),
        ]
    
    def __str__(self):
        return f"Payment #{self.id} - {self.invoice.invoice_number} - ₹{self.amount}"


class FeeConcession(models.Model):
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='fee_concessions')
    concession_type = models.CharField(max_length=20, choices=[
        ('SCHOLARSHIP', 'Scholarship'),
        ('FEE_WAIVER', 'Fee Waiver'),
        ('DISCOUNT', 'Discount'),
        ('OTHER', 'Other'),
    ])
    description = models.TextField()
    percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    fixed_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    applicable_fee_types = models.CharField(max_length=200)  # Comma-separated fee types
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    approved_by = models.CharField(max_length=100)
    approved_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.student.admission_number} - {self.get_concession_type_display()}"