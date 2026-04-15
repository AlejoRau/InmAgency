# AgentTool — InmoAgency

Herramienta web interna para agentes inmobiliarios. Genera descripciones profesionales y copies de Instagram a partir de un formulario con los datos de una propiedad.

## Stack
- **Backend**: Python + FastAPI
- **Frontend**: HTML/CSS/JS vanilla (Jinja2 templates)
- **IA**: OpenAI GPT-4o-mini
- **Fotos**: Cloudinary (almacenamiento en la nube)
- **Deploy**: Vercel (producción) / uvicorn (local)

## Correr en local
```bash
pip install -r requirements.txt
uvicorn main:app --reload
# http://localhost:8000
```

## Variables de entorno (.env)
```
OPENAI_API_KEY=
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=
```

## Estructura
```
main.py              — FastAPI app, endpoints, lógica OpenAI + Cloudinary
templates/
  index.html         — Formulario (6 secciones)
  result.html        — Página de resultados con botones de copia
static/
  css/style.css      — Diseño (paleta azul navy + dorado)
  js/app.js          — Preview fotos, spinner, copiar al portapapeles
uploads/             — Solo en local (en producción usa Cloudinary)
vercel.json          — Configuración deploy Vercel
```

## Contexto del negocio
- Agencia inmobiliaria en Argentina (venta y alquiler residencial)
- Agentes publican 3-5 propiedades por semana
- Propiedades: casas, departamentos, terrenos, penthouses
- Precios en USD
- Textos generados en español rioplatense
