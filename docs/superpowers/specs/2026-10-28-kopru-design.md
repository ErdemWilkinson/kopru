# Kopru: tasarım ve uygulama planı

## Bağlam
- Hedef: ana laptopun masaüstünü ikinci laptopa (PC2) **60 FPS** ile uzatmak. Windows'un "Bağlan" özelliği (Miracast) akıcı değil.
- Yeni uygulama Beamer'ın tüm animasyonlarını ve Tasarım sayfasını alacak.
- Yan görev: VS Code projelerinin işlem yükü PC2'nin donanımında çalışacak.
- Beamer çatalı rafa kalkıyor. Kopru, sıfırdan ayrı bir proje.

**Seçilen yol (A):** Arayüz, animasyonlar, otomatik akış, eşleştirme ve kurulum bizim. Görüntü motoru gizli çalışan açık kaynak araçlar:
- **VDD:** ana PC'de sanal monitör.
- **Sunshine:** ana PC'de NVENC ile kodlama.
- **Moonlight:** PC2'de tam ekran gösterim.

Motor bir arayüzün arkasında durur; ileride kendi motorumuzla değiştirilebilir.

**Kullanıcı kararları:**
- Bağlantı yalnızca Wi-Fi.
- PC2'nin klavye ve touchpad'i devre dışı.
- Ses ana PC'den çıkar.
- Geçişte Beamer gibi direnç ve efekt var.
- Tasarım sayfası Beamer'dan taşınır.
- Yan görev bu planın sonunda yapılır.
- Ad **Kopru**.
- Otomatik uzatma açık; Windows açılışında iki PC'de de otomatik başlar.
- Kurulum tek satır PowerShell ile.
- PC2'nin konumu ayardan seçilir (varsayılan sağ).
- Yeni klasör `Masaüstü\kopru`, public GitHub reposu, GPL-3.0 (Beamer kodu kullanıldığı için).

## Mimari
```
ANA PC (Kopru, yönetici değil)                 PC2 (Kopru, yönetici değil)
 MainController + ExtendFSM (saf)   <-TCP->     Pc2Agent
  Discovery (UDP)                   <-UDP--     Beacon
  VddDisplay (SetDisplayConfig)                 MoonlightViewer (CLI + izleme)
  SunshineStreamer (REST)                       Wi-Fi kontrolü, SSH (yan görev)
  SeamController (hook + ReturnEdge)
  EffectOverlay (tüm ekranlar, sanal dahil → efektler PC2'ye akar)
  Tasarım sayfası / tepsi / güncelleyici
 Sunshine servisi --- video (NVENC) ---> Moonlight tam ekran
```
- Kontrol portları: TCP 47110 ve UDP 47111. Güvenlik duvarında yalnızca "Özel ağ" profiline açılır.
- Motor arayüzleri:
  - `VirtualDisplay`: attach, detach, find, ensure_mode.
  - `Streamer`: health, target, lock_input, accept_pin.
  - `Viewer`: pair, start, stop.

## Yeniden kullanılan Beamer kodu (kaynak: `Ekran paylaşma uygulamam`)
- **Efekt motoru**, olduğu gibi kopyalanır:
  - `core/effects.py`, `core/fx_*.py`, `core/return_edge.py`.
  - `core/i18n.py` ve `core/locale.py`, dil Türkçe'ye sabitlenir.
- **Qt tarafı:**
  - `win_app/effect_overlay.py`, `edge_glow.py`, `frame_clock.py`, `effect_previews.py`.
  - `tokens.py`, `theme.py`, `titlebar.py`, `motion.py`, `tray_glyph.py`.
  - `widgets.py` (`core.ways` yerine küçük bir taklit).
  - Fontlar.
- **Geçiş (seam):**
  - `win_app/capture_win.py`, kırpılarak: Raw Input, düşük seviyeli fare kancası, `internal_seam_position` (:142).
  - `ReturnEdge(display=...)` modeli.
  - Beamer'ın sürüş yöntemleri `_on_pressure` (:5617), `_on_arrival` (:5653) ve `_hide_crossing` (:5704) örnek alınır.
