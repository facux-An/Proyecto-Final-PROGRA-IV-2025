from django import forms
from .models import Pedido
from productos.models import Producto


class DatosEnvioForm(forms.ModelForm):
    """
    Formulario de datos de envío para el checkout.
    Solo captura la información necesaria para despachar el paquete.
    """

    PROVINCIAS = [
        ('', 'Seleccioná tu provincia'),
        ('Buenos Aires', 'Buenos Aires'),
        ('CABA', 'Ciudad Autónoma de Buenos Aires'),
        ('Catamarca', 'Catamarca'),
        ('Chaco', 'Chaco'),
        ('Chubut', 'Chubut'),
        ('Córdoba', 'Córdoba'),
        ('Corrientes', 'Corrientes'),
        ('Entre Ríos', 'Entre Ríos'),
        ('Formosa', 'Formosa'),
        ('Jujuy', 'Jujuy'),
        ('La Pampa', 'La Pampa'),
        ('La Rioja', 'La Rioja'),
        ('Mendoza', 'Mendoza'),
        ('Misiones', 'Misiones'),
        ('Neuquén', 'Neuquén'),
        ('Río Negro', 'Río Negro'),
        ('Salta', 'Salta'),
        ('San Juan', 'San Juan'),
        ('San Luis', 'San Luis'),
        ('Santa Cruz', 'Santa Cruz'),
        ('Santa Fe', 'Santa Fe'),
        ('Santiago del Estero', 'Santiago del Estero'),
        ('Tierra del Fuego', 'Tierra del Fuego'),
        ('Tucumán', 'Tucumán'),
    ]

    class Meta:
        model = Pedido
        fields = [
            'nombre_envio',
            'email_envio',
            'telefono_envio',
            'direccion_envio',
            'ciudad_envio',
            'provincia_envio',
            'codigo_postal_envio',
            'notas_envio',
        ]
        widgets = {
            'nombre_envio': forms.TextInput(attrs={
                'class': 'form-control form-control-lg bg-light border-0 rounded-pill px-4',
                'placeholder': 'Ej: Juan Pérez',
                'autofocus': True,
            }),
            'email_envio': forms.EmailInput(attrs={
                'class': 'form-control form-control-lg bg-light border-0 rounded-pill px-4',
                'placeholder': 'tu@email.com',
            }),
            'telefono_envio': forms.TextInput(attrs={
                'class': 'form-control form-control-lg bg-light border-0 rounded-pill px-4',
                'placeholder': 'Ej: 11 6590 9847',
            }),
            'direccion_envio': forms.TextInput(attrs={
                'class': 'form-control form-control-lg bg-light border-0 rounded-pill px-4',
                'placeholder': 'Calle, número, piso, depto',
            }),
            'ciudad_envio': forms.TextInput(attrs={
                'class': 'form-control form-control-lg bg-light border-0 rounded-pill px-4',
                'placeholder': 'Ej: CABA, Córdoba, etc.',
            }),
            'codigo_postal_envio': forms.TextInput(attrs={
                'class': 'form-control form-control-lg bg-light border-0 rounded-pill px-4',
                'placeholder': 'Ej: 1425',
            }),
            'notas_envio': forms.Textarea(attrs={
                'class': 'form-control bg-light border-0 rounded-4 px-4 py-3',
                'placeholder': 'Instrucciones especiales (timbre, portería, horario preferido...)',
                'rows': 3,
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer obligatorios los campos esenciales
        self.fields['nombre_envio'].required = True
        self.fields['email_envio'].required = True
        self.fields['telefono_envio'].required = True
        self.fields['direccion_envio'].required = True
        self.fields['ciudad_envio'].required = True
        self.fields['provincia_envio'].required = True
        self.fields['codigo_postal_envio'].required = True
        self.fields['notas_envio'].required = False

        # Asignar las provincias al widget select
        self.fields['provincia_envio'].widget = forms.Select(
            choices=self.PROVINCIAS,
            attrs={
                'class': 'form-select form-select-lg bg-light border-0 rounded-pill px-4',
            }
        )
