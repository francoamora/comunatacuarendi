from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponseRedirect, HttpRequest, HttpResponse
from django.utils.crypto import get_random_string
from django.db.models import Q, Count
from django.core.paginator import Paginator
import random

# Importamos Modelos del Proyecto
from .models import (
    Historia, Autoridad, Obra, Tramite, Documento, Novedad, InfoCategoria,
    Reclamo, ReclamoImagen, Servicio, Sugerencia, Video
)
# Importamos Formularios
from .forms import HistoriaForm, ReclamoForm, ConsultaDNIForm, SugerenciaForm

CAPTCHA_SESSION_KEY = "captcha_code"

# =========================
#  UTILIDADES CAPTCHA
# =========================

def _set_captcha(request):
    """Genera un captcha alfanumérico aleatorio de 5 dígitos"""
    code = "".join([get_random_string(1, allowed_chars="0123456789") for _ in range(5)])
    request.session[CAPTCHA_SESSION_KEY] = code
    request.session.modified = True
    return code

def _get_captcha(request):
    """Obtiene el captcha actual o genera uno nuevo si no existe"""
    return request.session.get(CAPTCHA_SESSION_KEY) or _set_captcha(request)

def _set_math_captcha(request, key="sugerencia_captcha"):
    """Genera un captcha matemático simple (Ej: 3+2)"""
    a = random.randint(1, 9)
    b = random.randint(1, 9)
    res = str(a + b)
    request.session[key] = res
    request.session.modified = True
    return f"¿Cuánto es {a} + {b}?"

def _reclamos_allowed(user):
    """Permiso para ver la gestión interna de reclamos"""
    return user.is_authenticated and user.is_active and user.is_staff

# =========================
#  VISTA PRINCIPAL (HOME)
# =========================

def home(request: HttpRequest) -> HttpResponse:
    
    # 1. PROCESAR HISTORIAS (POST)
    if request.method == "POST" and request.POST.get("form_type") == "historia":
        historia_form = HistoriaForm(request.POST, request.FILES)
        if historia_form.is_valid():
            historia = historia_form.save(commit=False)
            historia.aprobado = False # Pendiente de aprobación
            historia.save()
            messages.success(request, "¡Tu historia fue recibida! La revisaremos pronto.")
            return HttpResponseRedirect(reverse("home") + "#historias")
        else:
            messages.error(request, "Error en el formulario de historia. Verificá los datos.")
            sug_form = SugerenciaForm(request=request) # Reiniciamos el otro
    
    # 2. PROCESAR SUGERENCIAS (POST)
    elif request.method == "POST" and request.POST.get("form_type") == "sugerencia":
        sug_form = SugerenciaForm(request.POST, request=request)
        if sug_form.is_valid():
            sug_form.save()
            messages.success(request, "¡Sugerencia recibida! Gracias por ayudarnos a mejorar.")
            return HttpResponseRedirect(reverse("home")) 
        else:
            messages.error(request, "Error en la sugerencia o respuesta de seguridad incorrecta.")
            historia_form = HistoriaForm() # Reiniciamos el otro
    
    else:
        # GET: Inicializar formularios vacíos
        historia_form = HistoriaForm()
        sug_form = SugerenciaForm(request=request)
    
    # Generar etiqueta del captcha para el modal de sugerencias
    sug_captcha_label = _set_math_captcha(request)

    # 3. CARGA DE DATOS (Optimizada)
    autoridad = Autoridad.objects.filter(activo=True).first()
    
    # Datos Principales
    obras = Obra.objects.filter(visible=True).prefetch_related("imagenes").order_by("-fecha_inicio")[:6]
    novedades = Novedad.objects.select_related("tipo").order_by("-fecha")[:6]
    videos = Video.objects.filter(visible=True, destacado=True).order_by("orden", "-fecha")[:6]
    tramites = Tramite.objects.all()[:6]
    documentos = Documento.objects.filter(visible=True).order_by("-fecha_publicacion")[:8]
    
    # Datos de Información y Contacto
    contactos = Servicio.objects.filter(tipo="contacto").order_by("titulo")
    
    # Historias aprobadas
    historias = Historia.objects.filter(aprobado=True).order_by("-fecha_publicacion")[:6]

    context = {
        "form": historia_form,
        "historia_form": historia_form, 
        "sug_form": sug_form,
        "sug_captcha_label": sug_captcha_label,
        "autoridad": autoridad,
        "obras": obras,
        "tramites": tramites,
        "documentos": documentos,
        "servicios_contacto": contactos,
        "historias_publicadas": historias,
        "novedades": novedades,
        "videos": videos,
    }
    return render(request, "core/index.html", context)


# =========================
#  SECCIONES INDIVIDUALES (Paginación)
# =========================

def novedades_list(request: HttpRequest) -> HttpResponse:
    news_list = Novedad.objects.select_related("tipo").order_by("-fecha")
    paginator = Paginator(news_list, 12) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, "core/novedades_list.html", {"novedades": page_obj})


noticias_list = novedades_list

def noticia_detail(request, slug):
    noticia = get_object_or_404(Novedad, slug=slug)
    otras = Novedad.objects.exclude(id=noticia.id)[:3]
    return render(request, "core/noticia_detail.html", {"noticia": noticia, "otras": otras})

def obras_list(request: HttpRequest) -> HttpResponse:
    works_list = Obra.objects.filter(visible=True).prefetch_related("imagenes").order_by("-fecha_inicio")
    paginator = Paginator(works_list, 9) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, "core/obras_list.html", {"obras": page_obj})

def obra_detail(request, slug):
    obra = get_object_or_404(Obra, slug=slug, visible=True)
    galeria = obra.imagenes.all().order_by('orden')
    return render(request, "core/obra_detail.html", {"obra": obra, "galeria": galeria})

