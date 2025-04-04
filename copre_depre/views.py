# copre_depre/views.py
import datetime

from django.contrib.staticfiles import finders
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.db import transaction
from reportlab.lib.pagesizes import A4, letter
from reportlab.pdfgen import canvas
import os
import logging
import pandas as pd
from decimal import Decimal
import json
from django.http import HttpResponse
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from copre_depre.utils import export_to_pdf  # Modelo padrão do Django
from .forms import LoginForm, RegisterForm, ResetPasswordForm, ComposicaoForm, InsumoForm, ComposicaoInsumoFormSet
from .models import Composicao, ComposicaoInsumo, Insumo

# Configura logging
logger = logging.getLogger (__name__)


def selecionar_composicoes_view(request):
    if not request.user.is_authenticated:
        return redirect ('login')

    if request.method == "POST":
        selected_ids = request.POST.getlist ('selected')
        if not selected_ids:
            messages.error (request, "Nenhuma composição selecionada!")
        else:
            composicoes = Composicao.objects.filter (id__in=selected_ids)
            export_to_pdf ([c.__dict__ for c in composicoes])
            messages.success (request, "PDF gerado com sucesso!")
        return redirect ('selecionar_composicoes')

    composicoes = Composicao.objects.all ()
    return render (request, 'selecionar_composicoes.html', {'composicoes': composicoes})


def login_view(request):
    if request.method == "POST":
        form = LoginForm (request.POST)
        if form.is_valid ():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate (request, username=username, password=password)
            if user is not None:
                login (request, user)
                return redirect ('main')
            else:
                messages.error (request, "Usuário ou senha inválidos!")
    else:
        form = LoginForm ()
    return render (request, 'login.html', {'form': form})


def register_view(request):
    if request.method == "POST":
        form = RegisterForm (request.POST)
        if form.is_valid ():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            if User.objects.filter (username=username).exists ():
                messages.error (request, "Usuário já existe!")
            else:
                user = User.objects.create_user (username=username, password=password)
                user.save ()
                messages.success (request, "Usuário cadastrado com sucesso!")
                return redirect ('login')
        else:
            messages.error (request, "Erro no cadastro!")
    else:
        form = RegisterForm ()
    return render (request, 'register.html', {'form': form})


def reset_password_view(request):
    if request.method == "POST":
        form = ResetPasswordForm (request.POST)
        if form.is_valid ():
            username = form.cleaned_data['username']
            try:
                user = User.objects.get (username=username)
                user.set_password ("senha123")
                user.save ()
                messages.success (request, "Senha redefinida para 'senha123'!")
            except User.DoesNotExist:
                messages.error (request, "Usuário não encontrado!")
            return redirect ('login')
    else:
        form = ResetPasswordForm ()
    return render (request, 'login.html', {'reset_form': form})


def logout_view(request):
    logout (request)
    return redirect ('login')


def main_view(request):
    if not request.user.is_authenticated:
        return redirect ('login')
    return render (request, 'main.html')


@login_required
def visualizar_composicao_view(request, id):
    composicao = get_object_or_404 (Composicao, id=id)
    print (f"Visualizar Composição: {composicao.__dict__}")  # Log para depuração
    print (
        f"ComposicaoInsumo associados: {list (composicao.composicaoinsumo_set.all ())}")  # Log para verificar insumos
    return render (request, 'visualizar_composicao.html', {'composicao': composicao})


