# SNES CRT保存のSD障害と保存中断

2026年11月16日（日本時間）。試験対象のfirmware `95871ef8e9ef547767b145cee4e85577e8bb4972` の保存・読込みをPCで確認した。予備microSDがないため、**実機試験は保留中。** SD障害の実機での再現と保存中の電源断は未実施。

## PC結果

- SNESを表すsystem IDで既存の `crt_restore_test.cpp` と `crt_save_test.cpp` が合格した。open・read・closeの読込み失敗、書込みの短縮と失敗、sync・close・再読込み検証の失敗、再試行前の再読込みを確認した。
- `tc_snes_sd_guard.cpp` の既存試験4条件が合格した。SNES用の読込みタイムアウトと書込みエラーはSD controllerをリセットし、その後のSD I/Oを電源再投入まで止める。
- SDKのFatFsと製品の保存・読込み処理を、メモリ上のFAT32で実行した。最新の正常recordがあるsectorから読込みエラーを返すと、`READ ERROR` になり、SAVEは書込み0件で拒否された。2 sectorを書き込んだ後に書込みエラーを返す条件では、再マウント後も直前の正常recordを採用した。
- 保存の中断42条件と、保存完了後の対照2条件を確認した。どの条件でも直前の正常record（b世代2）と同じdirectoryの別ファイルが残った。再マウント後はb世代2か、成功対照と全32 byteが一致するa世代3を採用した。

| 記憶媒体のモデル | 中断／対照 | b世代2を採用 | a世代3を採用 |
| --- | ---: | ---: | ---: |
| 成功した512 byteの書込みが直ちに残る | 9／1 | 7 | 3 |
| 同期までの書込みは電源断で失われる | 9／1 | 9 | 1 |
| 中断したsectorの先頭1・256・511 byteだけが残る | 24／0 | 19 | 5 |

ここで使った3モデルは、PCが再現した書込み順と残存範囲を表す。実機のSD driverで `CTRL_SYNC` は追加のカード命令を発行しない。実カード内部のcache、sector全体の読不能、FAT管理領域の損傷、電源回路による挙動は今回の結果からは確定できない。

## 再実行

親repositoryが参照する `firmware-bl616` を用意する。SDKのFatFsは、Bouffalo SDKのcommit `7f44f9ea6b4ccf96db8c5236c8024b68e2a76df7` にある実装を使用した。実行にはPython 3とGCC／G++が必要。

```powershell
python tools/test_osd2_sd_faults.py --firmware firmware-bl616 --sdk ../bouffalo_sdk --output ../osd2-sd-fault-pc --compiler-bin C:/msys64/ucrt64/bin
```

GCC／G++がPATHにあれば `--compiler-bin` は省略できる。試験用FAT32はprocess内のメモリに構築し、生成物は `--output` のみに置く。中断点ごとの採用結果とソースのSHA-256は `verification/osd2-sd-fault-20261116/pc-result.json` に記録した。

## 保留中の実機試験

試験用microSDへ通常起動に必要なファイルと対象ROM、前世代と最新世代の区別がつく試験用recordを用意する。普段のmicroSDは保管する。実機では、実際に書き込んだあと特定の段階で停止して合図を出せる診断版を用い、SAVEから目視で時間を推測する手順を避ける。

| 検査 | 確認点 |
| --- | --- |
| record読込み失敗 | 診断でFatFs層にだけ読込みエラーを返す場合は、OSD2の `SAVE READ: READ ERROR`、SAVE拒否、record不変を確認できる。SD controller自体の異常を検出した場合は通常firmwareが起動を中止するので、別の結果として記録する。 |
| SAVE中の処理失敗 | 対象recordの書込み・同期・closeで意図した失敗を発生させ、`SAVE FAILED` と、次に読み直したときの世代・recordの内容を照合する。 |
| 保存中断と再起動 | 試験用microSDへの保存を同期前の既知の地点で止め、合図を見て電源を切る。再起動後に採用した世代を確認し、PCで両slotのCRC、内容、他ファイルを照合する。 |

各条件の期待値と復元手順は、実機で使う診断版と試験用microSDの構成を確定した後に固定する。
