from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from PIL import Image
import pytesseract
import io
import cv2
import numpy as np


def scrape_url(url: str) -> dict:
    """
    Scrapes a JS-rendered webpage using Playwright and extracts:
    - Blog content
    - Service / landing page blocks
    - Headings
    - OCR image text
    """

    # ---------- Fetch rendered HTML ---------- #
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(url, timeout=30000)

        # Wait until page fully loads
        page.wait_for_load_state("networkidle")

        # ---------- OCR IMAGE EXTRACTION ---------- #
        image_texts = []

        images = page.locator("img")
        img_count = images.count()

        for i in range(img_count):
            try:
                src = images.nth(i).get_attribute("src")
                if not src or src.startswith("data:"):
                    continue

                img_bytes = page.evaluate(
                    """async (src) => {
                        const res = await fetch(src);
                        const buf = await res.arrayBuffer();
                        return Array.from(new Uint8Array(buf));
                    }""",
                    src
                )

                img_bytes = bytes(img_bytes)

                image = Image.open(io.BytesIO(img_bytes)).convert("RGB")
                open_cv_img = np.array(image)
                gray = cv2.cvtColor(open_cv_img, cv2.COLOR_RGB2GRAY)
                gray = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)[1]

                text = pytesseract.image_to_string(gray)

                if text and len(text.strip()) > 15:
                    image_texts.append(text.strip())

            except Exception:
                continue

        html = page.content()
        browser.close()

    # ---------- Parse HTML ---------- #
    soup = BeautifulSoup(html, "html.parser")

    # Remove noise containers
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
        tag.decompose()

    title = soup.title.string.strip() if soup.title else ""

    # ---------- Extract Headings ---------- #
    headings = []
    for h in soup.find_all(["h1", "h2", "h3"]):
        txt = h.get_text(strip=True)
        if txt:
            headings.append({"level": h.name, "text": txt})

    # ---------- Extract Main Content Safely ---------- #
    sections = []

    # 1️⃣ Blog posts (like your missing <p>)
    main_blog = soup.select_one(".wp-block-post-content, .entry-content")

    if main_blog:
        content = main_blog.get_text(separator=" ", strip=True)
        if content and len(content) > 100:
            sections.append({
                "header": title,
                "content": content
            })

    # 2️⃣ Service / Landing page blocks
    for section in soup.select(
        ".wp-block-uagb-container, .uagb-container, .wp-block-group"
    ):
        content = section.get_text(separator=" ", strip=True)

        if content and len(content) > 80:
            sections.append({
                "header": None,
                "content": content
            })

    # ---------- Build Final Text ---------- #
    final_text_parts = []

    for sec in sections:
        if sec["header"]:
            final_text_parts.append(sec["header"])
        final_text_parts.append(sec["content"])

    # Merge OCR text
    if image_texts:
        final_text_parts.append("Text extracted from images:")
        for t in set(image_texts):
            final_text_parts.append(t)

    # Fallback if sections empty
    if not final_text_parts:
        body_text = soup.get_text(separator="\n", strip=True)
        final_text_parts.append(body_text)

    final_text = "\n\n".join(final_text_parts)
    final_text = final_text.replace("\xa0", " ").strip()

    return {
        "text": final_text,
        "title": title,
        "headings": headings,
        "tables": [],
        "image_texts": list(set(image_texts))
    }