@login_required
def editar_composicao_view(request, id):
    composicao = get_object_or_404 (Composicao, id=id)
    if request.method == 'POST':
        composicao.solicitante = request.POST.get ('solicitante')
        composicao.autor = request.POST.get ('autor')
        composicao.unidade = request.POST.get ('unidade')
        composicao.data = request.POST.get ('data')
        composicao.codigo = request.POST.get ('codigo')
        composicao.numero = request.POST.get ('numero')
        composicao.obra = request.POST.get ('obra')
        composicao.descricao = request.POST.get ('descricao')
        composicao.io = request.POST.get ('io')
        composicao.save ()
        # Recalcula o valor_total após salvar
        composicao.calculate_valor_total ()
        return redirect ('selecionar_composicoes')
    print (f"Editar Composição: {composicao.__dict__}")  # Log para depuração
    print (
        f"ComposicaoInsumo associados: {list (composicao.composicaoinsumo_set.all ())}")  # Log para verificar insumos
    return render (request, 'editar_composicao.html', {'composicao': composicao})


@login_required
def excluir_composicao_view(request, id):
    composicao = get_object_or_404 (Composicao, id=id)
    if request.method == 'POST':
        composicao.delete ()
        return redirect ('selecionar_composicoes')
    return redirect ('selecionar_composicoes')


@login_required
def composition_form_view(request, composicao_id=None):
    if not request.user.is_authenticated:
        return redirect ('login')

    logger.debug ("Iniciando composition_form_view")

    if composicao_id:
        composicao = Composicao.objects.get (id=composicao_id)
        form = ComposicaoForm (request.POST or None, instance=composicao)
        formset = ComposicaoInsumoFormSet (request.POST or None, instance=composicao)
    else:
        form = ComposicaoForm (request.POST or None)
        formset = ComposicaoInsumoFormSet (request.POST or None)

    insumos_data = {
        str (insumo.id): {
            'codigo': insumo.codigo,
            'un': insumo.unidade,
            'data_custo': insumo.data_custo.strftime ('%d/%m/%Y') if insumo.data_custo else '',
            'valor': str (insumo.valor)
        } for insumo in Insumo.objects.all ()
    }

    if request.method == "POST":
        logger.debug ("Requisição POST recebida")
        logger.debug (f"Dados do formulário: {request.POST}")

        if form.is_valid () and formset.is_valid ():
            try:
                with transaction.atomic ():
                    composicao = form.save ()
                    logger.debug (f"Composição salva: {composicao.id}")

                    formset.instance = composicao
                    formset.save ()

                    insumos = ComposicaoInsumo.objects.filter (composicao=composicao)
                    logger.debug (f"Insumos encontrados: {list (insumos.values ())}")

                    total = sum (
                        Decimal (str (ci.quantidade)) * Decimal (str (ci.valor))
                        for ci in insumos
                        if ci.quantidade is not None and ci.valor is not None
                    )
                    composicao.valor_total = total
                    composicao.save (update_fields=['valor_total'])  # Atualiza apenas o campo valor_total
                    logger.debug (f"Valor total atualizado: {total}")

                    composicao_data = {
                        'solicitante': composicao.solicitante,
                        'autor': composicao.autor,
                        'unidade': composicao.unidade,
                        'data': composicao.data,
                        'codigo': composicao.codigo,
                        'numero': composicao.numero,
                        'obra': composicao.obra,
                        'descricao': composicao.descricao,
                        'io': composicao.io,
                        'valor_total': f"{composicao.valor_total:.2f}",  # Formata com 2 casas decimais
                        'insumos': [
                            {
                                'insumo': ci.insumo.insumo if ci.insumo else '',
                                'codigo': ci.codigo or '',
                                'un': ci.un or '',
                                'quantidade': str (ci.quantidade) if ci.quantidade is not None else '0',
                                'data_custo': ci.data_custo.strftime ('%d/%m/%Y') if ci.data_custo else '',
                                'valor': str (ci.valor) if ci.valor is not None else '0.00'
                            } for ci in insumos
                        ]
                    }
                    logger.debug (f"Dados para PDF: {composicao_data}")

                export_to_pdf (composicao_data)
                messages.success (request, "Composição salva com sucesso!")
                logger.debug ("Redirecionando para composicoes_cadastradas")
                return redirect ('composicoes_cadastradas')
            except Exception as e:
                logger.error (f"Erro ao salvar ou exportar: {str (e)}")
                messages.error (request, f"Erro ao salvar a composição: {str (e)}")
        else:
            logger.debug ("Formulário inválido")
            logger.debug (f"Erros do form: {form.errors}")
            logger.debug (f"Erros do formset: {formset.errors}")
            messages.error (request, "Erro ao validar o formulário. Verifique os campos.")

    return render (request, 'composition_form.html', {
        'form': form,
        'formset': formset,
        'insumos_json': json.dumps (insumos_data)
    })


