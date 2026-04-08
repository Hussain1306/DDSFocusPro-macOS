import os
import json
from datetime import datetime

def analiz_log_kaydet(tablo, sonuc, log_dosyasi="logs/analiz_kayitlari.json"):
    try:
        os.makedirs("logs", exist_ok=True)

        log = {
            "tarih": datetime.now().isoformat(),
            "tablo": tablo,
            "sonuc": sonuc,
            "geri_bildirim": "yok"
        }

        loglar = []
        if os.path.exists(log_dosyasi):
            with open(log_dosyasi, "r", encoding="utf-8") as f:
                try:
                    loglar = json.load(f)
                except:
                    loglar = []

        loglar.append(log)

        with open(log_dosyasi, "w", encoding="utf-8") as f:
            json.dump(loglar, f, indent=2, ensure_ascii=False)

        print(f" Log yazld: {tablo}")

    except Exception as e:
        print(f" Log yazlamad: {e}")
def otomasyon_kurallari_olustur(sonuc):
    # rnek basit mantk, OpenAI ile yazlsa daha gl olur
    return [
        {
            "kural": "rnek_kural",
            "aciklama": "Bu bir rnek kuraldr.",
            "eylem": "bildirim_gonder"
        }
    ]

def kurallari_kaydet(kurallar, dosya_yolu="rules/otomasyon_rules.json"):
    import os
    import json
    os.makedirs("rules", exist_ok=True)
    try:
        mevcut_kurallar = []
        if os.path.exists(dosya_yolu):
            with open(dosya_yolu, "r", encoding="utf-8") as f:
                mevcut_kurallar = json.load(f)
        mevcut_kurallar.extend(kurallar)
        with open(dosya_yolu, "w", encoding="utf-8") as f:
            json.dump(mevcut_kurallar, f, indent=2, ensure_ascii=False)
        print(" Kurallar baaryla kaydedildi.")
    except Exception as e:
        print(f" Kurallar kaydedilemedi: {e}")

