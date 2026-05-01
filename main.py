import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class UrlRequest(BaseModel):
    url: str

def scrape_site(url):
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
    soup = BeautifulSoup(response.text, "html.parser")

    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()

    text = " ".join(soup.get_text(" ").split())
    return text[:8000]

@app.post("/find-delivery-partner")
def find_delivery_partner(req: UrlRequest):
    text = scrape_site(req.url)

    prompt = f"""
You are analysing an ecommerce website.

Find any mentioned delivery partners or carriers, such as Royal Mail, DPD, DHL, Evri, FedEx, UPS, Yodel, etc.

Return only this JSON:
{{
  "delivery_partner": "name or unknown",
  "evidence": "short quote or explanation",
  "confidence": "low, medium, or high"
}}

Website text:
{text}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        response_format={"type": "json_object"},
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content