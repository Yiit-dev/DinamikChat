# DinamikChat

GPT entegreli, 3D model animasyonu ile sesli yanıt veren holografik sohbet uygulaması.

## Özellikler

- OpenAI ChatGPT API entegrasyonu
- 3D hologram modeli görüntüleme ve animasyon
- Ağız hareketleriyle sesli yanıt verme
- Gelişmiş kullanıcı hesap yönetimi
  - Kayıt ve giriş sistemi
  - E-posta doğrulama sistemi
  - Şifre sıfırlama
  - Doğrulama kodu tekrar gönderme
- Güvenlik özellikleri
  - Şifre gücü anlık kontrolü
  - Görsel şifre göstergesi
  - Göz ikonu ile şifre görünürlüğü kontrolü
  - Kapsamlı parola politikası
  - Güvenli oturum yönetimi
- Sohbet kanalları oluşturma ve yönetme
- Sohbet arşivleme ve dışa aktarma
- Tema seçenekleri
  - Koyu tema
  - Açık tema
- Modern ve animasyonlu arayüz
- Responsive tasarım
- Ses tanıma ile mesaj gönderme
- Farklı AI yanıt modları
  - Normal mod
  - Edebi mod
  - Öğretici mod
  - Teknik mod
  - Sohbet modu
- Web arama ve akıl yürütme özellikleri
- Özelleştirilebilir 3D modeller (Robot, Asistan)

## Kurulum

1. Gereksinimleri yükleyin:
   ```bash
   pip install -r requirements.txt
   ```

2. *Eklenecek*

3. 3D model dosyaları: (ESKI VERSIYON YENI MODEL GIF ILE YAPILACAK)
   - Varsayılan model: `assets/models/head.obj`
   - Ek modeller: `assets/models/robot.obj`, `assets/models/assistant.obj`

4. E-posta şablonları:
   - `email_templates/verification.html`
   - `email_templates/password_reset.html`

## Kullanım

Uygulamayı başlatmak için:

```bash
python main.py
```

- İlk kullanımda veritabanı otomatik olarak oluşturulur
- Varsayılan admin kullanıcısı:
  - Kullanıcı adı: `admin`
  - Parola: `admin123`

## Sistem Gereksinimleri

- Python 3.8 veya üzeri
- OpenGL destekleyen bir grafik kartı
- Mikrofon (sesli komutlar için) (Opsiyonel)
- Internet bağlantısı (:D)

## Proje Yapısı

- `database/`: Veritabanı modelleri ve işlemleri
- `ui/`: Kullanıcı arayüzü bileşenleri
- `utils/`: Yardımcı modüller (e-posta, API entegrasyonu, model yönetimi)
- `assets/`: 
  - `models/`: 3D model dosyaları
  - `icons/`: Arayüz ikonları
  - `styles/`: CSS stilleri
  - `textures/`: Doku dosyaları
- `email_templates/`: E-posta doğrulama ve şifre sıfırlama şablonları
- `uploads/`: Kullanıcı yüklemeleri
- `backups/`: Veritabanı yedekleri
- `settings.json`: Uygulama ayarları ve yapılandırma

## Eklenecekler

- Mail gönderme sorunu giderilecek
- Model entegrasyonu obj yerine gif haline getirilecek (yüksek ihtimalle ikisi bir arada olabilir)