# copre_depre_project/urls.py
from django.contrib import admin
from django.urls import path, include
from copre_depre import views  # Importa as visualizações do aplicativo copre_depre
from django.contrib.auth import views as auth_views
from copre_depre.views import custom_logout_view

urlpatterns = [
    path('admin/', admin.site.urls),
    #path('', views.login_view, name='login'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('', include('copre_depre.urls')),  # Inclui URLs da app copre_depre
    path('register/', views.register_view, name='register'),
    path('reset-password/', views.reset_password_view, name='reset_password'),
    path('main/', views.main_view, name='main'),
    path('composition/', views.composition_form_view, name='composition_form'),
    path('composition/<int:composicao_id>/', views.composition_form_view, name='edit_composition'),
    path('insumo/', views.insumo_form_view, name='insumo_form'),
    path('composicoes-cadastradas/', views.composicoes_cadastradas_view, name='composicoes_cadastradas'),
    path ('imprimir-composicao/<int:id>/', views.imprimir_composicao_view, name='imprimir_composicao'),
    path('pesquisar-composicoes/', views.pesquisar_composicoes_view, name='pesquisar_composicoes'),
    path('pesquisar-insumos/', views.pesquisar_insumos_view, name='pesquisar_insumos'),
    path('selecionar-composicoes/', views.selecionar_composicoes_view, name='selecionar_composicoes'),
    path('import-insumos-excel/', views.import_insumos_excel, name='import_insumos_excel'),
]