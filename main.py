import os
import tempfile
from pathlib import Path
from typing import List

import cloudinary
import cloudinary.uploader
import requests as http_client
from fastapi import FastAPI, Form, File, UploadFile, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fpdf import FPDF
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="AgentTool — InmoAgency")

BASE_DIR = Path(__file__).parent

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

templates = Jinja2Templates(directory=BASE_DIR / "templates")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
)


def build_property_summary(
    tipo: str,
    operacion: str,
    direccion: str,
    ciudad: str,
    provincia: str,
    precio: str,
    recamaras: str,
    banos: str,
    m2_construidos: str,
    m2_terreno: str,
    estacionamientos: str,
    amenidades: List[str],
    descripcion_agente: str,
) -> str:
    amenidades_str = ", ".join(amenidades) if amenidades else "ninguna especificada"
    return f"""
Tipo de propiedad: {tipo}
Operación: {operacion}
Dirección: {direccion}
Ciudad: {ciudad}, {provincia}
Precio: USD {precio}
Recámaras: {recamaras}
Baños: {banos}
Metros construidos: {m2_construidos} m²
Metros de terreno: {m2_terreno} m²
Estacionamientos: {estacionamientos}
Amenidades: {amenidades_str}
Notas del agente: {descripcion_agente}
""".strip()


def generate_professional_description(property_summary: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "Sos un redactor inmobiliario experto en el mercado argentino. "
                    "Escribís descripciones profesionales, atractivas y convincentes de propiedades. "
                    "Usás un tono formal pero cálido, en español rioplatense. "
                    "Destacás los puntos fuertes, la ubicación y el estilo de vida que ofrece la propiedad. "
                    "Nunca inventás datos que no te dieron. La descripción debe tener entre 150 y 200 palabras."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Escribí una descripción profesional para la siguiente propiedad:\n\n{property_summary}"
                ),
            },
        ],
        temperature=0.75,
        max_tokens=400,
    )
    return response.choices[0].message.content.strip()


def generate_instagram_copy(property_summary: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "Sos un experto en marketing inmobiliario para redes sociales en Argentina. "
                    "Creás copies para Instagram que generan interés y consultas. "
                    "Usás emojis estratégicamente, lenguaje dinámico y cercano. "
                    "El copy debe tener máximo 150 palabras más los hashtags. "
                    "Al final incluís entre 15 y 20 hashtags relevantes para el sector inmobiliario argentino, "
                    "populares y en español (ej: #propiedadesargentina #inmobiliaria #casaenventa #departamento #bienesraices)."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Creá un copy para Instagram para la siguiente propiedad:\n\n{property_summary}"
                ),
            },
        ],
        temperature=0.8,
        max_tokens=400,
    )
    return response.choices[0].message.content.strip()


def upload_to_cloudinary(upload: UploadFile) -> str:
    result = cloudinary.uploader.upload(
        upload.file,
        folder="inmoagency",
        resource_type="image",
    )
    return result["secure_url"]


# ── PDF helpers ────────────────────────────────────────────────────────────────

def _safe(text: str) -> str:
    """Encode text to Latin-1 for fpdf2 core fonts (covers all Spanish chars)."""
    return text.encode("latin-1", errors="replace").decode("latin-1")


def _download_image(url: str) -> str | None:
    """Download image URL to a temp file. Returns local path or None on failure."""
    try:
        resp = http_client.get(url, timeout=10)
        resp.raise_for_status()
        ext = ".png" if ".png" in url.lower() else ".jpg"
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
        tmp.write(resp.content)
        tmp.close()
        return tmp.name
    except Exception:
        return None


