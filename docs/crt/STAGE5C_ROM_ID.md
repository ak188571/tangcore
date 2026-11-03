# 第5c段階：読取り専用のROM ID

## 目的と範囲

実機確認済み第5b（crt-stage5b-hw-20261103、FW95113b1）を基準に、将来のゲーム別保存keyに必要なROM IDだけを追加する。保存・Reset・defaults読込み・controller profileは混在させない。CSV推奨値の適用は第5bの動作を維持する。以前の第5段階の起動停止原因を特定済みとはしない。

## IDと読取り

IDはvalid flag、volume（sd/usb）、system ID、CRC32/IEEE、64 bit sizeを持つ。filenameや表示名をIDへ含めない。同じvolume/systemで同一内容・sizeなら改名後も同じIDとなり、volume/system/sizeの異なるものは分離する。CRCは非圧縮のROM全byte（header・trainer・末尾を含む）を対象にする。現時点の実機対象はConsole138K/NESである。

実行位置はJTAG program・core ID・能力確認の後、既存ROM loaderの前。既存のnoncacheableなfcoreと64 byte整列のfbufを順に使い、FA_READでopenし8192 byteずつ読む。新たな大きいstack/heap bufferは確保しない。各chunk処理後にdelay(1)でtaskを譲る。読取り完了または失敗後にfileをcloseしてから既存loaderを呼ぶ。loaderそのものとJTAGは変更しない。

open/read/close失敗、空file、読取byte数とf_sizeの不一致、buffer容量を超える戻り値の場合はvalidにしない。前ゲームのIDはprogram開始・新ROM読込み開始・ROM load失敗でclearする。ID取得失敗だけを理由にゲーム起動を止めず、既存loaderは実行する。将来の保存処理でもvalidでないIDを使用しない前提である。

同じvolumeのFatFsへ複数taskが並行アクセスする設計にはしていない。今回のNES経路でmain taskが順次処理する範囲であり、他coreのstorage並行動作へ一般化しない。

## OSD2

識別表示はCRT ROM ID - STAGE5C。既存の空き行へROM ID: xxxxxxxxを表示し、取得できなければROM ID: UNAVAILABLEとする。表示する8桁はCRC32であり、内部のIDにはsize/system/volumeも含む。menuの選択行、CLOSE、POS、外形の行数は変えない。

新session開始時にIDとCSV初期値を渡す。OSD2を閉じて開き直してもIDと同ゲーム中の調整値を維持する。ゲームを起動し直すとIDを読み直し、設定はCSV推奨値またはbuiltin全OFFへ戻る。SDへの設定保存や起動log追記は行わない。

## 検証

関連8本（rom_id、CRT、OSD、launch、titles、folders、scroll、wrap）が成功し、firmware buildも成功した。実際のFatFs読取り関数をfake fileで実行し、IEEEの既知vector、chunk境界、全byte、改名/system/volume、size不一致、read/open/close失敗、早いEOF、異常なbyte数を確認した。実際のmain adapterでは対応coreのみ追加読取りすること、ID取得失敗でもloaderを呼ぶこと、失敗時clearと成功後のsessionへの受渡しを確認した。CRT関数の表示保持と新sessionでのclearも試験した。

compilerのstack usageではID読取り関数は96bytes（下位のFatFs/driverを含む全呼出深さではない）。fbuf/fcoreは既存領域を使う。新たなFPGA buildはなく、NES imageは実機合格第4b〜第5bと同じものを再利用する。

記録はverification/crt-stage5c-romid。firmware 223104bytes、SHA 409f25cc861182e2778dc82f777050cc349b6a82c98b3cd18cd189132f0df32f。PC試験成功を実機でのSD動作確認へ読み替えない。ROM全体をもう一度読むため、起動に読取時間が加わる。実機で起動時間・音声・操作・OSDも確認する。

## PC照合値と実機試験

