# CRT導入の作業順序とcommit方針

2026年11月3日の指示に基づき、今後は次の段階ごとに実装と検証を区切り、commitを作成する。以前の文書で「第1段階」と呼んでいた実機試験済みの範囲は、この表の1〜3に相当する。

| 順序 | 作業 | 確認すること | 現在の状態とcommitの区切り |
| --- | --- | --- | --- |
| 1 | crt_filterをbypassで挿入 | 従来映像と一致し、OSDの位置も変わらない | 完了。既存の1〜3の統合commitに含まれる |
| 2 | 設定転送とframe境界での反映 | 設定が安全に一括更新される | 完了。既存の1〜3の統合commitに含まれる |
| 3 | OSD2の最小構成 | OSD1との排他、項目操作、入力遮断、解放待ち | 完了。既存の1〜3の統合commitとOSD表示維持の修正で確認済み |
| 4a | 水平ぼかし | OSD2から実映像を調整でき、OFF時は基準映像と一致する。画面端の処理も正しい | 実装・自動試験・build・導入と依頼した全実機試験が完了。local tagはcrt-stage4a-hw-20261103。STAGE4A.mdとverification/crt-stage4a/を参照 |
| 4b | 走査線 | OSD2から実映像を調整でき、OFF時と水平ぼかし併用時も正しい | 修正版の実装・自動試験・build・導入と依頼した全実機再試験が完了。WAITING修正、元224行の明暗配分、表示端・入力・ゲーム切替も確認済み。local tagはcrt-stage4b-hw-20261103。STAGE4B.mdとverification/crt-stage4b-fix/を参照 |
| 5 | 推奨値、ゲーム別保存、Reset to Recommended | 再起動時の復元、推奨値への復帰、保存失敗時の処理が正しい | BL616側の実装・関連7本の自動試験・firmware build完了。NESは実機確認済み4bを再利用。実機導入・再起動試験待ち。STAGE5.mdとverification/crt-stage5/を参照。4bから分けてcommitを行う |

## 完了済みの履歴

1〜3は既にまとめて実装・commitされている。履歴は維持し、今後の変更を上表の単位で分ける。

- 親の統合commit：`ec95a01cd021847db6238d2755d1f1b6cd861348`。
- 初版firmware：`b77930d60db63e675a855b29f9f076fa556d108f`。
- NES core：`39af62a9042c5561ad8cf520471cff7f84519a2b`。
- OSD表示維持のfirmware修正：`5bd8a4404bd2ebe7496d7a28e62a3cbf2aea3f76`。
- 実機試験完了記録：親commit `81d1726`。
- 実機確認済みのlocal tag：`crt-osd2-stage1-hw-20261103`。

試験結果と確認範囲は `HARDWARE_STAGE1_20261103.md` を参照する。

## 今後の記録方法

一つの実装commitへ次の段階の機能を混在させない。各区切りで必要な自動試験とbuildを行い、結果と未確認事項を記録する。実機でしか確認できない画質や操作感は、実機試験前には未確認と明記し、報告後に試験記録を別commitで更新する。必要な不具合修正も対象段階を明示して独立したcommitにする。

submoduleを変更した場合は、対象submoduleで先にcommitし、親repositoryでその参照と関連文書・試験記録をcommitする。これにより、親commitから各段階のfirmwareとFPGA coreの組合せを再現できる。

基準branchは引き続き `tangcore-integrated`。作業は既存の `crt-osd2-stage1` 上で継続し、実機確認済みtagから復帰可能な状態を保つ。GitHubへのpushは、このlocal commit方針には含めない。