def transparencia(request):
    docs = Documento.objects.filter(visible=True).order_by('-fecha_publicacion')
    return render(request, "core/transparencia.html", {"documentos": docs})


# =========================
#  ESCUCHA CIUDADANA (Reclamos)
# =========================

def escucha_create(request: HttpRequest) -> HttpResponse:
    """Creación de reclamo con validación de Captcha"""
    
    if request.method == "POST":
        # Pasamos request para validar la sesión del captcha en el form
        form = ReclamoForm(request.POST, request.FILES, request=request)
        
        if form.is_valid():
            reclamo = form.save()

            imagenes = request.FILES.getlist("imagenes")
            if imagenes:
                ReclamoImagen.objects.bulk_create([
                    ReclamoImagen(reclamo=reclamo, imagen=img, orden=index)
                    for index, img in enumerate(imagenes)
                ])

            # Reseteamos captcha
            _set_captcha(request)
            
            # Redirigimos a la página de éxito
            return redirect("escucha_gracias", codigo=reclamo.codigo)
        
        # Si falla, regeneramos captcha por seguridad
        captcha_code = _set_captcha(request)
    else:
        # GET: Nuevo captcha y formulario limpio
        captcha_code = _set_captcha(request)
        form = ReclamoForm(request=request)

    return render(request, "core/escucha_create.html", {
        "form": form, 
        "captcha_code": captcha_code
    })


def escucha_gracias(request, codigo: str):
    """Pantalla de éxito tras enviar reclamo"""
    reclamo = get_object_or_404(Reclamo, codigo=codigo)
    return render(request, "core/escucha_gracias.html", {"reclamo": reclamo})


def escucha_consultar(request: HttpRequest) -> HttpResponse:
    """
    Buscador de reclamos: 
    - Funciona por GET (Buscador simple del header/home)
    - Funciona por POST (Formulario con DNI y Captcha)
    """
    captcha_code = _get_captcha(request)
    reclamos = None
    busqueda_realizada = False
    
    # 1. Búsqueda por Formulario POST (DNI + Captcha)
    if request.method == "POST":
        form = ConsultaDNIForm(request.POST, request=request)
        if form.is_valid():
            dni = form.cleaned_data["dni"]
            
            # Buscamos por DNI o por CÓDIGO
            reclamos = Reclamo.objects.select_related("secretaria").filter(
                Q(dni=dni) | Q(codigo__iexact=dni)
            ).order_by("-creado_en")
            
            busqueda_realizada = True
            captcha_code = _set_captcha(request)
        else:
            captcha_code = _set_captcha(request)

    # 2. Búsqueda por GET (Input simple "busqueda")
    elif request.method == "GET" and 'busqueda' in request.GET:
        form = ConsultaDNIForm(request=request) # Form vacío
        query = request.GET.get('busqueda').strip()
        if query:
            reclamos = Reclamo.objects.select_related("secretaria").filter(
                Q(dni=query) | Q(codigo__iexact=query)
            ).order_by("-creado_en")
            busqueda_realizada = True

    # 3. Carga inicial GET
    else:
        form = ConsultaDNIForm(request=request)

    return render(
        request, 
        "core/escucha_consultar.html", 
        {
            "form": form, 
            "captcha_code": captcha_code, 
            "reclamos": reclamos,
            "busqueda_realizada": busqueda_realizada
        }
    )


reclamo_create = escucha_create
reclamo_success = escucha_gracias
reclamo_seguimiento = escucha_consultar


# =========================
#  GESTIÓN INTERNA (STAFF)
# =========================

@login_required
@user_passes_test(_reclamos_allowed)
def gestion_reclamo_list(request: HttpRequest) -> HttpResponse:
    """Vista interna para empleados municipales"""
    q = (request.GET.get("q") or "").strip()
    estado = (request.GET.get("estado") or "").strip()

    base_qs = Reclamo.objects.select_related("secretaria", "asignado_a").order_by("-creado_en")

    if estado:
        base_qs = base_qs.filter(estado=estado)

    if q:
        base_qs = base_qs.filter(
            Q(codigo__icontains=q) | 
            Q(dni__icontains=q) | 
            Q(nombre_apellido__icontains=q) |
            Q(telefono__icontains=q)
        )

    # Estadísticas rápidas
    totals = Reclamo.objects.aggregate(
        total=Count("id"),
        recibidos=Count("id", filter=Q(estado=Reclamo.ESTADO_RECIBIDO)),
        en_proceso=Count("id", filter=Q(estado=Reclamo.ESTADO_EN_PROCESO)),
        resueltos=Count("id", filter=Q(estado=Reclamo.ESTADO_RESUELTO)),
    )

    paginator = Paginator(base_qs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "core/gestion_reclamo_list.html",
        {
            "reclamos": page_obj,
            "q": q,
            "estado": estado,
            "estado_choices": Reclamo.ESTADO_CHOICES,
            "filtered_count": paginator.count,
            "totals": totals,
        },
    )

@login_required
@user_passes_test(_reclamos_allowed)
def gestion_reclamo_detail(request, pk: int):
    """Detalle interno de reclamo"""
    reclamo = get_object_or_404(
        Reclamo.objects.select_related("secretaria", "asignado_a").prefetch_related("imagenes", "eventos__creado_por"),
        pk=pk,
    )
    
    # URL al admin de Django para editar
    admin_edit_url = reverse("admin:core_reclamo_change", args=[reclamo.pk])

    return render(
        request,
        "core/gestion_reclamo_detail.html",
        {
            "reclamo": reclamo, 
            "admin_edit_url": admin_edit_url
        },
    )
