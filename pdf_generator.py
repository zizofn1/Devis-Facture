# ==========================================
# PDF_GENERATOR.PY — Génération du PDF
# ==========================================

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle,
    Flowable, Paragraph, Spacer, HRFlowable, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER

from config import COMPANY, COLORS, DOC_TYPES
from number_to_letters import amount_to_letters


# ──────────────────────────────────────────
# Constantes layout
# ──────────────────────────────────────────
PAGE_W, PAGE_H = A4                 # 595.3 × 841.9 pt
MARGIN_L  = 15 * mm
MARGIN_R  = 15 * mm
MARGIN_T  = 42 * mm                 # espace pour l'en-tête dessiné en canvas
MARGIN_B  = 22 * mm
CONTENT_W = PAGE_W - MARGIN_L - MARGIN_R   # ~165 mm

# Hauteur disponible pour le contenu (sans header/footer canvas)
CONTENT_H = PAGE_H - MARGIN_T - MARGIN_B






# ──────────────────────────────────────────
# Utilitaires
# ──────────────────────────────────────────

def format_mad(amount) -> str:
    try:
        return f"{float(amount):,.2f}".replace(",", "\u202f")  # espace fine insécable
    except (ValueError, TypeError):
        return str(amount)


def _esc(text: str) -> str:
    """Échappe les caractères spéciaux XML pour ReportLab Paragraph."""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ──────────────────────────────────────────
# Styles
# ──────────────────────────────────────────

def _styles() -> dict:
    base = getSampleStyleSheet()
    C    = COLORS

    def ps(name, **kw):
        return ParagraphStyle(name, parent=base["Normal"], **kw)

    return {
        "doc_title": ps("DocTitle",
            fontName="Helvetica-Bold", fontSize=20,
            textColor=colors.HexColor(C["dark"]),
            spaceAfter=15, leading=26),

        "label": ps("Label",
            fontName="Helvetica-Bold", fontSize=8,
            textColor=colors.HexColor(C["primary"]),
            spaceBefore=0, spaceAfter=1),

        "value": ps("Value",
            fontName="Helvetica", fontSize=9.5,
            textColor=colors.HexColor(C["dark"]),
            leading=13),

        "value_bold": ps("ValueBold",
            fontName="Helvetica-Bold", fontSize=9.5,
            textColor=colors.HexColor(C["dark"]),
            leading=13),

        "table_body": ps("TableBody",
            fontName="Helvetica", fontSize=9,
            textColor=colors.HexColor(C["dark"]),
            leading=12),

        "totals_label": ps("TotalsLabel",
            fontName="Helvetica", fontSize=9,
            textColor=colors.HexColor(C["muted"]),
            alignment=TA_LEFT),

        "totals_value": ps("TotalsValue",
            fontName="Helvetica", fontSize=9,
            textColor=colors.HexColor(C["dark"]),
            alignment=TA_RIGHT),

        "totals_label_big": ps("TotalsLabelBig",
            fontName="Helvetica-Bold", fontSize=10,
            textColor=colors.HexColor(C["primary"]),
            alignment=TA_LEFT),

        "totals_value_big": ps("TotalsValueBig",
            fontName="Helvetica-Bold", fontSize=10,
            textColor=colors.HexColor(C["primary"]),
            alignment=TA_RIGHT),

        "cond_title": ps("CondTitle",
            fontName="Helvetica-Bold", fontSize=8.5,
            textColor=colors.HexColor(C["dark"]),
            spaceAfter=3),

        "cond_body": ps("CondBody",
            fontName="Helvetica", fontSize=8,
            textColor=colors.HexColor(C["muted"]),
            leading=12),

        "sign_label": ps("SignLabel",
            fontName="Helvetica-Bold", fontSize=8.5,
            textColor=colors.HexColor(C["dark"]),
            alignment=TA_CENTER),

        "sign_sub": ps("SignSub",
            fontName="Helvetica", fontSize=7.5,
            textColor=colors.HexColor(C["muted"]),
            alignment=TA_CENTER),
    }


