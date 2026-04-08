import pymysql
from .config_manager import config_manager

class VeritabaniYoneticisi:
    """
    Veritaban ilemlerini gerekletirmek iin bir snf.
    """

    def __init__(self, host=None, user=None, password=None, database=None, port=None):
        # Get database credentials from configuration manager
        db_config = config_manager.get_database_credentials()
        
        self.host = host or db_config.get("host", "92.113.22.65")
        self.user = user or db_config.get("user", "u906714182_sqlrrefdvdv")
        self.password = password or db_config.get("password", "3@6*t:lU")
        self.database = database or db_config.get("database", "u906714182_sqlrrefdvdv")
        self.port = port or db_config.get("port", 3306)
        self.connection = None
        
        print(f"[DEBUG] Database config loaded: {self.host}:{self.port}/{self.database}")

    def baglanti_olustur(self):
        """
        Veritabanna balant kurar.
        """
        try:
            self.connection = pymysql.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                port=self.port,
                cursorclass=pymysql.cursors.DictCursor
            )
            print("[SUCCESS] Veritabanna baaryla balanld.")
        except Exception as e:
            print(f"[ERROR] Veritaban balant hatas: {e}")
            self.connection = None

    def baglanti_testi(self):
        """
        Veritaban balantsnn geerli olup olmadn kontrol eder.
        """
        return self.connection is not None

    def sorgu_calistir(self, sorgu, degerler=None):
        """
        Verilen SQL sorgusunu altrr ve sonucu dndrr.
        """
        if not self.connection:
            raise ConnectionError(" Veritaban balants kurulamad.")
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(sorgu, degerler)
                return cursor.fetchall()
        except Exception as e:
            print(f"[ERROR] Sorgu altrma hatas: {e}")
            return None

    def komut_calistir(self, komut, degerler=None):
        """
        Verilen SQL komutunu altrr (INSERT, UPDATE, DELETE gibi).
        """
        if not self.connection:
            raise ConnectionError(" Veritaban balants kurulamad.")
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(komut, degerler)
                self.connection.commit()
                print(f"[SUCCESS] {cursor.rowcount} satr etkilendi.")
        except Exception as e:
            print(f"[ERROR] Komut altrma hatas: {e}")
            self.connection.rollback()

    def kapat(self):
        """
        Veritaban balantsn kapatr.
        """
        if self.connection:
            self.connection.close()
            print("[SUCCESS] Veritaban balants kapatld.")

