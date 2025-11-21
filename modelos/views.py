from django.shortcuts import render, HttpResponse, get_object_or_404
from django.forms.models import model_to_dict
from .models import Producto
import json

# Create your views here.

def inicio(request):
    
    if request.method == "GET":
        try:
            productos = {
                "productos": Producto.objects.all()
            }

        except:
            return render(request, "error.html")
        
    if request.method == "POST":
        
        formulario_ = request.POST
        
        if "accion" not in formulario_:
            return HttpResponse("error no tiene accion en formulario xd")

        if formulario_["accion"] == "ver_carrito":
            
            # Se obtiene unicamente el carrito del formulario
            carrito_get = json.loads(formulario_["carrito"])

            carrito = []
            total_productos = 0
            total = 0

            for producto_ in carrito_get:
                
                # Se obtiene la informacion del modelo por id
                resultado = get_object_or_404(Producto, pk=producto_["id"])
                resultado_dict = model_to_dict(resultado)

                # Se le agrega la cantidad enviada desde el formulario de inicio
                resultado_dict["cantidad"] = producto_["cantidad"]

                # Calcula el total y lo suma
                total += resultado_dict["precio"] * producto_["cantidad"]
                total_productos += producto_["cantidad"]
                carrito.append(resultado_dict)

            # Formateando salida xd
            carrito_items = {
                "carrito_items": carrito,
                "total_productos": total_productos,
                "total_precio": total
            }
            
            # Salida
            return render(request, "carrito.html", carrito_items)

        if formulario_["accion"] == "enviar_pedido":
            pass

    return render(request, "inicio.html", productos)