# ──────────────────────────────────────────
# Section 1 : En-tête du document (infos devis + client)
# ──────────────────────────────────────────

def _section_header(client_data: dict, doc_cfg: dict, st: dict) -> list:
    """
    Deux colonnes :
      Gauche  → titre (DEVIS / FACTURE) + numéro + date + validité
      Droite  → bloc client
    """
    # ── Colonne gauche ──
    left = [Paragraph(doc_cfg["title_pdf"], st["doc_title"])]

    meta_lines = [
        ("N° " + doc_cfg["label"],  _esc(client_data["num"])),
        ("Date d'émission",          _esc(client_data["date"])),
    ]
    if doc_cfg.get("validity_line"):
        # On retire le préfixe "Validité : " s'il est déjà dans la chaîne
        v = doc_cfg["validity_line"]
        if v.startswith("Validité :"):
            v = v  # on l'affiche tel quel
        meta_lines.append(("Validité", v.replace("Validité : ", "")))

    for lbl, val in meta_lines:
        left.append(Paragraph(lbl.upper(), st["label"]))
        left.append(Paragraph(val, st["value"]))
        left.append(Spacer(1, 1.5 * mm))

    # ── Colonne droite ──
    right = [
        Paragraph("À L'ATTENTION DE", st["label"]),
        Paragraph(_esc(client_data["name"]), st["value_bold"]),
        Spacer(1, 1 * mm),
    ]
    for lbl, val in [
        ("ICE",     client_data["ice"]),
        ("Adresse", client_data["address"]),
        ("Tél",     client_data["phone"]),
    ]:
        right.append(Paragraph(f"<b>{lbl} :</b> {_esc(val)}", st["value"]))

    col_l = CONTENT_W * 0.48
    col_r = CONTENT_W * 0.52

    tbl = Table([[left, right]], colWidths=[col_l, col_r])
    tbl.setStyle(TableStyle([
        ("VALIGN",  (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING",   (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 0),
        # Filet vertical de séparation entre les deux colonnes
        ("LINEAFTER", (0, 0), (0, -1), 0.5, colors.HexColor(COLORS["border"])),
        ("LEFTPADDING", (1, 0), (1, -1), 8),
    ]))
    return [tbl, Spacer(1, 6 * mm)]


# ──────────────────────────────────────────
# Section 2 : Tableau des articles
# ──────────────────────────────────────────

def _section_items(items_data: list, columns: list, st: dict) -> list:
    visible = [c for c in columns if c["visible"]]
    col_widths = [c["pdf_mm"] * mm for c in visible]

    # Ajuster proportionnellement si la somme dépasse CONTENT_W
    total_w = sum(col_widths)
    if total_w > CONTENT_W:
        ratio = CONTENT_W / total_w
        col_widths = [w * ratio for w in col_widths]

    # En-tête
    header_row = [Paragraph(c["label"].upper(), ParagraphStyle(
        "TH", fontName="Helvetica-Bold", fontSize=8.5,
        textColor=colors.white,
        alignment={"center": TA_CENTER, "e": TA_RIGHT, "w": TA_LEFT}
                  .get(c["anchor"], TA_LEFT)
    )) for c in visible]

    # Corps
    anchor_map = {"center": TA_CENTER, "e": TA_RIGHT, "w": TA_LEFT}
    body_rows = []
    for item in items_data:
        row = []
        for col in visible:
            val = item.get(col["key"], "")
            if col["key"] in ("pu", "total"):
                text = format_mad(val)
                align = TA_RIGHT
            elif col["key"] == "qte":
                text = str(val) if val != "" else ""
                align = TA_CENTER
            elif col["key"] == "desc":
                text = _esc(str(val))
                align = TA_LEFT
            else:
                text = _esc(str(val))
                align = anchor_map.get(col["anchor"], TA_LEFT)

            row.append(Paragraph(text, ParagraphStyle(
                f"TD_{col['key']}", fontName="Helvetica", fontSize=9,
                textColor=colors.HexColor(COLORS["dark"]),
                leading=12, alignment=align
            )))
        body_rows.append(row)

    table = Table(
        [header_row] + body_rows,
        colWidths=col_widths,
        repeatRows=1,
        hAlign="LEFT",
    )

    # Alternance de couleurs sur les lignes
    row_styles = []
    for i in range(1, len(body_rows) + 1):
        bg = "#f8fafc" if i % 2 == 0 else "#ffffff"
        row_styles.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor(bg)))

    table.setStyle(TableStyle([
        # En-tête
        ("BACKGROUND",    (0, 0), (-1, 0), colors.HexColor(COLORS["primary"])),
        ("ROWBACKGROUND", (0, 0), (-1, 0), colors.HexColor(COLORS["primary"])),
        ("TOPPADDING",    (0, 0), (-1, 0), 7),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 7),
        ("LEFTPADDING",   (0, 0), (-1, 0), 5),
        ("RIGHTPADDING",  (0, 0), (-1, 0), 5),
        # Corps
        ("TOPPADDING",    (0, 1), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
        ("LEFTPADDING",   (0, 1), (-1, -1), 5),
        ("RIGHTPADDING",  (0, 1), (-1, -1), 5),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        # Bordures
        ("LINEBELOW",  (0, 0), (-1, -1), 0.3, colors.HexColor(COLORS["border"])),
        ("BOX",        (0, 0), (-1, -1), 0.5, colors.HexColor(COLORS["border"])),
        *row_styles,
    ]))
    return [table, Spacer(1, 4 * mm)]


