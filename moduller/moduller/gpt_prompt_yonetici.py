import json
import os
from datetime import datetime

def gpt_analiz_prompt_olustur(yeni_veri, log_dosyasi="logs/analiz_kayitlari.json", max_gecmis=5):
    """
    Yeni veriyi analiz ettirmek iin GPT'ye balaml bir prompt hazrlar.
    """
    gecmis_prompt = ""

    if os.path.exists(log_dosyasi):
        with open(log_dosyasi, "r", encoding="utf-8") as f:
            try:
                loglar = json.load(f)
                loglar = sorted(loglar, key=lambda x: x.get("tarih", ""), reverse=True)[:max_gecmis]
            except:
                loglar = []

            for log in loglar:
                tarih = log.get("tarih", "?")
                tablo = log.get("tablo", "?")
                sonuc = log.get("sonuc", "")
                feedback = log.get("geri_bildirim", "yok")
                gecmis_prompt += f"\n[Tarih: {tarih}] Tablo: {tablo} | Geri Bildirim: {feedback}\n{sonuc}\n"

    prompt = f"""
Sen deneyimli bir veri analistisin. Grevin, yapsal verileri analiz ederek anlaml karmlar sunmak.

Aada baz nceki analizlerin ve aldn geri bildirimlerin kaytlar var. Bunlardan ders kar.
Sonrasnda yeni tablo yapsn analiz et.

{gecmis_prompt}

[Yeni Tablo Verisi]:
{json.dumps(yeni_veri, indent=2, ensure_ascii=False)}

Yorumunda unlara dikkat et:
- Kolonlar arasndaki balantlar
- Veri tipi dzenlilii
- Potansiyel problemler (bo deerler, anlamsz adlar)
- nerilebilecek otomasyon kurallar

Ltfen detayl ve teknik bir analiz sun.
"""

    return prompt

