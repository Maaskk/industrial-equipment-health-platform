from __future__ import annotations

import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "pdf" / "Guide_complet_soutenance_MLOps_DataOps.pdf"
SCRIPTS = ROOT / "docs" / "soutenance" / "scripts"

NAVY = colors.HexColor("#102A43")
BLUE = colors.HexColor("#1676D2")
TEAL = colors.HexColor("#0E9F9A")
INK = colors.HexColor("#243B53")
MUTED = colors.HexColor("#627D98")
PALE = colors.HexColor("#EAF4FB")
PALE_TEAL = colors.HexColor("#E7F7F5")
PALE_ORANGE = colors.HexColor("#FFF4E5")
LINE = colors.HexColor("#D9E2EC")
WHITE = colors.white


def register_fonts() -> None:
    base = Path("/System/Library/Fonts/Supplemental")
    pdfmetrics.registerFont(TTFont("Arial", str(base / "Arial.ttf")))
    pdfmetrics.registerFont(TTFont("Arial-Bold", str(base / "Arial Bold.ttf")))
    pdfmetrics.registerFont(TTFont("Arial-Italic", str(base / "Arial Italic.ttf")))
    pdfmetrics.registerFontFamily(
        "Arial",
        normal="Arial",
        bold="Arial-Bold",
        italic="Arial-Italic",
        boldItalic="Arial-Bold",
    )


def clean(value: str) -> str:
    return (
        value.replace("\u2011", "-")
        .replace("\u2013", "-")
        .replace("\u2014", "-")
        .replace("\u00a0", " ")
    )


def inline(value: str) -> str:
    value = clean(value.strip())
    value = html.escape(value)
    value = re.sub(r"`([^`]+)`", r'<font name="Courier">\1</font>', value)
    value = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", value)
    return value


register_fonts()
styles = getSampleStyleSheet()
styles.add(
    ParagraphStyle(
        name="CoverTitle",
        parent=styles["Title"],
        fontName="Arial-Bold",
        fontSize=28,
        leading=33,
        textColor=WHITE,
        alignment=TA_LEFT,
        spaceAfter=10 * mm,
    )
)
styles.add(
    ParagraphStyle(
        name="CoverSub",
        parent=styles["BodyText"],
        fontName="Arial",
        fontSize=14,
        leading=20,
        textColor=colors.HexColor("#D9EAF7"),
        spaceAfter=5 * mm,
    )
)
styles.add(
    ParagraphStyle(
        name="H1x",
        parent=styles["Heading1"],
        fontName="Arial-Bold",
        fontSize=20,
        leading=24,
        textColor=NAVY,
        spaceBefore=3 * mm,
        spaceAfter=4 * mm,
    )
)
styles.add(
    ParagraphStyle(
        name="H2x",
        parent=styles["Heading2"],
        fontName="Arial-Bold",
        fontSize=13,
        leading=17,
        textColor=BLUE,
        spaceBefore=4 * mm,
        spaceAfter=2 * mm,
    )
)
styles.add(
    ParagraphStyle(
        name="H3x",
        parent=styles["Heading3"],
        fontName="Arial-Bold",
        fontSize=10.5,
        leading=14,
        textColor=TEAL,
        spaceBefore=3 * mm,
        spaceAfter=1.5 * mm,
    )
)
styles.add(
    ParagraphStyle(
        name="Bodyx",
        parent=styles["BodyText"],
        fontName="Arial",
        fontSize=9.4,
        leading=13.2,
        textColor=INK,
        spaceAfter=2.5 * mm,
    )
)
styles.add(
    ParagraphStyle(
        name="Smallx",
        parent=styles["BodyText"],
        fontName="Arial",
        fontSize=8.2,
        leading=11.2,
        textColor=MUTED,
        spaceAfter=1.5 * mm,
    )
)
styles.add(
    ParagraphStyle(
        name="Bulletx",
        parent=styles["BodyText"],
        fontName="Arial",
        fontSize=9.2,
        leading=12.5,
        leftIndent=5 * mm,
        firstLineIndent=-3.5 * mm,
        bulletIndent=0,
        textColor=INK,
        spaceAfter=1.3 * mm,
    )
)
styles.add(
    ParagraphStyle(
        name="Quotex",
        parent=styles["BodyText"],
        fontName="Arial",
        fontSize=10,
        leading=14,
        leftIndent=5 * mm,
        rightIndent=3 * mm,
        textColor=INK,
        backColor=PALE,
        borderColor=BLUE,
        borderWidth=0.8,
        borderPadding=8,
        spaceAfter=3 * mm,
    )
)
styles.add(
    ParagraphStyle(
        name="Calloutx",
        parent=styles["BodyText"],
        fontName="Arial",
        fontSize=9.2,
        leading=13,
        leftIndent=4 * mm,
        rightIndent=3 * mm,
        textColor=INK,
        backColor=PALE_TEAL,
        borderColor=TEAL,
        borderWidth=0.7,
        borderPadding=7,
        spaceBefore=2 * mm,
        spaceAfter=3 * mm,
    )
)
styles.add(
    ParagraphStyle(
        name="Codex",
        parent=styles["Code"],
        fontName="Courier",
        fontSize=7.5,
        leading=10.5,
        textColor=colors.HexColor("#F0F4F8"),
        backColor=colors.HexColor("#1F2933"),
        borderPadding=7,
        spaceBefore=1.5 * mm,
        spaceAfter=3 * mm,
    )
)


