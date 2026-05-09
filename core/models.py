from django.db import models
from django.conf import settings
from django.utils import timezone
from ckeditor.fields import RichTextField
from urllib.parse import quote, urlparse, parse_qs

# =========================
# AUTORIDADES Y OBRAS
# =========================

class Autoridad(models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Nombre Completo")
    cargo = models.CharField(max_length=100, default="Presidente Comunal")
    mensaje = RichTextField(verbose_name="Mensaje de Bienvenida")
    foto = models.ImageField(upload_to="autoridades/", verbose_name="Foto de Perfil")
    firma = models.ImageField(
        upload_to="autoridades/firmas/", 
        verbose_name="Firma (PNG Transparente)", 
        null=True, blank=True,
        help_text="Subí una imagen de tu firma en formato PNG con fondo transparente."
    )
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Autoridades"

    def __str__(self):
        return f"{self.nombre} - {self.cargo}"


class Obra(models.Model):
    CATEGORIAS = [
        ('infraestructura', 'Obras Públicas'),
        ('educacion', 'Educación'),
        ('deporte', 'Deportes'),
        ('salud', 'Salud y Ambiente'),
        ('otros', 'Otros'),
    ]

    titulo = models.CharField(max_length=200)
    categoria = models.CharField(max_length=20, choices=CATEGORIAS, default='infraestructura')
    descripcion_corta = models.CharField(max_length=300, help_text="Resumen para la tarjeta")
    imagen = models.ImageField(upload_to="obras/", help_text="Imagen de portada")
    fecha_inicio = models.DateField(auto_now_add=True)
    visible = models.BooleanField(default=True)

    def __str__(self):
        return self.titulo


class ObraImagen(models.Model):
    obra = models.ForeignKey(Obra, on_delete=models.CASCADE, related_name="imagenes")
    imagen = models.ImageField(upload_to="obras/galeria/")
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['orden']
        verbose_name = "Imagen de Galería"
        verbose_name_plural = "Galería de la Obra"


# =========================
# GESTIÓN AL DÍA (NOVEDADES)
# =========================

class CategoriaNovedad(models.Model):
    """Modelo para crear tipos de novedades desde el Admin"""
    nombre = models.CharField(max_length=50, unique=True, verbose_name="Nombre de la Categoría")
    
    class Meta:
        verbose_name = "Categoría de Novedad"
        verbose_name_plural = "Categorías de Novedades"

    def __str__(self):
        return self.nombre


class Novedad(models.Model):
    titulo = models.CharField(max_length=200)
    
    # Ahora usamos ForeignKey para que sea editable
    tipo = models.ForeignKey(
        CategoriaNovedad, 
        on_delete=models.PROTECT, 
        verbose_name="Categoría"
    )
    
    # Campos opcionales para carga rápida (solo foto)
    bajada = models.CharField(
        max_length=300, 
        verbose_name="Resumen breve", 
        blank=True, null=True,
        help_text="Opcional. Texto corto para la tarjeta."
    )
    contenido = RichTextField(
        verbose_name="Desarrollo de la noticia", 
        blank=True, null=True,
        help_text="Opcional. Texto completo si el usuario hace clic."
    )
    
    imagen = models.ImageField(upload_to="novedades/", blank=True, null=True)
    fecha = models.DateField(default=timezone.now)
    destacada = models.BooleanField(default=False)

    class Meta:
        ordering = ['-fecha']
        verbose_name = "Novedad / Gestión"
        verbose_name_plural = "Gestión al Día"

    def __str__(self):
        return self.titulo


class Video(models.Model):
    CATEGORIAS = [
        ("obras", "Obras"),
        ("gestion", "Gestión"),
        ("comunidad", "Comunidad"),
        ("eventos", "Eventos"),
        ("entrevistas", "Entrevistas"),
    ]

    titulo = models.CharField(max_length=200)
    bajada = models.CharField(max_length=260, blank=True, verbose_name="Texto breve")
    url = models.URLField(verbose_name="URL del video")
    portada = models.ImageField(upload_to="videos/", blank=True, null=True, verbose_name="Portada")
    categoria = models.CharField(max_length=20, choices=CATEGORIAS, default="gestion")
    fecha = models.DateField(default=timezone.now)
    destacado = models.BooleanField(default=True)
    visible = models.BooleanField(default=True)
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["orden", "-fecha"]
        verbose_name = "Video"
        verbose_name_plural = "Videos"

    def __str__(self):
        return self.titulo

    @property
    def embed_url(self):
        parsed = urlparse(self.url)
        host = parsed.netloc.lower().replace("www.", "")
        path_parts = [part for part in parsed.path.strip("/").split("/") if part]
        query = parse_qs(parsed.query)

        if "youtu.be" in host and path_parts:
            return f"https://www.youtube.com/embed/{path_parts[0]}?rel=0"

        if "youtube.com" in host:
            video_id = query.get("v", [""])[0]
            if not video_id and len(path_parts) >= 2 and path_parts[0] in {"shorts", "embed"}:
                video_id = path_parts[1]
            if video_id:
                return f"https://www.youtube.com/embed/{video_id}?rel=0"

        if "vimeo.com" in host and path_parts:
            return f"https://player.vimeo.com/video/{path_parts[-1]}"

        if "facebook.com" in host or "fb.watch" in host:
            encoded_url = quote(self.url, safe="")
            return f"https://www.facebook.com/plugins/video.php?href={encoded_url}&show_text=false&width=960"

        if "instagram.com" in host and len(path_parts) >= 2 and path_parts[0] in {"p", "reel", "tv"}:
            return f"https://www.instagram.com/{path_parts[0]}/{path_parts[1]}/embed"

        return ""


# =========================
# TRÁMITES & INFO ÚTIL
# =========================

class Tramite(models.Model):
    nombre = models.CharField(max_length=100)
    icono = models.CharField(max_length=50, help_text="Clase FontAwesome")
    descripcion_breve = models.CharField(max_length=150)
    requisitos = models.TextField(blank=True, help_text="Lista de qué llevar")
    horario_atencion = models.CharField(max_length=100, blank=True)
    responsable = models.CharField(max_length=100, blank=True)
    telefono_area = models.CharField(max_length=50, blank=True)
    archivo_pdf = models.FileField(upload_to="tramites/", null=True, blank=True, verbose_name="Formulario PDF")

    def __str__(self):
        return self.nombre


class Documento(models.Model):
    TIPO_DOC = [
        ('balance', 'Balance Contable'),
        ('ordenanza', 'Ordenanza / Resolución'),
        ('boletin', 'Boletín Oficial'),
        ('licitacion', 'Licitación'),
        ('otro', 'Otro'),
    ]
    titulo = models.CharField(max_length=200)
    tipo = models.CharField(max_length=20, choices=TIPO_DOC, default='otro')
    archivo = models.FileField(upload_to="transparencia/")
    fecha_publicacion = models.DateField(default=timezone.now)
    visible = models.BooleanField(default=True)

    class Meta:
        ordering = ['-fecha_publicacion']
        verbose_name = "Documento de Transparencia"
        verbose_name_plural = "Documentos de Transparencia"

    def __str__(self):
        return self.titulo


class InfoCategoria(models.Model):
    COLORES = [
        ('red', 'Rojo'), ('blue', 'Azul'), ('green', 'Verde'),
        ('orange', 'Naranja'), ('purple', 'Violeta'), ('gray', 'Gris'),
    ]
    titulo = models.CharField(max_length=100)
    icono = models.CharField(max_length=50)
    color = models.CharField(max_length=20, choices=COLORES, default='green')
    orden = models.PositiveIntegerField(default=0)
    visible = models.BooleanField(default=True)

    class Meta:
        ordering = ['orden']
        verbose_name = "Tarjeta de Información"
        verbose_name_plural = "Tarjetas de Información (Info Útil)"

    def __str__(self):
        return self.titulo

    def get_bg_color(self):
        return {'red': '#fee2e2', 'blue': '#e0f2fe', 'green': '#dcfce7', 'orange': '#fef3c7', 'purple': '#f3e8ff', 'gray': '#f1f5f9'}.get(self.color, '#f1f5f9')

    def get_text_color(self):
        return {'red': '#ef4444', 'blue': '#0ea5e9', 'green': '#16a34a', 'orange': '#d97706', 'purple': '#9333ea', 'gray': '#475569'}.get(self.color, '#64748b')


class InfoDato(models.Model):
    categoria = models.ForeignKey(InfoCategoria, on_delete=models.CASCADE, related_name="datos")
    texto = models.CharField(max_length=255)
    icono_item = models.CharField(max_length=50, default="fa-solid fa-check")
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['orden']


# =========================
# CONTACTOS ESTRUCTURADOS
# =========================

class Servicio(models.Model):
    TIPO_CHOICES = [
        ("contacto", "Área / Secretaría"),
        ("emergencia", "Emergencia"),
        ("transporte", "Transporte"),
    ]
    
    titulo = models.CharField(max_length=100, verbose_name="Nombre del Área / Servicio")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    icono = models.CharField(max_length=50, default="fa-solid fa-building")
    
    encargado = models.CharField(max_length=100, blank=True, verbose_name="Encargado/a")
    telefono = models.CharField(max_length=50, blank=True, verbose_name="Teléfono / WhatsApp")
    email = models.EmailField(blank=True, verbose_name="Email de contacto")
    horario = models.CharField(max_length=100, blank=True, verbose_name="Días y Horarios")
    direccion = models.CharField(max_length=150, blank=True, verbose_name="Dirección Física")
    descripcion = models.TextField(blank=True, help_text="Descripción extra si hace falta")

    class Meta:
        verbose_name = "Contacto / Servicio"
        verbose_name_plural = "Contactos y Servicios"

    def __str__(self):
        return f"{self.titulo} ({self.get_tipo_display()})"


class Historia(models.Model):
    titulo = models.CharField(max_length=200)
    autor = models.CharField(max_length=100)
    email = models.EmailField()
    contenido = RichTextField()
    imagen = models.ImageField(upload_to="historias/", null=True, blank=True)
    fecha_publicacion = models.DateTimeField(auto_now_add=True)
    aprobado = models.BooleanField(default=False)

    class Meta:
        ordering = ["-fecha_publicacion"]

    def __str__(self):
        return f"{self.titulo} - {self.autor}"


# =========================
# ESCUCHA CIUDADANA & SUGERENCIAS
# =========================

class Secretaria(models.Model):
    nombre = models.CharField(max_length=80, unique=True)
    activo = models.BooleanField(default=True)
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["orden", "nombre"]
        verbose_name = "Secretaría"
        verbose_name_plural = "Secretarías"

    def __str__(self):
        return self.nombre


class Sugerencia(models.Model):
    AREA_CHOICES = [
        ('general', 'General'),
        ('obras', 'Obras y Servicios'),
        ('cultura', 'Cultura y Deporte'),
        ('atencion', 'Atención al Público'),
        ('seguridad', 'Seguridad'),
    ]
    area = models.CharField(max_length=20, choices=AREA_CHOICES, default='general')
    mensaje = models.TextField(verbose_name="Tu sugerencia")
    fecha = models.DateTimeField(auto_now_add=True)
    leido = models.BooleanField(default=False)

    class Meta:
        ordering = ['-fecha']
        verbose_name = "Sugerencia Anónima"
        verbose_name_plural = "Buzón de Sugerencias"

    def __str__(self):
        return f"Sugerencia {self.get_area_display()} - {self.fecha.strftime('%d/%m/%Y')}"


class Reclamo(models.Model):
    ESTADO_RECIBIDO = "recibido"
    ESTADO_EN_PROCESO = "en_proceso"
    ESTADO_RESUELTO = "resuelto"

    ESTADO_CHOICES = [
        (ESTADO_RECIBIDO, "Recibido"),
        (ESTADO_EN_PROCESO, "En proceso"),
        (ESTADO_RESUELTO, "Resuelto"),
    ]

    codigo = models.CharField(max_length=20, unique=True, blank=True)
    nombre_apellido = models.CharField(max_length=120)
    dni = models.CharField(max_length=12, db_index=True)
    email = models.EmailField(blank=True)
    barrio = models.CharField(max_length=80, blank=True)
    direccion = models.CharField(max_length=120, blank=True)
    telefono = models.CharField(max_length=30, blank=True)

    secretaria = models.ForeignKey(Secretaria, on_delete=models.PROTECT, related_name="reclamos")
    tema = models.CharField(
        max_length=100, 
        verbose_name="Tema del Reclamo",
        help_text="Ej: Alumbrado, Bacheo, Basura, Ruidos molestos..."
    )

    mensaje = models.TextField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default=ESTADO_RECIBIDO)
    prioridad = models.PositiveIntegerField(default=3)

    asignado_a = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="reclamos_asignados",
    )

    nota_interna = models.TextField(blank=True)
    respuesta_publica = models.TextField(blank=True)

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-creado_en"]
        verbose_name = "Reclamo"
        verbose_name_plural = "Reclamos"

    def __str__(self):
        return f"{self.codigo} - {self.tema}"

    def save(self, *args, **kwargs):
        creando = self.pk is None
        super().save(*args, **kwargs)
        if creando and not self.codigo:
            year = timezone.now().year
            codigo = f"TAC-{year}-{self.pk:06d}"
            self.codigo = codigo
            Reclamo.objects.filter(pk=self.pk).update(codigo=codigo)


class ReclamoImagen(models.Model):
    reclamo = models.ForeignKey(Reclamo, on_delete=models.CASCADE, related_name="imagenes")
    imagen = models.ImageField(upload_to="reclamos/")
    orden = models.PositiveIntegerField(default=0)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["orden", "creado_en"]

class ReclamoEvento(models.Model):
    reclamo = models.ForeignKey(Reclamo, on_delete=models.CASCADE, related_name="eventos")
    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    estado_anterior = models.CharField(max_length=20, blank=True)
    estado_nuevo = models.CharField(max_length=20, blank=True)
    comentario_interno = models.TextField(blank=True)
    comentario_publico = models.TextField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creado_en"]
