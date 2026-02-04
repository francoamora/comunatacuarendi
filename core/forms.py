from django import forms
from .models import Historia, Reclamo, Secretaria, Sugerencia

# Widget PRO para múltiples archivos
class MultiFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultiFileField(forms.FileField):
    def clean(self, data, initial=None):
        if not data:
            return []
        if not isinstance(data, (list, tuple)):
            data = [data]
        cleaned = []
        for f in data:
            cleaned.append(super().clean(f, initial))
        return cleaned

# --- FORMULARIOS ---

class HistoriaForm(forms.ModelForm):
    class Meta:
        model = Historia
        fields = ["titulo", "autor", "email", "contenido", "imagen"]
        widgets = {
            "titulo": forms.TextInput(attrs={"class": "form-input", "placeholder": "Ej: El carnaval de 1990"}),
            "autor": forms.TextInput(attrs={"class": "form-input", "placeholder": "Tu nombre completo"}),
            "email": forms.EmailInput(attrs={"class": "form-input", "placeholder": "contacto@ejemplo.com"}),
            "contenido": forms.Textarea(attrs={"class": "form-input", "rows": 4, "placeholder": "Cuéntanos tu historia..."}),
            "imagen": forms.ClearableFileInput(attrs={"class": "form-file"}),
        }


class SugerenciaForm(forms.ModelForm):
    """Formulario para el buzón anónimo con captcha matemático"""
    captcha = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={"class": "form-input", "placeholder": "Respuesta numérica"}),
        label="Seguridad"
    )

    class Meta:
        model = Sugerencia
        fields = ['area', 'mensaje']
        widgets = {
            'area': forms.Select(attrs={'class': 'form-input'}),
            'mensaje': forms.Textarea(attrs={'class': 'form-input', 'rows': 4, 'placeholder': 'Dejanos tu idea, crítica constructiva o sugerencia...'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

    def clean_captcha(self):
        val = (self.cleaned_data.get("captcha") or "").strip()
        if not self.request:
            return val
        expected = str(self.request.session.get("sugerencia_captcha", "")).strip()
        if not expected or val != expected:
            raise forms.ValidationError("La respuesta matemática es incorrecta.")
        return val


class ReclamoForm(forms.ModelForm):
    imagenes = MultiFileField(
        required=False,
        widget=MultiFileInput(attrs={"class": "form-file", "multiple": True}),
        help_text="Podés subir varias fotos (opcional).",
    )

    captcha = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={"class": "form-input", "placeholder": "Ingresá el código"}),
        label="Código de seguridad (*)",
    )

    class Meta:
        model = Reclamo
        fields = [
            "nombre_apellido", "dni", "email", "telefono", 
            "barrio", "direccion", 
            "secretaria", "tema", "mensaje" # Tema simplificado
        ]
        widgets = {
            "nombre_apellido": forms.TextInput(attrs={"class": "form-input", "placeholder": "Nombre y Apellido"}),
            "dni": forms.TextInput(attrs={"class": "form-input", "placeholder": "Solo números (sin puntos)"}),
            "email": forms.EmailInput(attrs={"class": "form-input", "placeholder": "Opcional"}),
            "telefono": forms.TextInput(attrs={"class": "form-input", "placeholder": "Ej: 3482..."}),
            "barrio": forms.TextInput(attrs={"class": "form-input", "placeholder": "Barrio"}),
            "direccion": forms.TextInput(attrs={"class": "form-input", "placeholder": "Calle y Altura"}),
            
            "secretaria": forms.Select(attrs={"class": "form-input"}),
            "tema": forms.TextInput(attrs={"class": "form-input", "placeholder": "Ej: Alumbrado, Bacheo, Basura..."}),
            
            "mensaje": forms.Textarea(attrs={"class": "form-input", "rows": 5, "placeholder": "Describí el problema con el mayor detalle posible..."}),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)
        # Filtramos secretarías activas
        self.fields["secretaria"].queryset = Secretaria.objects.filter(activo=True).order_by("orden", "nombre")
        
        # Campos obligatorios clave
        self.fields["dni"].required = True
        self.fields["telefono"].required = True
        self.fields["secretaria"].required = True
        self.fields["tema"].required = True

    def clean_dni(self):
        dni = (self.cleaned_data.get("dni") or "").strip().replace(".", "").replace(" ", "")
        if not dni.isdigit():
            raise forms.ValidationError("El DNI debe contener solo números.")
        return dni

    def clean_captcha(self):
        val = (self.cleaned_data.get("captcha") or "").strip()
        if not self.request:
            return val
        expected = str(self.request.session.get("captcha_code", "")).strip()
        if not expected or val != expected:
            raise forms.ValidationError("Código incorrecto.")
        return val


class ConsultaDNIForm(forms.Form):
    dni = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={"class": "form-input", "placeholder": "Ingresá tu DNI"}),
        label="DNI (*)",
    )
    captcha = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={"class": "form-input", "placeholder": "Ingresá el código"}),
        label="Código de seguridad (*)",
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

    def clean_captcha(self):
        val = (self.cleaned_data.get("captcha") or "").strip()
        if not self.request:
            return val
        expected = str(self.request.session.get("captcha_code", "")).strip()
        if not expected or val != expected:
            raise forms.ValidationError("Código incorrecto.")
        return val