class GuideDocTemplate(BaseDocTemplate):
    def __init__(self, filename: str):
        super().__init__(
            filename,
            pagesize=A4,
            leftMargin=18 * mm,
            rightMargin=18 * mm,
            topMargin=18 * mm,
            bottomMargin=17 * mm,
            title="Guide complet de soutenance MLOps et DataOps",
            author="Equipe Industrial Equipment Health Platform",
            subject="Scripts, démonstration et questions de soutenance",
        )
        frame = Frame(
            self.leftMargin,
            self.bottomMargin,
            self.width,
            self.height,
            id="content",
        )
        self.addPageTemplates(
            PageTemplate(id="main", frames=[frame], onPage=self.draw_page)
        )

    def draw_page(self, canvas, doc) -> None:
        canvas.saveState()
        if doc.page == 1:
            canvas.setFillColor(NAVY)
            canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
            canvas.setFillColor(TEAL)
            canvas.rect(0, A4[1] - 15 * mm, A4[0], 15 * mm, fill=1, stroke=0)
        else:
            canvas.setStrokeColor(LINE)
            canvas.line(18 * mm, A4[1] - 12 * mm, A4[0] - 18 * mm, A4[1] - 12 * mm)
            canvas.setFont("Arial", 7.5)
            canvas.setFillColor(MUTED)
            canvas.drawString(18 * mm, A4[1] - 9 * mm, "Industrial Equipment Health Platform")
            canvas.drawRightString(
                A4[0] - 18 * mm,
                A4[1] - 9 * mm,
                "Guide de soutenance",
            )
            canvas.line(18 * mm, 12 * mm, A4[0] - 18 * mm, 12 * mm)
            canvas.drawRightString(A4[0] - 18 * mm, 8 * mm, f"Page {doc.page}")
        canvas.restoreState()


def p(text: str, style: str = "Bodyx") -> Paragraph:
    return Paragraph(inline(text), styles[style])


def bullet(text: str) -> Paragraph:
    return Paragraph(f"• {inline(text)}", styles["Bulletx"])


def heading(text: str, level: int = 1) -> Paragraph:
    return Paragraph(inline(text), styles[{1: "H1x", 2: "H2x", 3: "H3x"}[level]])


def link(label: str, url: str) -> Paragraph:
    return Paragraph(
        f'<a href="{html.escape(url)}" color="#1676D2"><u>{inline(label)}</u></a><br/>'
        f'<font color="#627D98">{html.escape(url)}</font>',
        styles["Bodyx"],
    )


def callout(title: str, text: str, color: str = "teal") -> Paragraph:
    style = styles["Calloutx"]
    if color == "orange":
        style = ParagraphStyle(
            "OrangeCallout",
            parent=styles["Calloutx"],
            backColor=PALE_ORANGE,
            borderColor=colors.HexColor("#F0A202"),
        )
    return Paragraph(f"<b>{inline(title)}</b><br/>{inline(text)}", style)


def section_break(title: str, subtitle: str) -> list:
    return [
        PageBreak(),
        heading(title, 1),
        HRFlowable(width="100%", thickness=1.5, color=TEAL, spaceAfter=5 * mm),
        p(subtitle, "Bodyx"),
        Spacer(1, 2 * mm),
    ]


