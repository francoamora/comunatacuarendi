from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponseRedirect, HttpRequest, HttpResponse
from django.utils.crypto import get_random_string
from django.db.models import Q, Count
from django.core.paginator import Paginator
import random

# Importamos Modelos
from .models import Historia, Autoridad, Obra, Tramite, Servicio, Documento, InfoCategoria, Novedad
from .models import Reclamo, ReclamoImagen, Sugerencia
from .forms import HistoriaForm, ReclamoForm, ConsultaDNIForm, SugerenciaForm

CAPTCHA_SESSION_KEY = "captcha_code"

# =========================
#  UTILIDADES CAPTCHA
# =========================

def _set_captcha(request):
    """Captcha alfanumérico para reclamos"""
    code = "".join([get_random_string(1, allowed_chars="0123456789") for _ in range(5)])
    request.session[CAPTCHA_SESSION_KEY] = code
    request.session.modified = True
    return code

def _get_captcha(request):
    return request.session.get(CAPTCHA_SESSION_KEY) or _set_captcha(request)

def _set_math_captcha(request, key="sugerencia_captcha"):
    """Captcha matemático simple para sugerencias (Ej: 3+2)"""
    a = random.randint(1, 9)
    b = random.randint(1, 9)
    res = str(a + b)
    request.session[key] = res
    request.session.modified = True
    return f"¿Cuánto es {a} + {b}?"

def _reclamos_allowed(user):
    return user.is_authenticated and user.is_active and user.is_staff and user.has_perm("core.view_reclamo")

# =========================
#  VISTAS PÚBLICAS
# =========================

def home(request: HttpRequest) -> HttpResponse:
    
    # 1. PROCESAR HISTORIAS
    if request.method == "POST" and request.POST.get("form_type") == "historia":
        historia_form = HistoriaForm(request.POST, request.FILES)
        if historia_form.is_valid():
            historia = historia_form.save(commit=False)
            historia.aprobado = False
            historia.save()
            messages.success(request, "Tu historia fue recibida. ¡Gracias!")
            return HttpResponseRedirect(reverse("home") + "#historias")
        else:
            messages.error(request, "Error en el formulario de historia.")
    else:
        historia_form = HistoriaForm()

    # 2. PROCESAR SUGERENCIAS (ANÓNIMAS)
    if request.method == "POST" and request.POST.get("form_type") == "sugerencia":
        sug_form = SugerenciaForm(request.POST, request=request)
        if sug_form.is_valid():
            sug_form.save()
            messages.success(request, "¡Sugerencia recibida! Gracias por ayudarnos a mejorar.")
            return HttpResponseRedirect(reverse("home")) 
        else:
            messages.error(request, "Error en la sugerencia o respuesta de seguridad incorrecta.")
    else:
        sug_form = SugerenciaForm()
    
    sug_captcha_label = _set_math_captcha(request)

    # 3. CARGA DE DATOS (HOME LIGERA)
    autoridad = Autoridad.objects.filter(activo=True).first()
    
    # Solo las últimas 6 obras para la portada
    obras = Obra.objects.filter(visible=True).prefetch_related('imagenes').order_by('-fecha_inicio')[:6]
    
    tramites = Tramite.objects.all()
    documentos = Documento.objects.filter(visible=True).order_by('-fecha_publicacion')[:8]
    info_util = InfoCategoria.objects.filter(visible=True).prefetch_related('datos')
    
    contactos = Servicio.objects.filter(tipo="contacto")
    emergencias = Servicio.objects.filter(tipo="emergencia")
    transporte = Servicio.objects.filter(tipo="transporte")
    
    # Solo las últimas 6 noticias para la portada
    novedades = Novedad.objects.all().order_by('-fecha')[:6]
    
    historias = Historia.objects.filter(aprobado=True).order_by("-fecha_publicacion")[:6]

    context = {
        "form": historia_form, 
        "sug_form": sug_form,
        "sug_captcha_label": sug_captcha_label,
        "autoridad": autoridad,
        "obras": obras,
        "tramites": tramites,
        "documentos": documentos,
        "info_util": info_util,
        "servicios_contacto": contactos,
        "servicios_emergencia": emergencias,
        "servicios_transporte": transporte,
        "historias_publicadas": historias,
        "novedades": novedades, 
    }
    return render(request, "core/index.html", context)