# ──────────────────────────────────────────
# Section 3 : Totaux
# ──────────────────────────────────────────

def _section_totals(totals_data: dict, st: dict, is_auto_entrepreneur: bool = False) -> list:
    ht  = totals_data["ht"]
    pct = totals_data["tva_percent"]
    tva = totals_data["tva_val"]
    ttc = totals_data["ttc"]
    remise = totals_data.get("remise", 0.0)

    rows = [
        [Paragraph("Total HT",          st["totals_label"]),
         Paragraph(f"{format_mad(ht)} MAD",  st["totals_value"])],
    ]
    
    if remise > 0:
        rows.append(
            [Paragraph("Remise Globale",    st["totals_label"]),
             Paragraph(f"- {format_mad(remise)} MAD", st["totals_value"])]
        )
    
    ht_net = totals_data.get("ht_net", ht)
    if is_auto_entrepreneur:
        rows.append(
            [Paragraph("TVA non applicable, art. 293 B du CGI", st["totals_label"]),
             Paragraph("0.00 MAD", st["totals_value"])]
        )
    else:
        rows.append(
            [Paragraph(f"TVA ({pct:.4g}%)",  st["totals_label"]),
             Paragraph(f"{format_mad(tva)} MAD", st["totals_value"])]
        )
        
    rows.append(
        [Paragraph("Net à payer TTC",    st["totals_label_big"]),
         Paragraph(f"{format_mad(ttc)} MAD", st["totals_value_big"])]
    )

    inner = Table(rows, colWidths=[45 * mm, 45 * mm])
    inner.setStyle(TableStyle([
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("LINEABOVE",     (0, 2), (-1, 2), 1.0, colors.HexColor(COLORS["primary"])),
        ("LINEBELOW",     (0, 2), (-1, 2), 1.0, colors.HexColor(COLORS["primary"])),
    ]))

    # Aligner à droite via une table conteneur
    spacer_w = CONTENT_W - 90 * mm
    layout = Table([["", inner]], colWidths=[spacer_w, 90 * mm])
    layout.setStyle(TableStyle([
        ("LEFTPADDING",  (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING",   (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 0),
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
    ]))
    return [layout, Spacer(1, 6 * mm)]


# ──────────────────────────────────────────
# Section 4 : Conditions + Signatures
# (toujours groupées ensemble — KeepTogether)
# ──────────────────────────────────────────

def _section_footer_block(doc_cfg: dict, st: dict, totals_data: dict) -> list:
    """
    Bloc bas de page : conditions + paiement + zone de signature + montant en lettres.
    KeepTogether empêche de couper ce bloc sur plusieurs pages.
    """

    # ── Ligne séparatrice ──
    hr = HRFlowable(
        width="100%", thickness=0.5,
        color=colors.HexColor(COLORS["border"]),
        spaceAfter=3 * mm, spaceBefore=0,
    )

    # ── Montant en lettres ──
    text_lettres = amount_to_letters(totals_data.get("ttc", 0.0))
    lbl_text = "Arrêtée la présente facture à la somme de :" if doc_cfg["prefix"] == "FAC" else "Arrêté le présent devis à la somme de :"
    
    letters_block = Paragraph(
        f"<i>{lbl_text}</i><br/><b>{text_lettres} TTC</b>",
        ParagraphStyle("Lettres", fontName="Helvetica", fontSize=9, textColor=colors.HexColor(COLORS["dark"]), spaceAfter=8*mm)
    )

    # ── Conditions générales ──
    cond_items = "".join(
        f"• {_esc(c)}<br/>" for c in doc_cfg["conditions"]
    )
    cond_block = [
        Paragraph("Conditions Générales", st["cond_title"]),
        Paragraph(cond_items, st["cond_body"]),
    ]

    # ── Moyens de paiement ──
    pay_block = [
        Paragraph("Moyens de paiement", st["cond_title"]),
        Paragraph(
            f"Virement bancaire — <b>{_esc(COMPANY['rib_bank'])}</b><br/>"
            f"RIB : {_esc(COMPANY['rib'])}",
            st["cond_body"]
        ),
    ]

    col_w = CONTENT_W / 2
    cond_table = Table(
        [[cond_block, pay_block]],
        colWidths=[col_w, col_w],
    )
    cond_table.setStyle(TableStyle([
        ("VALIGN",         (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",    (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",   (0, 0), (-1, -1), 6),
        ("TOPPADDING",     (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 0),
        ("LINEAFTER",      (0, 0), (0, -1), 0.4, colors.HexColor(COLORS["border"])),
        ("LEFTPADDING",    (1, 0), (1, -1), 8),
    ]))

    # ── Zone de signatures ──
    sign_left_name  = _esc(doc_cfg["sign_left"])
    sign_right_name = _esc(doc_cfg["sign_right"])   # texte pur, pas de \n ni <br/>
    company_name    = _esc(COMPANY["name"])

    def sign_cell(title: str, subtitle: str) -> list:
        return [
            Spacer(1, 30 * mm),                    # espace grand format pour la signature manuscrite et cachet
            HRFlowable(width="80%", thickness=0.5,
                       color=colors.HexColor(COLORS["border"]),
                       hAlign="CENTER", spaceAfter=2 * mm),
            Paragraph(title,    st["sign_label"]),
            Paragraph(subtitle, st["sign_sub"]),
            Spacer(1, 10 * mm),  # 3 cm d'espace en bas pour le cachet et la signature
        ]

    sign_table = Table(
        [[sign_cell(sign_left_name, company_name),
          sign_cell(sign_right_name, "Date : _______________")]],
        colWidths=[col_w, col_w],
    )
    sign_table.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    inner = [hr, letters_block, cond_table, Spacer(1, 5 * mm), sign_table]
    return [KeepTogether(inner)]


# ──────────────────────────────────────────
# Header / Footer canvas (dessiné sur chaque page)
# ──────────────────────────────────────────

_IMAGE_CACHE = {}

def _draw_page(canvas, doc):
    """En-tête et pied de page fixes sur toutes les pages."""
    canvas.saveState()
    C = COLORS

    # ── Logo ──
    logo_path = COMPANY["logo"]
    logo_x    = MARGIN_L
    logo_y    = PAGE_H - 12 * mm - 20 * mm   # 12mm du bord haut, hauteur 20mm
    if os.path.exists(logo_path):
        try:
            if logo_path not in _IMAGE_CACHE:
                _IMAGE_CACHE[logo_path] = ImageReader(logo_path)
            
            canvas.drawImage(
                _IMAGE_CACHE[logo_path],
                logo_x, logo_y,
                width=20 * mm, height=20 * mm,
                preserveAspectRatio=True, mask="auto",
            )
        except Exception:
            pass

    # ── Nom entreprise ──
    text_x = MARGIN_L + 24 * mm
    canvas.setFont("Helvetica-Bold", 15)
    canvas.setFillColor(colors.HexColor(C["dark"]))
    canvas.drawString(text_x, PAGE_H - 14 * mm, COMPANY["name"])

    canvas.setFont("Helvetica", 8.5)
    canvas.setFillColor(colors.HexColor(C["muted"]))
    canvas.drawString(text_x, PAGE_H - 20 * mm, COMPANY["slogan"])

    canvas.setFont("Helvetica-Oblique", 7.5)
    canvas.setFillColor(colors.HexColor(C["muted"]))
    canvas.drawString(text_x, PAGE_H - 26 * mm, COMPANY["manager"])

    # ── Coordonnées (droite) ──
    rx = PAGE_W - MARGIN_R
    canvas.setFont("Helvetica-Bold", 8.5)
    canvas.setFillColor(colors.HexColor(C["dark"]))
    canvas.drawRightString(rx, PAGE_H - 14 * mm, "Siège Social")

    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor(C["muted"]))
    for i, line in enumerate([
        COMPANY["address"],
        COMPANY["city"],
        f"GSM : {COMPANY['phone']}",
        f"Email : {COMPANY['email']}",
    ]):
        canvas.drawRightString(rx, PAGE_H - (20 + i * 6) * mm, line)

    # ── Ligne de séparation header ──
    # Positionnée juste EN DESSOUS du texte header, au-dessus de la zone content
    sep_y = PAGE_H - MARGIN_T + 2 * mm
    canvas.setStrokeColor(colors.HexColor(C["border"]))
    canvas.setLineWidth(0.8)
    canvas.line(MARGIN_L, sep_y, PAGE_W - MARGIN_R, sep_y)

    # ── Pied de page ──
    footer = (
        f"{COMPANY['name']}   ·   RC : {COMPANY['rc']}"
        f"   ·   Patente : {COMPANY['patente']}"
        f"   ·   IF : {COMPANY['if_num']}"
        f"   ·   ICE : {COMPANY['ice']}"
    )
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor(C["footer"]))
    canvas.drawCentredString(PAGE_W / 2, MARGIN_B / 2, footer)

    # Numéro de page (si plusieurs pages)
    if doc.page > 1 or True:
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(colors.HexColor(C["muted"]))
        canvas.drawRightString(
            PAGE_W - MARGIN_R,
            MARGIN_B / 2,
            f"Page {doc.page}"
        )

    canvas.restoreState()


# ──────────────────────────────────────────
# Point d'entrée public
# ──────────────────────────────────────────

def create_pdf(filename: str, client_data: dict, items_data: list,
               totals_data: dict, doc_type: str = "devis",
               columns: list = None, is_auto_entrepreneur: bool = False) -> None:
    """
    Génère le PDF du devis ou de la facture.

    La logique de pagination est entièrement gérée par ReportLab :
    - Le contenu s'étend naturellement sur plusieurs pages si nécessaire.
    - La section signature (KeepTogether) ne sera jamais coupée en deux.
    - Elle reste sur la même page que les totaux si la place le permet,
      sinon elle bascule proprement à la page suivante.
    """
    from config import DEFAULT_COLUMNS
    if columns is None:
        columns = DEFAULT_COLUMNS

    doc_cfg = DOC_TYPES[doc_type]
    st      = _styles()

    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        leftMargin=MARGIN_L,
        rightMargin=MARGIN_R,
        topMargin=MARGIN_T,
        bottomMargin=MARGIN_B,
    )

    story = []
    story += _section_header(client_data, doc_cfg, st)
    story += _section_items(items_data, columns, st)
    story += _section_totals(totals_data, st, is_auto_entrepreneur)
    story += _section_footer_block(doc_cfg, st, totals_data)

    doc.build(story, onFirstPage=_draw_page, onLaterPages=_draw_page)