def generate_pdf_bytes(
    tipo: str,
    operacion: str,
    direccion: str,
    ciudad: str,
    provincia: str,
    precio: str,
    recamaras: str,
    banos: str,
    m2_construidos: str,
    m2_terreno: str,
    estacionamientos: str,
    amenidades: List[str],
    descripcion_profesional: str,
    nombre_agente: str,
    telefono_agente: str,
    email_agente: str,
    cover_photo: str,
    extra_photos: List[str],
) -> bytes:
    NAVY   = (26,  46,  74)
    GOLD   = (201, 168, 76)
    WHITE  = (255, 255, 255)
    DARK   = (40,  40,  40)
    GRAY   = (100, 100, 100)
    LIGHT  = (245, 246, 248)

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_left_margin(15)
    pdf.set_right_margin(15)

    temp_files: list[str] = []

    try:
        # ── HEADER ──────────────────────────────────────────────────────────
        pdf.set_fill_color(*NAVY)
        pdf.rect(0, 0, 210, 24, "F")
        pdf.set_xy(15, 5)
        pdf.set_text_color(*GOLD)
        pdf.set_font("Helvetica", "B", 17)
        pdf.cell(180, 8, "AgentTool", align="C")
        pdf.set_xy(15, 14)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*WHITE)
        pdf.cell(180, 5, "by InmoAgency", align="C")
        pdf.set_y(29)

        # ── COVER PHOTO ─────────────────────────────────────────────────────
        if cover_photo:
            path = _download_image(cover_photo)
            if path:
                temp_files.append(path)
                pdf.image(path, x=15, y=pdf.get_y(), w=180, h=88)
                pdf.set_y(pdf.get_y() + 91)

        # ── TITLE BLOCK ─────────────────────────────────────────────────────
        pdf.set_text_color(*NAVY)
        pdf.set_font("Helvetica", "B", 17)
        pdf.cell(0, 9, _safe(f"{tipo} en {operacion}"), ln=True, align="C")

        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*GRAY)
        pdf.cell(0, 5, _safe(f"{direccion}, {ciudad}, {provincia}"), ln=True, align="C")

        pdf.set_font("Helvetica", "B", 15)
        pdf.set_text_color(*GOLD)
        pdf.cell(0, 8, f"USD {precio}", ln=True, align="C")
        pdf.ln(5)

        # ── SPECS ROW ───────────────────────────────────────────────────────
        specs: list[tuple[str, str]] = []
        if recamaras and recamaras != "0":
            specs.append(("Recamaras", recamaras))
        if banos:
            specs.append(("Banos", banos))
        if m2_construidos:
            specs.append(("M2 construidos", f"{m2_construidos} m2"))
        if m2_terreno and m2_terreno != "0":
            specs.append(("M2 terreno", f"{m2_terreno} m2"))
        if estacionamientos and estacionamientos != "0":
            specs.append(("Estacionamientos", estacionamientos))

        if specs:
            col_w = 180 / len(specs)
            start_y = pdf.get_y()
            for i, (label, value) in enumerate(specs):
                x = 15 + i * col_w
                pdf.set_fill_color(*LIGHT)
                pdf.set_draw_color(200, 200, 200)
                pdf.rect(x, start_y, col_w, 15, "FD")
                pdf.set_xy(x, start_y + 1)
                pdf.set_font("Helvetica", "B", 12)
                pdf.set_text_color(*NAVY)
                pdf.cell(col_w, 6, _safe(value), align="C")
                pdf.set_xy(x, start_y + 8)
                pdf.set_font("Helvetica", "", 7)
                pdf.set_text_color(*GRAY)
                pdf.cell(col_w, 5, _safe(label), align="C")
            pdf.set_y(start_y + 19)

        # ── AMENIDADES ──────────────────────────────────────────────────────
        if amenidades:
            pdf.set_fill_color(*NAVY)
            pdf.set_text_color(*WHITE)
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 8, "  Amenidades", ln=True, fill=True)
            pdf.ln(2)

            tag_w = 57
            per_row = 3
            for i, am in enumerate(amenidades):
                if i % per_row == 0:
                    pdf.set_x(15)
                pdf.set_fill_color(238, 242, 247)
                pdf.set_text_color(*NAVY)
                pdf.set_font("Helvetica", "", 9)
                pdf.cell(tag_w, 6, _safe(f"  \u2022  {am}"), fill=True)
                if (i + 1) % per_row == 0:
                    pdf.ln()
            if len(amenidades) % per_row != 0:
                pdf.ln()
            pdf.ln(5)

        # ── PROFESSIONAL DESCRIPTION ────────────────────────────────────────
        pdf.set_fill_color(*NAVY)
        pdf.set_text_color(*WHITE)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 8, "  Descripcion profesional", ln=True, fill=True)
        pdf.ln(3)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*DARK)
        pdf.multi_cell(0, 5.5, _safe(descripcion_profesional))
        pdf.ln(5)

        # ── EXTRA PHOTOS GALLERY ────────────────────────────────────────────
        if extra_photos:
            pdf.set_fill_color(*NAVY)
            pdf.set_text_color(*WHITE)
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 8, "  Galeria de fotos", ln=True, fill=True)
            pdf.ln(3)

            img_w, img_h, gap, per_row = 55, 40, 5, 3
            row_y = pdf.get_y()
            placed = 0

            for photo_url in extra_photos[:9]:
                path = _download_image(photo_url)
                if not path:
                    continue
                temp_files.append(path)
                col = placed % per_row
                if col == 0 and placed > 0:
                    row_y += img_h + gap
                    if row_y + img_h > 280:
                        pdf.add_page()
                        row_y = pdf.get_y()
                pdf.image(path, x=15 + col * (img_w + gap), y=row_y, w=img_w, h=img_h)
                placed += 1

            if placed > 0:
                last_row_full = placed % per_row == 0
                pdf.set_y(row_y + img_h + (gap if last_row_full else gap) + 3)

        # ── AGENT FOOTER ────────────────────────────────────────────────────
        pdf.set_fill_color(*NAVY)
        pdf.set_text_color(*WHITE)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 8, "  Agente de contacto", ln=True, fill=True)
        pdf.ln(3)
        pdf.set_text_color(*NAVY)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 6, _safe(nombre_agente), ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*GRAY)
        pdf.cell(0, 5, f"Tel: {telefono_agente}", ln=True)
        pdf.cell(0, 5, f"Email: {email_agente}", ln=True)

    finally:
        for f in temp_files:
            try:
                os.unlink(f)
            except Exception:
                pass

    return bytes(pdf.output())


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.post("/generate", response_class=HTMLResponse)
async def generate(
    request: Request,
    tipo: str = Form(...),
    operacion: str = Form(...),
    direccion: str = Form(...),
    ciudad: str = Form(...),
    provincia: str = Form(...),
    precio: str = Form(...),
    recamaras: str = Form("0"),
    banos: str = Form(...),
    m2_construidos: str = Form(...),
    m2_terreno: str = Form("0"),
    estacionamientos: str = Form("0"),
    amenidades: List[str] = Form(default=[]),
    descripcion_agente: str = Form(...),
    nombre_agente: str = Form(...),
    telefono_agente: str = Form(...),
    email_agente: str = Form(...),
    fotos: List[UploadFile] = File(default=[]),
):
    # Upload photos to Cloudinary
    photo_urls = []
    for foto in fotos:
        if foto.filename:
            url = upload_to_cloudinary(foto)
            photo_urls.append(url)

    cover_photo = photo_urls[0] if photo_urls else None
    extra_photos = photo_urls[1:] if len(photo_urls) > 1 else []

    # Build property summary for prompts
    summary = build_property_summary(
        tipo, operacion, direccion, ciudad, provincia, precio,
        recamaras, banos, m2_construidos, m2_terreno, estacionamientos,
        amenidades, descripcion_agente,
    )

    # Generate content with OpenAI
    try:
        descripcion_profesional = generate_professional_description(summary)
        copy_instagram = generate_instagram_copy(summary)
        error = None
    except Exception as e:
        descripcion_profesional = ""
        copy_instagram = ""
        error = str(e)

    return templates.TemplateResponse(
        request,
        "result.html",
        {
            "tipo": tipo,
            "operacion": operacion,
            "direccion": direccion,
            "ciudad": ciudad,
            "provincia": provincia,
            "precio": precio,
            "recamaras": recamaras,
            "banos": banos,
            "m2_construidos": m2_construidos,
            "m2_terreno": m2_terreno,
            "estacionamientos": estacionamientos,
            "amenidades": amenidades,
            "descripcion_profesional": descripcion_profesional,
            "copy_instagram": copy_instagram,
            "cover_photo": cover_photo,
            "extra_photos": extra_photos,
            "nombre_agente": nombre_agente,
            "telefono_agente": telefono_agente,
            "email_agente": email_agente,
            "error": error,
        },
    )


@app.post("/pdf")
async def download_pdf(
    tipo: str = Form(...),
    operacion: str = Form(...),
    direccion: str = Form(...),
    ciudad: str = Form(...),
    provincia: str = Form(...),
    precio: str = Form(...),
    recamaras: str = Form("0"),
    banos: str = Form(""),
    m2_construidos: str = Form(""),
    m2_terreno: str = Form("0"),
    estacionamientos: str = Form("0"),
    amenidades: List[str] = Form(default=[]),
    descripcion_profesional: str = Form(""),
    nombre_agente: str = Form(""),
    telefono_agente: str = Form(""),
    email_agente: str = Form(""),
    cover_photo: str = Form(""),
    extra_photos: List[str] = Form(default=[]),
):
    pdf_bytes = generate_pdf_bytes(
        tipo, operacion, direccion, ciudad, provincia, precio,
        recamaras, banos, m2_construidos, m2_terreno, estacionamientos,
        amenidades, descripcion_profesional, nombre_agente, telefono_agente,
        email_agente, cover_photo, extra_photos,
    )
    filename = f"propiedad-{tipo}-{ciudad}.pdf".replace(" ", "-").lower()
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
