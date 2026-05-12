from django.db import models
import uuid
import os

def company_logo_path(instance, filename):
    """Function to define the upload path for company logos"""
    # Get the file extension
    ext = filename.split('.')[-1]
    # Generate a new filename with UUID
    filename = f"{uuid.uuid4()}.{ext}"
    # Return the upload path
    return os.path.join('company_logos', filename)

class Company(models.Model):
    """Model for storing company information"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, verbose_name="Nombre de la Empresa")
    logo = models.ImageField(upload_to=company_logo_path, null=True, blank=True, verbose_name="Logo de la Empresa")
    email = models.EmailField(max_length=100, null=True, blank=True, verbose_name="Email de Contacto")
    phone = models.CharField(max_length=20, null=True, blank=True, verbose_name="Telefono de Contacto")
    address = models.TextField(null=True, blank=True, verbose_name="Direccion de la Empresa")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Company"
        verbose_name_plural = "Companies"

    def __str__(self):
        return self.name

    @classmethod
    def get_solo(cls):
        """Get the first company record or create one if none exists"""
        obj, created = cls.objects.get_or_create(pk=cls.objects.first().pk if cls.objects.exists() else None)
        return obj
