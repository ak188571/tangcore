# OSD2 起動時情報の明確化と追加実機試験

2026年11月7日。対象はConsole138K、共有BL616 firmware、SNESTangとNES回帰。
実機合格済み小型版を基準とし、tangcore-integratedで実施する。
SYSTEM／RECOVEREDの通常①〜⑧・補助①〜⑨・preview・取消しは実機正常とのユーザー報告を受領した。
SYSTEM試験後のSD全66file・属性の不変を新しい退避で照合した。GLOBAL試験fileへ切替済み。
GLOBAL／BAD SAVEの通常動作・通常①〜⑧・補助①〜⑨・preview・取消しも実機正常とのユーザー報告を受領した。
GLOBAL試験後のSD全66file・属性の不変を新しい退避で照合し、最後の異常時試験fileへ切り替えた。
BUILT-IN／NEW SCHEMA／BAD FILEの通常動作・通常①〜⑧・補助①〜⑨と、SAVE FAILED・snapshot維持・取消しのA〜Cは想定どおりとのユーザー報告を受領した。
SNESは予定の3回で表示確認を終了。SAVE拒否後の全66file・属性不変を新しい退避で照合した。
a7 Reset／b6 USERを全byte・属性で復旧し、一時defaultsを除去。元の全65file・属性への一致も確認した。
NES回帰と最終SD照合は未完了。追加のSNES起動は行わない。
日本語一覧・映像・音声・通常操作は同じ質問で依頼したが、回答では個別には再記載されていない。
PC試験の合格を実機合格とは扱わない。

## 補助表示の意味

通常表示はCRT、BLUR、SCAN、SAVE、RESET、POS、START:INFOを維持する。
英語、通常16×10 cells、STARTで開く補助表示24×17 cellsを維持する。
OSD1、ASCII font、FPGA image、タイトル一覧、titles.csvの内容と順序は変更しない。

| 旧表示 | 新表示 | 意味 |
| --- | --- | --- |
| INITIAL | LOADED FROM | ROM読込み時に実際に採用した設定値の出所 |
| STORE | SAVE READ | 同じROM読込み時の保存record読取り・選択結果 |
| DEFAULT | BUILT-IN | fileに推奨値がなく組込みの全OFFを採用 |

LOADED FROMのUSERは明示保存した値、CSVはゲーム別推奨値、SYSTEMはdefaults.tsvのsnes行、GLOBALは同fileの*行を表す。
優先順位はUSER、CSV、SYSTEM、GLOBAL、BUILT-IN。
SAVE READのRESETは保存値そのものを固定せず、現在の推奨値に従うrecordを読んだことを表す。
そのためLOADED FROMがSYSTEMでSAVE READがRESETまたはRECOVEREDでも矛盾しない。

両行はROM読込み時のsnapshotであり、その後のpreview、SAVE、RESETでは更新しない。
現在の保存状態は上のSAVE行と補助表示のSAVE状態で示す。
OSD1のRestart GameはROMやmetadataを読み直さないため、採用元の比較には新たなROM読込みが必要。

| SAVE READ | 読取り結果 |
| --- | --- |
| USER / RESET | 選んだ有効recordの種類 |
| RECOVERED | 一方のrecordが不正で、他方の有効recordを採用 |
| MISSING | 保存recordがない |
| BAD SAVE | 有効な保存recordがなく、不正なrecordを検出 |
| NEW SCHEMA | 未対応のschemaを検出し、保存値を採用せず書込みも拒否 |
| CONFLICT | 世代順序または同世代の内容が競合 |
| READ ERROR | 読取りに失敗し、古い保存値を推測採用しない |
| NO ROM ID | 利用可能なROM identityがない |

## 最小起動の実機計画

SNESは同じスーパーマリオコレクションを合計3回起動する。
各回の確認はその起動中にまとめる。firmware導入は1回のみ。

| 回 | 一時fileの状態 | 設定値 | LOADED FROM | SAVE READ | DEFAULTS |
| --- | --- | --- | --- | --- | --- |
| 1 | SYSTEMとGLOBAL、a7 Reset正常、b6 CRC不正 | ON/STD/WEAK | SYSTEM | RECOVERED | OK |
| 2 | GLOBALのみ、a/bともCRC不正 | ON/WEAK/STRONG | GLOBAL | BAD SAVE | OK |
| 3 | 不正なdefaults、aは未対応schema、b6正常 | OFF/OFF/OFF | BUILT-IN | NEW SCHEMA | BAD FILE |

1回目は有効なSYSTEMが異なるGLOBAL値より優先することと、壊れた片側からの復旧を確認。
2回目はSYSTEMがないときにGLOBALが採用されることと、両側不正時の表示を確認。
3回目は不正なdefaultsを全体として拒否し、既知schemaの片側を推測採用しないことを確認。
3回目だけUSER保存を1回要求し、SAVE FAILED、補助SAVE: FAILED、取消しを確認する。
production保存処理が未対応schemaを検出した時点でmkdir、書込み用open、write、syncより前に拒否することをPC試験で確認する。
物理的なSD抜去や故障注入は行わない。正常SAVEはこの試験では実行しない。

既存のa7 Resetとb6 USERは実際のユーザー操作による保存値であり、以前のa3/b4へは戻さない。
毎回SD全fileを新たに読取り退避し、現在の一時fileが完全一致した場合だけ次のfileへ更新する。
知らないUSER保存、他fileの変化、属性変化を見つけた場合は退避を残して停止し、上書き復旧しない。
3回目後に現在の一時fileを照合し、今回の最初の退避からa7/b6を全byte・属性復旧し、一時defaultsだけを除去する。
titles.csvは全段階で書き込まない。NES回帰は復旧後に1回だけ行い、最後にSD不変を読取り照合する。

## PC検証と範囲

firmware commit: 95c4416187bf19d42793336ba0390b75946d1614。
共有firmwareは230976 byte、SHA256は次の通り。

```text
f033d8c2240fc9c9d658ba95aa5e46b8a05d9eb95c6a9d6c7bdaeb73401348ba
```

関連host試験16群が合格。実際の読取り・保存・表示処理へ試験fileを通し、3条件の表示と未対応schemaでの無書込みを確認した。
通常画面の全cell・位置・枠は前回合格版と同一。補助表示は最長のBUILT-INとREAD ERRORも既存幅に収まる。
NES/SNES両systemで、USER/Reset SAVE後もLOADED FROMとSAVE READのsnapshotが維持され、SAVE状態だけが更新されることを確認した。
buildのproduction入力99fileはcommitと一致し、ELFのSDH wrapper結合とSDK sourceの維持を照合した。
FPGAの変更はなく、既存のSNES/NES/monitor合格版を使用する。

今回の実機試験ではCONFLICT、実際のREAD ERROR、SAVE中の電源断、P2/DS2/BL616側USB、全PPU映像modeの合格を主張しない。
