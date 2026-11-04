# CRT・OSD2 第1段階 実機試験結果

2026年11月3日、Console138K／NESの現在の接続環境で、依頼した第1段階の実機試験をすべて完了した。映像・音声・操作、OSDの表示と入力制御、frame適用確認、session内の保持と別ゲーム起動時の初期化について、利用者から正常との報告を受けた。

## 基準となる版

- 基準branch：`tangcore-integrated`、親commit `a67003941a26ccc856134f0d9142298d94b34483`。
- 作業branch：`crt-osd2-stage1`。
- 実機確認済みの基準tag：`crt-osd2-stage1-hw-20261103`（local）。
- BL616 firmware：`5bd8a4404bd2ebe7496d7a28e62a3cbf2aea3f76`、220,560 byte。
- firmware SHA-256：`c14f474dc3305b759d3ee36e99abc8193c57f5b9e3714532b1b835472ad5c136`。
- NES core：`39af62a9042c5561ad8cf520471cff7f84519a2b`。
- NES image SHA-256：`f273d30b546403e7e330803f0be822b740760ba002d5955dec5b69e5e64189f0`。

firmwareは書き込み後に基板側のSHA-256と4 MiB全体の読み戻しを照合した。0x40000未満と0x80000以降は退避した内容と一致している。OSD修正時にmicroSDとNES coreは変更していない。

## 確認結果

| 項目 | 結果 |
| --- | --- |
| NESの映像・音声・ゲーム操作 | 正常 |
| SELECT＋左でOSD2を独立して開く | 正常 |
| 要求値変更後にFRAME ACKが表示される | 正常 |
| 項目・値変更時にOSDが一瞬消える問題 | firmware修正後に解消を確認 |
| 中央と四隅の5位置で文字が欠けない | 正常 |
| OSD2表示中のSELECT＋右でOSD1が重ならず、要求値も変わらない | 正常 |
| 閉じてから開いたOSD1が中央に表示される | 正常 |
| OSD操作がゲームへ流れない | 正常 |
| 終了button保持中は操作を再開せず、全button解放後に復帰する | 正常 |
| 同じゲームでOSD2を開き直すと要求値と位置を保持する | 正常 |
| 一覧へ戻ったときの日本語表示とtitles.csv順序 | 正常 |
| 別のNESゲームで3つの要求値がOFFとなり、FRAME ACKが表示される | 正常 |

実機表示と操作の判定は利用者の報告による。使用controllerと接続先は未申告であり、すべての入力sourceや他のcoreへ結果を一般化しない。別ゲーム起動時のPOS初期化は確認対象に含めていない。全ROMの表示順序を機械的に照合したという意味でもない。

機械可読記録は `verification/osd-inplace-20261103/` の `hardware-stage1.json`、`hardware-retest.json`、`functional-tests.json`、`session-tests.json`、`deployment.json` を参照する。

## 次の段階

現在の版はbypassのみであり、要求値をONにしてもCRTの画質効果は発生しない。水平blurを追加する際は、この版を基準にOFF時の映像一致、端の画素処理、設定のframe境界反映を検証する。その後にscanline、推奨初期値、Reset to Recommended、ゲーム単位の保存を進める。
