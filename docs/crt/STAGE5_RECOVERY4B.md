# 第5段階の起動退行と第4b段階への復旧

## 実機報告と診断

診断版c166944の導入後、利用者から「信号なし」、続けて「電源投入直後から一覧も出ない」と報告された。回収したmicroSDのcrt-boot.logにはmonitor.binのprogram-failedが残っていた。ID=0x0001081b、初回と最終status=0x00000622、UserCode=0、確認3回で不成立。DONEがなくbad-command bitが立っている。元のNES選択後の停止に加えて、monitor起動にも退行が出た。元の第5段階不具合の原因をこのlogだけで特定済みとはしない。

利用者の実機確認と矛盾するPC試験結果を優先しない。診断版の継続投入を止め、最後に依頼した実機試験がすべて合格したcrt-stage4b-hw-20261103へ戻した。

## 復旧内容と照合

2026-11-03T21:56:36.219671+09:00、既知Console138Kで次を完了した。

- 現在のmicroSD全59filesを新たに退避し、起動記録も保全した。
- 第4b段階の検証済み全flashから0x40000〜0x7ffffの262144bytesを取り出し、この専用領域だけを復元した。再buildしたfirmwareではない。
- 基板側SHAを確認後、4 MiB全flashを読戻し、合格時のsnapshotと全byteが一致した。全flash SHAはf1bbe0c2f3e001e2deec837b6683100d86c684d13f92092c87975f05b395a0ea。firmware SHAはbe73e95967114f96d0c4aa829c9cef125c4756c90191bdbdde87b9a604c7d9a0。
- nes/titles.csvは初版第5段階の導入前に退避した元の2列へ戻した。SHAは4f5a576757f68ebad58f9b5b20ef42fc7449470a0fd79076c0897034ca1e30fe。試験用3列CSVは今回のSD退避にも残っている。
- CSV以外の58filesは変更されていない。NES image、monitor image、ROM、font、起動logを保持した。
- SDK設定を元のbyteへ復帰した。全flashの初回mode2読取は接続確立に失敗し、再書込みせずmode0の読取りで成功した。前回までの接続傾向と異なるため、読取方式の成功を一般化しない。

書込み前flashの保全には、直前の導入時に検証済みの全読戻しをコピーして使った。今回新たな書込み前読取を行ったとは記録しない。復旧後の全読戻しは今回実施した。

## 現在の状態と次の条件

基板のflashは実機合格第4b段階と完全一致し、CSVも元へ戻っている。ただし、今回の通常起動で映像が戻ったことは利用者の確認待ちである。まず日本語一覧とNESゲームの起動・映像・音声・操作を確認する。第4b段階には第5段階のゲーム別保存・推奨値接続は含まれない。

作業branchの第5段階sourceと不合格記録は調査用に保持し、基板に現在動作するrevisionと混同しない。新たな実機完了tagは作らない。第5段階の実装を再開するときは、回復を確認した第4b基準から変更を小さく分けて原因を絞る。広範囲のJTAG変更を再投入する前に、既存の動作経路との差を説明できるようにする。

生の起動記録はverification/crt-stage5-recovery4b/boot-diagnostic.log、復旧照合は同deployment.json。個別の試験不合格はverification/crt-stage5-jtag2/hardware-results.jsonを参照する。

## 復旧後の実機確認

利用者から「1, 2正常」と返信があり、通常起動後の日本語NES一覧、およびドクター・マリオの起動・映像・音声・操作が正常に戻ったことを確認した。今回の回復結果をverification/crt-stage5-recovery4b/hardware-results.jsonに記録した。第5段階の推奨値・保存・Resetは未確認のままで、完了扱いにしない。次の変更を導入する前に、第4bの経路を基準として第5段階で増えた処理を切り分ける。
