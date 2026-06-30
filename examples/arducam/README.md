# arducam

Arducam MEGA（SPI 接続）で撮影した画像を、SORACOM Harvest Files に定期的にアップロードするサンプルです。

## 構成

| ファイル | 内容 |
|:---------|:-----|
| `main.py` | メイン処理（撮影・LTE 接続・アップロード） |
| `camera.py` | Arducam MEGA 制御クラス（[Core Electronics の Arducam MicroPython ライブラリ](https://github.com/CoreElectronics/CE-Arducam-MicroPython)を改変） |

## 動作概要

1. Arducam MEGA で JPEG 画像を撮影
2. SORACOM Air で LTE に接続
3. NTP で現在時刻を取得してタイムスタンプ付きのファイル名で SORACOM Harvest Files にアップロード
4. 15 秒待機して繰り返す

## 接続

Arducam MEGA は SPI0 に接続してください。

| 信号 | GPIO |
|:-----|:-----|
| SCK  | 18   |
| MISO | 16   |
| MOSI | 19   |
| CS   | 17   |