最新の退避ROMをSHAで照合し、PCのzlibでCRCを算出した。ROM自体は配布物へ入れない。

| ROM | byte数 | CRC32 |
| --- | ---: | --- |
| Dr. Mario (Japan, USA) (Rev 1).nes | 65552 | 7623dffd |
| Pac-Man (Japan) (Rev 2).nes | 24592 | ebbb19bf |

firmwareのみ更新し、CSV/ROM/NES/monitor/font/既存logを維持する。SD全体と直前の実機確認済み第5b全flashを保全する。

通常起動と日本語一覧・順序、Dr. MarioとPac-Manの起動・映像・音声・操作、CRC表示がPC値と一致することを確認する。Dr. MarioはCSV推奨ON/WEAK/STANDARD・INITIAL CSV・FRAME ACK、Pac-Manは全OFF・INITIAL DEFAULT・FRAME ACKを期待する。同ゲームでOSDを開き直した際のID保持、別ゲームでの切替、再起動して同じCRCになることも確認する。保存試験・SD抜去・電源断中の書込み試験は行わない。

## 第5c版の実機反映

2026-11-03T23:39:57.003243+09:00、既知Console138Kへfirmwareだけを反映した。基板SHA、新FW全byte、4MiB全flash読戻しと更新範囲外を照合した。SD全59filesを新たに退避し、CSV/ROM/NES/monitor/font/既存logを含む全fileが同一と確認した。初回mode0 READの接続確立に失敗し、再programせずmode2 READで成功した。SDK設定を元のbyteへ復帰した。

復旧用には実機合格第5bの全読戻しをコピーして保持する。新たな書込み前flash読取を行ったとは記録しない。導入照合はverification/crt-stage5c-romid/deployment.json。通常起動と2本のROM ID表示、CSV推奨値とFRAME ACK、IDの保持・切替・再取得は利用者の実機確認待ちである。第5c完了tagはまだ作らない。

## 起動・CRC照合の実機結果

利用者が「1-3 正常」と回答した。日本語一覧と順序、Dr. Marioの起動・映像・音声・操作、STAGE5C表示、CRC7623dffdとPC計算値の一致、CSV ON/WEAK/STANDARD・FRAME ACK、OSD1で一覧へ戻りPac-Manを起動し、CRCebbb19bf・DEFAULT全OFF・FRAME ACKになることを確認した。結果はverification/crt-stage5c-romid/hardware-results.json。

起動時間の数値測定や、改名・別volumeの実機試験を確認済みとはしない。同ゲームでOSDを開き直した際のID保持と、Dr. Marioを改めて起動した際の同じCRC再取得は残りの確認とする。追加書込みは不要。第5c完了tagはまだ作らない。

## 第5c段階の実機試験完了

利用者が残り2項目を「1,2正常」と回答した。Pac-ManでOSD2を閉じて開き直してもCRCebbb19bf、DEFAULT全OFF、FRAME ACKが保たれること、一覧へ戻ってDr. Marioを起動し直すとCRC7623dffd、CSV ON/WEAK/STANDARD、FRAME ACKとなることを確認した。初回の2本の起動・CRC照合と合わせ、依頼した第5cの実機試験はすべて正常である。

第5cの実装・関連8試験・build・導入照合・依頼した実機試験を完了し、local tag crt-stage5c-hw-20261103を基準として保持する。FW83d7055、NES c8df819a、現在の試験CSVと2本の記録済みROMの組合せで確認した範囲である。改名や別volumeでのID分離はPC試験で扱ったもので、実機でも確認済みとはしない。

保存・Reset・defaultsは未実装のままで、第5段階全体は未完了。過去の初版第5段階の停止原因も特定済みとはしない。以後の追加変更前に、この実機確認済み第5cへ復帰できる状態を保持する。

試験結果はverification/crt-stage5c-romid/hardware-results.json。本文前半の確認待ち記述は各時点の経過であり、最新状態は本節を優先する。
