# 第5a段階：CSV読込みだけを分離した起動確認

## 基準と目的

第4b段階へ復旧後、利用者が日本語NES一覧とドクター・マリオの起動・映像・音声・操作の正常を確認した。第5段階の初版と2つの修正版は不合格として保持し、そのまま再投入しない。

第4bと初版第5段階を独立した場所でsourceから再buildした。SDKのboard.cに残っていた表示用日時を元の値（Nov 1 2026 23:29:46）へSOURCE_DATE_EPOCHでそろえると、両者とも実際の導入binaryと全byteで一致した。新規buildとincremental buildの日時の差で16bytesの差が生じていたが、元の不具合の原因と断定しない。記録はverification/crt-stage5a-csv/baseline-reproduction.json。基板はこの比較で変更していない。

第5a段階は、実機合格FW4708296を基に、titles.csvの3列目crt_v1を読み取る部分だけを加えた切り分け版である。初版第5段階から保存処理等を一括して戻す方式を止め、まず一覧の読込みと起動を確認する。

## 含む変更

- 従来のname/titleの2列に加え、version付き3列目crt_v1を受け付ける。値は空欄またはenable:blur:scanline、各範囲は0/1、0〜3、0〜3。
- 名前・日本語表示名・順序・folderの対応を保ったまま、推奨値を一覧の並行vectorに保持する。範囲外・形式不正・folderへの値設定はCSV errorとして扱い、部分的な更新を避ける。
- 共通settings型をheaderへ移す。OSD2の識別表示だけをCRT CSV CHECK - STAGE5Aへ変更する。

推奨値は読んで保持するだけで、映像の要求値へ接続していない。Dr. Marioの試験値1:1:2がCSVにあっても、この版の新しいゲーム開始時はCRT ENABLE/H BLUR/SCANLINEがすべてOFFになる。OSD2の変更値は同じゲームの間だけ保持する従来の第4b動作である。

## 維持する経路

JTAGのprogrammer.cpp/.h、main.cppのprogram→ID→ROM load、全coreのloader、入力・OSD排他・解放待ち、SDK/FatFs設定は第4bとsourceが同一である。ui16_crt_storeは含まれず、ROMのCRC識別、defaults読込み、ゲーム別保存、Reset、SDへの起動log追記も行わない。FPGA/NES imageは合格第4bと同一で、新たなFPGA build/timing結果はない。

過去の診断版sourceはFW branch crt-osd2-stage1のc166944、初版はe8c617fとして保持する。今回のFWはcrt-stage5a-csv-20261103で4bから分岐する。親branchはcrt-osd2-stage1を継続し、新しいgitlinkを記録する。いずれもtangcore-integratedの統合基準を引き継ぐ。GitHubへpushしない。

## PC検証と限界

CRT/OSD/起動/日本語titles/folder/scroll/改行の7本が成功した。2列互換、3列の値・順序、不正値、既存の起動adapterと入力も確認した。変更しない経路はGitの第4b sourceと照合し、試験対象のsource commitとblobをresult.jsonへ保存する。firmware buildは成功し、custom領域内に収まる。

第5段階の停止原因はまだ特定していない。同じsourceのJTAGでもbinary配置が変わるため、この版の起動は実機で確認する必要がある。PC上の試験成功を実機成功として扱わない。

## 実機試験

firmwareを更新し、退避済みの3列試験CSVを再配置する。表示名と一覧順序は元と同一で、Dr. Marioの行だけに1:1:2が入る。元の2列CSVと現行SDの内容を新たに保全する。NES/monitor/ROM/fontは変更しない。既存crt-boot.logは保全し、この版では追記しない。

通常起動で日本語一覧と順序を確認し、Dr. Marioと別のNESゲームの起動・映像・音声・操作を確認する。OSD2の識別表示と3項目OFF/FRAME ACKを確認する。この結果が正常なら、次にROM識別・推奨値解決・設定適用・保存を段階ごとに追加する。いずれかの起動に失敗した場合は追加を止め、再び4bとの小さい差分を調べる。

## 第5a版の実機反映

2026-11-03T22:22:16.587859+09:00、既知Console138Kへfirmwareと3列試験CSVを反映した。基板SHA、新firmware全byte、4MiB全flash、更新範囲外を照合した。SD全59filesを新たに退避し、CSV以外の58files（NES/monitor/ROM/font/既存crt-boot.logを含む）は同一である。初回mode0 READの接続確立に失敗し、再programせずmode2 READで成功した。SDK設定は元のbyteへ復帰した。

復旧用には直前の復旧時に検証した第4b全flashと元2列CSVを保持している。新たな書込み前flash読取を行ったとは記録しない。導入照合はverification/crt-stage5a-csv/deployment.json。日本語一覧と2本のNESゲームの起動、OSD2識別表示・初期3項目OFF・FRAME ACKは利用者の確認待ちである。第5段階全体の完了にはしない。

## 第5a版の実機結果

利用者が「1-3正常」と回答し、日本語NES一覧とCSV順序、Dr. Marioの起動・映像・音声・操作、OSD2識別表示、初期3項目OFF、FRAME ACK、OSD1から一覧へ戻って別のNESゲームを起動する操作が正常と確認した。記録はverification/crt-stage5a-csv/hardware-results.json。第5aのlocal tagはcrt-stage5a-hw-20261103。CSV読込みだけの実機合格であり、第5段階全体は未完了。