def table(data: list[list[str]], widths: list[float], header: bool = True) -> Table:
    formatted = []
    for row_index, row in enumerate(data):
        formatted.append(
            [
                Paragraph(
                    inline(str(cell)),
                    ParagraphStyle(
                        f"cell-{row_index}",
                        parent=styles["Smallx"],
                        textColor=WHITE if header and row_index == 0 else INK,
                        fontName="Arial-Bold" if header and row_index == 0 else "Arial",
                    ),
                )
                for cell in row
            ]
        )
    t = Table(formatted, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    commands = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.4, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    if header:
        commands.extend(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, colors.HexColor("#F5F8FA")]),
            ]
        )
    t.setStyle(TableStyle(commands))
    return t


def parse_script(path: Path, skip_first_h1: bool = False) -> list:
    story = []
    lines = path.read_text(encoding="utf-8").splitlines()
    paragraph_lines: list[str] = []
    first_h1_seen = False

    def flush() -> None:
        nonlocal paragraph_lines
        if paragraph_lines:
            text = " ".join(x.strip() for x in paragraph_lines).strip()
            style = "Quotex" if text.startswith("«") else "Bodyx"
            story.append(Paragraph(inline(text), styles[style]))
            paragraph_lines = []

    for raw in lines:
        line = raw.rstrip()
        if not line:
            flush()
            continue
        if line.startswith("# "):
            flush()
            if skip_first_h1 and not first_h1_seen:
                first_h1_seen = True
                continue
            first_h1_seen = True
            story.append(heading(line[2:], 1))
        elif line.startswith("## "):
            flush()
            story.append(heading(line[3:], 2))
        elif re.match(r"^\d+\. ", line):
            flush()
            story.append(bullet(re.sub(r"^\d+\. ", "", line)))
        elif line.startswith("   ") and story and isinstance(story[-1], Paragraph):
            paragraph_lines.append(line)
        else:
            paragraph_lines.append(line)
    flush()
    return story


