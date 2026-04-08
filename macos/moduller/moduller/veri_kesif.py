class VeriKesif:
    """
    Veritabannda otomatik keif ilemleri iin bir snf.
    """

    def __init__(self, veritabani):
        self.veritabani = veritabani

    def tablo_ve_sutunlari_kesfet(self):
        """
        Veritabanndaki tm tablo ve stunlar kefeder.
        """
        sorgu = """
        SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
        LIMIT 1000
        """

        try:
            print(" Fetching table schema...")
            tablolari_sutunlari = self.veritabani.sorgu_calistir(sorgu)

            if not tablolari_sutunlari:
                print(" No tables found or DB returned empty.")
                return {}

            organize_veriler = {}
            for satir in tablolari_sutunlari:
                tablo = satir.get("TABLE_NAME")
                sutun = satir.get("COLUMN_NAME")
                veri_tipi = satir.get("DATA_TYPE")

                if tablo not in organize_veriler:
                    organize_veriler[tablo] = []
                organize_veriler[tablo].append({
                    "sutun": sutun,
                    "veri_tipi": veri_tipi
                })

            print(f" {len(organize_veriler)} tables discovered.")
            return organize_veriler

        except Exception as e:
            print(f" Error during table discovery: {e}")
            return {}

    def veri_analizine_hazirla(self):
        """
        Tablolar ve stunlar analiz iin JSON formatnda hazrlar.
        """
        print(" Veri kefi balatlyor...")
        organize_veriler = self.tablo_ve_sutunlari_kesfet()
        print(" Veri kefi tamamland.")
        return organize_veriler

