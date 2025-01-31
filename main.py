import streamlit as st
import requests
import matplotlib.pyplot as plt
import validators
from bs4 import BeautifulSoup
import json
from openai import OpenAI
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import HexColor
from textwrap import wrap
import io
import base64
import os

# Import all the functions from your original script

def get_color(score):
    """Gibt die Farbe basierend auf dem Punktebereich zurück."""
    if 0 <= score <= 49:
        return 'red'
    elif 50 <= score <= 89:
        return 'yellow'
    elif 90 <= score <= 100:
        return 'green'

def plot_donut(score, title):
    """Plot a donut chart for a given score and title."""
    color = get_color(score)
    labels = [f'{score}%', '']
    sizes = [score, 100 - score]
    colors = [color, 'lightgrey']

    fig, ax = plt.subplots()
    ax.pie(sizes, labels=labels, colors=colors, startangle=90, wedgeprops={'width': 0.3, 'edgecolor': 'white'})
    ax.set(aspect="equal")
    plt.title(title)
    plt.savefig(f"{title.lower()}.png")

SYSTEM_PROMPT = """
Du bist ein Spezialist für SEO-Optimierung. Erstelle einen umfassenden Bericht auf Grundlage dieser Website-Daten. Bei Bedarf kannst du weitere Informationen hinzufügen.
Verwende den Nummerierungsstil. Füge zwischen den Zeilen einen doppelten Zeilenabstand ein. Für eine neue Zeile verwende \n.
"""

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

def draw_wrapped_text(c, text, max_width, x, y, font="Helvetica", font_size=14, line_spacing=16):
    """
    Draws wrapped text on the canvas.
    """
    c.setFont(font, font_size)
    wrapped_text = wrap(text, width=int(max_width / (font_size * 0.5)))
    for i, line in enumerate(wrapped_text):
        c.drawCentredString(x, y - (i * line_spacing), line)

