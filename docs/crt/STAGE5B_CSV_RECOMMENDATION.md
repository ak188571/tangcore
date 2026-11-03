# 第5b段階：CSV推奨値の起動時適用

## 範囲と基準

第5aの日本語一覧・順序、2本のNESゲーム起動、OSD2識別表示、初期3項目OFF、FRAME ACKは利用者が正常と確認した。基準はcrt-stage5a-hw-20261103、FW40fe027である。以前の第5段階とJTAG修正版は不合格の履歴として保持し、原因特定済みとはしない。

今回は既に一覧読込み時に解析したtitles.csvの推奨値を、選択ROMの起動成功後にCRT設定へ渡す部分だけを追加した。ゲーム別保存、ROM識別CRC、defaultsファイル、Reset、起動logへの書込みは含まれない。JTAG・FPGA・ROM loader・入力処理を変更しない。mainの既存new_session呼出箇所に推奨値を引数として渡す。

## 値の受渡し

1. A/Bでゲームを確定した時点で、元のfilename・relative pathと同じ選択位置の推奨値をUi16LaunchRequestへ値としてコピーする。CSV順序変更・folder内のゲームでも対応を保つ。
2. titles_errorがある場合、並行vectorの数が名前の数と違う場合、CSV推奨値が空欄の場合は推奨値なしとする。選択後の別行を参照したり、起動のためにCSVを再読込みしたりしない。
3. 従来のprogram→core ID→能力確認→ROM loadを完了し、Ui16LaunchError::Noneの場合だけ、CRT対応coreへ新しいsessionの初期値を送る。呼出し位置と入力解放待ちの順序は第5aと同じである。
4. 有効な推奨値があればその3項目を使用し、なければbuiltinの全OFFを使用する。公開APIへ範囲外の値が渡った場合も全OFFへ戻す。
5. CRT予約bit以外のcore_configを維持し、既存の設定転送・frame境界反映・ACK/retryを利用する。新sessionでは前sessionのACKをclearする。

## OSD2とsession

識別表示はCRT PRESET - STAGE5B。SESSION ONLY / NO SAVEを維持し、INITIAL: CSVまたはINITIAL: DEFAULTを表示する。INITIALは起動時の値の由来であり、その後の手動変更の保存状態を示すものではない。

CSVが明示的な0:0:0なら全OFFでもINITIAL: CSV、空欄・欠損等のbuiltin初期値ならINITIAL: DEFAULTである。DEFAULTはdefaultsファイルを読んだという意味ではない。この段階では同ファイルを扱わない。

OSD2を閉じて同じゲームで開き直すと、手動変更をそのまま保持する。ゲームを改めて起動すると、CSV推奨値または全OFFから開始する。推奨値はmenu作成時に再適用しない。電源再投入で手動変更を復元する機能はまだない。

## PC検証

CRT/OSD/launch/titles/folders/scroll/wrapの7本が成功した。実際のCSV parserとbrowserで順序変更・folder・空欄・明示OFF・不正な一覧の扱いを確認した。実際のmain.cppから成功後の引渡し部分を抽出してcompileし、失敗・非対応coreへの非適用、有効推奨値と推奨値なしの引渡しを確認した。実際のCRT関数で3項目の適用、他bitの維持、前のACKのclear、同ゲーム中の変更保持、新ゲームのOFF復帰と再適用を確認した。

関連sourceのcommit/blobと試験/build結果はverification/crt-stage5b-recommendedへ保存する。firmwareはcustom領域内。NESは実機合格第4b/第5aと同じimageであり、新しいFPGA build/timing結果はない。実機確認前に成功と扱わない。

## 実機試験

既存の3列試験CSVを変更せずfirmwareだけ更新する。SD全体を新たに退避し、基準第5aの検証済み全flashを復旧用に保持する。試験CSVのDr. Marioだけに1:1:2があり、表示名・順序は元と同じである。この値は動作確認用で、画質の推奨を正式決定したものではない。

最初に通常起動と日本語一覧、Dr. Marioの起動・映像・音声・操作を確認する。OSD2はCRT ENABLE=ON、H BLUR=WEAK、SCANLINE=STANDARD、INITIAL: CSV、APPLY: FRAME ACKを期待する。別NESでは3項目OFF、INITIAL: DEFAULT、FRAME ACKを期待する。

続いて同ゲームの変更→Close→開き直しで保持されること、一覧へ戻ってDr. Marioを再起動するとCSV値へ戻ることを確認する。保存試験とReset試験はこの段階の対象ではない。第5段階全体の完了tagはまだ作らない。

## 第5b版の実機反映

2026-11-03T22:48:43.487035+09:00、既知Console138Kへfirmwareだけを反映した。基板SHA、新firmware全byte、4MiB全flash、更新範囲外を照合した。SD全59filesを新たに退避し、CSV/ROM/NES/monitor/font/既存起動logを含む全fileが同一と確認した。初回mode0 READの接続確立に失敗し、再programせずmode2 READで成功した。SDK設定は元のbyteへ復帰した。

復旧用には直前の実機合格第5aの検証済み全flashと現在のCSVを保持する。今回新たな書込み前flash読取を行ったとは記録しない。導入照合はverification/crt-stage5b-recommended/deployment.json。通常起動・CSV推奨値適用・別ゲームの全OFF・同ゲーム中の変更保持と再起動時の推奨値復帰は実機確認待ちである。第5段階全体の完了にはしない。
