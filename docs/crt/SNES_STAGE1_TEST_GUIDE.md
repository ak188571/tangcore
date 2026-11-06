# SNES CRT・OSD2 S1/S2 実機確認手順

2026年11月6日。言語設定 ja-JP。対象：Console138K。SNESの最初の適用段階。ぼかし・走査線の画質効果と保存機能はまだ有効にしていない。FRAME ACKは設定のframe適用を確認する表示で、画質効果の完成や保存成功を意味しない。

## 導入前

FPGA build・timing・関連試験が合格した版だけを導入する。媒体・基板を識別し、SDの全file内容・属性と全flashを新しく退避する。更新対象は共有firmwareとSNES imageの2点。NES image・monitor・font・CSV・既存保存recordを照合して保持する。実機操作は担当者の案内に沿って行い、ゲーム動作中にSDを抜かない。

## 1. 通常起動

日本語一覧の文字、SNESのtitles.csv記載順、選択・scrollを確認する。SNESを1本起動し、ゲーム名・映像・音声・通常のcontroller操作を記録する。controllerの種類、接続先、P1/P2を区別して記録する。

## 2. OSD2（画面の上から順）

P1のSELECT＋左で開き、呼出しbuttonをすべて離す。次の順序で確認する。

| 順 | 表示・項目 | この段階での確認 |
| --- | --- | --- |
| 1 | BYPASS ONLY - STAGE 1 | OSD2が単独で開く。背景ではゲーム映像・音声が進む。 |
| 2 | SAVE: UNAVAILABLE | 保存未対応と表示する。SAVEDにならない。 |
| 3 | INITIAL: DEFAULT | 起動時の基準は全OFF。CSVや保存値を採用した表示にならない。 |
| 4 | CRT REQUEST | 左右またはA/BでOFF/ONを切り替える。映像位置・色は変わらない。 |
| 5 | H BLUR REQ | OFF/WEAK/STANDARD/STRONGの要求を切り替える。まだぼかし効果は出ない。 |
| 6 | SCANLINE REQ | 同じ4段階を切り替える。まだ走査線効果は出ない。 |
| 7 | STORE: UNAVAILABLE | 保存recordは読んでいない。 |
| 8 | APPLY | WAITINGからFRAME ACKへ収束する。連続変更・A/B保持後も、操作を止めれば最終要求へ収束する。 |
| 9 | ROM ID: UNAVAILABLE | ROM IDはまだ取得していない。 |
| 10 | SAVE: NOT AVAILABLE | 選択対象へ入らず、SDへ書かない。 |
| 11 | RESET: NOT AVAILABLE | 選択対象へ入らず、推奨値や保存recordを変更しない。 |
| 12 | DEFAULTS: UNAVAILABLE | defaults.tsvはまだ読んでいない。 |
| 13 | POS | CENTER、TOP LEFT、TOP RIGHT、BOTTOM LEFT、BOTTOM RIGHTを順に確認する。文字更新中にOSDが一度消えず、panel外にゲームが見える。 |

起動直後とX/Yで未保存変更を破棄した後の要求値は、次の3行が全OFFになる。

```text
CRT REQUEST  OFF
H BLUR REQ   OFF
SCANLINE REQ OFF
```

CRT REQUEST・H BLUR REQ・SCANLINE REQを変更した状態でX/Yを押し、押したまま少し保持する。ゲームへ終了buttonが流れず、全buttonを離してから通常操作が戻ることを確認する。再度OSD2を開くと要求は全OFFへ戻る。

OSD2を開いてSELECT＋右を押してもOSD1へ切り替わらないことを確認する。buttonを部分的に離している間も項目が勝手に変わらないことを確認する。

## 3. OSD1（表示順）

X/YでOSD2を閉じ、全解放後にP1のSELECT＋右でOSD1を開く。中央固定であることを確認する。

1. Restart Game：決定して全buttonを離すと、同じゲームのタイトル等へ再起動する。再起動後もOSD2を開け、FRAME ACKが得られる。

2. Return to Game List：一覧へ戻り、日本語表示・titles.csv順序・選択位置を確認する。

OSD1中にSELECT＋左を押してもOSD2へ切り替わらないことを確認する。左右同時の呼出しではどちらも開かず、全解放後に通常操作が戻ることを確認する。

## 4. NESの回帰

既存のNESを1本起動し、映像・音声・操作・日本語一覧を確認する。OSD2では既存の設定値・INITIAL・STORE・SAVE状態が維持され、ぼかし・走査線のpreviewが動作することを確認する。未保存変更はX/Yで破棄する。今回の最初の確認では新たなSAVE/Reset操作を要求しない。

NESのOSD1でRestart Game、Return to Game Listの順に確認する。最後に再びSNESへ入り、NESの設定値や保存状態を引き継がず、SNESのbypass・DEFAULT・UNAVAILABLE表示になることを確認する。

## 記録する範囲

「正常」の報告は、試したゲーム・controller・接続先・P1/P2の範囲へ限定する。今回の比較試験は、既存の239行・field等の入力を従来と同じ形で扱うことを確かめるもので、SNESの全映像modeが本来の解像度で表示できるという認定ではない。

表示不良、WAITINGが残る、閉じる際の入力漏れ、音声不良等があれば、その項目と直前の操作を記録する。実機合格前にぼかし・走査線・保存の次段階へ進めない。
