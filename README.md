# Kopru

Kopru, iki Windows laptopu yan yana tek bir masaüstü gibi kullanmak için yapılıyor:

- **Uzat:** Ana PC'nin masaüstü ikinci laptopun (PC2) ekranına 60 FPS ile uzar. Pencereler ve sekmeler normal bir ikinci monitördeymiş gibi oraya sürüklenir. Windows'un kablosuz ekran özelliğinden (Miracast) çok daha akıcıdır.
- **Geçiş efektleri:** Fare iki ekran arasında geçerken Beamer'ın direnç ve animasyonları oynar.
- **PC2'nin gücü:** "VS Code'u PC2'de aç" ile kod, terminal ve derleme PC2'nin donanımında çalışır, pencere ise uzatılmış ekranda durur.

> Durum: geliştiriliyor (M1). Tasarım ve yol haritası: [docs/superpowers/specs/2026-10-28-kopru-design.md](docs/superpowers/specs/2026-10-28-kopru-design.md)

## Nasıl çalışır

Görüntüyü üç açık kaynak program taşır; Kopru bunları arka planda yönetir:

| Nerede | Program | Görevi |
|---|---|---|
| Ana PC | Virtual Display Driver | Windows'a sanal bir ikinci monitör ekler |
| Ana PC | Sunshine | O monitörün görüntüsünü ekran kartıyla (NVENC) sıkıştırıp yayınlar |
| PC2 | Moonlight | Yayını tam ekran gösterir |

Ses ana PC'de kalır. PC2'nin klavyesi ve touchpad'i uzatma sırasında devre dışıdır.

## Testler

```
python run_tests.py
```

## Kurtarma

Bir şeyler ters giderse ana PC'de **Win+P → "Yalnızca bilgisayar ekranı"** pencereleri ana ekrana geri getirir.

## Lisans

GPL-3.0 (bkz. [LICENSE](LICENSE)). Efekt motoru ve bazı parçalar Beamer'dan alınmıştır; ayrıntılar [NOTICE](NOTICE) dosyasında.