@login_required
def insumo_form_view(request):
    if not request.user.is_authenticated:
        return redirect ('login')

    if request.method == "POST":
        form = InsumoForm (request.POST)
        if form.is_valid ():
            form.save ()
            messages.success (request, "Insumo cadastrado com sucesso!")
            return redirect ('insumo_form')
        else:
            messages.error (request, "Erro ao cadastrar insumo!")
    else:
        form = InsumoForm ()
    return render (request, 'insumo_form.html', {'form': form})


@login_required
def composicoes_cadastradas_view(request):
    if not request.user.is_authenticated:
        return redirect ('login')

    composicoes = Composicao.objects.all ()
    return render (request, 'composicoes_cadastradas.html', {'composicoes': composicoes})


@login_required
def pesquisar_composicoes_view(request):
    logger.debug (f"Requisição recebida: {request.method}")

    if request.method == "GET":
        query = request.GET.get ('q', '')
        composicoes = Composicao.objects.filter (
            Q (codigo__icontains=query) |
            Q (descricao__icontains=query) |
            Q (numero__icontains=query)
        ) if query else Composicao.objects.all ()
        logger.debug (f"Composições encontradas: {composicoes.count ()}")
        return render (request, 'pesquisar_composicoes.html', {'composicoes': composicoes, 'query': query})

    if request.method == "POST":
        logger.debug (f"Dados do POST: {dict (request.POST)}")
        if 'export_pdf' in request.POST:
            logger.debug ("Botão 'Exportar para PDF' detectado!")
            selected_ids = request.POST.getlist ('selected')
            logger.debug (f"IDs selecionados: {selected_ids}")

            if not selected_ids:
                messages.error (request, "Nenhuma composição selecionada!")
                logger.debug ("Nenhuma composição selecionada.")
                return redirect ('pesquisar_composicoes')

            try:
                composicoes_selecionadas = Composicao.objects.filter (
                    id__in=selected_ids
                ).prefetch_related ('composicaoinsumo_set')
                logger.debug (f"Composições selecionadas: {list (composicoes_selecionadas.values ('id', 'codigo'))}")

                # Gerar PDF
                buffer = BytesIO ()
                doc = SimpleDocTemplate (
                    buffer,
                    pagesize=letter,
                    leftMargin=0.5 * inch,
                    rightMargin=0.5 * inch,
                    topMargin=0.5 * inch,
                    bottomMargin=0.5 * inch
                )
                elementos = []

                estilos = getSampleStyleSheet ()
                estilo_titulo = ParagraphStyle (
                    'Titulo',
                    parent=estilos['Heading1'],
                    fontSize=16,
                    textColor=colors.darkblue,
                    alignment=1
                )
                estilo_normal = estilos['Normal']
                estilo_normal.fontSize = 10

                # Adicionar cabeçalho
                caminho_logo = finders.find ('images/emop_branco_g1.png')
                if caminho_logo:
                    logger.debug (f"Logo encontrado: {caminho_logo}")
                    logo = Image (caminho_logo, width=2 * inch, height=1 * inch)
                    logo.hAlign = 'CENTER'
                    elementos.append (logo)
                else:
                    logger.warning ("Logo não encontrado nos arquivos estáticos")

                elementos.append (Paragraph ("COORDENADORIA DE PREÇOS - COPRE", estilo_titulo))
                elementos.append (Paragraph ("DEPARTAMENTO DE APROPRIAÇÃO DE PREÇOS - DEPRE", estilo_normal))
                elementos.append (Spacer (1, 0.25 * inch))

                # Adicionar cada composição
                for composicao in composicoes_selecionadas:
                    # Dados principais
                    dados_principais = [
                        f"<b>Solicitante:</b> {composicao.solicitante or ''}",
                        f"<b>Autor:</b> {composicao.autor or ''}",
                        f"<b>Unidade:</b> {composicao.unidade or ''}",
                        f"<b>Data:</b> {composicao.data.strftime ('%d/%m/%Y') if composicao.data else ''}",
                        f"<b>Código:</b> {composicao.codigo or ''}",
                        f"<b>Número:</b> {composicao.numero or ''}",
                        f"<b>Obra:</b> {composicao.obra or ''}",
                        f"<b>Descrição:</b> {composicao.descricao or ''}",
                        f"<b>IO:</b> {composicao.io or ''}"
                    ]
                    for dado in dados_principais:
                        elementos.append (Paragraph (dado, estilo_normal))
                    elementos.append (Spacer (1, 0.15 * inch))

                    # Tabela de insumos
                    estilo_tabela = ParagraphStyle (
                        'TextoTable',
                        parent=estilo_normal,
                        fontSize=8,
                        leading=10
                    )
                    dados_insumos = [['Insumo', 'Código', 'UN', 'Quantidade', 'Data Custo', 'Valor']]

                    for ci in composicao.composicaoinsumo_set.all ():
                        dados_insumos.append ([
                            Paragraph (ci.insumo.insumo if ci.insumo else '', estilo_tabela),
                            ci.codigo or '',
                            ci.un or '',
                            f"{ci.quantidade:.2f}" if ci.quantidade else '0.00',
                            ci.data_custo.strftime ('%d/%m/%Y') if ci.data_custo else '',
                            f"R$ {ci.valor:.2f}" if ci.valor else 'R$ 0.00'
                        ])

                    if len (dados_insumos) > 1:
                        tabela = Table (
                            dados_insumos,
                            colWidths=[2.5 * inch, 1 * inch, 0.5 * inch, 0.8 * inch, 1 * inch, 0.8 * inch]
                        )
                        tabela.setStyle (TableStyle ([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, 0), 10),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                            ('FONTSIZE', (0, 1), (-1, -1), 8),
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                            ('LEFTPADDING', (0, 0), (-1, -1), 4),
                            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                        ]))
                        elementos.append (Paragraph ("<b>Insumos</b>", estilo_normal))
                        elementos.append (Spacer (1, 0.1 * inch))
                        elementos.append (tabela)
                    else:
                        elementos.append (Paragraph ("Nenhum insumo registrado.", estilo_normal))

                    valor_total = composicao.valor_total if composicao.valor_total else Decimal ('0.00')
                    elementos.append (Paragraph (f"<b>Valor Total:</b> R$ {valor_total:.2f}", estilo_normal))
                    elementos.append (Spacer (1, 0.5 * inch))

                # Construir PDF
                doc.build (elementos)
                buffer.seek (0)
                response = HttpResponse (buffer.getvalue (), content_type='application/pdf')
                response['Content-Disposition'] = 'attachment; filename="composicoes_selecionadas.pdf"'
                buffer.close ()
                logger.debug ("PDF gerado com sucesso!")
                return response

            except Exception as e:
                logger.error (f"Erro ao gerar PDF: {str (e)}", exc_info=True)
                messages.error (request, f"Erro ao gerar PDF: {str (e)}")
                return redirect ('pesquisar_composicoes')

        messages.error (request, "Ação inválida.")
        return redirect ('pesquisar_composicoes')

    return render (request, 'pesquisar_composicoes.html', {'composicoes': [], 'query': ''})


