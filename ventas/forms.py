from django import forms
from .models import Pedido


class PedidoForm(forms.ModelForm):
    class Meta:
        model = Pedido
        # Campos que el usuario puede completar al crear un pedido
        fields = ['producto', 'cantidad', 'fecha_entrega']
        widgets = {
            'producto': forms.Select(attrs={'class': 'form-select'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'fecha_entrega': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        producto = cleaned_data.get('producto')
        cantidad = cleaned_data.get('cantidad')

        # Validación de stock al crear un nuevo pedido
        if self.instance.pk is None and producto and cantidad:
            if producto.stock < cantidad:
                raise forms.ValidationError(
                    f"❌ No hay stock suficiente para el producto '{producto.nombre}'. "
                    f"Stock disponible: {producto.stock}"
                )
        return cleaned_data
