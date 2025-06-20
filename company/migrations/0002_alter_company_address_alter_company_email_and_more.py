# Generated by Django 5.2.1 on 2025-06-16 05:05

import company.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='company',
            name='address',
            field=models.TextField(blank=True, null=True, verbose_name='Direccion de la Empresa'),
        ),
        migrations.AlterField(
            model_name='company',
            name='email',
            field=models.EmailField(blank=True, max_length=100, null=True, verbose_name='Email de Contacto'),
        ),
        migrations.AlterField(
            model_name='company',
            name='logo',
            field=models.ImageField(blank=True, null=True, upload_to=company.models.company_logo_path, verbose_name='Logo de la Empresa'),
        ),
        migrations.AlterField(
            model_name='company',
            name='name',
            field=models.CharField(max_length=100, verbose_name='Nombre de la Empresa'),
        ),
        migrations.AlterField(
            model_name='company',
            name='phone',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='Telefono de Contacto'),
        ),
    ]
