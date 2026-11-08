# Console138K UART8 CPU処理の重ね合わせ

2026年11月8日（日本時間）。共通tag `uart8-cpu-overlap-hw-20261108`、統合先 `tangcore-integrated`。
軽量計測・詳細計測をともにOFFにした通常版で、2 MiB・4 MiBの起動・下段表示・一覧復帰を確認した。

## 対応するsourceと配布物

| repository | commit |
|---|---|
| firmware-bl616 | `72fa65aaad17cf87276e62e73d893c035d811c99` |
| snestang | `4d6007736b488b477131e573ee550a609805e757` |

親のgitlinkはこの2件を指す。他coreのgitlinkと過去tagは保持する。
[通常版の配布ZIP](../../verification/uart8-cpu-overlap-20261108/verified-normal-pair.zip)と
[軽量計測版ZIP](../../verification/uart8-cpu-overlap-20261108/verified-trace-pair.zip)に、
対応firmware・SNES core・source commit・SHA256SUMSを収録する。

| 対象 | byte数 | SHA-256 |
|---|---:|---|
| 通常版firmware | 241472 | `fa0e48157191afb19be3ac7ecfbaf4ffd0d00cefcda9bf6294b6f5700c4ec0eb` |
| 軽量計測版firmware | 246240 | `3dbad29760326de14118b0517e06899b3880b466cf378d8247d7cc0a9be99811` |
| SNES core | 4767636 | `ca489a5fe2696716d58dc968854ed1bfb75d67b37365b68b5c3f1f88e218e191` |

## 実装と維持条件

8 Mbit/s・Window=2・最大1024 byte DATAのまま、DMA送信中に次frame準備・frame CRC・stream CRC・届いたACKの処理を進める。
共通Sessionの非blocking pollを使い、UARTのDMA・RX ring・baud変更はadapterが管理する。
送信bufferは物理送信終了と連続した先頭ACKの確定後に解放する。投機的CRCはACK確定時だけ正式な値へ反映し、
再送は同じbyte列を保持する。最大4回の試行・session／sequence／offset確認・ENDの実SDRAM全ROM読戻しを維持する。
SPIも同じSessionを共用できるが、物理SPIは未実装・未検証。

前段のSDRAM連続格納も公開する。sinkは8 byte先読みと次wordの組立てを重ね、同期したACK後に次requestを許可する。
最後のwordのACKと回復待ちを経てDATA ACKを返す。controller・PLL・制約・ENDの読戻し範囲とCRC式は変更していない。

## 原因調査と実機比較

SDRAM格納単体の模型では78.36%短縮したが、実機の転送時間はほぼ変わらなかった。
詳細計測ではDATA ACKがすでに届いており、SD読み出しもsend区間内にあった。
残るCPU処理・CRC・ACK解析を送信中に重ねた結果が以下。
詳細計測は約7%の負荷と試行差を含むため、今回の比較には詳細計測OFFの対照版を用いた。

| 区間 | 2 MiB | 4 MiB |
|---|---:|---:|
| 前回DATA転送 | 3.286302秒 | 6.564648秒 |
| 今回DATA転送 | 2.723655秒 | 5.432306秒 |
| DATA短縮率 | 17.12% | 17.25% |
| 前回END | 0.487776秒 | 0.975429秒 |
| 今回END | 0.487768秒 | 0.975417秒 |
| 再送回数 | 0回 | 0回 |
| stream CRC | c287a01c | 21e24729 |

DATAはRomBegin→RomQueuedで、開始交渉と全DATA ACK完了を含む。ENDはRomQueued→END ACK。
各条件各ROM1回。CRCは元ROMと64 byte headerからの独立計算に一致した。
send callback区間中の次frame準備／stream CRCは1975・3978件、ACK確定は2048・4096件。
物理DMA busyのedgeや重なった時間を直接測った件数ではない。
通常版の転送・タイトル到達時刻は再計時していない。

## 通常版の適用・保全・動作確認

切替前にmicroSDの91 user filesを保存し、SHA-256・属性・mtimeを照合した。
全flash 4 MiBを2回保存・全byte照合して復元用256 KiBを保存し、firmware領域0x40000～0x7ffffだけを更新した。
resident方式の読出し1回は応答確認で失敗したため記録を保持し、成功したBOOT ROM方式2回を照合した。
BOOT再接続後の独立した全flash読戻しでfirmware・boot領域・0x80000以降の一致を確認した。
通常版全flash SHA-256は `7b0e1a58807062ae3e786cefe11da94395fefdda8f3a81538bce35f29ba432f5`。
microSDは実行後も91ファイル全件の内容・属性・mtimeが一致し、SNES coreは変更していない。
保存はuser file単位で、sector imageではない。

利用者確認: 「2本とも正常。接続済み」。対象はマリオコレクション（2 MiB）とドンキーコング（4 MiB）。
起動・下段の準備／転送／照合表示・OSD1の一覧復帰を確認した。現在の実機は通常版を保持する。

## PC検証とtiming

共通Sessionと受信RTLで2／4 MiB、CRC破損、ACK欠落・遅延・分割・順序違い、重複内容違い、奇数byte境界、
SDRAM応答停止・読戻し破損・FIFO超過を確認した。実UART adapterは早いACKでも送信中bufferが不変であること、
全ACK欠落時の4回打切り、SD読み出し失敗、DMA停止を検証した。
UART信号は2→8→2 Mbit/s、連続8N1、bit周期±2%、実50 ms／10秒の期限とwatchdogを含む。
UART制御を外した共通Session／RTLも通過。通常版・軽量計測版のfirmware buildは成功。

対応coreはGowin 1.9.12.03の全build済み。setup／hold違反0／0件、Fmaxは80 MHz系86.214 MHz、96 MHz系96.085 MHz。
96 MHz系の余裕は小さく、既存PLL／generic routing警告を保持した制約下の結果。
温度・電源・controllerの組合せ・長時間信頼性を広げた検証は行っていない。
公開する実行sourceは試験・build・実機適用したsourceと改行形式を除いて一致する。

[検証記録](../../verification/uart8-cpu-overlap-20261108/)に原測定記録・比較・PC結果・source照合・配布物照合値を収録する。
全flash・microSDコピー・ゲームROMは公開しない。
