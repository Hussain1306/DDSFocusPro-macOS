# moduller/yardimci.py
import json
import os
from datetime import datetime


def analiz_log_kaydet(tablo_adi, analiz_sonucu):
    """
    GPT analiz sonucunu logs/analiz_kayitlari.json dosyasna kaydeder.
    """
    os.makedirs("logs", exist_ok=True)
    log_dosyasi = "logs/analiz_kayitlari.json"
    loglar = []

    if os.path.exists(log_dosyasi):
        with open(log_dosyasi, "r", encoding="utf-8") as f:
            try:
                loglar = json.load(f)
            except:
                loglar = []

    loglar.append({
        "tarih": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "tablo": tablo_adi,
        "sonuc": analiz_sonucu,
        "geri_bildirim": None
    })

    with open(log_dosyasi, "w", encoding="utf-8") as f:
        json.dump(loglar, f, indent=2, ensure_ascii=False)


def geri_bildirim_ekle(tablo_adi, yorum, log_dosyasi="logs/analiz_kayitlari.json"):
    """
    Belirtilen tabloya ait son GPT analiz kaydna kullanc geri bildirimi ekler.
    """
    if not os.path.exists(log_dosyasi):
        return False

    try:
        with open(log_dosyasi, "r+", encoding="utf-8") as f:
            loglar = json.load(f)
            # En son bu tabloya ait analiz kaydn bul
            for log in reversed(loglar):
                if log["tablo"] == tablo_adi and (log["geri_bildirim"] in [None, "", "yok"]):
                    log["geri_bildirim"] = yorum
                    break
            f.seek(0)
            f.truncate()
            json.dump(loglar, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f" Feedback update failed: {e}")
        return False