- **Tasarım sayfası:** `kvm_bridge_win.py` içinde :3720-4320 arasında. Bağımsız bir `DesignPage(QWidget)` olarak çıkarılır. Ayrıca `pages_win.py` içindeki `style_groups`, `colour_groups` ve `is_effect` gelir.
- **Eşleştirme:** `core/pairing.py` içindeki CPace (6 haneli PIN) ve test vektörleri.
- **Kurulum ve güncelleme:**
  - `kur.ps1`.
  - `win_app/fork_update_win.py`. Geliştirme klasörüne asla dokunmama korumasıyla birlikte gelir.
  - `pc2-hizlandir.ps1`, `autostart_win.py`, `firewall_win.py`.
- **Düzeltme:** `docs/UZAT-MODU.md` içindeki Moonlight bayrakları yanlış:
  - Ses ana PC'den çıkacağı için `--audio-on-host` kullanılmalı.
  - PC2'nin girişi kapalı olacağı için `--capture-system-keys never` kullanılmalı; Sunshine'da da `keyboard`, `mouse` ve `controller` kapatılmalı.

## Akış
- **Eşleştirme (bir kez):**
  1. PC2 tepside 6 haneli bir kod gösterir; kod ana PC'ye girilir (CPace).
  2. Ardından Moonlight ile Sunshine kendiliğinden eşleşir: PC2'de `Moonlight pair --pin`, ana PC'de Sunshine `POST /api/pin`.
- **Kontrol kanalı:**
  - Mesajlar uzunluk önekli JSON çerçeveler.
  - Oturum anahtarı HKDF ile türetilir; her çerçeve HMAC ile imzalanır ve sıra numarası taşır.
  - PC2'den her saniye bir "nabız" mesajı gelir.
- **Durumlar (ana PC):** Kurulum eksik → PC2 eşlenmedi → PC2 bekleniyor → Hazır → Bağlanıyor → **Uzatıldı · 60 fps** → Bağlantı koptu → Kapatılıyor. Bunlara ek olarak bir Hata durumu var; tekrar deneme 2, 5, 15, 30 ve 60 sn aralıklarla yapılır.
- **Başlatma sırası:**
  1. Sanal ekranı PC2'nin çözünürlüğünde, seçilen tarafa yerleştir.
  2. Sunshine'ı o ekrana yönlendir.
  3. PC2'ye "başlat" komutunu gönder.
  4. Akışın başladığı bildirimini bekle.
  5. Geçişi (seam) aç.
- **Kopma ve durdurma:**
  - Nabız 5 sn gelmezse: "Bağlantı koptu". Sanal ekran yerinde kalır, pencereler zıplamaz.
  - 20 sn gelmezse: sanal ekran kapatılır, pencereler ana ekrana döner ve bildirim gösterilir.
  - Kullanıcı PC2'de durdurursa otomatik yeniden başlatma olmaz.
  - Kopru açılışında, çökmeden kalmış bir sanal ekran varsa kapatılır.
- **Geçiş:**
  - İki `ReturnEdge` modeli çalışır: ana PC'den PC2'ye ve PC2'den ana PC'ye.
  - Basınç büyürken imleç geçişte tutulur (HOLD); eşik aşılınca serbest bırakılır (CROSS) ve varış animasyonu oynar.
  - Fare kancası yalnızca durumu günceller; çizim GUI iş parçacığında yapılır.
- **Moonlight komutu:** `stream <ip> "Desktop" --resolution WxH --fps 60 --bitrate 30000 --display-mode fullscreen --video-codec HEVC --video-decoder hardware --audio-on-host --capture-system-keys never --keep-awake`
  - Profiller: akıcı (vsync açık) veya düşük gecikme.
  - HEVC başarısız olursa H.264 denenir.
- **Yönetici izni:** Yalnızca kurulumda, tek bir UAC onayıyla. Sanal ekranı açıp kapatmak `SetDisplayConfig` ile yönetici izni gerektirmemeli; bu M0'da doğrulanacak. Gerekirse yedek plan zamanlanmış görev ya da Sunshine'ın hazırlık komutları.
- **Gizli bilgiler:** Eşleştirme anahtarı ve Sunshine parolası DPAPI ile saklanır. Sunshine sertifikası sabitlenir.

## Proje düzeni
- `core/` (saf, tamamen test edilir):
  - Beamer'dan kopyalananlar: `effects`, `fx_*`, `return_edge`, `i18n`.
  - Yeniler: `settings.py`, `protocol.py`, `pairing_cpace.py`, `extend_fsm.py`, `layout.py`, `moonlight_args.py`, `sunshine_conf.py`, `ssh_config.py`.