@login_required
def import_insumos_excel(request):
    if not request.user.is_authenticated:
        return redirect ('login')

    if request.method == "POST":
        if 'excel_file' not in request.FILES:
            messages.error (request, "Nenhum arquivo selecionado!")
            return redirect ('import_insumos_excel')

        excel_file = request.FILES['excel_file']
        try:
            # Lê o arquivo Excel
            df = pd.read_excel (excel_file)

            # Verifica se as colunas esperadas estão presentes
            expected_columns = {"insumo", "codigo", "unidade", "data_custo", "valor"}
            if not expected_columns.issubset (set (df.columns)):
                messages.error (request,
                                "O arquivo Excel deve conter as colunas: insumo, codigo, unidade, data_custo, valor")
                return redirect ('import_insumos_excel')

            # Processa cada linha do Excel
            for _, row in df.iterrows ():
                # Trata valores nulos ou NaT
                insumo_data = {
                    "insumo": str (row["insumo"]) if pd.notna (row["insumo"]) else "",
                    "codigo": str (row["codigo"]) if pd.notna (row["codigo"]) else "",
                    "unidade": str (row["unidade"]) if pd.notna (row["unidade"]) else "",
                    "data_custo": row["data_custo"] if pd.notna (row["data_custo"]) else None,
                    "valor": row["valor"] if pd.notna (row["valor"]) else 0.00
                }

                # Validação básica
                if not insumo_data["insumo"] or not insumo_data["codigo"] or not insumo_data["unidade"]:
                    continue  # Pula linhas incompletas

                # Converte data_custo para formato DateField, se válida
                if insumo_data["data_custo"]:
                    if isinstance (insumo_data["data_custo"], pd.Timestamp):
                        insumo_data["data_custo"] = insumo_data["data_custo"].date ()
                    elif isinstance (insumo_data["data_custo"], str):
                        try:
                            day, month, year = map (int, insumo_data["data_custo"].split ('/'))
                            insumo_data["data_custo"] = datetime.date (year, month, day)
                        except (ValueError, IndexError):
                            insumo_data["data_custo"] = None  # Usa None se a data for inválida

                # Converte valor para Decimal, tratando NaN/NaT
                try:
                    valor = Decimal (str (insumo_data["valor"]).replace (",", "."))
                    if valor < 0:
                        continue  # Pula valores negativos
                    insumo_data["valor"] = valor
                except (ValueError, TypeError, Decimal.InvalidOperation):
                    insumo_data["valor"] = Decimal ('0.00')  # Usa 0.00 se inválido

                # Salva o insumo
                insumo = Insumo (
                    insumo=insumo_data["insumo"],
                    codigo=insumo_data["codigo"],
                    unidade=insumo_data["unidade"],
                    data_custo=insumo_data["data_custo"],
                    valor=insumo_data["valor"]
                )
                insumo.save ()

            messages.success (request, f"Insumos importados com sucesso! ({len (df)} linhas processadas)")
        except Exception as ex:
            messages.error (request, f"Erro ao importar insumos: {str (ex)}")
        return redirect ('import_insumos_excel')

    return render (request, 'import_insumos_excel.html')


