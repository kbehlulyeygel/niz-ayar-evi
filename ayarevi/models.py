from django.db import models
from django.contrib.auth.models import User

class MusteriProfili(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profil')
    firma_adi = models.CharField(max_length=150, verbose_name="Firma / Müşteri Adı")
    telefon = models.CharField(max_length=20, verbose_name="Ana Telefon Numarası", blank=True, null=True)
    ek_telefonlar = models.CharField(max_length=250, verbose_name="Ek Telefon Numaraları (Virgülle Ayırarak Yazınız)", blank=True, null=True)
    adres = models.TextField(verbose_name="Firma Adresi", blank=True, null=True)
    zorunlu_sifre_degisimi = models.BooleanField(default=True, verbose_name="İlk Girişte Şifre Değiştirsin mi?")

    class Meta:
        verbose_name = "Müşteri Profili"
        verbose_name_plural = "Müşteri Profilleri"

    def __str__(self):
        return self.firma_adi

class Rapor(models.Model):
    musteri = models.ForeignKey(MusteriProfili, on_delete=models.CASCADE, related_name='raporlar')
    rapor_no = models.CharField(max_length=50, verbose_name="Rapor No")
    analiz_cinsi = models.CharField(max_length=100, verbose_name="Analiz Cinsi")
    takoz_agirligi = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Takoz Ağırlığı (gr)")
    cesni_agirligi = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Çeşni Ağırlığı (gr)")
    altin_binde = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="Altın Binde")
    gumus_binde = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="Gümüş Binde")
    tarih = models.DateTimeField(auto_now_add=True, verbose_name="İşlem Tarihi")

    class Meta:
        verbose_name = "Analiz Raporu"
        verbose_name_plural = "Analiz Raporları"

    def __str__(self):
        return f"{self.rapor_no} - {self.musteri.firma_adi}"

class HesaplamaKaydi(models.Model):
    musteri = models.ForeignKey(MusteriProfili, on_delete=models.CASCADE, related_name='hesaplamalar')
    islem_turu = models.CharField(max_length=50, verbose_name="İşlem Türü")
    detay = models.TextField(verbose_name="İşlem Detayı / Girdiler")
    sonuc = models.TextField(verbose_name="Hesaplanan Sonuç")
    tarih = models.DateTimeField(auto_now_add=True, verbose_name="İşlem Zamanı")

    class Meta:
        verbose_name = "Hesaplama Kaydı"
        verbose_name_plural = "Hesaplama Kayıtları"

    def __str__(self):
        return f"{self.musteri.firma_adi} - {self.islem_turu}"