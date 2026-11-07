# OSD2 起動時情報の明確化と追加実機試験

2026年11月7日。対象はConsole138K、共有BL616 firmware、SNESTangとNES回帰。
実機合格済み小型版を基準とし、tangcore-integratedで実装・検証した。
通常の小型表示と英語を維持し、起動時情報をLOADED FROM／SAVE READへ改称した。
SNESは3回、NESは1回の起動依頼で、以下の実機正常・想定どおりの報告を受領した。

| 対象 | 実機で報告された結果 |
| --- | --- |
| SNES 1回目 | SYSTEM／RECOVERED、通常①〜⑧・補助①〜⑨、preview・取消し正常 |
| SNES 2回目 | GLOBAL／BAD SAVE、通常動作と両表示、preview・取消し正常 |
| SNES 3回目 | BUILT-IN／NEW SCHEMA／BAD FILE、通常動作と両表示、SAVE拒否・snapshot維持・取消しが想定どおり |
| NES 1回 | 通常動作、CSV／RESET、両表示、START保持中の入力遮断、preview・取消し正常 |

SNESはスーパーマリオコレクション、NESはドクターマリオ、接続はUSB P1。
SYSTEM段階の一覧・映像・音声・通常操作は同じ質問で依頼したが、回答は①〜⑧正常であり個別には再記載されていない。
GLOBAL・異常時・NESでは通常動作も明示報告された。NESの結果からSNES合格を推定していない。

各SNES試験後の全66file・属性不変を新しい退避で照合した。
元のa7 Reset／b6 USERを全byte・属性で復旧し、一時defaultsを除去した。
NES確認後も新しい読取り退避で、開始時の全65file・属性、titles.csv、NES設定との一致を確認した。
追加のSNES/NES起動は不要。実機観察はユーザー報告であり、PC試験と区別して記録した。
GitHub公開対象と合格tagはGITHUB_PUBLICATION_OSD2_LOAD_INFO_20261107.mdに記録する。

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

## 実施した試験条件と保護手順

SNESは同じスーパーマリオコレクションを合計3回の起動依頼で確認した。
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

## 確認記録

firmwareの変更commitは95c4416187bf19d42793336ba0390b75946d1614。
verification/osd2-load-info-20261107/results.jsonに最終結果を、hardware-system/global/errors/nes.jsonに回答原文と確認範囲を記録した。
各段階の導入・SD不変・復旧を別commitに記録している。
最終SD照合は全65 user fileの内容・属性が対象であり、全sectorやFAT領域のimage一致を意味しない。
実機へ追加書込み・追加起動を要求せず、この確認範囲を完了とする。
