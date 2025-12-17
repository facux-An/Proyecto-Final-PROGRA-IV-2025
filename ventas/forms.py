from django import forms
from .models import Pedido
from productos.models import Producto

class VentaPresencialForm(forms.ModelForm):
    # Definimos las opciones aquí para mayor orden
    METODOS_PAGO = [
        ('efectivo', 'Efectivo'),
        ('debito', 'Débito'),
        ('transferencia', 'Transferencia'),
        ('mercadopago', 'Mercado Pago (Manual)'),
    ]

    # Sobrescribimos el campo para asegurar que solo acepte estas opciones
    metodo_pago = forms.ChoiceField(
        choices=METODOS_PAGO, 
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Pedido
        fields = ['producto', 'cantidad', 'metodo_pago']
        widgets = {
            'producto': forms.Select(attrs={'class': 'form-select'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        producto = cleaned_data.get("producto")
        cantidad = cleaned_data.get("cantidad")

        if producto and cantidad:
            if producto.stock < cantidad:
                raise forms.ValidationError(
                    f"No hay stock suficiente. Solo quedan {producto.stock} unidades de {producto.nombre}."
                )
        return cleaned_data