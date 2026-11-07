# 小型OSD2 適用結果

2026年11月7日。通常表示を小さくし、補助情報をSTARTで開閉するOSD2を導入した。START後の全解放待ちを含む最終版について、SNESとNESの報告範囲、最終SD不変を確認した。OSD1/OSD2は全機種で英語を維持し、日本語化しない。既存の日本語一覧とtitles.csv順序は保全した。

## 表示と操作

通常枠は26×17から16×10文字となり、面積を63.8%減らした。既存fontと文字の大きさは同じ。補助表示は24×17文字で、STARTで収納すると枠も小さく戻る。

```text
通常：CRT / BLUR / SCAN / SAVE / RESET
保存済み SAVE OK / 未保存 SAVE * / 失敗 SAVE FAILED
START:INFO <-> START:HIDE
STD = STANDARD / RESET = RECOMMENDED
POS: C / TL / TR / BL / BR
```

ROM ID、INITIAL、STORE、FRAME ACK、DEFAULTS等は補助表示へ移した。非表示中もACK照会と再送は続く。STARTは1押下で1回だけ開閉し、その後は全button解放まで追加のA/B・方向を遮断する。全解放後の通常操作とX/Y取消しは利用できる。OSD1の文言・操作・geometry、CRT効果、保存engineは変更していない。

## 検証と最終状態

SNESはスーパーマリオコレクション・USB P1で通常動作、OSD補助項目、START保持中の入力遮断、全解放後の操作、縮小復帰・取消しを正常と報告された。NESはドクターマリオの通常表示1〜8・補助表示1〜9を正常と報告された。SNESの合格をNES結果から推定していない。その他のゲーム・接続先まで実機合格を拡張しない。

関連host試験15組と導入保護30件が合格した。hostでは両systemの全32設定・5位置、実文字RAM書込み、START保持後に追加したbuttonの遮断、解放後の意図したSAVEとUSER/Reset双方の同値SAVE省略を確認した。最終firmwareのproduction 99file、commit/build入力、実ELFのSDH wrapperも照合した。

最終firmwareは230,960byte。sourceとSHA256は次のとおり。

```text
source a1b6755a271e8dfc29f388e85bb3aef772862f18
SHA256 943f883476aa57d49367c0b19992553c42ee36e68b36938d5f80f626cf1ec622
```

修正版のfirmware書込みは1回。全4MiBの読戻しでfirmware全byteとcustom領域外の不変を確認した。NES/SNES/monitorのFPGA source・imageは保持した。新しいFPGA buildやtiming合格を追加したものではない。

最後にSD全65fileを新しく読取り退避し、今回の導入前退避との全内容・属性の一致を確認した。現在の保存値は次のまま保持している。

```text
SNES ROM ID: 232bb5b8 / raw size: 2097152
.a RESET generation 7 / value 0
.b USER  generation 6 / ON / OFF / OFF
```

以前のrecord更新は利用者が意図して行ったSAVEと確認済みであり、softwareの不具合による更新とは扱わない。現在の値を基準に退避し、以前のgenerationへ戻していない。修正版の最終確認では両record・全65file・属性が不変だった。SD書込みは0回。

## 後続作業

INITIAL/STOREが起動時の情報であることを分かりやすくする表示整理と、SYSTEM/GLOBAL・異常statusの実機表示確認は、利用者方針どおり後続作業として残す。OSD日本語化は行わない。

実装・試験・実機報告はtangcore-integrated上でcommitし、合格tagはosd2-compact-hw-20261107とする。この小型版の新しいcommit/tagはGitHubへまだpushしていない。公開済みS4c合格tagは保持した。

microSDはPCへ接続した状態で照合を終えた。安全に取り外して、電源を切った本体へ戻せばよい。追加の起動・確認報告は不要。
