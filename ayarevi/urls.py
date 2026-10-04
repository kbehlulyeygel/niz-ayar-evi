from django.urls import path
from . import views

urlpatterns = [
    path('', views.anasayfa, name='anasayfa'),
    path('giris/', views.giris_yap, name='giris'),
    path('cikis/', views.cikis_yap, name='cikis'),
    path('sifre-degistir/', views.sifre_degistir, name='sifre_degistir'),
    path('panel/', views.musteri_paneli, name='musteri_paneli'),
    path('islem-kaydet/', views.islem_kaydet, name='islem_kaydet'),
    path('rapor/<int:rapor_id>/pdf/', views.rapor_pdf_indir, name='rapor_pdf_indir'),
]