- `app/` (Qt ve Windows):
  - Ana parçalar: `main.py`, `seam.py`, `display_win.py`, `engines/{base,vdd,sunshine,moonlight}.py`, `channel.py`, `controller_main.py`, `agent_pc2.py`, `power_win.py`, `secrets_win.py`, `tray.py`, `design_page.py`, `updater.py`, `ssh_remote.py`, `log.py`.
  - Beamer'dan kopyalanan Qt modülleri de burada.
- `kur.ps1`, `scripts/kur-yonetici.ps1`, `scripts/pc2-hizlandir.ps1`, `scripts/kaldir.ps1`.
- `tests/`, `docs/`, `locales/tr.po`, `LICENSE` (GPL-3.0), `NOTICE` (Beamer kaynağı).

## Kilometre taşları
Her aşamada önce testler yazılır (TDD, ECC `tdd-workflow`). Kod incelemesi ECC `python-review` / `code-review` ile yapılır; güvenlikle ilgili aşamalarda ayrıca `security-review`. Commit mesajlarında Claude anılmaz.

- **M0 – Denemeler (elle yapılır, kurulum onayı alınarak):**
  1. VDD, Sunshine ve Moonlight elle kurulup uçtan uca denenir; FPS, gecikme ve imlecin görünürlüğü ölçülür.
  2. Hibrit GPU: sanal ekran RTX 4050'de çizilmeli, Sunshine `adapter_name` aynı GPU'yu göstermeli.
  3. Sanal ekranı yönetici izni olmadan açıp kapatma, dört tarafa yerleştirme.
  4. VDD ayar XML'i ve nasıl yeniden yükleneceği.
  5. Sunshine API ayrıntıları, girişin gerçekten kapandığı.
  6. Moonlight CLI: `pair`, `quit`, ses ana PC'de kalıyor mu.
  7. Pencere sürüklerken geçişte tutmanın sürüklemeyi bozup bozmadığı.

  Ayrıca alternatifler karşılaştırılır: Sunshine'ın kendi `dd_*` ekran seçenekleri ve Apollo.

  Sonuçlar `docs/SPIKE-SONUCLARI.md` dosyasına yazılır. **Çıkış ölçütü:** 5 dakika boyunca en az 55 FPS ve en fazla %1 kare kaybı.
