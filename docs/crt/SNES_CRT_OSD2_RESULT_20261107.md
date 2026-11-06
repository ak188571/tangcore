# SNESTang CRT・OSD2 適用結果

2026年11月7日。Console138K向けの段階的な適用を、報告された実機範囲で完了した。水平ぼかし・走査線・OSD2・SDのUSER保存・Resetによる推奨値追従を実装した。日本語一覧、titles.csvの順序、既存NES設定を維持し、一時的な試験metadataは復旧済み。

## 最終sourceと実機成果物

対象repositoryはすべてtangcore-integratedを使用した。各段階の実装・試験・実機報告をcommitした。変更はlocalに保持しており、今回GitHubへのpushは行っていない。

| 対象 | 最終commit | 状態 |
| --- | --- | --- |
| firmware-bl616 | 8f05446 | S4c Reset・SD保存を導入 |
| snestang | 8cf6353 | 確認済みS3bのFPGAを維持 |
| nestang | ec33410 | 今回のSNES適用でsource変更なし |
| monitor | e12b253 | 今回のSNES適用でsource変更なし |

firmwareは230,960byte、SNES imageは5,066,442byte。SHA256は次のとおり。

```text
firmware:
cc7a60c5b51c5a7e031e02c6fb3299e30b6ecff512a7e840ed1f6b1f99002b44
SNES image:
bcc879e4f6da1194b8fa43edb487f71ac13c8b6037086558a42b6fa80b0dc429
```

## 段階ごとの結果

S0でSNES映像経路、UART、OSD、controller、共有storageの所有を調査した。NESと異なる256×224の読出し・拡大経路を基準とし、NESの実機結果をSNESへ流用していない。S1でbypass、OSD2、frame ACKを導入し、S3aで水平ぼかし、S3bで走査線を追加した。OSDの文字と枠はCRT効果の後に合成する。

S4aでSD上のraw ROM identityと読取り専用復元、共有storage lease、SD fault guardを導入した。S4bで明示USER SAVEと取消し・電源再投入後の復元を確認し、S4cでReset preview・明示保存・現在の推奨値への追従を確認した。

最終firmwareは関連host試験15組、導入保護30件、一時metadata保護15件が合格した。導入予定の実metadataをproduction C++ parserにも通し、全name/title/行順の一致を確認した。production 99fileがcommit/build入力と一致し、実ELFのSDH wrapper接続も照合した。S3b FPGAのsetup/hold違反は0/0。既存のPLL・routing警告は残る。

## 実機で確認した範囲

SNESはスーパーマリオコレクション・USB P1を使用した。段階ごとに通常起動・映像・音声・操作、OSD2、効果、FRAME ACK、取消しを報告された範囲で記録した。OSD1の再起動・一覧復帰はS1/S3aで確認した。controllerは利用者申告のSFC風、pid:vid=0079:0006。

S4cはSNES起動2回へまとめた。1回目に既存USER値の優先、CSV推奨値へのReset preview、保存前の取消し、明示Reset SAVE、同mode再SAVE、保存後の取消しを確認した。2回目は一時metadataの復旧後に、古いCSV数値を固定せず全OFFへ追従することをOSD2項目1〜13の正常報告で確認した。

共有firmware変更時にはNESのドクターマリオでも回帰を依頼した。最新の返答はOSD2項目1〜13正常であり、その範囲を記録した。その他の依頼項目まで個別の正常報告があったとは扱わない。

## 保存と最終SD状態

明示SAVEはOSDを開いたまま保存する。X/Yは未保存previewを最後の保存成功値へ戻す。Resetは現在のCSV、system defaults、global defaults、built-in OFFの順で推奨値を解決し、明示SAVEでReset modeを保存する。次回起動時にその時点の推奨値を採用する。

実SDで検証した最終recordは次のとおり。ROM IDは232bb5b8、raw sizeは2,097,152byte。

```text
.a  USER   generation 3  ON / WEAK / STRONG
.b  RESET  generation 4  値0
```

両slotのschema・kind・key・reserved・CRCを照合し、同mode再SAVEの世代不増加を確認した。.aは以前のUSER値を保持し、最新の.bがResetとして選ばれる。現在は全OFFで起動し、起動時sourceはDEFAULT、保存modeはRESET、defaultsはMISSINGと表示される。

一時SNES titles.csvは元の全byteへ復元し、今回作成したdefaultsだけを除去した。SDは元と同じ65fileで、実SAVEにより更新した.b以外の元64file・属性は一致した。2回目起動後にも全65file・属性と両recordが不変であることを、新しい読取り退避で確認した。

S4cのfirmware書込みは1回。全4MiBの読戻しでfirmware全byteとcustom領域外の不変を確認した。復旧用のSD全体・全flash・custom領域の退避は各kitのsessionに保持する。最終SD照合は読取りだけで、追加の実機起動・書込みは不要。

## 確認範囲の境界

全ゲーム・他のcontroller接続先は未確認。SYSTEM/GLOBALの採用、不正defaults全体拒否はhost試験で確認した。SD fault guardもhostの代替処理で検証しており、物理faultは未注入。USB storageでのCRT保存は有効にしていない。

現在のConsole映像経路は256×224を表示する。239行全体、高解像度、interlace、PALの全modeを確認した結果ではない。詳細な監査、各段階の依頼と返答、試験log、SD照合結果はdocs/crt/SNES_STAGE*.mdとverification/snes-crt-stage*に残した。

microSDはPCへ接続した状態で最終照合を終えた。PCで安全に取り外して、電源を切ったConsole138Kへ戻せばよい。追加の確認報告は不要。
