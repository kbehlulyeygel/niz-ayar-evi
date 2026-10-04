import os
import json
from io import BytesIO

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse, Http404
from django.template.loader import get_template
from django.conf import settings
from django.contrib.staticfiles import finders

from xhtml2pdf import pisa
from .models import MusteriProfili, Rapor, HesaplamaKaydi


def link_callback(uri, rel):
    """
    xhtml2pdf motorunun statik dosyaları (logo, fontlar vb.) 
    diskte doğru bulabilmesi için dosya yollarını çözer.
    """
    result = finders.find(uri)
    if result:
        if not isinstance(result, (list, tuple)):
            result = [result]
        result = result[0]
    else:
        s_url = settings.STATIC_URL
        if uri.startswith(s_url):
            uri_clean = uri[len(s_url):]
        else:
            uri_clean = uri.lstrip('/')

        s_root = getattr(settings, 'STATIC_ROOT', None)
        if s_root and os.path.exists(os.path.join(s_root, uri_clean)):
            result = os.path.join(s_root, uri_clean)
        else:
            result = os.path.join(settings.BASE_DIR, 'static', uri_clean)

    if not os.path.isfile(result):
        alt_path = os.path.join(settings.BASE_DIR, uri.lstrip('/'))
        if os.path.isfile(alt_path):
            return alt_path

    return result


def anasayfa(request):
    """Halka açık ana sayfa ve hesaplama motoru."""
    return render(request, 'index.html')


def giris_yap(request):
    """Müşteri giriş ekranı. Başarılı girişte doğrudan ana sayfaya yönlendirir."""
    if request.user.is_authenticated:
        return redirect('anasayfa')

    hata = None
    if request.method == 'POST':
        kullanici_adi = request.POST.get('username')
        sifre = request.POST.get('password')
        user = authenticate(request, username=kullanici_adi, password=sifre)

        if user is not None:
            login(request, user)
            if user.is_superuser:
                return redirect('/admin/')

            if hasattr(user, 'profil'):
                if user.profil.zorunlu_sifre_degisimi:
                    return redirect('sifre_degistir')
                return redirect('anasayfa')
            return redirect('anasayfa')
        else:
            hata = "Kullanıcı adı veya şifre hatalı."

    return render(request, 'giris.html', {'hata': hata})


def cikis_yap(request):
    """Oturumu sonlandırır ve ana sayfaya yönlendirir."""
    logout(request)
    return redirect('anasayfa')


@login_required
def sifre_degistir(request):
    """Müşterinin şifre yenilediği ekran."""
    hata = None
    if request.method == 'POST':
        yeni_sifre = request.POST.get('yeni_sifre')
        yeni_sifre_tekrar = request.POST.get('yeni_sifre_tekrar')

        if not yeni_sifre or len(yeni_sifre) < 6:
            hata = "Şifreniz en az 6 karakter olmalıdır."
        elif yeni_sifre != yeni_sifre_tekrar:
            hata = "Girdiğiniz şifreler birbiriyle eşleşmiyor."
        else:
            request.user.set_password(yeni_sifre)
            request.user.save()
            update_session_auth_hash(request, request.user)

            if hasattr(request.user, 'profil'):
                request.user.profil.zorunlu_sifre_degisimi = False
                request.user.profil.save()

            return redirect('anasayfa')

    return render(request, 'sifre_degistir.html', {'hata': hata})


@login_required
def musteri_paneli(request):
    """Müşteri analiz portalı."""
    if not hasattr(request.user, 'profil'):
        return redirect('/admin/')

    profil = request.user.profil
    if profil.zorunlu_sifre_degisimi:
        return redirect('sifre_degistir')

    raporlar = profil.raporlar.all().order_by('-tarih', '-id')
    son_rapor = raporlar.first()
    hesaplamalar = profil.hesaplamalar.all().order_by('-tarih')

    return render(request, 'panel.html', {
        'profil': profil,
        'son_rapor': son_rapor,
        'raporlar': raporlar,
        'hesaplamalar': hesaplamalar,
    })


@login_required
def islem_kaydet(request):
    """Müşterinin yaptığı hesaplamaları arka planda kaydeden AJAX uç noktası."""
    if request.method == 'POST':
        try:
            if not hasattr(request.user, 'profil'):
                return JsonResponse({'status': 'error', 'message': 'Müşteri profili bulunamadı.'}, status=400)

            data = json.loads(request.body)
            HesaplamaKaydi.objects.create(
                musteri=request.user.profil,
                islem_turu=data.get('islem_turu'),
                detay=data.get('detay'),
                sonuc=data.get('sonuc')
            )
            return JsonResponse({'status': 'ok'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'invalid method'}, status=405)


@login_required
def rapor_pdf_indir(request, rapor_id):
    """
    A5 formatında Türkçe karakter ve LOGO destekli analiz raporu üretir.
    """
    if not hasattr(request.user, 'profil'):
        raise Http404("Yetkisiz erişim.")

    profil = request.user.profil
    rapor = get_object_or_404(Rapor, id=rapor_id, musteri=profil)

    # 1. TÜRKÇE FONT DOSYALARI
    font_regular = os.path.join(settings.BASE_DIR, 'static', 'fonts', 'Arial.ttf')
    font_bold = os.path.join(settings.BASE_DIR, 'static', 'fonts', 'Arial-Bold.ttf')

    if not os.path.exists(font_regular):
        for f_path in [
            os.path.join(settings.BASE_DIR, 'static', 'fonts', 'arial.ttf'),
            '/System/Library/Fonts/Supplemental/Arial.ttf',
            '/Library/Fonts/Arial.ttf',
        ]:
            if os.path.exists(f_path):
                font_regular = f_path
                break

    if not os.path.exists(font_bold):
        for f_path in [
            os.path.join(settings.BASE_DIR, 'static', 'fonts', 'arial-bold.ttf'),
            os.path.join(settings.BASE_DIR, 'static', 'fonts', 'Arial_Bold.ttf'),
            os.path.join(settings.BASE_DIR, 'static', 'fonts', 'ArialBold.ttf'),
            '/System/Library/Fonts/Supplemental/Arial Bold.ttf',
            '/Library/Fonts/Arial Bold.ttf',
            '/System/Library/Fonts/Supplemental/Arial-Bold.ttf',
            '/Library/Fonts/Arial-Bold.ttf',
        ]:
            if os.path.exists(f_path):
                font_bold = f_path
                break

    # 2. KURUMSAL LOGO DOSYA YOLU (PDF İÇİN GERİ EKLENDİ)
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'logo.png')

    template = get_template('rapor_a5_pdf.html')
    context = {
        'rapor': rapor,
        'profil': profil,
        'logo_path': logo_path,
        'font_regular': font_regular,
        'font_bold': font_bold,
    }
    html_content = template.render(context)

    result = BytesIO()
    pdf = pisa.pisaDocument(
        BytesIO(html_content.encode("UTF-8")),
        result,
        encoding='UTF-8',
        link_callback=link_callback
    )

    if not pdf.err:
        goruntule = request.GET.get('goruntule') == '1'
        disposition = 'inline' if goruntule else 'attachment'
        response = HttpResponse(result.getvalue(), content_type='application/pdf')

        firma_temiz = "".join(c for c in profil.firma_adi if c.isalnum() or c in (' ', '_', '-')).strip()
        dosya_adi = f"{rapor.rapor_no}_{firma_temiz}.pdf"
        response['Content-Disposition'] = f'{disposition}; filename="{dosya_adi}"'
        return response

    return HttpResponse("PDF belgesi oluşturulurken bir hata meydana geldi.", status=500)