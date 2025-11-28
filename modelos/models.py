from django.db import models
from django.contrib.auth.models import User, Group
from decimal import Decimal
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone #Kevin

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

    precio = models.IntegerField() 

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
    
    def clean(self): #Kevin
        super().clean()
        if len(self.nombre.strip()) < 3:
            raise ValidationError({'nombre': "El nombre debe tener al menos 3 caracteres."})
        if self.precio is not None and self.precio <= 0:
            raise ValidationError({'precio': "El precio debe ser un numero entero mayor que cero."})
        if self.stock < 0:
            raise ValidationError({'stock': "El stock no puede ser negativo."})


class Pedido(models.Model):
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('EN_PREPARACION', 'En preparación'),
        ('LISTO', 'Listo para despacho'),
        ('ENVIADO', 'Enviado'),
        ('CANCELADO', 'Cancelado'),
    ]

    id = models.BigAutoField(primary_key=True)
    cliente = models.ForeignKey('Cliente', on_delete=models.SET_NULL, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=30, choices=ESTADO_CHOICES, default='PENDIENTE')
    tiempo_despacho = models.DateTimeField(null=True, blank=True, help_text="Fecha/hora programada de despacho")
    almacenamiento_especial = models.BooleanField(default=False)
    observaciones = models.TextField(blank=True, null=True)
    # si ya tenías detalles de pedido con FK a Pedido, mantenlos
    # Relation to notifications (reverse relation provided by Notificacion.pedido)

    def __str__(self):
        return f"Pedido #{self.id} - {self.cliente or 'Cliente desconocido'} - {self.estado}"
    
    def clean(self): #Kevin
        if not self.cliente:
            raise ValidationError({'cliente': "Debe asignarse un cliente al pedido."})
        if self.tiempo_despacho and self.tiempo_despacho < self.fecha_creacion:
            raise ValidationError({'tiempo_despacho': "La fecha de despacho no puede ser anterior a la creación del pedido."})



class DetallePedido(models.Model):
    id = models.BigAutoField(primary_key=True)

    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
    )

    producto = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT,
    )

    cantidad = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )

    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Precio unitario registrado al momento del pedido"
    )

    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        editable=False
    )

    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Detalle de pedido"
        verbose_name_plural = "Detalles de pedido"
        unique_together = ('pedido', 'producto')
        ordering = ['-creado']

    def __str__(self):
        return f"Pedido #{self.pedido_id} - {self.producto.nombre} x{self.cantidad}"

    def save(self, *args, **kwargs):
        # Si no se pasó precio_unitario, tomar el precio actual del producto
        if self.precio_unitario in [None, ""]:
            self.precio_unitario = getattr(self.producto, 'precio', Decimal('0.00'))

        # asegurar Decimal para la multiplicación
        precio = Decimal(self.precio_unitario)
        qty = Decimal(self.cantidad)
        self.subtotal = (precio * qty).quantize(Decimal('0.01'))

        super().save(*args, **kwargs)

    @property
    def to_dict(self):
        """Útil para serializar rápido en vistas sin serializer."""
        return {
            "id": self.id,
            "pedido_id": self.pedido_id,
            "producto_id": self.producto_id,
            "producto_nombre": self.producto.nombre if self.producto_id else None,
            "cantidad": self.cantidad,
            "precio_unitario": float(self.precio_unitario),
            "subtotal": float(self.subtotal),
            "creado": self.creado,
        }
    def clean(self): #Kevin
        if self.precio_unitario <= 0:
            raise ValidationError({'precio_unitario': "El precio unitario debe ser mayor que cero."})
        if self.producto and self.cantidad > self.producto.stock:
            raise ValidationError({'cantidad': f"Solo hay {self.producto.stock} unidades disponibles de {self.producto.nombre}."})



class Notificacion(models.Model):

    TIPO_CHOICES = [
        ('FALTA_PRODUCTO', 'Falta de producto'),
        ('CAMBIO_PEDIDO', 'Cambio pedido'),
        ('INFO_GENERAL', 'Información general'),
    ]
    RESPUESTA_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('ACEPTADO', 'Aceptado'),
        ('RECHAZADO', 'Rechazado'),
    ]

    id = models.BigAutoField(
        primary_key = True
    )
    pedido = models.ForeignKey(
        Pedido, 
        on_delete = models.CASCADE,
        related_name = 'notificaciones'
    )
    remitente = models.ForeignKey(
        User,
        on_delete = models.SET_NULL,
        null = True,
        related_name = 'notificaciones_enviadas'
    )
    destinatario = models.ForeignKey(
        User,
        on_delete = models.SET_NULL,
        null=True,
        blank=True,
        related_name='notificaciones_recibidas'
    )
    tipo = models.CharField(
        max_length=30,
        choices=TIPO_CHOICES,
        default='INFO_GENERAL'
    )
    mensaje = models.TextField(
        max_length=1000
    )
    fecha_envio = models.DateTimeField(
        auto_now_add = True
    )
    leida = models.BooleanField(
        default=False
    )
    estado_respuesta = models.CharField(
        max_length=20,
        choices=RESPUESTA_CHOICES,
        default='PENDIENTE'
    )
    respuesta_texto = models.TextField(
        blank=True, null=True
    )
    fecha_respuesta = models.DateTimeField(
        null=True,
        blank=True
    )

    def __str__(self):
        return f"Notificación #{self.id} ({self.tipo}) -> Pedido {self.pedido_id}"
    
    def clean(self): #Kevin
        if len(self.mensaje.strip()) < 5:
            raise ValidationError({'mensaje': "El mensaje debe tener al menos 5 caracteres."})
        if self.estado_respuesta != 'PENDIENTE' and not self.respuesta_texto:
            raise ValidationError({'respuesta_texto': "Debe ingresar una respuesta si el estado no es 'Pendiente'."})



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
    
    def clean(self): #Kevin
        if len(self.nombre.strip()) < 2:
            raise ValidationError({'nombre': "El nombre debe tener al menos 2 caracteres."})
        if len(self.apellido.strip()) < 2:
            raise ValidationError({'apellido': "El apellido debe tener al menos 2 caracteres."})
        if self.telefono and not self.telefono.isdigit():
            raise ValidationError({'telefono': "El teléfono debe contener solo números."})