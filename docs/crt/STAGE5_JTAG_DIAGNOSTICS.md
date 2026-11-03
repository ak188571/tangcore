# 第5段階の起動停止・追加修正と診断

追記：この診断版c166944の実機試験も不合格。利用者から「電源投入直後から一覧も出ない」「信号なし」と報告された。microSDの記録ではmonitor.binのprogram-failed、ID=0x0001081b、status=0x00000622、UserCode=0、3回確認でも不成立だった。DONEがなく、bad-command bitが立っている。以前のNES選択後の停止に加え、monitor起動にも影響が出た退行として扱う。PC試験成功は実機の動作保証にならなかった。確認済み第4b段階への復旧を優先し、診断版を継続使用しない。実機原文と値はverification/crt-stage5-jtag2/hardware-results.jsonを参照する。第5段階の元の起動停止の原因はなお未確定である。

## 実機で分かったこと

2026年11月3日、最初の起動修正版01f38f4でも停止が続くと利用者から報告された。表示は初版のUsercode=0からUsercode=0x0000e613へ変わり、status=0、他のNESゲームでも停止する。原文はverification/crt-stage5-fix/hardware-results.jsonに保存した。

0xe613は使用中のNES imageの.fsに記録されたUserCodeと一致する。ただし、一つの値の一致はDONEや正常動作の証明にならない。前回修正のPC試験は成功したが、実機の起動回復には至っていない。最後の実機合格基準はcrt-stage4b-hw-20261103で、第5段階は未完了とする。

画面表示を出す場所はFPGA書込みの終了確認である。ただし、表示が残っていることだけでは、CPUがその命令に留まっているか、後続の処理で止まったかは特定できない。CRTのROM識別・推奨値読込みより後の段階へ到達したとも断定しない。

## 今回の変更

- 高速データ送信後にEXIT1_DR→UPDATE_DR→RUN_TEST_IDLEを明示し、6 clockのidleを経てCONFIG_DISABLEを送る。高速のMSBデータ送信自体は変更しない。
- 制御と読取りではTCKを下げ、TMS/TDIを設定し、1 µs待つ。low期間にTDOを読み、TCKを上げて1 µs待つ。個別GPIO registerへのread-modify-writeを制御用の経路から除き、SDKのGPIO操作に統一する。制御clockは最大500 kHzで、bulk送信速度は別扱いとする。
- 終了時はstatusを先に読み、device ID、UserCodeを記録する。成功には対象IDの一致、DONE、CRC/command/ID errorなしを要求する。全bitが1のstatusも拒否する。UserCodeだけで成功にはしない。
- 不成立の場合はTAPだけをresetして読み直し、最大3回で終了する。SRAM再書込みやDONE判定の省略は行わない。
- 状態待ちは500 msまたは512回の早い方で打ち切る。全bitが0／1の読取値を「bitがclear済み」の成功にしない。待ちが続く間も一定間隔でtaskを譲る。
- 起動記録を同じvolumeの/crt-boot.logへ追記する。記録段階はprogram開始／成功／失敗、core ID待ち、CRT準備開始／終了、ROM load開始／結果。statusの初回と最終値、ID、UserCode、再確認回数、直近pollのmask・期待値・読取値を含む。

記録は既存内容を上書きせず、64 KiBに収まらなければ新たな追記を止める。書込み・seek・sync等が失敗しても、診断記録のためにゲーム起動を失敗にはしない。log保存前にはFPGA入力ファイルをcloseし、programming用のcritical sectionを必ず抜ける。設定保存用の/crtファイルとは独立している。起動時のlog書込みが加わるため、通常版の採否は実機結果を踏まえて判断する。

## 根拠と留保

[Gowin UG704E](https://cdn.gowinsemi.com.cn/UG704E.pdf)のstatus定義では、GW5AST-138のbit13はDone Finalである。[openFPGALoaderのGowin実装](https://github.com/trabucayre/openFPGALoader/blob/master/src/gowin.cpp)も、SRAMデータ送信の終了をidleへ移し、CONFIG_DISABLE/NOOP後にstatusを確認している。今回のidle手順とstatus確認を照合する参照にした。製品別の全sequenceを同実装へ置換したものではない。

制御clockの余裕不足、終了時のidle、読取り順序のどれが今回の実機症状へ影響したかは未確定である。新しい診断値と実機再試験で切り分ける。500 kHzや待ち時間を全基板で検証済みとはしない。

## PCでの検証

実際の制御clock・IR/DR移動・終了確認・poll関数を、独立した16状態TAPとfalling-edge TDOのmodelに接続する。low/setup/high/hold、idle経由、命令と読取り順、正常DONE、0／全1／CRC等error／DONEなし／異なるID、最大3回、timerが進まない場合を含むpoll上限を確認する。これは電気的な測定ではない。

実際のlog関数についても、追記、既存内容維持、64 KiB上限、open/seek/write/短いwrite/syncの失敗を模擬する。実際のmain.cpp adapterで段階の記録位置を確認する。前回の高速writer・file/interrupt/GPIO cleanupの試験も維持する。CRT保存・OSD・日本語一覧・folder・scroll・改行を含む関連8本を実行し、記録はverification/crt-stage5-jtag2へ保存する。buildの成否は同folderの記録を参照する。

NESは実機合格4bと同じimageを再利用する。今回のFPGA buildや新しいtiming結果はない。microSDのNES/CSV/ROMは書き換えず、firmwareだけを更新する。通常起動で診断logが追加される点はSDの想定変更として扱う。

## 実機再試験

まずDr. Marioと別のNESゲームの起動だけを確認する。成功後に推奨値表示と保存試験へ進む。停止した場合は画面の全文と、通常のROM load表示へ進んだかを記録し、電源断後にmicroSDのcrt-boot.logをPCで読む。最後の段階とstatus/IDの組合せから次の調査箇所を決める。修正前の不合格版をrollbackの実機合格基準にしない。

## 追加修正版の実機反映

2026-11-03T21:48:42.915172+09:00、既知Console138Kへfirmwareを反映した。基板SHAと4 MiB全flashの読戻しが一致し、0x40000未満と0x80000以降を直前の検証済みsnapshotと照合した。microSD全58filesを新たに退避し、NES/CSV/ROMを含む全fileが同一であることを確認した。SDファイルは書き換えていない。通常起動後には診断logの追記を想定する。

全flashの初回読取りはmode0の接続確立に失敗し、再programせずmode2の読取りで成功した。SDK設定は元のbyteへ復元済み。直前の復旧snapshotは最初の起動修正版であり、実機合格版ではない。最後の合格4bと元の2列CSVは別に保持する。

導入記録はverification/crt-stage5-jtag2/deployment.json。今回の起動回復と保存成功はまだ確認していない。まず2本のNESゲームの起動だけを再試験する。
