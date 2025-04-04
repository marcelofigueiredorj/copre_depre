# copre_depre/urls.py
from django.contrib.auth import views as auth_views
from django.urls import path, include
from render import render

from . import views
from .models import Composicao

urlpatterns = [
    path('', views.home_view, name='home'),
    path('main/', views.main_view, name='main'),
    path('composition/', views.composition_form_view, name='composition'),
    path('composicoes-cadastradas/', views.composicoes_cadastradas_view, name='composicoes_cadastradas'),
    path('importar-insumos/', views.importar_insumos_view, name='importar_insumos'),
    path('insumos/', views.insumos_view, name='insumos'),
    path('pesquisar-insumos/', views.pesquisar_insumos_view, name='pesquisar_insumos'),
    path('pesquisar-composicoes/', views.pesquisar_composicoes_view, name='pesquisar_composicoes'),
    path('selecionar-composicoes/', views.selecionar_composicoes_view, name='selecionar_composicoes'),
    path('visualizar-composicao/<int:id>/', views.visualizar_composicao_view, name='visualizar_composicao'),
    path('imprimir-composicao/<int:id>/', views.imprimir_composicao_view, name='imprimir_composicao'),
    path('editar-composicao/<int:id>/', views.editar_composicao_view, name='editar_composicao'),
    path('excluir-composicao/<int:id>/', views.excluir_composicao_view, name='excluir_composicao'),
]

def home_view(request):
    return render(request, 'home.html')

def main_view(request):
    return render(request, 'main.html')

def composicoes_cadastradas_view(request):
    composicoes = Composicao.objects.all()
    return render(request, 'composicoes_cadastradas.html', {'composicoes': composicoes})