- **M1:** İskelet, public repo, efekt motorunun taşınması ve testleri, `settings.py`.
- **M2:** Yalnızca ana PC'de geçiş ve efektler; iki yönde, dört tarafta.
- **M3:** Kontrol protokolü, CPace, durum makinesi (FSM), motorlar, DPAPI, kontrol kanalı, otomatik uzatma. Sahte motorlarla tek makinede uçtan uca test; güvenlik incelemesi.
- **M4:** Tasarım sayfası (Beamer'dan; "Bağlantı" bölümü eklenir: taraf, otomatik uzatma, direnç, profil, bit hızı) ve tepsi menüleri.
- **M5:** `kur.ps1` (rol: ana ya da pc2), yönetici gerektiren kurulum betiği, otomatik başlatma, güncelleyici; güvenlik incelemesi.
- **M6 – Yan görev:**
  - PC2'de OpenSSH sunucusu (yalnızca anahtarla giriş, Özel ağ profili).
  - Anahtar, Kopru'nun kanalıyla PC2'ye gönderilir.
  - Ana PC'de `~/.ssh/config` içine `kopru-pc2` bloğu yazılır.
  - VS Code Remote-SSH kurulur.
  - Tepside "VS Code'u PC2'de aç": `code --folder-uri vscode-remote://ssh-remote+kopru-pc2/...` çalıştırır ve pencereyi PC2'nin ekranına yerleştirir.
- **M7:** İki makinede doğrulama, hataların düzeltilmesi, `v0.1.0`.

## M0 bulguları (2026-10-28)
- **VDD:** `Root\MttVDD` aygıtı olarak kuruldu (`ROOT\DISPLAY\0000`). Ayar dosyası `C:\VirtualDisplayDriver\vdd_settings.xml`; içinde GPU'yu RTX 4050'ye sabitleyen `friendlyname` girdisi var.
- **Kanıtlanmış sorun:** VDD aygıtı etkinken, sanal monitör masaüstüne bağlı olmasa bile, Ekran Alıntısı Aracı takılıyor ve ekran görüntüsü alınamıyor. Aygıt devre dışı bırakılınca düzeliyor.
  - Karar: VDD aygıtı **yalnızca uzatma sırasında etkin** olacak. Başlatma sırası "aygıtı etkinleştir"le başlar, durdurma sırası "aygıtı devre dışı bırak"la biter.
  - Aygıtı açıp kapatmak yönetici izni ister. Kopru ise yönetici olmadan çalışıyor. Bu yüzden ya Sunshine'ın yönetici yetkisiyle çalıştırdığı hazırlık komutu (`global_prep_cmd`, `elevated: true`) ya da yönetici haklı bir zamanlanmış görev gerekiyor; M0'da hangisinin olacağına karar verilecek.
  - M0'da denenecek: uzatma etkinken (sanal monitör bağlıyken) Ekran Alıntısı Aracı çalışıyor mu?
- **Sunshine 2026.914:**
  - H.264, HEVC ve AV1 kodlayıcıları NVENC ile çalışıyor.
  - Yönetim kullanıcısı `kopru`. Parola `%APPDATA%\Kopru\sunshine.cred` dosyasında, DPAPI ile şifreli.
  - Ayarlar: `keyboard`, `mouse` ve `controller` kapalı; `origin_web_ui_allowed=pc`; `adapter_name` RTX 4050.
  - API'ye PowerShell 5.1 TLS yüzünden bağlanamıyor; `curl.exe -k -K <config>` çalışıyor. Kopru'da Python'un `ssl` modülü kullanılacak.
  - `--creds` komutu servis durdurulmadan çalışmıyor (servis günlük dosyasını kilitliyor).

## Riskler
- **PC2'nin Wi-Fi kartı (AC 3168) zaman zaman takılıyor.** Önlemler: Moonlight kare dengeleme, 20-30 Mbps bit hızı, 5 GHz bant, güç tasarrufu kapalı. Kesin çözüm bir USB-Ethernet adaptörü.
- **PC2'de imleç görüntünün içinde gelir.** Bu yüzden imleç gecikmesi görüntü gecikmesine eşittir; bunu önlemenin yolu yok.
- **Sanal ekranı açıp kapatmak yönetici izni isteyebilir.** M0'da denenir; yedek planı var.
- **Beamer ile aynı anda çalışırsa çakışırlar.** Kopru, Beamer açıksa uyarı verir.
- **Kurtarma yolu:** Win+P → "Yalnızca bilgisayar ekranı" pencereleri her zaman ana ekrana geri getirir.

## Doğrulama (M7, iki makinede)
1. Tek satırla temiz kurulum; her PC'de tek bir UAC onayı.
2. PIN ile eşleştirme; Moonlight eşleştirmesi elle kod girmeden tamamlanır.
3. İki PC açıldıktan sonra 15 sn içinde ekran kendiliğinden uzar.
4. Moonlight istatistikleri: 5 dakika boyunca ortalama en az 58 FPS, en fazla %1 kare kaybı.
5. 240 fps telefon çekimiyle ölçülen gecikmenin ortancası 60 ms veya altı.
6. Not Defteri ve bir tarayıcı PC2'ye sürüklenip orada kullanılabilir. PC2'nin klavyesi ve touchpad'i ana PC'de hiçbir şey yapmaz.
7. PC2'ye taşınan bir pencerenin sesi ana PC'den çıkar.
8. Geçişte direnç ve efekt iki yönde de çalışır; tüm stil aileleri ve dört taraf denenir.
9. Tasarım sayfasındaki her değişiklik canlı efektte hemen görünür ve yeniden başlatmadan sonra korunur.
10. PC2'nin Wi-Fi'ı 3 sn kesilince hiçbir şey olmaz. 30 sn kesilince pencereler ana ekrana döner; Wi-Fi gelince ekran yeniden uzar.
11. PC2'de akış durdurulunca otomatik yeniden başlamaz; tepsiden "Uzat" ile yeniden başlar.
12. Ana PC uyuyup uyanınca, PC2 hâlâ oradaysa ekran yeniden uzar; değilse sanal ekran kapanır.
13. Moonlight, Sunshine ya da Kopru zorla kapatılınca sistem 30 sn içinde toparlanır.
14. İki PC yeniden başlatıldıktan sonra hiç tıklamadan ekran uzar.
15. Uygulama içi güncelleme çalışır; geliştirme klasörü asla güncelleme önermez.
16. "VS Code'u PC2'de aç": terminalde `hostname` PC2'nin adını verir, derleme sırasında yük PC2'nin Görev Yöneticisi'nde görünür.
17. Win+P ile kurtarma çalışır.
