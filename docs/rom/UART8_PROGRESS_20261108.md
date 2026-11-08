# Console138KのUART 8 Mbit/s実機確認済み到達点

共通tagは `uart8-progress-hw-20261108`。統合先は `tangcore-integrated`。
通常版firmwareと対応するSNES coreで、起動とロード中の表示が正常であることを利用者が2026年11月8日に確認した。

## 公開する組み合わせ

| repository | commit |
| --- | --- |
| firmware-bl616 | `d6328c9d1caa412f1b3ec068170c296814d25e28` |
| snestang | `06ee0670252a0486d905b6b011fab8c49e83c06c` |

通常版は237,680 byte、SHA-256は `1f1bdb2455e99210b420a9e94bd20b2565db7506c1f79deb086fba87733403f2`。
SNES coreは4,878,740 byte、SHA-256は `e3b9565a05791420073f20d6d8ebd0b8d40b42eddfc05e04f4cdf6340540613f`。
親repositoryのgitlinkもこの組み合わせを指す。

配布用の通常版とcoreは `verification/uart8-progress-20261108/verified-normal-pair.zip` に収録する。
詳細な比較文書・計測用firmwareを含む作業成果物のZIPのSHA-256は `93836071b3a3bee63f816ff356d69d06819827269e524890f3de6fa182aa68b2`。

## 実装

- UART 8 Mbit/sのROM転送にdma0_ch3を使用する。
- CRC・連番・ACK・再送をUART専用処理から分離し、将来のSPIでも共用する構成とした。
- ACKはSDRAM格納後に返し、ENDでは実際のSDRAMを全ROM分読み戻して照合する。
- 最下段にPreparing SNES core、ROM transfer xx%、Verifying ROMを表示する。転送率は格納済みのROM本体に応じて5%刻みで更新する。
- 準備画面を作る間はOSDを隠し、旧画面の文字とロゴ用RAMを消去する。
- FPGAのタイミングを満たすため、ROM連番計算を分割し、USB descriptorの先頭部と本文の保存を分けた。

## 確認結果

| 測定条件 | マリオコレクション | ドンキーコング |
| --- | --- | --- |
| 従来2 Mbit/s、確定からタイトル | 21.55秒 | 54.36秒 |
| 8 Mbit/s、進捗追加前、確定からタイトル | 13.92秒 | 27.83秒 |
| 最初の進捗表示版、確定からタイトル | 13.83秒 | 28.62秒 |
| 最下段表示の初版、確定からタイトル | 15.06秒 | 未測定 |

各測定は各版・各タイトル1回。最終通常版では起動・ロード中表示の正常動作を確認した。
最終通常版でのタイトル到達時間は再計時していない。
最終計測用firmwareのマリオではROM転送3.989秒、読み戻し照合0.488秒、再送0回。
約4.2 Mbit/sはROM本体の実効速度で、UART設定は8 Mbit/s・8N1。

共通C++とRTLの接続試験、2 MiB・4 MiBの転送、CRC破損・ACK消失・重複・SDRAM破損時の処理、
既存の映像・OSD、ロゴ消去後の画素比較をPCで確認した。
公開する実装ファイルは試験・ビルド・実機適用した作業ソースと改行形式を除いて一致する。
Gowin 1.9.12.03による採用coreの解析はsetup違反0件、hold違反0件。
Fmaxは96 MHz系96.325 MHz、80 MHz系81.127 MHz。
通常版firmwareは全flashの読み戻しと対象外領域の一致を確認した。

## 次の高速化

現在は1 KiBごとの送信・SDRAM格納・ACK待ちを直列に行う。
次の候補はUART受信と前ブロックの格納の重畳、SDRAM格納の連続化、block長の拡大。
このtagは現在の直列転送を実機で確認した構成を記録する。

実機確認、測定値、成果物の照合値は `verification/uart8-progress-20261108/` を参照する。

## 後続の確認済み版

UART受信とSDRAM格納の並行化、および通常版の実機確認は[UART8_OVERLAP_20261108.md](UART8_OVERLAP_20261108.md)と共通tag `uart8-overlap-hw-20261108` に記録した。この文書と旧tagは直列転送版の履歴として保持する。
