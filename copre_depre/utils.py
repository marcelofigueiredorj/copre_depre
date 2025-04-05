# copre_depre/utils.py
from io import BytesIO
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER
import os
import logging

logger = logging.getLogger (__name__)


def export_to_pdf(composicoes_data):
    logger.debug ("Gerando PDF em memória")
    buffer = BytesIO ()

    # Configuração do documento
    doc = SimpleDocTemplate (
        buffer,
        pagesize=letter,
        leftMargin=0.5 * inch,
        rightMargin=0.5 * inch,
        topMargin=0.1 * inch,
        bottomMargin=1 * inch
    )

    elements = []
    styles = getSampleStyleSheet ()

    # ========= CABEÇALHO =========
    logo_path = os.path.join ('copre_depre', 'static', 'images', 'emop_branco_g1.png')
    if os.path.exists (logo_path):
        logo = Image (logo_path, width=1.8 * inch, height=0.8 * inch)
        logo.hAlign = 'CENTER'
        elements.append (logo)
        elements.append (Spacer (1, 0.1 * inch))  # Espaço após logo reduzido
    else:
        logger.warning (f"Logo não encontrado em {logo_path}")

    title_style = ParagraphStyle (
        'Title',
        parent=styles['Heading1'],
        fontSize=14,
        textColor=colors.darkblue,
        alignment=TA_CENTER,
        spaceAfter=2 # Espaçamento após o título reduzido
    )

    subtitle_style = ParagraphStyle (
        'Subtitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.grey,
        alignment=TA_CENTER,
        spaceAfter=2 # Espaçamento após o título reduzido
    )

    elements.append (Paragraph ("CORDENADORIA DE PREÇOS - COPRE", title_style))
    elements.append (Paragraph ("DEPARTAMENTO DE APROPRIAÇÃO DE PREÇOS - DEPRE", subtitle_style))
    elements.append (Spacer (1, 0.05 * inch))  # Espaçamento reduzido de 0.25 para 0.1 polegadas

    # ========= CONTEÚDO PRINCIPAL =========
    if isinstance (composicoes_data, dict):
        composicoes = [composicoes_data]
    else:
        composicoes = composicoes_data

    for i, composicao in enumerate (composicoes):
        # DETALHES DA COMPOSIÇÃO
        details = [
            f"<b>Solicitante:</b> {composicao.get ('solicitante', 'N/A')}",
            f"<b>Autor:</b> {composicao.get ('autor', 'N/A')}",
            f"<b>Unidade:</b> {composicao.get ('unidade', 'N/A')}",
            f"<b>Data:</b> {composicao.get ('data', 'N/A')}",
            f"<b>Código:</b> {composicao.get ('codigo', 'N/A')}",
            f"<b>Número:</b> {composicao.get ('numero', 'N/A')}",
            f"<b>Obra:</b> {composicao.get ('obra', 'N/A')}",
            f"<b>Descrição:</b> {composicao.get ('descricao', 'N/A')}",
            f"<b>IO:</b> {composicao.get ('io', 'N/A')}"
        ]

        for detail in details:
            elements.append (Paragraph (detail, styles['Normal']))

        elements.append (Spacer (1, 0.2 * inch))

        # TABELA DE INSUMOS
        insumos_data = [
            [
                Paragraph ('<b>Insumo</b>', ParagraphStyle ('Header', fontSize=9, fontName='Helvetica-Bold')),
                Paragraph ('<b>Código</b>', ParagraphStyle ('Header', fontSize=9, fontName='Helvetica-Bold')),
                Paragraph ('<b>UN</b>', ParagraphStyle ('Header', fontSize=9, fontName='Helvetica-Bold')),
                Paragraph ('<b>Quantidade</b>', ParagraphStyle ('Header', fontSize=9, fontName='Helvetica-Bold')),
                Paragraph ('<b>Data Custo</b>', ParagraphStyle ('Header', fontSize=9, fontName='Helvetica-Bold')),
                Paragraph ('<b>Valor Unitário</b>', ParagraphStyle ('Header', fontSize=9, fontName='Helvetica-Bold'))
            ]
        ]

        # Estilo para células de dados
        cell_style = ParagraphStyle(
            'CellStyle',
            fontName='Helvetica',
            fontSize=8,
            leading=9,
            wordWrap='LTR'
        )

        for insumo in composicao['insumos']:
            insumos_data.append([
                Paragraph(insumo.get('insumo', 'N/A'), cell_style),
                Paragraph(insumo.get('codigo', 'N/A'), cell_style),
                Paragraph(insumo.get('un', 'N/A'), cell_style),
                Paragraph(f"{float(insumo.get('quantidade', 0)):.2f}", cell_style),
                Paragraph(insumo.get('data_custo', 'N/A'), cell_style),
                Paragraph(f"R$ {float(insumo.get('valor', 0)):.2f}", cell_style)
            ])

        table = Table(
            insumos_data,
            colWidths=[3.2*inch, 0.9*inch, 0.6*inch, 1.0*inch, 1.0*inch, 1.2*inch],  # Largura aumentada
            repeatRows=1
        )

        table.setStyle(TableStyle([
            # ... (configurações de cor e alinhamento)
            ('GRID', (0,0), (-1,-1), 0.8, colors.HexColor('#444')),  # Linhas mais escuras
            ('LINEBELOW', (0,0), (-1,0), 1.2, colors.HexColor('#222')),  # Linha header reforçada
            ('VALIGN', (0,0), (-1,-1), 'TOP')
        ]))

        elements.append(table)
        elements.append (Spacer (1, 0.3 * inch))
        elements.append (Paragraph (
            f"<b>Valor Total:</b> R$ {float (composicao.get ('valor_total', 0)):.2f}",
            ParagraphStyle ('Total', fontSize=10, textColor=colors.HexColor ('#2c3e50'))
        ))

        if i < len (composicoes) - 1:
            elements.append (PageBreak ())

    # ========= RODAPÉ =========
    def add_footer(canvas, doc):
        canvas.saveState ()
        footer_text = (
            "Campo de São Cristóvão, 138 São Cristóvão, Rio de Janeiro | "
            "CEP: 20921-904 | Telefone: (21) 2222-2222 | "
            "SECRETARIA DE INFRAESTRUTURA E OBRAS PÚBLICAS"
        )
        footer_style = ParagraphStyle (
            'FooterStyle',
            fontSize=8,
            leading=10,
            alignment=TA_CENTER,
            textColor=colors.grey
        )
        footer = Paragraph (footer_text, footer_style)
        footer.wrap (doc.width, 0.5 * inch)
        footer.drawOn (canvas, doc.leftMargin, 0.4 * inch)
        canvas.restoreState ()

    # ========= GERAR PDF =========
    try:
        doc.build (elements, onFirstPage=add_footer, onLaterPages=add_footer)
        buffer.seek (0)
        response = HttpResponse (buffer.getvalue (), content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="composicoes.pdf"'
        buffer.close ()
        logger.debug ("PDF gerado com sucesso")
        return response
    except Exception as e:
        logger.error (f"Erro ao gerar PDF: {str (e)}")
        raise