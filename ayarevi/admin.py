from django.contrib import admin
from .models import MusteriProfili, Rapor, HesaplamaKaydi

@admin.register(MusteriProfili)
class MusteriProfiliAdmin(admin.ModelAdmin):
    list_display = ('firma_adi', 'telefon', 'ek_telefonlar', 'user')
    search_fields = ('firma_adi', 'telefon', 'ek_telefonlar', 'user__username')
    list_filter = ('zorunlu_sifre_degisimi',)

@admin.register(Rapor)
class RaporAdmin(admin.ModelAdmin):
    list_display = ('rapor_no', 'musteri', 'analiz_cinsi', 'tarih', 'altin_binde')
    search_fields = ('rapor_no', 'musteri__firma_adi')
    list_filter = ('tarih', 'analiz_cinsi')

@admin.register(HesaplamaKaydi)
class HesaplamaKaydiAdmin(admin.ModelAdmin):
    list_display = ('musteri', 'islem_turu', 'tarih', 'sonuc')
    search_fields = ('musteri__firma_adi', 'islem_turu', 'detay')
    list_filter = ('islem_turu', 'tarih')