def home_view(request):
    return render (request, 'home.html')


@login_required
def main_view(request):
    return render (request, 'main.html')


@login_required
def composicoes_cadastradas_view(request):
    composicoes = Composicao.objects.all ()
    return render (request, 'composicoes_cadastradas.html', {'composicoes': composicoes})


@login_required
def importar_insumos_view(request):
    if request.method == 'POST':
        # Lógica para importar insumos (ex.: upload de arquivo) pode ser adicionada aqui
        pass
    return render (request, 'importar_insumos.html')


@login_required
def insumos_view(request):
    insumos = Insumo.objects.all ()  # Lista todos os insumos
    return render (request, 'insumos.html', {'insumos': insumos})


@login_required
def pesquisar_insumos_view(request):
    query = request.GET.get ('q', '')
    insumos = Insumo.objects.filter (insumo__icontains=query) if query else Insumo.objects.all ()
    return render (request, 'pesquisar_insumos.html', {'insumos': insumos, 'query': query})


@login_required
def pesquisar_composicoes_view(request):
    logger.debug (f"Requisição recebida: {request.method}")

    if request.method == "GET":
        query = request.GET.get ('q', '')
        composicoes = Composicao.objects.filter (
            Q (codigo__icontains=query) |
            Q (descricao__icontains=query) |
            Q (numero__icontains=query)
        ) if query else Composicao.objects.all ()
        logger.debug (f"Composições encontradas: {composicoes.count ()}")
        return render (request, 'pesquisar_composicoes.html', {'composicoes': composicoes, 'query': query})

    if request.method == "POST":
        logger.debug (f"Dados do POST: {dict (request.POST)}")
        if 'export_pdf' in request.POST:
            logger.debug ("Botão 'Exportar para PDF' detectado!")
            selected_ids = request.POST.getlist ('selected')
            logger.debug (f"IDs selecionados: {selected_ids}")
            if not selected_ids:
                messages.error (request, "Nenhuma composição selecionada!")
                logger.debug ("Nenhuma composição selecionada.")
                return redirect ('pesquisar_composicoes')

            # Retorno simples para teste
            response = HttpResponse (content_type='text/plain')
            response['Content-Disposition'] = 'attachment; filename="teste.txt"'
            response.write ("Teste de exportação funcionando!")
            logger.debug ("Retornando arquivo de teste.")
            return response

        logger.debug ("POST recebido, mas 'export_pdf' não encontrado.")
        messages.error (request, "Ação inválida.")
        return redirect ('pesquisar_composicoes')

    logger.debug ("Método não suportado.")
    return render (request, 'pesquisar_composicoes.html', {'composicoes': [], 'query': ''})


