"""Clinical-grade PDF report generation (ReportLab + matplotlib).

Produces a formal, hospital/diagnostic-style report:

    Letterhead  ->  Examination Details  ->  Clinical Summary / Findings  ->
    Speaker Analysis (overview table)  ->  Acoustic Statistics (charts)  ->
    Per-speaker Detailed Findings  ->  Verbatim Transcript (KN + EN)

Key properties
--------------
* Embeds Unicode + Kannada-capable fonts so Kannada source text renders
  correctly instead of showing as boxes (falls back gracefully).
* All long values (acoustic features, transcript lines) wrap; nothing is
  clipped at the page edge.
* Transcript entries are kept together so a speaker block never splits across
  a page boundary.
* Restrained navy/slate palette, hairline rules, "Page X of Y", and a clinical
  disclaimer footer.
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from app.core.logging import get_logger
from app.utils.timestamp import format_range, format_timestamp

logger = get_logger(__name__)

BRAND = "AblePro Solutions"
SUBBRAND = "Speech & Voice Diagnostics"
DOCTYPE = "SPEECH ANALYSIS REPORT"
DISCLAIMER = (
    "This is an AI-assisted screening report and is not a substitute for "
    "professional clinical diagnosis. Findings should be confirmed by a qualified clinician."
)

# --- Formal clinical palette ------------------------------------------------
INK = "#0F172A"
NAVY = "#1E3A5F"
TEAL = "#0E7490"
MUTED = "#64748B"
HAIR = "#D7DEE8"
ZEBRA = "#F6F8FB"
TINT = "#EEF3F9"
OK = "#15803D"
BAD = "#B91C1C"

# Muted, professional per-speaker colours (consistent across tables/charts).
SPEAKER_PALETTE = (
    "#1E3A5F", "#0E7490", "#7C3AED", "#B45309",
    "#15803D", "#9D174D", "#475569", "#0F766E",
)

# Friendly labels + units for the acoustic feature readout.
FEATURE_LABELS: dict[str, tuple[str, str, int]] = {
    "f0_mean": ("Mean F0", " Hz", 0),
    "f0_std": ("F0 variability", " Hz", 0),
    "jitter": ("Jitter", "", 3),
    "shimmer": ("Shimmer", "", 3),
    "hnr": ("HNR", " dB", 1),
    "latency_to_speak_sec": ("Speech latency", " s", 2),
    "pause_to_speech_ratio": ("Pause-to-speech", "", 2),
    "pronunciation_flux_var": ("Pronunciation flux", "", 2),
    "speech_rate": ("Speech rate", " w/s", 2),
}
FEATURE_ORDER = list(FEATURE_LABELS.keys())


@dataclass(slots=True)
class ReportContext:
    job_id: str
    generated_at: datetime
    user_name: str
    user_email: str
    original_filename: str
    duration_seconds: float | None
    sample_rate: int | None
    channels: int | None
    detected_speakers: int
    language_source: str
    language_target: str
    processing_time_seconds: float | None
    speakers: list[dict]
    model_note: str | None = None


# --------------------------------------------------------------------------- #
# Fonts (Unicode body + Kannada). Registered once.
# --------------------------------------------------------------------------- #
_FONTS: dict[str, str] | None = None


def _register_fonts() -> dict[str, str]:
    """Register a Unicode body font and a Kannada-capable font if available.

    Returns a mapping with keys: body, body_bold, kannada. Values are the
    registered ReportLab font names (or Helvetica fallbacks).
    """
    global _FONTS
    if _FONTS is not None:
        return _FONTS

    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    fonts = {"body": "Helvetica", "body_bold": "Helvetica-Bold", "kannada": "Helvetica"}

    # Clean Unicode body font (DejaVu ships with matplotlib -> always present).
    try:
        import matplotlib

        ttf_dir = Path(matplotlib.__file__).parent / "mpl-data" / "fonts" / "ttf"
        dejavu = ttf_dir / "DejaVuSans.ttf"
        dejavu_b = ttf_dir / "DejaVuSans-Bold.ttf"
        if dejavu.exists():
            pdfmetrics.registerFont(TTFont("Body", str(dejavu)))
            fonts["body"] = "Body"
        if dejavu_b.exists():
            pdfmetrics.registerFont(TTFont("BodyBold", str(dejavu_b)))
            fonts["body_bold"] = "BodyBold"
    except Exception as exc:  # noqa: BLE001
        logger.warning("body_font_register_failed", error=str(exc))

    # Kannada-capable font: prefer Noto (Linux/Docker), then macOS system fonts.
    candidates: list[tuple[str, int]] = [
        ("/usr/share/fonts/truetype/noto/NotoSansKannada-Regular.ttf", 0),
        ("/usr/share/fonts/truetype/noto/NotoSerifKannada-Regular.ttf", 0),
        ("/System/Library/Fonts/Supplemental/Kannada Sangam MN.ttc", 0),
        ("/System/Library/Fonts/Supplemental/Kannada MN.ttc", 0),
    ]
    # Glob common font dirs for any NotoSansKannada variant.
    for root in ("/usr/share/fonts", "/usr/local/share/fonts"):
        p = Path(root)
        if p.exists():
            for match in p.rglob("NotoSansKannada*-Regular.ttf"):
                candidates.insert(0, (str(match), 0))
                break

    for path, idx in candidates:
        if not Path(path).exists():
            continue
        try:
            pdfmetrics.registerFont(TTFont("Kannada", path, subfontIndex=idx))
            fonts["kannada"] = "Kannada"
            logger.info("kannada_font_registered", path=path)
            break
        except Exception as exc:  # noqa: BLE001
            logger.warning("kannada_font_register_failed", path=path, error=str(exc))

    if fonts["kannada"] == "Helvetica":
        # No Kannada glyphs available -> fall back to the Unicode body font so
        # at least Latin/transliterated text renders cleanly (no tofu boxes).
        fonts["kannada"] = fonts["body"]
        logger.warning("kannada_font_unavailable", note="install fonts-noto-core for Kannada")

    _FONTS = fonts
    return fonts


def _has_kannada(text: str) -> bool:
    return any("\u0c80" <= ch <= "\u0cff" for ch in (text or ""))


# --------------------------------------------------------------------------- #
# Charts (matplotlib) — clinical styling
# --------------------------------------------------------------------------- #
def _mpl():  # type: ignore[no-untyped-def]
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        return plt
    except Exception as exc:  # noqa: BLE001
        logger.warning("matplotlib_unavailable", error=str(exc))
        return None


def _speaking_time_donut(ctx: ReportContext, colors: list[str]) -> bytes | None:
    plt = _mpl()
    if plt is None:
        return None
    sizes = [max(0.0, s["total_speech_seconds"]) for s in ctx.speakers]
    if not sizes or sum(sizes) == 0:
        return None
    total = sum(sizes)

    def _clock(v: float) -> str:
        m, s = divmod(int(round(v)), 60)
        return f"{m}:{s:02d}"

    labels = [
        f"Speaker {s['label']}   ·   {_clock(v)}   ({v / total * 100:.0f}%)"
        for s, v in zip(ctx.speakers, sizes, strict=False)
    ]

    fig, ax = plt.subplots(figsize=(4.0, 3.7), dpi=200)
    wedges, _ = ax.pie(
        sizes, colors=colors[: len(sizes)], startangle=90, counterclock=False,
        wedgeprops={"width": 0.42, "edgecolor": "white", "linewidth": 2},
    )
    m, s = divmod(int(total), 60)
    ax.text(0, 0.08, f"{m}:{s:02d}", ha="center", va="center", fontsize=15,
            fontweight="bold", color=INK)
    ax.text(0, -0.20, "total speech", ha="center", va="center", fontsize=7, color=MUTED)
    # Single-column legend below the donut with seconds + percentage — no overlap.
    ax.legend(wedges, labels, loc="upper center", bbox_to_anchor=(0.5, -0.01),
              ncol=1, fontsize=7.5, frameon=False, handlelength=0.9, handletextpad=0.6,
              labelspacing=0.5)
    ax.set(aspect="equal")
    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", transparent=True)
    plt.close(fig)
    return buf.getvalue()


def _speech_pause_bar(ctx: ReportContext) -> bytes | None:
    plt = _mpl()
    if plt is None:
        return None
    labels = [f"Speaker {s['label']}" for s in ctx.speakers]
    speech = [s["total_speech_seconds"] for s in ctx.speakers]
    pauses = [s["total_pause_seconds"] for s in ctx.speakers]
    if not labels:
        return None

    import numpy as np

    y = np.arange(len(labels))
    h = 0.36
    fig, ax = plt.subplots(figsize=(4.0, 3.7), dpi=200)
    ax.barh(y + h / 2, speech, height=h, color=NAVY, label="Speech", zorder=3)
    ax.barh(y - h / 2, pauses, height=h, color=TEAL, label="Pauses", zorder=3)

    maxv = max([*speech, *pauses, 1.0])
    for yy, v in zip(y + h / 2, speech, strict=False):
        ax.text(v + maxv * 0.02, yy, f"{v:.0f}s", va="center", fontsize=7, color=NAVY)
    for yy, v in zip(y - h / 2, pauses, strict=False):
        ax.text(v + maxv * 0.02, yy, f"{v:.0f}s", va="center", fontsize=7, color=TEAL)

    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlim(0, maxv * 1.20)
    ax.xaxis.grid(True, color=HAIR, linewidth=0.5)
    ax.set_axisbelow(True)
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color(HAIR)
    ax.tick_params(labelsize=8, length=0)
    ax.set_xlabel("Seconds", fontsize=8, color=MUTED)
    ax.legend(fontsize=7.5, frameon=False, loc="lower right", ncol=2)
    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", transparent=True)
    plt.close(fig)
    return buf.getvalue()


# --------------------------------------------------------------------------- #
# Numbered canvas — adds "Page X of Y"
# --------------------------------------------------------------------------- #
def _make_numbered_canvas(fonts: dict[str, str]):  # type: ignore[no-untyped-def]
    from reportlab.lib.colors import HexColor
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas

    class NumberedCanvas(canvas.Canvas):
        def __init__(self, *args, **kwargs):  # type: ignore[no-untyped-def]
            super().__init__(*args, **kwargs)
            self._saved_states: list[dict] = []

        def showPage(self):  # type: ignore[no-untyped-def]
            self._saved_states.append(dict(self.__dict__))
            self._startPage()

        def save(self):  # type: ignore[no-untyped-def]
            total = len(self._saved_states)
            for state in self._saved_states:
                self.__dict__.update(state)
                self.setFont(fonts["body"], 7)
                self.setFillColor(HexColor(MUTED))
                self.drawRightString(
                    self._pagesize[0] - 18 * mm, 9 * mm, f"Page {self._pageNumber} of {total}"
                )
                super().showPage()
            super().save()

    return NumberedCanvas


# --------------------------------------------------------------------------- #
# Report builder
# --------------------------------------------------------------------------- #
class ReportGenerator:
    def generate(self, ctx: ReportContext) -> tuple[bytes, int]:
        from reportlab.lib.colors import HexColor, white
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import (
            HRFlowable,
            Image,
            KeepTogether,
            PageBreak,
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )

        fonts = _register_fonts()
        BODY, BOLD, KAN = fonts["body"], fonts["body_bold"], fonts["kannada"]

        # Display colours per speaker (clinical palette, consistent everywhere).
        colors_by_label = {
            s["label"]: SPEAKER_PALETTE[i % len(SPEAKER_PALETTE)]
            for i, s in enumerate(ctx.speakers)
        }
        chart_colors = [colors_by_label[s["label"]] for s in ctx.speakers]

        # ---- Styles --------------------------------------------------------
        def ps(name, **kw):  # type: ignore[no-untyped-def]
            kw.setdefault("fontName", BODY)
            return ParagraphStyle(name, **kw)

        st_eyebrow = ps("eyebrow", fontName=BOLD, fontSize=7.5, textColor=HexColor(TEAL),
                        leading=10, spaceAfter=3)
        st_h1 = ps("h1", fontName=BOLD, fontSize=20, textColor=HexColor(INK), leading=23)
        st_meta = ps("meta", fontSize=8.5, textColor=HexColor(MUTED), leading=12)
        st_section = ps("section", fontName=BOLD, fontSize=11.5, textColor=HexColor(NAVY),
                        leading=14, spaceBefore=2, spaceAfter=4)
        st_body = ps("body", fontSize=9, leading=13.5, textColor=HexColor(INK))
        st_small = ps("small", fontSize=7.8, leading=11, textColor=HexColor(MUTED))
        st_kvk = ps("kvk", fontName=BOLD, fontSize=8, textColor=HexColor(MUTED), leading=11)
        st_kvv = ps("kvv", fontSize=8.5, textColor=HexColor(INK), leading=11.5)
        st_th = ps("th", fontName=BOLD, fontSize=8, textColor=white, leading=10)
        st_td = ps("td", fontSize=8.3, textColor=HexColor(INK), leading=11)
        st_tnum = ps("tnum", fontSize=8.3, textColor=HexColor(INK), leading=11, alignment=2)
        st_feat = ps("feat", fontSize=8, leading=12.5, textColor=HexColor(INK))
        st_tsh = ps("tsh", fontName=BOLD, fontSize=8.7, leading=12)
        st_kn = ps("kn", fontName=KAN, fontSize=8.7, leading=12.5, textColor=HexColor("#334155"))
        st_en = ps("en", fontSize=8.7, leading=12.5, textColor=HexColor(INK))
        st_avatar = ps("avatar", fontName=BOLD, fontSize=10, leading=11, textColor=white,
                       alignment=TA_CENTER)
        st_kntag = ps("kntag", fontName=BOLD, fontSize=6.5, leading=9, textColor=HexColor(MUTED))

        def rule(color=HAIR, w=0.6, space=4):  # type: ignore[no-untyped-def]
            return HRFlowable(width="100%", thickness=w, color=HexColor(color),
                              spaceBefore=space, spaceAfter=space)

        story: list = []

        # ---- Title block ---------------------------------------------------
        story.append(Paragraph("CONFIDENTIAL · CLINICAL SPEECH ANALYSIS", st_eyebrow))
        story.append(Paragraph("Multi-Speaker Speech Analysis Report", st_h1))
        story.append(Spacer(1, 2))
        story.append(Paragraph(
            f"Report ID&nbsp;<b>{ctx.job_id[:8].upper()}</b> &nbsp;|&nbsp; "
            f"Issued {ctx.generated_at.strftime('%d %b %Y · %H:%M UTC')}", st_meta))
        story.append(rule(NAVY, 1.4, 8))

        # ---- Examination details (bordered) --------------------------------
        duration = _resolve_duration(ctx)
        details = [
            [Paragraph("EXAMINATION DETAILS", st_th), "", "", ""],
            [Paragraph("Subject", st_kvk), Paragraph(_esc(ctx.user_name) or "—", st_kvv),
             Paragraph("Report ID", st_kvk), Paragraph(ctx.job_id[:8].upper(), st_kvv)],
            [Paragraph("Email", st_kvk), Paragraph(_esc(ctx.user_email) or "—", st_kvv),
             Paragraph("Date issued", st_kvk),
             Paragraph(ctx.generated_at.strftime("%d %b %Y, %H:%M UTC"), st_kvv)],
            [Paragraph("Source file", st_kvk), Paragraph(_esc(ctx.original_filename), st_kvv),
             Paragraph("Duration", st_kvk), Paragraph(_fmt_clock(duration), st_kvv)],
            [Paragraph("Speakers detected", st_kvk), Paragraph(str(ctx.detected_speakers), st_kvv),
             Paragraph("Language", st_kvk),
             Paragraph(f"{ctx.language_source.upper()} &rarr; {ctx.language_target.upper()}", st_kvv)],
            [Paragraph("Sample rate", st_kvk),
             Paragraph(f"{ctx.sample_rate} Hz" if ctx.sample_rate else "—", st_kvv),
             Paragraph("Channels", st_kvk), Paragraph(str(ctx.channels or "—"), st_kvv)],
            [Paragraph("Analysis engine", st_kvk), Paragraph("AblePro AI Pipeline", st_kvv),
             Paragraph("Processing time", st_kvk),
             Paragraph(f"{ctx.processing_time_seconds or 0:.1f} s", st_kvv)],
        ]
        det_tbl = Table(details, colWidths=[30 * mm, 57 * mm, 30 * mm, 57 * mm])
        det_tbl.setStyle(TableStyle([
            ("SPAN", (0, 0), (-1, 0)),
            ("BACKGROUND", (0, 0), (-1, 0), HexColor(NAVY)),
            ("TOPPADDING", (0, 0), (-1, 0), 5), ("BOTTOMPADDING", (0, 0), (-1, 0), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 1), (-1, -1), 5), ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, HexColor(ZEBRA)]),
            ("LINEBELOW", (0, 1), (-1, -2), 0.4, HexColor(HAIR)),
            ("BOX", (0, 0), (-1, -1), 0.7, HexColor(HAIR)),
            ("LINEAFTER", (1, 1), (1, -1), 0.4, HexColor(HAIR)),
        ]))
        story.append(det_tbl)
        story.append(Spacer(1, 7 * mm))

        # ---- Clinical summary / findings -----------------------------------
        atypical = [s for s in ctx.speakers if s.get("atypicality") == "atypical"]
        typical_n = ctx.detected_speakers - len(atypical)
        story.append(Paragraph("Clinical Summary", st_section))
        summary = (
            f"Automated acoustic-prosodic screening was performed on a multi-speaker "
            f"recording containing <b>{ctx.detected_speakers}</b> distinct speaker(s) over "
            f"<b>{_fmt_clock(duration)}</b> of audio. Of the speakers analysed, "
            f"<b>{typical_n}</b> presented within typical parameters and "
            f"<b>{len(atypical)}</b> were flagged as <b>atypical</b> for clinical review."
        )
        callout = [[Paragraph(summary, st_body)]]
        if ctx.model_note:
            callout.append([Paragraph(f"<i>{_esc(ctx.model_note)}</i>", st_small)])
        ct = Table(callout, colWidths=[174 * mm])
        ct.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), HexColor(TINT)),
            ("LINEBEFORE", (0, 0), (0, -1), 3, HexColor(TEAL)),
            ("LEFTPADDING", (0, 0), (-1, -1), 12), ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ("TOPPADDING", (0, 0), (-1, -1), 9), ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ]))
        story.append(ct)
        story.append(Spacer(1, 7 * mm))

        # ---- Speaker analysis table ----------------------------------------
        story.append(Paragraph("Speaker Analysis", st_section))
        header = ["Speaker", "Gender", "Age group", "Classification", "Speech", "Pauses", "Words"]
        rows = [[Paragraph(h, st_th) for h in header]]
        for s in ctx.speakers:
            color = colors_by_label[s["label"]]
            spk = Paragraph(f'<font color="{color}">&#9679;</font> Speaker {s["label"]}', st_td)
            cls = _title(s.get("atypicality"))
            cls_color = BAD if s.get("atypicality") == "atypical" else OK
            rows.append([
                spk,
                Paragraph(_title(s.get("gender")), st_td),
                Paragraph(_title(s.get("age_group")), st_td),
                Paragraph(f'<font color="{cls_color}"><b>{cls}</b></font>', st_td),
                Paragraph(f"{s['total_speech_seconds']:.1f}s", st_tnum),
                Paragraph(f"{s['total_pause_seconds']:.1f}s", st_tnum),
                Paragraph(str(s["word_count"]), st_tnum),
            ])
        spk_tbl = Table(rows, repeatRows=1,
                        colWidths=[34 * mm, 24 * mm, 24 * mm, 30 * mm, 22 * mm, 22 * mm, 18 * mm])
        spk_tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), HexColor(NAVY)),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, HexColor(ZEBRA)]),
            ("LINEBELOW", (0, 1), (-1, -1), 0.4, HexColor(HAIR)),
            ("BOX", (0, 0), (-1, -1), 0.7, HexColor(HAIR)),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (4, 0), (-1, -1), "RIGHT"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(spk_tbl)
        story.append(Spacer(1, 7 * mm))

        # ---- Statistics (charts) -------------------------------------------
        donut = _speaking_time_donut(ctx, chart_colors)
        bar = _speech_pause_bar(ctx)
        if donut or bar:
            cells = []
            if donut:
                cells.append(Image(io.BytesIO(donut), width=80 * mm, height=68 * mm))
            if bar:
                cells.append(Image(io.BytesIO(bar), width=80 * mm, height=68 * mm))
            chart_tbl = Table([cells], colWidths=[87 * mm] * len(cells))
            chart_tbl.setStyle(TableStyle([
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOX", (0, 0), (-1, -1), 0.7, HexColor(HAIR)),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, HexColor(HAIR)),
                ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))
            # Keep the section heading with its charts so it is never orphaned
            # at the foot of a page.
            story.append(KeepTogether([
                Paragraph("Acoustic Statistics", st_section),
                Spacer(1, 1 * mm),
                chart_tbl,
            ]))

        # ---- Detailed findings per speaker ---------------------------------
        story.append(PageBreak())
        story.append(Paragraph("Detailed Acoustic Findings", st_section))
        story.append(Spacer(1, 1 * mm))
        for s in ctx.speakers:
            color = colors_by_label[s["label"]]
            blocks: list = []
            title = Table(
                [[Paragraph(f'<font color="{color}">&#9679;</font>&nbsp; '
                            f'<b>Speaker {s["label"]}</b>', st_body),
                  Paragraph(f'diarization id: {_esc(s["diarization_id"])}', st_small)]],
                colWidths=[60 * mm, 114 * mm],
            )
            title.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3), ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
            ]))
            blocks.append(title)

            atyp = s.get("atypicality")
            cls_color = BAD if atyp == "atypical" else OK
            _ga_src = s.get("gender_age_source")
            if _ga_src == "llm":
                src = "AI audio analysis (Gemini)"
            elif _ga_src == "hf":
                src = "Wav2Vec2 audio models (Hugging Face)"
            else:
                src = "Acoustic feature model"
            findings = [
                [Paragraph("Gender", st_kvk),
                 Paragraph(f"{_title(s.get('gender'))} &nbsp;<font color='{MUTED}'>"
                           f"({_pct(s.get('gender_confidence'))} conf.)</font>", st_kvv)],
                [Paragraph("Age group", st_kvk),
                 Paragraph(f"{_title(s.get('age_group'))} &nbsp;<font color='{MUTED}'>"
                           f"({_pct(s.get('age_confidence'))} conf.)</font>", st_kvv)],
                [Paragraph("Classification", st_kvk),
                 Paragraph(f"<font color='{cls_color}'><b>{_title(atyp)}</b></font> &nbsp;"
                           f"<font color='{MUTED}'>(score {s.get('atypicality_score', 0):.3f}, "
                           f"{_pct(s.get('atypicality_confidence'))} conf.)</font>", st_kvv)],
                [Paragraph("Prediction source", st_kvk), Paragraph(src, st_kvv)],
                [Paragraph("Acoustic features", st_kvk),
                 Paragraph(_format_features(s.get("features")), st_feat)],
            ]
            ft = Table(findings, colWidths=[34 * mm, 140 * mm])
            ft.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 0), (-1, -1), [white, HexColor(ZEBRA)]),
                ("LINEBELOW", (0, 0), (-1, -2), 0.4, HexColor(HAIR)),
                ("BOX", (0, 0), (-1, -1), 0.7, HexColor(HAIR)),
                ("LINEAFTER", (0, 0), (0, -1), 0.4, HexColor(HAIR)),
                ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            blocks.append(ft)
            blocks.append(Spacer(1, 5 * mm))
            story.append(KeepTogether(blocks))

        # ---- Transcript ----------------------------------------------------
        story.append(PageBreak())
        story.append(Paragraph("Verbatim Transcript", st_section))
        story.append(Paragraph(
            "Chronological record of each utterance with timestamp, speaker and the "
            "English (EN) translation of the spoken content.", st_small))
        story.append(rule(HAIR, 0.6, 5))

        segments = _ordered_segments(ctx)
        if not segments:
            story.append(Paragraph("No transcribed speech available.", st_body))
        for seg in segments:
            color = colors_by_label.get(seg["label"], NAVY)
            tint = _tint(color, 0.12)

            # Avatar: a small colour-filled square with the speaker label,
            # nested so it stays compact (does not stretch to bubble height).
            avatar = Table(
                [[Paragraph(_esc(str(seg["label"])), st_avatar)]],
                colWidths=[9 * mm], rowHeights=[9 * mm],
            )
            avatar.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), HexColor(color)),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]))

            # Bubble content: header (speaker + time) + English translation only.
            bubble: list = [
                Paragraph(
                    f'<font color="{color}"><b>Speaker {seg["label"]}</b></font> &nbsp;'
                    f'<font color="{MUTED}">{format_range(seg["start"], seg["end"])}</font>',
                    st_tsh,
                )
            ]
            if seg.get("text_translated"):
                bubble.append(Paragraph(f'<b>{_esc(seg["text_translated"])}</b>', st_en))
            else:
                bubble.append(Paragraph(
                    '<font color="%s"><i>(no speech translated)</i></font>' % MUTED, st_en))

            row = Table([[avatar, bubble]], colWidths=[11 * mm, 163 * mm])
            row.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                # avatar cell — flush, small right gap to the bubble
                ("LEFTPADDING", (0, 0), (0, 0), 0), ("RIGHTPADDING", (0, 0), (0, 0), 3),
                ("TOPPADDING", (0, 0), (0, 0), 0), ("BOTTOMPADDING", (0, 0), (0, 0), 0),
                # bubble cell — tinted background + speaker-colour edge
                ("BACKGROUND", (1, 0), (1, 0), HexColor(tint)),
                ("LINEBEFORE", (1, 0), (1, 0), 2.5, HexColor(color)),
                ("LEFTPADDING", (1, 0), (1, 0), 9), ("RIGHTPADDING", (1, 0), (1, 0), 9),
                ("TOPPADDING", (1, 0), (1, 0), 6), ("BOTTOMPADDING", (1, 0), (1, 0), 6),
            ]))
            story.append(KeepTogether([row, Spacer(1, 3 * mm)]))

        # ---- Build ---------------------------------------------------------
        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf, pagesize=A4,
            topMargin=26 * mm, bottomMargin=18 * mm, leftMargin=18 * mm, rightMargin=18 * mm,
            title=f"AblePro Speech Analysis Report — {ctx.job_id}", author=BRAND,
        )

        page_count = {"n": 0}

        def _furniture(canvas, doc_):  # type: ignore[no-untyped-def]
            page_count["n"] += 1
            _draw_furniture(canvas, doc_, fonts)

        canvas_maker = _make_numbered_canvas(fonts)
        doc.build(story, onFirstPage=_furniture, onLaterPages=_furniture, canvasmaker=canvas_maker)
        pdf_bytes = buf.getvalue()
        logger.info("report_generated", job_id=ctx.job_id, bytes=len(pdf_bytes), pages=page_count["n"])
        return pdf_bytes, page_count["n"]


# --------------------------------------------------------------------------- #
# Page furniture (slim clinical header + footer)
# --------------------------------------------------------------------------- #
def _draw_furniture(canvas, doc, fonts: dict[str, str]) -> None:  # type: ignore[no-untyped-def]
    from reportlab.lib.colors import HexColor
    from reportlab.lib.units import mm

    width, height = doc.pagesize
    body, bold = fonts["body"], fonts["body_bold"]

    # Header
    canvas.saveState()
    canvas.setFillColor(HexColor(NAVY))
    canvas.setFont(bold, 11)
    canvas.drawString(18 * mm, height - 14 * mm, BRAND)
    canvas.setFont(body, 7.5)
    canvas.setFillColor(HexColor(MUTED))
    canvas.drawString(18 * mm, height - 18 * mm, SUBBRAND)
    canvas.setFont(bold, 8)
    canvas.setFillColor(HexColor(TEAL))
    canvas.drawRightString(width - 18 * mm, height - 14 * mm, DOCTYPE)
    canvas.setStrokeColor(HexColor(NAVY))
    canvas.setLineWidth(1.2)
    canvas.line(18 * mm, height - 21 * mm, width - 18 * mm, height - 21 * mm)
    canvas.setStrokeColor(HexColor(TEAL))
    canvas.setLineWidth(0.5)
    canvas.line(18 * mm, height - 21.8 * mm, width - 18 * mm, height - 21.8 * mm)

    # Footer
    canvas.setStrokeColor(HexColor(HAIR))
    canvas.setLineWidth(0.5)
    canvas.line(18 * mm, 13 * mm, width - 18 * mm, 13 * mm)
    canvas.setFont(body, 6.6)
    canvas.setFillColor(HexColor(MUTED))
    canvas.drawString(18 * mm, 9 * mm, "CONFIDENTIAL — AI-assisted analysis · not a clinical diagnosis")
    canvas.drawCentredString(width / 2, 9 * mm, datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"))
    canvas.restoreState()


# --------------------------------------------------------------------------- #
# Formatting helpers
# --------------------------------------------------------------------------- #
def _fmt_clock(seconds: float | None) -> str:
    if not seconds or seconds <= 0:
        return "—"
    return format_timestamp(seconds)


def _resolve_duration(ctx: ReportContext) -> float | None:
    """Use the probed duration, else fall back to the last transcript timestamp."""
    if ctx.duration_seconds and ctx.duration_seconds > 0:
        return ctx.duration_seconds
    ends = [
        t.get("end", 0.0)
        for s in ctx.speakers
        for t in s.get("segments", [])
    ]
    return max(ends) if ends else None


def _format_features(features: dict | None) -> str:
    if not features:
        return "—"
    parts: list[str] = []
    for key in FEATURE_ORDER:
        val = features.get(key)
        if not isinstance(val, (int, float)):
            continue
        label, unit, prec = FEATURE_LABELS[key]
        parts.append(f"<b>{label}</b> {val:.{prec}f}{unit}")
    if not parts:
        return "—"
    return f' <font color="{HAIR}">·</font> '.join(parts)


def _pct(value: float | None) -> str:
    return f"{value * 100:.1f}%" if value is not None else "n/a"


def _title(value: str | None) -> str:
    return (value or "—").replace("_", " ").title()


def _tint(hex_color: str, amount: float = 0.12) -> str:
    """Return a very light tint of ``hex_color`` (blend toward white).

    ``amount`` is the proportion of the original colour retained (0.12 -> a
    soft 12% wash on white), used for chat-bubble backgrounds.
    """
    h = (hex_color or "").lstrip("#")
    if len(h) != 6:
        return ZEBRA
    try:
        r, g, b = (int(h[i : i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return ZEBRA
    r = round(r * amount + 255 * (1 - amount))
    g = round(g * amount + 255 * (1 - amount))
    b = round(b * amount + 255 * (1 - amount))
    return f"#{r:02X}{g:02X}{b:02X}"


def _esc(text: str) -> str:
    return (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _ordered_segments(ctx: ReportContext) -> list[dict]:
    segs: list[dict] = []
    for s in ctx.speakers:
        for t in s.get("segments", []):
            segs.append({**t, "label": s["label"]})
    segs.sort(key=lambda x: x["start"])
    return segs


# --------------------------------------------------------------------------- #
# ORM -> ReportContext adapter
# --------------------------------------------------------------------------- #
def build_context_from_job(job, user, *, model_note: str | None = None) -> ReportContext:  # type: ignore[no-untyped-def]
    audio = job.audio_file
    speakers: list[dict] = []
    for sp in sorted(job.speakers, key=lambda s: s.label):
        pred = sp.prediction
        speakers.append({
            "label": sp.label,
            "diarization_id": sp.diarization_id,
            "color": sp.color,
            "total_speech_seconds": sp.total_speech_seconds,
            "total_pause_seconds": sp.total_pause_seconds,
            "word_count": sp.word_count,
            "gender": pred.gender.value if pred else "unknown",
            "gender_confidence": pred.gender_confidence if pred else None,
            "age_group": pred.age_group.value if pred else "unknown",
            "age_confidence": pred.age_confidence if pred else None,
            "atypicality": pred.atypicality.value if pred else "unknown",
            "atypicality_score": pred.atypicality_score if pred else None,
            "atypicality_confidence": pred.atypicality_confidence if pred else None,
            "features": pred.features if pred else None,
            "gender_age_source": pred.gender_age_source if pred else "model",
            "segments": [
                {
                    "start": t.start_time,
                    "end": t.end_time,
                    "text_source": t.text_source,
                    "text_translated": t.text_translated,
                }
                for t in sorted(sp.transcriptions, key=lambda t: t.start_time)
            ],
        })

    return ReportContext(
        job_id=str(job.id),
        generated_at=datetime.now(UTC),
        user_name=user.full_name or "",
        user_email=user.email,
        original_filename=audio.original_filename,
        duration_seconds=audio.duration_seconds,
        sample_rate=audio.sample_rate,
        channels=audio.channels,
        detected_speakers=job.detected_speakers or len(job.speakers),
        language_source="kn",
        language_target="en",
        processing_time_seconds=job.processing_time_seconds,
        speakers=speakers,
        model_note=model_note,
    )


_generator: ReportGenerator | None = None


def get_report_generator() -> ReportGenerator:
    global _generator
    if _generator is None:
        _generator = ReportGenerator()
    return _generator
