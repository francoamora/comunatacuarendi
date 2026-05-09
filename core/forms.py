from django import forms
from django.core.exceptions import ValidationError
from .models import Historia, Reclamo, Secretaria, Sugerencia


class MultiFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultiFileField(forms.FileField):
    def clean(self, data, initial=None):
        if not data:
            return []
        if not isinstance(data, (list, tuple)):
            data = [data]
        return [super(MultiFileField, self).clean(item, initial) for item in data]

# --- FORMULARIOS ---

class HistoriaForm(forms.ModelForm):
    # Honeypot: Campo oculto para atrapar bots (si lo llenan, es spam)
    trap = forms.CharField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = Historia
        fields = ["titulo", "autor", "email", "contenido", "imagen"]
        widgets = {
            "titulo": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej: El carnaval de 1990"}),
            "autor": forms.TextInput(attrs={"class": "form-control", "placeholder": "Tu nombre completo"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "contacto@ejemplo.com"}),
            "contenido": forms.Textarea(attrs={"class": "form-control", "rows": 4, "placeholder": "Cuéntanos tu historia..."}),
            "imagen": forms.FileInput(attrs={"class": "form-control-file"}),
        }
    
    def clean_trap(self):
        if self.cleaned_data.get('trap'):
            raise ValidationError("Spam detectado.")
        return ""


class SugerenciaForm(forms.ModelForm):
    """Formulario para el buzón anónimo con captcha matemático"""
    captcha = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Respuesta numérica"}),
        label="Seguridad"
    )

    class Meta:
        model = Sugerencia
        fields = ['area', 'mensaje']
        widgets = {
            'area': forms.Select(attrs={'class': 'form-control'}),
            'mensaje': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Dejanos tu idea o crítica constructiva...'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

    def clean_captcha(self):
        val = (self.cleaned_data.get("captcha") or "").strip()
        if not self.request:
            return val
        
        # Validamos contra la sesión específica de sugerencias
        expected = str(self.request.session.get("sugerencia_captcha", "")).strip()
        
        if not expected or val != expected:
            raise forms.ValidationError("La respuesta matemática es incorrecta.")
        return val


class ReclamoForm(forms.ModelForm):
    website = forms.CharField(required=False, widget=forms.HiddenInput)
    imagenes = MultiFileField(
        required=False,
        widget=MultiFileInput(attrs={"class": "form-control-file", "multiple": True}),
        help_text="Podés subir varias fotos (opcional).",
    )

    # Captcha Alfanumérico (Validación contra sesión)
    captcha = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            "class": "form-control", 
            "placeholder": "Ingresá el código de arriba", 
            "autocomplete": "off"
        }),
        label="Código de seguridad",
    )

    class Meta:
        model = Reclamo
        fields = [
            "nombre_apellido", "dni", "email", "telefono",
            "barrio", "direccion", "secretaria", "tema", "mensaje",
        ]
        widgets = {
            "nombre_apellido": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nombre y Apellido"}),
            "dni": forms.TextInput(attrs={"class": "form-control", "placeholder": "Solo números (sin puntos)"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "Opcional"}),
            "telefono": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej: 3482..."}),
            "barrio": forms.TextInput(attrs={"class": "form-control", "placeholder": "Barrio"}),
            "direccion": forms.TextInput(attrs={"class": "form-control", "placeholder": "Calle y altura"}),
            "secretaria": forms.Select(attrs={"class": "form-control"}),
            "tema": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej: Alumbrado, Bacheo, Basura..."}),
            "mensaje": forms.Textarea(attrs={"class": "form-control", "rows": 5, "placeholder": "Describí el problema con el mayor detalle posible..."}),
        }

    def __init__(self, *args, **kwargs):
        # Recibimos el request para validar la sesión del captcha
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)
        self.fields["secretaria"].queryset = Secretaria.objects.filter(activo=True).order_by("orden", "nombre")
        
        # Hacemos obligatorios los campos clave
        self.fields["dni"].required = True
        self.fields["telefono"].required = True
        self.fields["secretaria"].required = True
        self.fields["tema"].required = True

    def clean_website(self):
        if self.cleaned_data.get("website"):
            raise ValidationError("Spam detectado.")
        return ""

    def clean_dni(self):
        dni = (self.cleaned_data.get("dni") or "").strip().replace(".", "").replace(" ", "")
        if not dni.isdigit():
            raise forms.ValidationError("El DNI debe contener solo números.")
        return dni

    def clean_captcha(self):
        val = (self.cleaned_data.get("captcha") or "").strip()
        
        if not self.request:
            return val
            
        # Recuperamos el código alfanumérico de la sesión
        expected = str(self.request.session.get("captcha_code", "")).strip()
        
        # Validación insensible a mayúsculas/minúsculas
        if not expected or val.lower() != expected.lower():
            raise forms.ValidationError("El código de seguridad es incorrecto.")
        return val


class ConsultaDNIForm(forms.Form):
    dni = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Ingresá tu DNI o Código"}),
        label="DNI o Código",
    )
    captcha = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Código de seguridad", "autocomplete": "off"}),
        label="Seguridad",
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

    def clean_captcha(self):
        val = (self.cleaned_data.get("captcha") or "").strip()
        if not self.request:
            return val
        
        expected = str(self.request.session.get("captcha_code", "")).strip()
        
        if not expected or val.lower() != expected.lower():
            raise forms.ValidationError("El código de seguridad es incorrecto.")
        return val
