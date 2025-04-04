# copre_depre/utils.py
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import os
import logging

logger = logging.getLogger(__name__)

def export_to_pdf(composicoes_data):
    pdf_file = "composicoes_selecionadas.pdf"  # Nome fixo para múltiplas composições
    logger.debug(f"Gerando PDF: {pdf_file}")

    try:
        doc = SimpleDocTemplate(
            pdf_file,
            pagesize=letter,
            leftMargin=0.5 * inch,
            rightMargin=0.5 * inch,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch
        )
        elements = []

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.darkblue,
            alignment=1
        )
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.grey,
            alignment=1
        )
        normal_style = styles['Normal']
        normal_style.fontSize = 10
        table_style = ParagraphStyle(
            'TableText',
            parent=styles['Normal'],
            fontSize=8,
            leading=10  # Espaçamento entre linhas
        )

        # Logo (adicionado apenas uma vez no início)
        logo_path = os.path.join('copre_depre', 'static', 'images', 'emop_branco_g1.png')
        if os.path.exists(logo_path):
            logger.debug(f"Logo encontrado em {logo_path}")
            logo = Image(logo_path, width=2 * inch, height=1 * inch)
            logo.hAlign = 'CENTER'
            elements.append(logo)
        else:
            logger.warning(f"Logo não encontrado em {logo_path}")

        elements.append(Paragraph("CORDENADORIA DE PREÇOS - COPRE", title_style))
        elements.append(Paragraph("DEPARTAMENTO DE APROPRIAÇÃO DE PREÇOS - DEPRE", subtitle_style))
        elements.append(Spacer(1, 0.25 * inch))

        # Iterar sobre cada composição na lista
        for i, composicao_data in enumerate(composicoes_data):
            # Dados principais da composição
            dados_principais = [
                f"<b>Solicitante:</b> {composicao_data.get('solicitante', '')}",
                f"<b>Autor:</b> {composicao_data.get('autor', '')}",
                f"<b>Unidade:</b> {composicao_data.get('unidade', '')}",
                f"<b>Data:</b> {composicao_data.get('data', '')}",
                f"<b>Código:</b> {composicao_data.get('codigo', '')}",
                f"<b>Número:</b> {composicao_data.get('numero', '')}",
                f"<b>Obra:</b> {composicao_data.get('obra', '')}",
                f"<b>Descrição:</b> {composicao_data.get('descricao', '')}",
                f"<b>IO:</b> {composicao_data.get('io', '')}"
            ]
            for dado in dados_principais:
                elements.append(Paragraph(dado, normal_style))
            elements.append(Spacer(1, 0.25 * inch))

            # Tabela de insumos (se houver)
            insumos = composicao_data.get('insumos', [])
            if not insumos and 'id' in composicao_data:
                # Se não houver insumos no dicionário, buscar do banco
                from .models import ComposicaoInsumo  # Importar aqui para evitar circular import
                composicao_id = composicao_data['id']
                insumos = ComposicaoInsumo.objects.filter(composicao_id=composicao_id)
                insumos = [
                    {
                        'insumo': ci.insumo.insumo if ci.insumo else '',
                        'codigo': ci.codigo or '',
                        'un': ci.un or '',
                        'quantidade': str(ci.quantidade) if ci.quantidade is not None else '0',
                        'data_custo': ci.data_custo.strftime('%d/%m/%Y') if ci.data_custo else '',
                        'valor': str(ci.valor) if ci.valor is not None else '0.00'
                    } for ci in insumos
                ]

            insumos_data = [['Insumo', 'Código', 'UN', 'Quantidade', 'Data Custo', 'Valor']]
            for insumo in insumos:
                insumos_data.append([
                    Paragraph(insumo.get('insumo', ''), table_style),
                    insumo.get('codigo', ''),
                    insumo.get('un', ''),
                    insumo.get('quantidade', ''),
                    insumo.get('data_custo', ''),
                    insumo.get('valor', '')
                ])

            if len(insumos_data) > 1:
                logger.debug(f"Insumos para tabela: {insumos_data}")
                table = Table(insumos_data, colWidths=[2.5 * inch, 1 * inch, 0.5 * inch, 0.8 * inch, 1 * inch, 0.8 * inch])
                table.setStyle(TableStyle([
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
                    ('WORDWRAP', (0, 1), (0, -1), 'CJK'),
                ]))
                elements.append(Paragraph("<b>Insumos</b>", normal_style))
                elements.append(Spacer(1, 0.1 * inch))
                elements.append(table)
            else:
                elements.append(Paragraph("Nenhum insumo registrado.", normal_style))
            elements.append(Spacer(1, 0.25 * inch))

            elements.append(Paragraph(f"<b>Valor Total:</b> R$ {composicao_data.get('valor_total', '0.00')}", normal_style))

            # Adicionar quebra de página entre composições (exceto a última)
            if i < len(composicoes_data) - 1:
                elements.append(PageBreak())

        doc.build(elements)
        logger.debug(f"PDF gerado com sucesso: {pdf_file}")
        return pdf_file  # Retornar o caminho do arquivo para uso posterior
    except Exception as e:
        logger.error(f"Erro ao gerar PDF: {str(e)}")
        raise