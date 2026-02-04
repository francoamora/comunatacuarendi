from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views 

from core.views import (
    home,
    escucha_create,
    escucha_gracias,
    escucha_consultar,
    gestion_reclamo_list,
    gestion_reclamo_detail,
    # Nuevas vistas para las páginas "Ver más"
    novedades_list,
    obras_list,
)

urlpatterns = [
    # --- INTERCEPTAR LOGIN DEL ADMIN ---
    path("admin/login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="admin_login"),

    # Panel de Admin (Jazzmin)
    path("admin/", admin.site.urls),

    # Sistema de Autenticación General
    path("accounts/", include("django.contrib.auth.urls")),

    # Página de Inicio
    path("", home, name="home"),

    # --- SECCIONES COMPLETAS (Paginación) ---
    path("gestion-al-dia/", novedades_list, name="novedades_list"),
    path("obras/", obras_list, name="obras_list"),

    # Escucha ciudadana (público)
    path("escucha/", escucha_create, name="escucha_create"),
    path("escucha/gracias/<str:codigo>/", escucha_gracias, name="escucha_gracias"),
    path("escucha/consultar/", escucha_consultar, name="escucha_consultar"),

    # Gestión (solo staff)
    path("gestion/reclamos/", gestion_reclamo_list, name="gestion_reclamo_list"),
    path("gestion/reclamos/<int:pk>/", gestion_reclamo_detail, name="gestion_reclamo_detail"),
]

# Servir archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)