from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Autoridad, Obra, ObraImagen, Tramite, Servicio, Historia, Documento,
    Secretaria, Reclamo, ReclamoImagen, ReclamoEvento,
    InfoCategoria, InfoDato, Sugerencia, 
    Novedad, CategoriaNovedad, Video
)

# --- SUGERENCIAS ---
@admin.register(Sugerencia)
class SugerenciaAdmin(admin.ModelAdmin):
    list_display = ('area', 'fecha', 'leido')
    list_filter = ('leido', 'area')
    readonly_fields = ('fecha', 'mensaje')
    list_editable = ('leido',)

# --- HISTORIAS ---
@admin.register(Historia)
class HistoriaAdmin(admin.ModelAdmin):
    list_display = ("titulo", "autor", "aprobado", "fecha_publicacion")
    list_filter = ("aprobado",)
    list_editable = ("aprobado",)
    search_fields = ("titulo", "autor", "email")

# --- OBRAS ---
class ObraImagenInline(admin.TabularInline):
    model = ObraImagen
    extra = 1

@admin.register(Obra)
class ObraAdmin(admin.ModelAdmin):
    list_display = ("titulo", "categoria", "visible", "fecha_inicio")
    list_filter = ("visible", "categoria")
    search_fields = ("titulo",)
    inlines = [ObraImagenInline]

# --- GESTIÓN AL DÍA (NOVEDADES) ---
# 1. Registramos las categorías para poder crearlas
@admin.register(CategoriaNovedad)
class CategoriaNovedadAdmin(admin.ModelAdmin):
    list_display = ('nombre',)

# 2. Registramos las novedades con los campos opcionales
@admin.register(Novedad)
class NovedadAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'tipo', 'fecha', 'destacada', 'ver_imagen')
    list_filter = ('tipo', 'destacada', 'fecha')
    search_fields = ('titulo', 'bajada')
    date_hierarchy = 'fecha'
    ordering = ('-fecha',)

    def ver_imagen(self, obj):
        if obj.imagen:
            return format_html('<img src="{}" style="width: 50px; height: auto; border-radius: 4px;" />', obj.imagen.url)
        return "-"
    ver_imagen.short_description = "Portada"


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ("titulo", "categoria", "fecha", "destacado", "visible", "orden", "ver_portada")
    list_filter = ("categoria", "destacado", "visible", "fecha")
    list_editable = ("destacado", "visible", "orden")
    search_fields = ("titulo", "bajada", "url")
    date_hierarchy = "fecha"
    ordering = ("orden", "-fecha")

    def ver_portada(self, obj):
        if obj.portada:
            return format_html('<img src="{}" style="width: 64px; height: 42px; object-fit: cover; border-radius: 6px;" />', obj.portada.url)
        return "-"
    ver_portada.short_description = "Portada"

# --- SERVICIOS / CONTACTOS ---
@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ("titulo", "tipo", "encargado", "telefono")
    list_filter = ("tipo",)
    search_fields = ("titulo", "encargado")
    fieldsets = (
        ("Principal", {"fields": ("titulo", "tipo", "icono")}),
        ("Datos de Contacto", {"fields": ("encargado", "telefono", "email", "horario", "direccion")}),
        ("Legacy (Opcional)", {"fields": ("descripcion",), "classes": ("collapse",)}),
    )

# --- TRÁMITES & INFO ---
@admin.register(Tramite)
class TramiteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'responsable', 'telefono_area')
    search_fields = ('nombre', 'descripcion_breve')

@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'tipo', 'fecha_publicacion', 'visible')
    list_filter = ('tipo', 'visible', 'fecha_publicacion')
    search_fields = ('titulo',)

class InfoDatoInline(admin.TabularInline):
    model = InfoDato
    extra = 1

@admin.register(InfoCategoria)
class InfoCategoriaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'color', 'orden', 'visible')
    list_editable = ('orden', 'visible')
    inlines = [InfoDatoInline]

# --- AUTORIDADES ---
@admin.register(Autoridad)
class AutoridadAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'cargo', 'activo', 'ver_foto')
    list_editable = ('activo',)
    
    def ver_foto(self, obj):
        if obj.foto:
            return format_html('<img src="{}" style="height: 40px; border-radius: 50%;" />', obj.foto.url)
        return "-"

# --- RECLAMOS ---
@admin.register(Secretaria)
class SecretariaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "activo", "orden")
    list_editable = ("activo", "orden")
    search_fields = ("nombre",)

class ReclamoImagenInline(admin.TabularInline):
    model = ReclamoImagen
    extra = 0
    readonly_fields = ("ver_imagen",)
    
    def ver_imagen(self, obj):
        if obj.imagen:
            return format_html('<a href="{0}" target="_blank"><img src="{0}" style="height: 100px;"/></a>', obj.imagen.url)
        return ""

class ReclamoEventoInline(admin.TabularInline):
    model = ReclamoEvento
    extra = 0
    fields = ("creado_en", "estado_anterior", "estado_nuevo", "comentario_publico", "comentario_interno", "creado_por")
    readonly_fields = ("creado_en", "estado_anterior", "estado_nuevo", "creado_por")
    can_delete = False

@admin.register(Reclamo)
class ReclamoAdmin(admin.ModelAdmin):
    list_display = ("codigo", "dni", "tema", "secretaria", "estado", "actualizado_en")
    list_filter = ("estado", "secretaria")
    search_fields = ("codigo", "dni", "nombre_apellido", "telefono", "email", "tema")
    list_editable = ("estado",)
    readonly_fields = ("codigo", "creado_en", "actualizado_en")
    list_select_related = ("secretaria", "asignado_a")
    date_hierarchy = "creado_en"

    fieldsets = (
        ("Identificación", {"fields": ("codigo", "estado", "prioridad", "creado_en", "actualizado_en")}),
        ("Datos del ciudadano", {"fields": ("nombre_apellido", "dni", "telefono", "email", "barrio", "direccion")}),
        ("Clasificación", {"fields": ("secretaria", "tema", "asignado_a")}),
        ("Contenido", {"fields": ("mensaje",)}),
        ("Seguimiento", {"fields": ("respuesta_publica", "nota_interna")}),
    )

    inlines = [ReclamoImagenInline, ReclamoEventoInline]
