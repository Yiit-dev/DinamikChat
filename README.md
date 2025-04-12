# DinamikChat

GPT entegreli, 3D model animasyonu ile sesli yanıt veren holografik sohbet uygulaması.

## Özellikler

- OpenAI ChatGPT API entegrasyonu
- 3D hologram modeli görüntüleme ve animasyon
- Ağız hareketleriyle sesli yanıt verme
- Kullanıcı hesap yönetimi (kayıt, giriş, şifre sıfırlama)
- E-posta doğrulama sistemi
- Sohbet kanalları oluşturma ve yönetme
- Sohbet arşivleme ve dışa aktarma
- Karanlık tema ve modern arayüz
- Responsive tasarım ve animasyonlar
- Ses tanıma ile mesaj gönderme
- Farklı AI yanıt modları (Normal, Edebi, Öğretici)
- Web arama ve akıl yürütme özellikleri

## Kurulum

1. Gereksinimleri yükleyin:
   ```bash
   pip install -r requirements.txt
   ```

2. `settings.json` dosyasını yapılandırın:
   - `api.openai.api_key` alanına OpenAI API anahtarınızı girin
   - `email.user` ve `email.password` alanlarını e-posta gönderimi için yapılandırın

3. 3D model dosyasını `assets/models/` dizinine yerleştirin:
   - Bir `.obj` formatında kafa modelini `assets/models/head.obj` olarak kaydedin veya
   - `settings.json` dosyasında model yolunu değiştirin

4. Simgeler ve diğer görsel öğeleri `assets/icons/` ve `assets/styles/` dizinlerine yerleştirin.

## Kullanım

Uygulamayı başlatmak için:

```bash
python main.py
```

- İlk kullanımda veritabanı otomatik olarak oluşturulur.
- Varsayılan admin kullanıcısı:
  - Kullanıcı adı: `admin`
  - Parola: `admin123`

## Sistem Gereksinimleri

- Python 3.8 veya üzeri
- OpenGL destekleyen bir grafik kartı
- Mikrofon (sesli komutlar için)
- Internet bağlantısı (ChatGPT API için)

## Proje Yapısı

- `database/`: Veritabanı modelleri ve işlemleri
- `ui/`: Kullanıcı arayüzü bileşenleri
- `utils/`: Yardımcı modüller (e-posta, API entegrasyonu, model yönetimi)
- `assets/`: Görsel öğeler ve 3D modeller
- `settings.json`: Uygulama ayarları ve yapılandırma (API anahtarları, e-posta bilgileri)

## Lisans

Bu proje MIT lisansı altında lisanslanmıştır. 