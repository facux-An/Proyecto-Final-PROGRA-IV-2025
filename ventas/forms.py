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

    LOCALIDADES_BSAS = [
        'Adrogué', 'Avellaneda', 'Banfield', 'Beccar', 'Bella Vista',
        'Berazategui', 'Bernal', 'Boulogne', 'Burzaco', 'Caballito',
        'Caseros', 'Castelar', 'City Bell', 'Ciudadela', 'Claypole',
        'Del Viso', 'Don Torcuato', 'El Palomar', 'El Talar', 'Esteban Echeverría',
        'Ezeiza', 'Florencio Varela', 'Florida', 'General Pacheco', 'General San Martín',
        'Gerli', 'Glew', 'González Catán', 'Grand Bourg', 'Haedo',
        'Hurlingham', 'Isidro Casanova', 'Ituzaingó', 'José C. Paz', 'José Mármol',
        'La Lucila', 'La Matanza', 'La Plata', 'La Tablada', 'Lanús',
        'Llavallol', 'Lomas de Zamora', 'Longchamps', 'Los Polvorines', 'Luis Guillón',
        'Luján', 'Malvinas Argentinas', 'Mar del Plata', 'Martínez', 'Merlo',
        'Monte Grande', 'Moreno', 'Morón', 'Muñiz', 'Munro',
        'Olivos', 'Pablo Podestá', 'Paso del Rey', 'Pergamino', 'Pilar',
        'Quilmes', 'Rafael Calzada', 'Ramos Mejía', 'Remedios de Escalada', 'San Antonio de Padua',
        'San Fernando', 'San Isidro', 'San Justo', 'San Martín', 'San Miguel',
        'San Nicolás', 'Santos Lugares', 'Sarandí', 'Temperley', 'Tigre',
        'Tortuguitas', 'Tres de Febrero', 'Turdera', 'Vicente López', 'Villa Ballester',
        'Villa Bosch', 'Villa Celina', 'Villa Luzuriaga', 'Villa Madero', 'Villa Martelli',
        'Wilde', 'William Morris', 'Zárate',
        # CABA barrios principales
        'CABA - Palermo', 'CABA - Belgrano', 'CABA - Recoleta', 'CABA - Caballito',
        'CABA - Flores', 'CABA - Villa Urquiza', 'CABA - Almagro', 'CABA - Barracas',
        'CABA - Boedo', 'CABA - Colegiales', 'CABA - Devoto', 'CABA - Liniers',
        'CABA - Mataderos', 'CABA - Nuñez', 'CABA - Once', 'CABA - Pompeya',
        'CABA - Puerto Madero', 'CABA - Retiro', 'CABA - San Cristóbal', 'CABA - San Telmo',
        'CABA - Villa Crespo', 'CABA - Villa del Parque', 'CABA - Villa Lugano',
    ]

    class Meta:
        model = Pedido
        fields = [
            'nombre_envio',
            'email_envio',
            'telefono_envio',
            'direccion_envio',
            'numero_envio',
            'piso_envio',
            'depto_envio',
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
                'placeholder': 'Calle',
            }),
            'numero_envio': forms.TextInput(attrs={
                'class': 'form-control form-control-lg bg-light border-0 rounded-pill px-4',
                'placeholder': 'Número',
            }),
            'piso_envio': forms.TextInput(attrs={
                'class': 'form-control form-control-lg bg-light border-0 rounded-pill px-4',
                'placeholder': 'Piso (Opcional)',
            }),
            'depto_envio': forms.TextInput(attrs={
                'class': 'form-control form-control-lg bg-light border-0 rounded-pill px-4',
                'placeholder': 'Depto (Opcional)',
            }),
            'ciudad_envio': forms.TextInput(attrs={
                'class': 'form-control form-control-lg bg-light border-0 rounded-pill px-4',
                'placeholder': 'Empezá a escribir tu localidad...',
                'list': 'localidades-bsas',
                'autocomplete': 'off',
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
        self.fields['numero_envio'].required = True
        self.fields['piso_envio'].required = False
        self.fields['depto_envio'].required = False
        self.fields['ciudad_envio'].required = True
        self.fields['provincia_envio'].required = True
        self.fields['codigo_postal_envio'].required = True
        self.fields['notas_envio'].required = False

        # Restringir provincia a Buenos Aires y CABA
        self.fields['provincia_envio'].widget = forms.Select(
            choices=[
                ('', 'Seleccioná tu provincia'),
                ('Buenos Aires', 'Buenos Aires'),
                ('CABA', 'Ciudad Autónoma de Buenos Aires'),
            ],
            attrs={
                'class': 'form-select form-select-lg bg-light border-0 rounded-pill px-4',
            }
        )
