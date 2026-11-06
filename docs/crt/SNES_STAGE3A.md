# SNES S3a：水平ぼかし

2026年11月6日。基準は実機確認済みS1/S2、親tag `snes-crt-stage1-hw-20261106`、SNES `a142a29`、共有firmware `70d39d8`。作業branchは`tangcore-integrated`。NES/monitorのsourceは変更しない。

## 適用内容

SNESの拡大後ゲームRGB888へ水平3点FIRを接続する。BGR555の各5bitへ下位0を3bit付ける従来変換は維持する。基本kernel `[1,2,1]/4`のWEAKは1/4、STANDARDは1/2、STRONGは全量のblendで、各channelを整数の四捨五入で計算する。gamma変換は追加しない。左右端の不足した隣画素は中央画素で補い、別の行を混ぜない。演算moduleはNESの`crt_filter.sv`をbyte単位で再利用するが、SNES独自の統合試験と実機確認を行う。

SNESの現在のscalerは出力画素ごとにxcntへ256を加え、960で繰り上げる。blurの3出力画素の先読みに必要な加算は768なので、source列の繰上り条件は`xcnt>=192`、進むsource列は最大1。enableとblur強度が有効な場合にだけ、既存B-port addressのXをこの先読み値へ切り替える。OFFやblur=OFFの場合は、同時書込みも含めた元のaddressを厳密に使う。Y phaseやSNESのsource sampling条件は変更しない。

FIRはRGB履歴と結果の3clock分を補償する。OSD合成は処理後に行う。新しい行buffer/framebufferは追加しない。239行・high-resolution・interlace等の本来の表示対応はS3b前の別調査であり、この変更の完成範囲に含めない。

Console138K topだけでCRT_BLUR/SUPPORT_BLURを有効にし、能力文字列へCRTBLR1を追加する。CRTSCN1は通知しない。scanline要求bitはframe mailbox/返信で保持するが、pixel処理への入力では0へmaskし、走査線効果を有効化しない。

## OSDと共有firmware

SNESは引き続き全OFF基準のvolatile preview。見出しはSNES CRT PREVIEW、CRT ENABLEとH BLURだけを操作可能にする。SCANLINEはNOT YETで選択できない。SAVE/Reset/ROM ID/defaultsは未対応のまま。X/Yで閉じると全OFFへ戻すので、まだ閉じたまま調整値を保持する段階ではない。

NESのmenu・保存・Reset・推奨値解決は維持する。SNES専用のpreview制限によってNES側の選択行やSAVEが無効にならないことをhostで回帰試験する。JTAG、ROM loader、storage所有guard、controller/USB回路、OSD1のreset配線は変更しない。

## 検証方法と限界

- 7種の独立pattern、幅1〜32、3強度、各channelの整数丸め、両端clamp、resetをFIR単体で試験する。
- 公開SNES基準`32433c5`の実buffer/scalerを独立した参照とし、1,450万画素で強度・位置・OSD5位置・余白・音声・frame同期を比較する。blurの空間比較中だけ書込みを停止し、BRAM同時read/writeの曖昧さを除く。bypassはその前後の連続書込み中にも厳密一致を確認する。
- blurがOFFの場合、未実装のscanline要求bitを含んでも従来映像に一致することを確認する。S1 default parameterのbypass試験4,400万画素も回帰実行する。
- 2 Mbaud・実clock相当UARTでCRTBLR1とCRTSCN1非通知、全32設定値、frame適用、RX継続、poll中の文字/設定更新を試験する。
- 共有firmwareの12 host試験、NES/SNESのROM保持型再起動、SNESの12button解放待ちを回帰する。

FPGA/firmware buildと実機結果は`verification/snes-crt-stage3a-20261106`へ記録する。PCの画素比較やNESの過去の画質結果をSNES実機合格へ読み替えない。S3a実機合格後にS3bへ進む。

## PC build結果

SNES `ac7fe8f`、共有firmware `3560c1b`をcommitした。FPGAの合成・配置配線・bitstream生成が成功し、setup/hold違反は0/0。imageは5,016,064byte、SHA256 `081ed1df198c62ad68fa178e82cc13d774bd3ed7baaebe41d5f1072af2e77357`。S1からregister 82、LUT 229、ALU 110増加、BSRAM/乗算資源の増加は0。既存PLL/routing等のwarningは残る。

共有firmwareは229,168byte、SHA256 `c19bffa18855ffd38ea56ce5bc0f452463551bf6239bf05a5a0cdfcae3d42e5c`。関連試験16command、導入scriptの代替媒体/flash試験27件に合格した。build中の設計file不変、commitした入力180fileとの改行正規化後の一致、rootのDSP初期値2fileとS1基準の一致を確認した。

実機確認手順は`SNES_STAGE3A_TEST_GUIDE.md`、ODT版はlocal導入用directoryにある。導入時には現在のS1のSD/flashを新しく退避し、別段階の古い退避を今回の直前状態として扱わない。

## 実機導入記録

同日に導入した。SDの63fileを新しく退避し、独立した全flash読取り2回と書込み直前の読取りの一致を確認した。今回の退避は実機確認済みS1のfirmware/SNES imageと一致し、S1実機試験後のSD内容・属性の変更は0だった。

SDはSNES imageだけを更新し、他62fileと全file属性を維持した。firmwareは0x40000から1回だけ書き込み、全4MiBの読戻しでfirmware全byteの一致、0x40000未満および0x80000以降の不変を確認した。最初の読戻しはbootrom接続のhandshakeで失敗したため、再書込みせずresident modeの読取りで検証を完了した。utility設定と生成fileの復元も検証済み。詳細は`deployment.json`に記録した。

S3aのSNES実機確認では、通常起動を「正常」、OSD2表示順1〜13を「1-13正常」、取消し・再起動・一覧復帰を「1-3正常」と利用者から報告された。依頼したスーパーマリオコレクション・USB P1の範囲で水平ぼかし3強度、端処理、位置不変、OSD鮮明性、FRAME ACKを合格とする。他の接続先・映像modeへ拡張しない。

続くNES回帰はOSD2表示順1〜13を「1-13正常」と報告された。この返答では、それ以外に依頼した操作の結果は個別に述べられていないため合格範囲へ追加しない。利用者からSNES起動に時間がかかるため最小限にするよう要望された。以後は段階内の必要な確認を同じ起動中にまとめ、変更に関係しない再起動・別ゲーム起動の反復を避ける。