# --- NUEVAS VISTAS PARA "VER MÁS" (PAGINACIÓN) ---

def novedades_list(request: HttpRequest) -> HttpResponse:
    """Muestra todas las novedades con paginación"""
    news_list = Novedad.objects.all().order_by('-fecha')
    
    # Paginación: 12 noticias por página
    paginator = Paginator(news_list, 12) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, "core/novedades_list.html", {"novedades": page_obj})


def obras_list(request: HttpRequest) -> HttpResponse:
    """Muestra todas las obras con paginación"""
    works_list = Obra.objects.filter(visible=True).prefetch_related('imagenes').order_by('-fecha_inicio')
    
    # Paginación: 9 obras por página (grilla de 3x3)
    paginator = Paginator(works_list, 9) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, "core/obras_list.html", {"obras": page_obj})


# =========================
#  ESCUCHA CIUDADANA
# =========================

def escucha_create(request: HttpRequest) -> HttpResponse:
    captcha_code = _get_captcha(request)

    if request.method == "POST":
        form = ReclamoForm(request.POST, request.FILES, request=request)
        if form.is_valid():
            reclamo = form.save()

            imagenes = request.FILES.getlist("imagenes")
            if imagenes:
                ReclamoImagen.objects.bulk_create([
                    ReclamoImagen(reclamo=reclamo, imagen=img) for img in imagenes
                ])

            _set_captcha(request)
            return redirect("escucha_gracias", codigo=reclamo.codigo)
        
        captcha_code = _set_captcha(request)
    else:
        form = ReclamoForm(request=request)

    return render(request, "core/escucha_create.html", {"form": form, "captcha_code": captcha_code})


def escucha_gracias(request, codigo: str):
    reclamo = get_object_or_404(Reclamo, codigo=codigo)
    return render(request, "core/escucha_gracias.html", {"reclamo": reclamo})


def escucha_consultar(request: HttpRequest) -> HttpResponse:
    captcha_code = _get_captcha(request)
    reclamos = None

    if request.method == "POST":
        form = ConsultaDNIForm(request.POST, request=request)
        if form.is_valid():
            dni = form.cleaned_data["dni"]
            reclamos = (
                Reclamo.objects.filter(dni=dni)
                .select_related("secretaria")
                .prefetch_related("imagenes")
                .order_by("-creado_en")
            )
            captcha_code = _set_captcha(request)
        else:
            captcha_code = _set_captcha(request)
    else:
        form = ConsultaDNIForm(request=request)

    return render(
        request, 
        "core/escucha_consultar.html", 
        {"form": form, "captcha_code": captcha_code, "reclamos": reclamos}
    )

# =========================
#  GESTIÓN INTERNA (STAFF)
# =========================

@login_required
@user_passes_test(_reclamos_allowed)
def gestion_reclamo_list(request: HttpRequest) -> HttpResponse:
    q = (request.GET.get("q") or "").strip()
    estado = (request.GET.get("estado") or "").strip()

    base_qs = (
        Reclamo.objects.all()
        .select_related("secretaria", "asignado_a")
        .order_by("-creado_en")
    )

    if estado:
        base_qs = base_qs.filter(estado=estado)

    if q:
        base_qs = base_qs.filter(
            Q(codigo__icontains=q) | 
            Q(dni__icontains=q) | 
            Q(nombre_apellido__icontains=q) |
            Q(telefono__icontains=q)
        )

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
    reclamo = get_object_or_404(
        Reclamo.objects.select_related("secretaria", "asignado_a")
        .prefetch_related("imagenes", "eventos__creado_por"),
        pk=pk,
    )

    can_edit = request.user.has_perm("core.change_reclamo")
    admin_edit_url = reverse("admin:core_reclamo_change", args=[reclamo.pk]) if can_edit else None

    return render(
        request,
        "core/gestion_reclamo_detail.html",
        {"reclamo": reclamo, "admin_edit_url": admin_edit_url, "can_edit": can_edit},
    )