@login_required
def selecionar_composicoes_view(request):
    composicoes = Composicao.objects.all ()
    return render (request, 'selecionar_composicoes.html', {'composicoes': composicoes})


def custom_logout_view(request):
    logout (request)
    request.session.flush ()  # Limpa completamente a sessão
    return redirect ('/')


@login_required
def imprimir_composicao_view(request, id):
    composicao = get_object_or_404 (Composicao, id=id)
    insumos = composicao.composicaoinsumo_set.all ()  # Usando ComposicaoInsumo conforme o código atual

    try:
        response = HttpResponse (content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="composicao_{composicao.codigo}.pdf"'
        p = canvas.Canvas (response, pagesize=A4)
        p.drawString (100, 800, f"Composição: {composicao.codigo} - {composicao.descricao}")
        p.drawString (100, 780, f"Solicitante: {composicao.solicitante}")
        p.drawString (100, 760, f"Unidade: {composicao.unidade}")
        p.drawString (100, 740, f"Data: {composicao.data}")
        p.drawString (100, 720, f"Valor Total: R$ {composicao.valor_total:.2f}")

        # Listar insumos
        y = 700
        for insumo in insumos:
            y -= 20
            p.drawString (100, y,
                          f"{insumo.insumo.codigo if insumo.insumo else ''} - Qtd: {insumo.quantidade} {insumo.un} - R$ {insumo.valor}")

        # Adicionar imagem, se existir
        image_path = os.path.join ('copre_depre', 'static', 'images', 'emop_branco_g1.png')
        if os.path.exists (image_path):
            p.drawImage (image_path, 50, y - 50, width=100, height=100)
        else:
            logger.warning (f"Imagem não encontrada: {image_path}")

        p.showPage ()
        p.save ()
        logger.debug (f"PDF gerado para composição {composicao.codigo}")
        return response
    except Exception as e:
        logger.error (f"Erro ao gerar PDF: {e}")
        messages.error (request, f"Erro ao gerar PDF: {e}")
        return redirect ('pesquisar_composicoes')