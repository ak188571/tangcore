# Console138KのOSDからの一覧復帰を短縮

2026年11月13日、OSDからタイトル一覧に戻る際の初回RELOAD後に、TCKを出力するGPIO処理を軽量化した。100万clockの最初の1 clockはSDKのGPIO関数を使ってpad検査を行い、残りはTCKのbitだけをSET/CLEAR registerに書く。bitstreamのJTAG転送は20 MHz、ROM転送は32 MHz。[前回の20 MHz JTAG実機確認](JTAG20_20261112.md)

## 区間別の実測

20 MHz JTAGの基準計測版とGPIO軽量化を追加した計測版で、2 MiBと4 MiBのSNESタイトルを各3回起動し、毎回OSDから一覧に戻った。表は各版6回の平均。

| 区間 | 基準計測版 | GPIO軽量化版 |
| --- | ---: | ---: |
| RELOAD命令 | 38.5 µs | 40.7 µs |
| NOOP命令 | 38.0 µs | 34.2 µs |
| 100万clock | 773.271 ms | 100.427 ms |
| TAP reset開始から最低1秒待機の開始まで | 773.382 ms | 100.534 ms |
| 待機開始から安全確認による待機完了まで | 1.001026秒 | 1.001168秒 |
| OSD復帰受理から一覧再描画完了まで | 4.414秒 | 3.737秒 |

100万clock区間は平均672.844 ms短縮し、一覧復帰全体は平均676.987 ms短縮した。軽量化版の6回すべてで初回復帰に成功し、JTAGエラーと再試行は0件だった。待機時間は1.001132～1.001202秒。計測ログは基準が `uart-0110.txt`～`uart-0115.txt`、軽量化版が `uart-0116.txt`～`uart-0121.txt`。

## 安全確認と再試行

100万clockの後に最低1秒待ち、FPGAのID・USERCODE・状態、UARTの送信状態、GPIO28のnative選択と入力レベルを確認する。消去直前の照合、2回のSRAM消去、CRC・DONE・monitorの確認を行う。初回の書き込み失敗時は、従来のGPIO処理でRELOADからやり直し、5秒待機する。PC試験では100万組のLow→High出力と、安全確認に失敗した場合に消去を開始せず従来の5秒経路へ進むことを確認した。

## 通常版の実機確認

通常版は計測版と同じソースを `TC_LAUNCH_TRACE=OFF`、`TC_ROM_PROFILE=OFF` でbuildした。その他の設定はConsole138K／BL616、C++17、`TC_JTAG_SPI_HZ=20000000`、`TC_ROM_SPI=ON`、`TC_ROM_UART=ON`、`TC_ROM_CPU_PIPELINE=ON`、`UI16_SYSTEM_MENU=ON`、`UI16_SD_FONT=ON`。区間計測とmicroSDへの計測ログ出力は無効。上の表は計測版で取得した値で、通常版では時間を計測していない。

BOOT再接続後のFlash全4 MiBの独立読み戻しで、通常版の248,608 byteが書き込み元と一致し、対象sector外も退避データと一致した。通常版で起動、ゲーム動作、OSDから一覧に戻る操作に異常の報告はなかった。動作確認後のmicroSDは121件の既存ログのファイル名とSHA-256がすべて一致し、新規ログは0件だった。

| 実機に使用したfirmware | Byte | SHA-256 |
| --- | ---: | --- |
| 基準計測版 | 258224 | `fe8424c54bd8b69c5ccce5e6eda422f29d597f8b1dc5a52aa1d614d6ad4d62fc` |
| GPIO軽量化計測版 | 258352 | `dd7a01162804b1db059a83e01ad831e0ad0cbca326ddca92a2c22a7659cc079c` |
| GPIO軽量化通常版 | 248608 | `e60ef33db7bf38a02d88bf5e7fee8aac444c502ad4fa3dc7dc2ecbf16458d77a` |

monitorとSNESTangには[前回の実機確認と同じイメージ](JTAG20_20261112.md#build設定と実機確認済みイメージ)を使用した。firmwareに埋め込まれるソースパスが異なるため、別の場所で再buildしたBINのSHA-256は表の値と異なることがある。