def build() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    story: list = []

    story.extend(
        [
            Spacer(1, 32 * mm),
            Paragraph("GUIDE COMPLET DE SOUTENANCE", styles["CoverSub"]),
            Paragraph("Industrial Equipment<br/>Health Platform", styles["CoverTitle"]),
            HRFlowable(width="42%", thickness=3, color=TEAL, hAlign="LEFT", spaceAfter=8 * mm),
            Paragraph(
                "Scripts individuels, explication du projet, démonstration en direct et réponses aux questions",
                styles["CoverSub"],
            ),
            Spacer(1, 20 * mm),
            Paragraph("MLOps et DataOps", styles["CoverSub"]),
            Paragraph("Équipe de 7 présentateurs", styles["CoverSub"]),
            Spacer(1, 52 * mm),
            Paragraph(
                "Version finale préparée pour la soutenance. Les valeurs de production doivent être vérifiées le jour de la démonstration.",
                ParagraphStyle("CoverNote", parent=styles["Smallx"], textColor=colors.HexColor("#B8D4E8")),
            ),
        ]
    )

    story.extend(section_break("1. Comment utiliser ce guide", "Un seul document pour préparer les prises de parole et la démonstration."))
    for item in [
        "Chaque personne apprend les idées et les transitions, pas chaque phrase mot à mot.",
        "Chaque intervention reste sous cinq minutes, conformément aux consignes de soutenance.",
        "Une seule personne pilote l'écran pendant la démonstration afin d'éviter les changements de session.",
        "Les valeurs dynamiques, notamment le commit, le run GitHub Actions et la version déployée, sont contrôlées juste avant la soutenance.",
        "Si un service ne répond pas, utiliser les captures datées et les réponses JSON conservées hors ligne.",
    ]:
        story.append(bullet(item))
    story.append(callout("Message central", "Le projet ne se limite pas à un modèle. Il relie données, qualité, entraînement, registre, API, conteneurs, déploiement et monitoring dans une chaîne reproductible."))

    story.extend(section_break("2. Le projet expliqué simplement", "Cette partie permet de comprendre l'ensemble avant d'apprendre les scripts."))
    story.append(heading("Le problème", 2))
    story.append(p("Une panne industrielle peut provoquer un arrêt coûteux. La maintenance corrective intervient après la panne. La maintenance préventive intervient selon un calendrier. La maintenance prédictive utilise les mesures réelles de l'équipement pour estimer le moment utile d'intervention."))
    story.append(heading("La réponse du projet", 2))
    story.append(p("La plateforme estime la Remaining Useful Life, appelée RUL, c'est à dire le nombre de cycles restant avant une défaillance. Une API renvoie cette estimation avec un niveau de risque, la version du modèle et la latence."))
    story.append(heading("Les données", 2))
    story.append(p("Le jeu NASA C-MAPSS simule la dégradation de turboréacteurs. FD001 à FD004 couvrent 709 moteurs d'entraînement, 707 moteurs de test, trois réglages opérationnels et 21 capteurs. L'évaluation finale utilise le dernier cycle observé de chaque moteur de test."))
    story.append(heading("Le résultat scientifique", 2))
    story.append(table([
        ["Élément", "Valeur à présenter"],
        ["Modèle retenu", "HistGradientBoostingRegressor"],
        ["MAE", "12,56 cycles"],
        ["RMSE", "16,93 cycles"],
        ["Score NASA", "4 466"],
        ["Population finale", "707 moteurs de test"],
        ["Champion MLflow observé", "Version 2"],
    ], [48 * mm, 110 * mm]))
    story.append(callout("Interprétation", "La MAE mesure l'erreur typique. La RMSE accentue les grandes erreurs. Le score NASA pénalise davantage une surestimation de la RUL, car elle peut retarder une maintenance nécessaire."))

    story.extend(section_break("3. Architecture complète", "Le trajet d'une donnée depuis la NASA jusqu'à la démonstration."))
    pipeline = [
        ["Étape", "Technologie", "Rôle"],
        ["Source", "NASA C-MAPSS", "Trajectoires de moteurs jusqu'à la défaillance"],
        ["Ingestion", "dlt", "Chargement déclaratif et schéma"],
        ["Stockage", "DuckDB", "Tables brutes, intermédiaires et marts"],
        ["Transformation", "dbt", "SQL, tests et documentation"],
        ["Orchestration", "Dagster", "Dépendances, matérialisation et planning quotidien"],
        ["Modélisation", "scikit-learn", "Features temporelles et comparaison de cinq modèles"],
        ["Expériences", "MLflow", "Runs, métriques, artefacts et registre"],
        ["Service", "FastAPI", "Validation, santé, prédiction et monitoring"],
        ["Conteneurs", "Docker Compose", "API, MLflow, Dagster et volumes persistants"],
        ["Déploiement", "Komodo", "Stack, conteneurs, logs et cycle de livraison"],
        ["Validation", "GitHub Actions", "Tests, build et smoke test"],
    ]
    story.append(table(pipeline, [29 * mm, 34 * mm, 97 * mm]))
    story.append(heading("Automatisation réelle", 2))
    story.append(p("Dagster lance le pipeline complet tous les jours à 06:00, heure de Casablanca. Le rapport de drift est généré pour le monitoring. Il ne déclenche pas le réentraînement. Après l'entraînement, un candidat MLflow devient champion uniquement si sa MAE et sa RMSE ne se dégradent pas."))
    story.append(heading("Déploiement présenté", 2))
    story.append(p("Komodo gère la Stack sur le serveur partagé de l'université. L'API FastAPI est exposée sur le port 3402, MLflow sur 3401 et Dagster sur 3403. L'interface publique existante communique avec cette API. Pendant la soutenance, il faut distinguer clairement l'interface, qui affiche le produit, et les services MLOps, qui tournent sur le serveur."))

    story.extend(section_break("4. Liens à préparer", "Ouvrir les pages avant le début de la soutenance et les garder dans cet ordre."))
    links = [
        ("Application publique", "https://industrial-equipment-health-platfor.vercel.app/"),
        ("Komodo", "https://komodo.s3.fsbm.ma/"),
        ("FastAPI", "http://exp.s3.fsbm.ma:3402/"),
        ("Documentation FastAPI", "http://exp.s3.fsbm.ma:3402/docs"),
        ("Santé FastAPI", "http://exp.s3.fsbm.ma:3402/health"),
        ("MLflow", "http://exp.s3.fsbm.ma:3401/"),
        ("Dagster", "http://exp.s3.fsbm.ma:3403/"),
        ("Dépôt GitHub", "https://github.com/Maaskk/industrial-equipment-health-platform"),
        ("GitHub Actions", "https://github.com/Maaskk/industrial-equipment-health-platform/actions"),
        ("Pull request équipe et scripts", "https://github.com/Maaskk/industrial-equipment-health-platform/pull/12"),
    ]
    for label, url in links:
        story.append(link(label, url))
    story.append(callout("Attention", "Les ports sont ceux de la plage 34XX du groupe. Si le professeur ou l'administrateur modifie le routage, vérifier les trois liens serveur avant la soutenance."))

    story.extend(section_break("5. Répartition et chronométrage", "La présentation orale dure 29 minutes 30, puis la démonstration dure 5 minutes."))
    team = [
        ["Ordre", "Personne", "Durée", "Responsabilité présentée"],
        ["1", "Ilyass", "4 min 15", "Contexte, données, EDA et KPI"],
        ["2", "Mohamed", "4 min", "Architecture DataOps et Dagster"],
        ["3", "Hamza", "4 min", "Qualité, lignage et CI"],
        ["4", "Mouhcine", "4 min 15", "Features, modèles et métriques"],
        ["5", "Ossama", "4 min 30", "MLflow, réentraînement, Docker et Komodo"],
        ["6", "Hajar", "4 min", "FastAPI et parcours de démonstration"],
        ["7", "Aya Moujoud", "4 min 30", "QA, monitoring, Komodo et limites"],
        ["Équipe", "Démonstration", "5 min", "Preuves en direct"],
    ]
    story.append(table(team, [16 * mm, 32 * mm, 24 * mm, 88 * mm]))
    story.append(callout("Durée totale", "34 minutes 30. La limite correspondant à sept étudiants est 35 minutes."))

    story.extend(section_break("6. Scripts individuels", "Texte complet de chaque présentateur avec décision technique et questions probables."))
    script_files = [
        "01-ilyass.md",
        "02-mohamed.md",
        "03-hamza.md",
        "04-mouhcine.md",
        "05-ossama.md",
        "06-hajar.md",
        "07-aya-moujoud.md",
    ]
    for index, filename in enumerate(script_files):
        if index:
            story.append(PageBreak())
        story.extend(parse_script(SCRIPTS / filename))

    story.extend(section_break("7. Démonstration en direct", "Un scénario de cinq minutes qui relie le produit aux preuves MLOps."))
    story.extend(parse_script(SCRIPTS / "08-demonstration-equipe.md", skip_first_h1=True))

    story.extend(section_break("8. Préparation de la démonstration", "Contrôles à effectuer avant de commencer."))
    story.append(heading("La veille", 2))
    for item in [
        "Confirmer que la Stack Komodo est en état Running et que les conteneurs API, MLflow et Dagster sont sains.",
        "Vérifier que la version déployée correspond au commit que vous allez annoncer.",
        "Ouvrir MLflow et confirmer l'alias champion ainsi que la version réellement chargée.",
        "Ouvrir Dagster et confirmer le planning quotidien à 06:00.",
        "Ouvrir le dernier workflow GitHub Actions vert et noter son commit.",
        "Exécuter une prédiction et conserver la réponse JSON ainsi qu'une capture.",
        "Exporter les preuves hors ligne dans un dossier unique.",
    ]:
        story.append(bullet(item))
    story.append(heading("Quinze minutes avant", 2))
    checks = """git status --short
git rev-parse HEAD
docker compose -f deploy/compose.production.yml config --quiet
docker compose -f deploy/compose.production.yml ps
curl -f http://exp.s3.fsbm.ma:3402/health
curl -f http://exp.s3.fsbm.ma:3402/demo-payload -o /tmp/demo-payload.json
curl -f -H 'Content-Type: application/json' --data @/tmp/demo-payload.json http://exp.s3.fsbm.ma:3402/predict"""
    story.append(Paragraph(html.escape(checks).replace("\n", "<br/>"), styles["Codex"]))
    story.append(heading("Onglets à ouvrir", 2))
    for item in [
        "Application, vue flotte déjà chargée.",
        "FastAPI documentation ouverte sur POST /predict.",
        "MLflow ouvert sur le modèle enregistré et son alias champion.",
        "Dagster ouvert sur les assets et le schedule.",
        "Komodo ouvert sur la Stack et la liste des conteneurs.",
        "GitHub Actions ouvert sur le dernier run vert.",
        "Rapport d'évaluation ouvert sur les métriques finales.",
    ]:
        story.append(bullet(item))

    story.extend(section_break("9. Ce qu'il faut montrer dans chaque outil", "Le professeur doit voir une preuve, pas seulement entendre le nom de l'outil."))
    tools = [
        ["Outil", "Preuve à afficher", "Phrase courte"],
        ["Application", "Flotte, moteur, historique et résultat", "La décision visible vient de la même API que celle testée."],
        ["FastAPI", "GET /health, POST /predict et réponse", "Le contrat valide l'entrée et renvoie RUL, risque, modèle et latence."],
        ["MLflow", "Run, métriques, artefacts, modèle et alias", "L'API charge l'alias champion et non un numéro codé."],
        ["Dagster", "Assets, dépendances, dernier run et schedule", "Le job complet est planifié chaque jour à 06:00."],
        ["Komodo", "Stack, conteneurs, état, logs et serveur", "Komodo gère le cycle de vie de la Stack sur le serveur partagé."],
        ["GitHub", "Code, branches, PR et documentation", "Le dépôt conserve le code, les responsabilités et les preuves."],
        ["Actions", "Run vert, tests, build et smoke", "La livraison est bloquée si la qualité ou le démarrage échoue."],
        ["Rapports", "MAE, RMSE, NASA et drift", "Les chiffres annoncés sont reliés à des artefacts versionnés."],
    ]
    story.append(table(tools, [25 * mm, 60 * mm, 75 * mm]))

    story.extend(section_break("10. Questions probables du professeur", "Réponses courtes, exactes et défendables."))
    questions = [
        ("Quel est l'objectif métier ?", "Estimer la durée de vie restante d'un moteur pour prioriser une maintenance avant la panne."),
        ("Pourquoi NASA C-MAPSS ?", "Il fournit des trajectoires multivariées jusqu'à la défaillance avec une vérité terrain RUL et un protocole reproductible."),
        ("Pourquoi plafonner la RUL à 125 cycles ?", "La longue phase initiale contient peu de signal de dégradation. Le plafonnement réduit son influence sur l'apprentissage."),
        ("Comment évitez-vous la fuite de données ?", "La séparation est faite par moteur et respecte l'ordre temporel. Un moteur de validation n'apparaît jamais dans l'entraînement."),
        ("Pourquoi des fenêtres de cinq cycles ?", "Elles capturent la tendance récente avec moyenne, écart type et pente sans trop lisser les changements."),
        ("Pourquoi HistGradientBoosting ?", "Il donne le meilleur compromis sur MAE, RMSE et score NASA avec une inférence adaptée au service."),
        ("Pourquoi le score NASA ?", "Il pénalise davantage la surestimation de la RUL, plus risquée dans un contexte de maintenance."),
        ("Que fait MLflow ?", "Il trace les paramètres, métriques et artefacts, enregistre le modèle et gère l'alias champion."),
        ("Comment un modèle devient champion ?", "Le candidat est promu seulement si sa MAE et sa RMSE ne se dégradent pas par rapport au champion."),
        ("Le réentraînement est-il automatique ?", "Oui. Dagster lance le pipeline chaque jour à 06:00. Ce déclenchement est planifié."),
        ("Le drift déclenche-t-il un entraînement ?", "Non. Le drift informe le monitoring. Il ne déclenche pas le job."),
        ("Pourquoi dlt et dbt ?", "dlt charge les données et gère le schéma. dbt transforme les tables, teste les règles et documente le lignage SQL."),
        ("Pourquoi DuckDB ?", "Le volume tient sur une machine. DuckDB apporte SQL et reproductibilité sans administration d'un serveur de base de données."),
        ("Que garantit la CI ?", "Elle exécute les contrats, tests, entraînement, build et smoke test sur un commit précis. Elle ne garantit pas les futures données réelles."),
        ("Pourquoi Docker ?", "Docker fixe les dépendances et rend le même service reproductible en CI et sur le serveur."),
        ("Pourquoi Komodo ?", "Komodo gère la Stack, les conteneurs, les logs, les mises à jour et l'observation sur le serveur partagé."),
        ("Pourquoi FastAPI ?", "FastAPI fournit un contrat Pydantic strict, OpenAPI, des tests simples et un service Python adapté au modèle."),
        ("Quelles sont les limites ?", "Les données sont simulées, le drift est partiel, les seuils de risque ne sont pas calibrés sur un coût industriel et FD001 allège la production de démonstration."),
        ("Que feriez-vous ensuite ?", "Connecter une vraie télémétrie, suivre le drift par variable, valider les seuils avec le métier et ajouter une règle de réentraînement fondée sur des critères approuvés."),
        ("Que fait chaque membre ?", "Chaque rôle correspond à une partie vérifiable du pipeline. La répartition et les livrables sont documentés dans le README, CONTRIBUTORS et les fiches d'équipe."),
    ]
    for question, answer in questions:
        story.append(KeepTogether([heading(question, 3), p(answer)]))

    story.extend(section_break("11. Aya dans GitHub", "Pourquoi elle n'apparaît pas encore dans les deux zones montrées sur les captures."))
    story.append(heading("Le bloc Team du README", 2))
    story.append(p("La branche de la pull request 12 contient déjà Aya dans le tableau Team et retire Akram de la liste des présentateurs actifs. La capture montre encore la branche principale. Tant que la pull request n'est pas approuvée et fusionnée, GitHub affiche l'ancien README sur la page principale."))
    story.append(heading("Le graphe Contributors", 2))
    story.append(p("Le graphe Contributors n'est pas la liste des collaborateurs. Il est calculé à partir des commits attribués sur la branche par défaut. Aya possède déjà l'accès write, mais cet accès ne crée pas un commit et ne modifie donc pas ce graphe."))
    story.append(callout("Procédure correcte", "Aya doit effectuer un vrai changement depuis son propre compte, avec une adresse vérifiée, puis ouvrir une pull request. Après revue et fusion dans main, GitHub pourra lui attribuer ce commit et afficher son profil dans Contributors. Il ne faut pas fabriquer un commit en son nom."))
    story.append(heading("Contribution adaptée à Aya", 2))
    for item in [
        "Exécuter la checklist finale de production.",
        "Compléter la fiche de validation avec les résultats et captures datées.",
        "Vérifier Komodo, FastAPI, MLflow, Dagster et le monitoring.",
        "Documenter les limites constatées sans modifier les résultats scientifiques.",
        "Soumettre cette preuve depuis son compte ayamoujoud.",
    ]:
        story.append(bullet(item))

    story.extend(section_break("12. Plan de secours", "À utiliser si le réseau ou un service externe tombe pendant la soutenance."))
    for item in [
        "Capture de la Stack Komodo et des conteneurs sains.",
        "Capture de MLflow montrant le modèle et l'alias champion.",
        "Capture de Dagster montrant les assets et le planning.",
        "Réponses JSON de /health, /predict, /api/model/info et /api/monitoring/summary.",
        "Rapport final_evaluation.json avec MAE, RMSE et score NASA.",
        "Rapport promotion_decision.json.",
        "Rapport drift_report.json avec sa date et sa source.",
        "Capture du dernier GitHub Actions vert.",
    ]:
        story.append(bullet(item))
    story.append(callout("Règle", "Ne jamais annoncer une valeur qui ne peut pas être reliée à une capture, une réponse JSON, un rapport ou un écran de la plateforme."))

    story.extend(section_break("13. Conclusion à retenir", "La phrase qui résume le projet en vingt secondes."))
    story.append(Paragraph(
        inline("« Nous avons construit une chaîne MLOps et DataOps complète pour estimer la durée de vie restante d'un moteur. Les données NASA sont ingérées et contrôlées, les modèles sont comparés et suivis dans MLflow, le champion est servi par FastAPI, puis Docker et Komodo rendent la solution reproductible et observable. La démonstration relie chaque résultat à une preuve technique. »"),
        styles["Quotex"],
    ))
    story.append(Spacer(1, 8 * mm))
    story.append(p("Fin du guide. Refaire la checklist et noter les valeurs dynamiques le jour de la soutenance.", "Smallx"))

    doc = GuideDocTemplate(str(OUTPUT))
    doc.build(story)


if __name__ == "__main__":
    build()
