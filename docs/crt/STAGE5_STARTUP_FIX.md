# 第5段階の起動停止とJTAG処理の修正

追記：この最初の修正版でも起動停止が継続し、Usercode=0x0000e613、status=0が報告された。実機結果はverification/crt-stage5-fix/hardware-results.json、次の追加修正と未確定事項はSTAGE5_JTAG_DIAGNOSTICS.mdを参照する。本書中の「再試験待ち」は導入当時の状態であり、起動回復を確認した記録ではない。

## 実機報告と確認できた範囲

第5段階の初版firmware `e8c617f` を導入後、利用者から、一覧でゲームを選ぶとROMのload画面へ進まず、`Usercode=0x00000000, status=0x0` で停止すると報告された。通常起動し直して別のNESゲームを選んでも同じ症状であった。保存と推奨値の実機試験は未到達であり、第5段階を完了にしない。原文は `verification/crt-stage5/hardware-results.json` に保存する。

この表示を出すのは `writeSRAM_end()` のFPGA image書込み確認である。Ui16Runtimeの呼出順ではprogram→core ID確認→能力確認→ROM loaderであり、CRTのROM識別・推奨値読込はこの後である。表示だけから保存ファイルや特定ROMの問題と断定しない。

## コードから再現した不整合と修正

1. 高速JTAG送信では、最後のbitでTMSを1にしてもsoftware側のTAP状態がSHIFT_DRに残っていた。通常のread_writeではこのedgeでEXIT1_DRへ更新している。高速経路も同じ更新を行い、続くIRへの移動と実際に送ったTMS列が一致するようにした。空chunkは状態を変えない。
2. 書込み終了確認が失敗すると、critical sectionを抜けずにerror表示・ファイルclose・monitor復旧へ進む経路があった。転送後は先にGPIO modeを戻してinterruptを復帰し、終了確認・表示・close・復旧を通常の実行状態で行う。途中read失敗・短い読取でもcleanupを実行する。
3. f_readの戻り値と実byte数を検証し、宣言sizeの全byteを送れた場合だけ終了確認を行う。途中の失敗を成功として返さない。
4. 高速経路では使用していなかった8 KiB bufferの確保を止め、低速経路では必要時だけ確保して必ず解放する。detectChainの負のerror値も失敗として扱う。

該当するprogrammer.cppは、実機合格4bと初版第5段階で同一だった。上記は今回調査で見つかった既存処理の不整合であり、「第5段階の保存処理が直接JTAGを壊した」とは結論しない。今回の実機停止の全要因をこの2つの再現試験だけで特定したものではなく、修正版で起動が回復するかを実機で再確認する。

## 検証

独立した16状態のTAP modelで、実際の高速送信関数とset_stateを使用し、MSB順の全bit、chunk境界、最後のbitのEXIT1_DR、次のIRとidleへの移動を照合した。旧sourceではsoftware状態とmodel状態の一致が失敗し、修正版では成功した。

実際のfpga_programを使ったhost試験で、成功、終了確認失敗、open/read/短読/予期しないEOF/chain/erase/start/close失敗を模擬し、interrupt、GPIO mode、file、確保bufferの解放を確認した。高速・低速経路を別々にcompileして確認した。旧sourceでは終了確認失敗後のcritical section保持が再現した。

第5段階の保存・推奨値・Reset、日本語一覧、OSD、起動、folder、scroll、改行の試験も合わせて8本を実行し、すべて成功した。firmware buildは成功。NES imageと試験用CSVは初版第5段階から変更しない。FPGAの新buildや新しいtiming検証を行ったと記録しない。

新しい記録は `verification/crt-stage5-fix/`、初版とその失敗記録は `verification/crt-stage5/` に分けて保持する。修正版の実機導入・全flash読戻し照合は完了。通常起動と保存は利用者の再試験待ちである。

## 修正版の実機反映

2026年11月3日21:23頃、既知Console138Kへ修正版firmwareを反映した。microSDの58ファイルを新たに退避し、NES image・試験用CSV・ROMを含む全58ファイルが変更されていないことを照合した。SDファイルの更新は行っていない。

firmwareの基板側SHA-256と4 MiB全flashの読戻しが一致し、0x40000未満と0x80000以降が直前の検証済み初版第5段階snapshotと一致した。SDK設定は元のbyteへ復元した。初回の全flash読取は接続確立に失敗し、firmwareの再書込みをせず読取方式を切り替えて成功した。両logを保存している。

即前の復旧用flashは、初版第5段階の検証済み全読戻しをコピーしたもので、初版が実機合格版という意味ではない。最後の実機合格4bのflashと元の2列CSVも別に保持する。今回新たに書込み前のflash読取を行ったとは記録しない。

実績は `verification/crt-stage5-fix/deployment.json` を参照する。ゲーム起動が回復したことと保存が動くことは、通常起動後に改めて確認する。第5段階の実機完了tagはまだ作成しない。
