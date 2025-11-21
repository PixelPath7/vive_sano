from django.db import models
from django.contrib.auth.models import User, Group

# Create your models here.

class Producto(models.Model):

    id = models.BigAutoField(primary_key=True)

    nombre = models.CharField(
        max_length = 100
    )
    
    descripcion = models.TextField(
        blank = True,
        null = True
    )

    precio = models.DecimalField(
        max_digits = 10,
        decimal_places = 2
    ) 

    stock = models.IntegerField(
        default = 0
    )
    
    categoria = models.CharField(
        max_length = 50, 
        blank = True
    )
    
    imagen = models.ImageField(
        upload_to = 'productos/',
        null = True,
        blank = True
    )

    def __str__(self):
        return self.nombre

"""class Pedidos(models.Model):
    pass"""

class Cliente(models.Model):
    
    user = models.OneToOneField(
        User,
        on_delete = models.CASCADE,
        null = True,
        blank = True
    )

    nombre = models.CharField(
        max_length = 100
    )

    apellido = models.CharField(
        max_length = 100
    )

    email = models.EmailField(
        unique = True
    )

    telefono = models.CharField(
        max_length = 15,
        blank = True
    )

    direccion = models.CharField(
        max_length = 255,
        blank = True
    )

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