def create_seo_report_cover(pdf_buffer, report_title, website_url):
    c = canvas.Canvas(pdf_buffer, pagesize=A4)
    width, height = A4
    margin = 50
    footer_height = 50
    footer_y_position = 30
    min_y_position = footer_y_position + 10

    # ... (rest of the PDF generation code remains the same)
    # Add Logo
    if report_title:       

        # Add company tagline below the logo
        tagline_y_position = height - 180  # Spacing below the logo
        c.setFont("Helvetica", 14)
        c.drawCentredString(width / 2, tagline_y_position+30, "adojo GmbH")
        c.drawCentredString(width / 2, tagline_y_position, "Ihre Online-Marketing Agentur aus Nürnberg")

    # Add Title (Wrapped)
    title_y_position = height - 250
    draw_wrapped_text(c, report_title, width - 2 * margin, width / 2, title_y_position, font="Helvetica-Bold", font_size=22, line_spacing=24)

    # Add Website URL (Wrapped)
    url_y_position = title_y_position - 80  # Give space below title

    
    draw_wrapped_text(c, "Analysierte URL:", width - 2 * margin, width / 2, url_y_position, font="Helvetica", font_size=14, line_spacing=18)
    draw_wrapped_text(c, url, width - 2 * margin, width / 2, url_y_position - 20, font="Helvetica", font_size=14, line_spacing=18)

    # Add Footer
    footer_height = 50
    footer_y_position = 30  # Distance from bottom
    min_y_position = footer_y_position + 10  # Minimum Y position before new page


    # Draw footer background
    c.setFillColor(HexColor("#007f7f"))
    c.rect(0, footer_y_position - 10, width, footer_height, fill=True, stroke=False)

    # Footer Text
    c.setFillColor("white")  # White text on colored background
    c.setFont("Helvetica", 10)
    footer_text = "adojo GmbH  Königstraße 87 (6. OG)  90402 Nürnberg    Telefon: +49 911 24 030 050    E-Mail: info@adojo.de"
    c.drawCentredString(width / 2, footer_y_position + 10, footer_text)

    # Save PDF
    c.showPage()
    # section 2
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width / 2, height - 100, "Website-Audit und Analyse")
    
    table_width = 2 * 200 + 10  # 2 columns * cell width + spacing
    table_height = 2 * 200 + 10  # 2 rows * cell height + spacing
    table_x = (width - table_width) / 2
    table_y = (height + table_height) / 2 - 210  # Center vertically
    cell_width, cell_height = 200, 200
    
    graph_files = ["performance.png", "accessibility.png", "best-practices.png", "seo.png"]
    
    for i, graph in enumerate(graph_files):
        x = table_x + (i % 2) * (cell_width + 10)
        y = table_y - (i // 2) * (cell_height + 10)
        c.rect(x, y, cell_width, cell_height)
        c.drawImage(graph, x, y, width=cell_width, height=cell_height, preserveAspectRatio=True, mask='auto')
   
    # Footer
    c.setFillColor(HexColor("#007f7f"))
    c.rect(0, footer_y_position - 10, width, footer_height, fill=True, stroke=False)
     
    c.setFillColor("white")  # White text on colored background
    c.setFont("Helvetica", 10)
    footer_text = "adojo GmbH  Königstraße 87 (6. OG)  90402 Nürnberg    Telefon: +49 911 24 030 050    E-Mail: info@adojo.de"
    c.drawCentredString(width / 2, footer_y_position + 10, footer_text)
    c.showPage()


     
     # section 3
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width / 2, height - 80, "Website-Datenanalyse")
    
    start_y = height - 120  # Start position for content

    def check_new_page():
        nonlocal start_y
        if start_y < min_y_position:
            c.showPage()
            start_y = height - 100

    def draw_heading(heading):
        nonlocal start_y
        check_new_page()
        c.setFont("Helvetica-Bold", 14)
        c.drawString(margin, start_y, heading)
        start_y -= 30
    
    def draw_description(description):
        nonlocal start_y
        c.setFont("Helvetica", 10)
        wrapped_desc = wrap(description, width=90)
        for line in wrapped_desc:
            check_new_page()
            c.drawString(margin + 20, start_y, line)
            start_y -= 14
        start_y -= 5  # Extra space after description
    
    def draw_separator():
        nonlocal start_y
        check_new_page()
        c.setFont("Helvetica", 12)
        c.drawString(margin, start_y, "--------------")
        start_y -= 15
    
    # Adding the SEO data
    draw_heading("Seitentitel:")
    draw_description(title if title else "Kein Titel für diese URL gefunden")
    draw_heading("Beschreibung:")
    draw_description("Ein angemessener Titel für diese Seite ist erforderlich" if not title else ("Die Titellänge muss optimiert werden" if len(title) < 50 or len(title) > 60 else "Die Titellänge ist optimal"))
    draw_separator()
    
    draw_heading("Meta-Beschreibung:")
    draw_description(meta_content if meta_content else "Keine Meta-Beschreibung gefunden")
    draw_heading("Beschreibung:")
    draw_description("Muss optimiert werden" if not meta_content or len(meta_content) < 50 or len(meta_content) > 160 else "Die Meta-Beschreibung ist optimal")
    draw_separator()
    
    draw_heading("<h1>-Tag-Anzahl:")
    draw_description(str(len(h1_tags)))
    draw_heading("Beschreibung:")
    draw_description("<h1>-Tags sollten beschreibend und gut strukturiert sein")
    draw_separator()
    
    draw_heading("<h1>-Inhalt:")
    draw_description(h1_content if h1_content else "Keine <h1>-Tags gefunden")
    draw_heading("Beschreibung:")
    draw_description("Korrekte <h1>-Tags verbessern das SEO-Ranking")
    draw_separator()
    
    draw_heading("Bilder ohne Alt-Text:")
    formatted_images = '\n'.join([f"{i+1}. {url}" for i, url in enumerate(image_src_list)])

    draw_description(formatted_images if image_src_list else "Alle Bilder haben Alt-Attribute")

    draw_heading("Beschreibung:")
    draw_description("Ein Bild fehlt der Alt-Text" if len(image_src_list) == 1 else (f"{len(image_src_list)} Bildern fehlt der Alt-Text" if len(image_src_list) > 1 else "Alle Bilder haben Alt-Text"))
    draw_separator()
     # Footer
    c.setFillColor(HexColor("#007f7f"))
    c.rect(0, footer_y_position - 10, width, footer_height, fill=True, stroke=False)
     
    c.setFillColor("white")  # White text on colored background
    c.setFont("Helvetica", 10)
    footer_text = "adojo GmbH  Königstraße 87 (6. OG)  90402 Nürnberg    Telefon: +49 911 24 030 050    E-Mail: info@adojo.de"
    c.drawCentredString(width / 2, footer_y_position + 10, footer_text)
    c.showPage()

    #section 4
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width / 2, height - 80, "KI-gestützte SEO-Empfehlungen")
    
    start_y = height - 120  # Reset start position for new section

    draw_heading("KI-Empfehlungen:")
    paragraphs=ai_recommendations.split("\n")
    for paragraph in paragraphs:
        draw_description(paragraph)
        

    # Footer
    c.setFillColor(HexColor("#007f7f"))
    c.rect(0, footer_y_position - 10, width, footer_height, fill=True, stroke=False)
     
    c.setFillColor("white")  # White text on colored background
    c.setFont("Helvetica", 10)
    footer_text = "adojo GmbH  Königstraße 87 (6. OG)  90402 Nürnberg    Telefon: +49 911 24 030 050    E-Mail: info@adojo.de"
    c.drawCentredString(width / 2, footer_y_position + 10, footer_text)



    c.save()

