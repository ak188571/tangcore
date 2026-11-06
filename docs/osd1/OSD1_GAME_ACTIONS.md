# OSD1：ゲーム再起動と一覧復帰

2026年11月6日。対象はConsole138KのNES・SNES。日本語一覧・CSV順序・既存NES CRT/OSD2の経路を維持し、OSD1を2項目にした。

## 操作と今回の方針

| 操作 | 動作 |
| --- | --- |
| P1 SELECT + RIGHT | OSD1を中央固定で開く。Restart Game／Return to Game Listの2項目。 |
| A/B | 選択を決定。Restart Gameは全ボタン解放後に実行する。 |
| X/Y | 閉じてゲームへ戻る。 |
| NES P1 SELECT + LEFT | 既存OSD2を独立して開く。POSは中央・四隅の5か所。 |
| 別OSDの呼出し | 現在のOSDを維持し、全ボタン解放まで残りの入力も処理しない。 |
| 左右同時の呼出し | どちらも開かず、全ボタン解放を待つ。 |

OSD1はOSD2のPOSに影響されない。P2のゲーム入力もOSD表示中は遮断する。通常のOSD表示のためのpause/muteは追加していない。閉じ方や入力の細部は今回採用した方針であり、引き継ぎ資料の推奨案を追加の確定要求として扱っていない。

SNESのCRT/OSD2は今回未実装であり、SELECT + LEFTでは開かない。他のcoreの専用メニューは今回変更していない。

## ROMを保持する再起動

対応coreは能力文字列 `RSTROM1` を通知する。firmwareは実行状態・core ID・能力を確認して、引数なしの `AA 00 01 13` を送信する。旧coreではRestart Gameを実行せず、更新が必要と表示する。一覧復帰は利用できる。

FPGAは専用counterで公称20 msのゲームresetを生成する。NESはNES本体reset、SNESはmainのRESET_Nへ接続する。ROM loader、header parser、SDRAM制御、FPGA再構成、USB host、OSD、CRT設定のresetへは接続しない。ROM読込み状態0x06とデータ転送0x07を再起動には使用しない。P1予約入力と部分解放時の遮断も維持する。

要求長が1以外、ROM転送中、OSD非表示、reset中の再要求は受理しない。既定では能力を無効とし、今回更新したConsole138K用topだけで有効にする。firmwareの送信はcritical sectionで保護し、公称reset時間より長い25 msを待ってからOSDを閉じる。これはゲームの起動完了時間の実測ではない。

Return to Game Listは既存monitor復帰経路を使い、フォルダー・選択・表示位置を復元する。Restart Gameではmonitorへ戻らず、ROM ID/CRT設定のsessionも作り直さない。

## 検証と範囲

実装ソースは実機導入したbuild元と照合した。firmware build成功、NES・SNESの合成・配置配線・bitstream生成成功、setup/hold違反は両方0。既存PLL関連warningやSNESのaudio_en未駆動warning等は残っており、無warningの版とはしない。

host試験12件とUART回路試験2件が合格。UART試験は実iosys_bl616と実送受信回路を用い、能力通知、reset counter長、2回の独立したreset、繰返し要求の非延長、ROM転送中/長さ不正/OSD非表示/能力無効時の拒否、設定とOSD windowの保持を確認する。game CPUで全ROMを実行する試験ではない。

実機の確認は利用者の報告に基づく。NESはドクターマリオとパックマン、SNESはスーパーマリオコレクション。映像・音声・操作、OSD1中央表示、取消し、ゲーム自身のタイトルへの再起動と一覧復帰について正常報告を得た。NESではOSD2の5位置、OSD1中央固定、排他表示・長押し/部分解放、P2接続での確認も報告された。controller型式・接続方式、SNESのP2は独立して記録していない。

新しいSD退避と独立した2回の全flash読取りを行ってから導入した。新firmware全byteの読戻しと、更新範囲外の不変を確認した。SDはNES・SNESの2 fileのみ更新し、他の61 file・全file属性・既存CRT保存recordを導入直後に照合した。機器識別情報、ROM、実機退避、私有導入設定は公開しない。

保存RAMの内容比較、実機UARTの物理記録、一覧からの総起動時間、全game/mapper/拡張chip、長時間動作は未確認。ROM再送なしはソースと制御回路試験の確認であり、実機の0x07非発生を信号観測したとの扱いにはしない。reset完了返信・再送は未追加。work RAM消去を伴う電源投入相当の状態も保証しない。SNESのゲーム保存RAMを媒体へbackupする機能は追加していない。

Restart Gameは維持する。3秒程度以下という省略条件は未評価で、自動的に削除しない。

## 再現方法

親repositoryから、記録したsubmodule commitを取得する。

```sh
git submodule update --init firmware-bl616 nestang snestang
cd firmware-bl616
bash tools/ui16/test_osd.sh
bash tools/ui16/test_crt.sh
bash tools/ui16/test_launch.sh
python tools/ui16/test_osd1_dispatch.py
cd ..
bash tools/test_osd1_restart.sh nes
bash tools/test_osd1_restart.sh snes
```

host側はC++17 compiler、Python、Windowsでは既存MSYS2環境を使用した。RTL試験はVerilatorを使う。生成物はbuild-osd1-testsへ出力する。FPGA buildの入口は、各子repository内の `build_console138k_usb.tcl console138k ds2`。firmwareは既存のConsole138K/UI16・SD font設定でbuildした。

詳細な公開用結果は `verification/osd1-20261106/results.json` に記録する。ソース変更だけの公開では実機へ書き込まない。