# The rest of your PDF generation functions remain the same

# Example Usage


st.set_page_config(page_title="SEO-Analyse-Tool", layout="wide")

st.title("SEO-Analyse-Tool")
pic=st.image("adojo.jpg", width=300)
print (st.session_state)
# URL input
url = st.text_input("Geben Sie die Website-URL zur Analyse ein (z. B. https://example.com):")
message_placeholder = st.empty()
if url and validators.url(url):
    message_placeholder.info("Die Website wird analysiert. Dies kann einen Moment dauern...")

    # Fetch and parse website content
    response = requests.get(url)
    soup = BeautifulSoup(response.content.decode("utf-8"), "lxml")

    # Extract website data (title, meta description, H1 tags, images without alt)
    title = soup.title.string if soup.title else ""
    meta_content = soup.find('meta', attrs={'name': 'description'})['content'] if soup.find('meta', attrs={'name': 'description'}) else "Keine Meta-Beschreibung gefunden"
    h1_tags = soup.find_all('h1')
    h1_content = " | ".join(tag.get_text(strip=True) for tag in h1_tags) if h1_tags else "Keine <h1>-Tags gefunden"
    image_src_list = [img['src'] for img in soup.find_all('img', attrs={'alt': ''}) if 'src' in img.attrs]

    # Extract main content
    main_content = soup.find('main')
    elements = (main_content or soup).find_all(['h1', 'h2', 'h3', 'p'])
    cleaned_content = '\n'.join([f"{element.name.upper()}: {element.get_text(separator=' ').strip()}" 
                                 for element in elements]) if elements else ""

    # Fetch Google PageSpeed Insights data
    if GOOGLE_API_KEY:
        params = {"url": url, "strategy": "mobile", "category": ["performance", "accessibility", "best-practices", "seo"], "key": GOOGLE_API_KEY}
        response_google = requests.get("https://www.googleapis.com/pagespeedonline/v5/runPagespeed", params=params)
        scores = {c: round(response_google.json()['lighthouseResult']['categories'][c]['score'] * 100, 1) for c in ['performance', 'accessibility', 'best-practices', 'seo']}
    else:
        raise ValueError("Google API Key is missing. Please provide a valid API key.")
    
    # Structure data for AI
    website_daten = {
        "Titel": {
            "Inhalt": title,
            "Zeichenanzahl": len(title)
        },
        "Meta-Beschreibung": {
            "Inhalt": meta_content,
            "Zeichenanzahl": len(meta_content)
        },
        "<h1>-Tag": {            
            "Inhalt": h1_content,
            "Anzahl": len(h1_tags)
        },
        "Bilder ohne Alt-Text": {
            "Anzahl": len(image_src_list),
            "Quellen": image_src_list
        },
        "Website-Inhalt": cleaned_content,
        "Google API-Bewertungen": scores
    }

    # Get AI recommendations
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        openai_client = OpenAI(api_key=api_key)
        response_ai = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": json.dumps(website_daten, ensure_ascii=False, indent=2)}]
        )
        ai_recommendations = response_ai.choices[0].message.content
    else:
        raise ValueError("OpenAI API Key is missing. Please provide a valid API key.") 

    # Generate PDF report
    pdf_buffer = io.BytesIO()
    create_seo_report_cover(pdf_buffer, "Umfassende SEO-Analyse und Performance-Insights für bessere Rankings", url)
    pdf_buffer.seek(0)

    # Offer PDF download
    st.download_button(
        label="Vollständigen SEO-Bericht herunterladen (PDF)",
        data=pdf_buffer,
        file_name="seo_bericht.pdf",
        mime="application/pdf"
    )
    message_placeholder.empty()

elif url:
    st.error("Ungültige URL. Bitte geben Sie eine korrekte Website-URL ein.")

