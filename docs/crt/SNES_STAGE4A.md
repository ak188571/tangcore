# SNES S4a：SD上の設定の読取り専用復元

2026年11月6日。S3bの実機報告を基準に、共有firmware `cffb1fa34995e9e511e77e432ff979bfa6b43c6d`でSNESのCSV/defaults・raw ROM ID・保存recordの読取りを接続した。作業branchは`tangcore-integrated`。FPGAは確認済みS3b `8cf6353`のimageを維持し、NES/monitorのRTLは変更しない。SNESのSAVE/Resetは無効のまま。

## 所有と失敗経路の調査結果

実buildが使うSDKのFatFs portとSDH driverを確認した。FatFsはFF_FS_REENTRANT=0、FF_FS_LOCK=0。従来のjoypad用mutexはstorageの排他ではない。UART type4はfloppy有効判定より前にfbufへ書き、type4/5にcore別guardもなかった。

新しいapplicationのstorage leaseで、UI16のfile/core確認、FPGA program、ROM ID→record→defaults→ROM loader、既存NESの明示SAVEと、UARTのfloppy I/Oを直列化する。PC/XTを退役させてからprogram用のleaseを待つため、途中のfloppy I/Oを追い越して共有bufferを再利用しない。UARTはPC/XT実行中かつ正しいpacket長の場合だけdisk要求を受理し、lease取得後にも所有を再判定する。

部分的なfloppy write packetはCPU専用の512byte静的bufferに受け、共有fbufへのcopyはpacket完成後・所有確認後・lease中に行う。DMAには従来の64byte整列・noncacheableなfbuf/FILを用いる。新しいFILや大bufferをstackへ置かない。拒否した既知長payloadは読み捨て、内部の0xAAを別commandへ読み替えない。

これはSNES/CRTとprogram/loadの所有境界の整備であり、既存PC/XTの全menu操作や全USB storage経路のthread安全を保証する変更ではない。USB HIDのcontroller入力とUSB storageは区別する。

## SDのDMA失敗時

使用中SDKのSDH_ReadMultiBlocksは正常時には転送完了を待つ一方、timeout時にcontroller resetをせず戻る経路がある。FatFs portのwriteにはtimeoutを無条件に再試行するloopもある。

SDKの保管fileは変更せず、applicationのlink wrapperを置いた。SNESのSD読取りscopeでI/Oが失敗した場合だけ、転送interruptをmaskし、SDKのSW_RST_ALL完了待ちを含むSDH_Resetを呼んでからhard errorを返す。以後のSD read/writeは電源再投入まで拒否し、同じbufferへ遅れたDMAが来る状態で次処理へ進まない。Reset自体が完了しなければ呼出しから戻らず、bufferを再利用しない。

元のSDKのcard初期化状態がcachedであるため、ここでの自動再初期化・timeout再試行は追加しない。SNES scope外で新しいfaultがない場合は元のSDKの戻り値を維持する。SD故障後のlatchは全SD I/Oに及び、回復には電源再投入を要する。USB storageのDMA abortはこの変更に含めず、SNESのUSB上のROMは従来のvolatile previewを継続する。

実ELFのMMC_disk_read/writeからwrapperへのcallを逆assemblyで照合した。hostの代替driverでreset完了前にbufferを再利用しない処理順とlatchを試験したが、物理SD故障の注入試験や電気的なDMA完了確認を実施したという意味ではない。

## 起動とOSD

SD上のSNESだけ、JTAG完了後にraw ROM全byteのCRC32/IEEEと64bit sizeを求め、system ID=2のrecord、同じvolumeのdefaults、既存ROM loaderを順に扱う。512byte copier headerもIDへ含め、header付き/なしは別IDになる。優先順位はUSER→CSV→SYSTEM→GLOBAL→builtin全OFF。各起動・program開始・失敗で前のID/restore/defaultsを消し、成功時だけsessionを作る。

SNES loaderはLoROM/HiROM/ExHiROMのheader判定を維持し、raw sizeとheader offset、headerのread結果、全payloadの読取り量、close結果を確認する。読取り不足・I/O失敗・close失敗ではcore_runningを立てず、load adapterもID/sessionを消す。ROM転送の64byte headerとpayload形式は維持する。

OSD見出しはSNES CRT READ ONLY、SAVE状態はREAD ONLY。INITIAL/STORE/ROM ID/DEFAULTSは実際に読んだ結果を表示する。操作できるのはenable・blur・scanlineとPOSだけで、SAVE/RESETは表示を残して選択不能。X/Yは起動時に解決した値へ戻る。NESは既存のSAVE/Resetを維持し、SNESのsave callbackは従来guardでも拒否する。

## PC検証と導入物

関連host試験15組が合格した。system=1/2のrecord復元・破損/競合/世代/未知schema/I/O拒否、SNESのraw/copier512 CRC、read-only UI、実main.cppの起動順/失敗clear、実UART decoderのcore切替・不正長・入力継続、実loaderのmapper/読取り不足/close失敗、SD fault処理順、既存NESのSAVE/defaults、日本語一覧/CSV順序を含む。

導入手順の代替媒体/flash試験33件も合格した。一時recordの既存file保護・payload破損拒否、同一SNES imageの再copy省略、SD退避破損時の停止、一時record変更時の復旧拒否、確認済み一時recordだけの除去を含む。実機へはまだ書き込んでいない。

firmwareは230,560byte、SHA256 `330730232ac021b8176e3a08fcd00f135919caea775ae4b1960d2129a537115b`。99のproduction fileがcommit/build入力と一致し、build中の変更はない。SNES FPGA imageはSHA256 `bcc879e4f6da1194b8fa43edb487f71ac13c8b6037086558a42b6fa80b0dc429`を保持する。新しいFPGA build/timingの結果とは扱わない。

実機はSNESを1回だけ起動し、PCで用意する一時的な32byteのUSER recordを読む。対象はスーパーマリオコレクション、ROM ID `232bb5b8`、size 2,097,152、値ON/STANDARD/WEAK、generation 1。これはfirmwareのSAVEで作ったrecordではない。既存titles.csv、defaults、NES recordは変更しない。CSV/defaults fallbackや破損拒否の組合せは今回PCで検証し、実機合格範囲へ広げない。

導入時は媒体・現在のS3b image・確認済みS3a firmwareの全flashを新しく照合し、全SD/flashを退避する。firmwareだけを更新し、一時recordを追加する。実機後のSD読取りでは、導入直後と全file/属性を比較してfirmwareが書かなかったことを確認する。その後、一時recordの内容が一致した場合にだけ除去できるようにする。S4aの実機は未確認。

## 実機への導入記録

同日、媒体情報とS3b imageを識別してSD63fileを新しく退避した。S3bの実機試験後も全fileの内容・属性は導入直後と一致し、defaults fileと対象のSNES recordは未存在だった。退避したraw ROMのCRC32 `232bb5b8`、size 2,097,152もfixtureと一致した。

全flashの独立した読取り2回は一致し、以前の確認済みfirmwareの全4MiBとも一致した。書込み直前の読取りでも新しい退避と一致した。同じ基板をBOOT付きで再接続した後、firmwareを0x40000へ1回だけ書き込み、resident modeの全flash読戻しでfirmware全byteの一致、0x40000未満・0x80000以降の不変を確認した。

SDは一時USER recordの32byteを追加した64fileになった。既存63fileの内容と属性は不変で、SNES FPGA image・CSV・defaults・NES recordへの書込みは行っていない。fixtureのschema/key/CRCとutility設定・生成fileの復元も照合した。詳細は`deployment.json`。S4aの実機動作と試験後のSD不変は確認待ち。

## SNESの実機報告

通常動作を「正常」、OSD2項目1〜13を「1-13正常」、X/Y保持・解放待ちと起動時値への取消しを「1-2正常」と利用者から報告された。依頼したスーパーマリオコレクション・USB P1の範囲で、raw ID `232bb5b8`、USERのON/STANDARD/WEAK復元、読取り専用表示、preview/ACK、取消しを合格とする。CSV/defaults fallback・破損record・他の映像mode/接続先へ合格を拡張しない。NES回帰と試験後のSD不変は別途確認待ち。

続くNES回帰もOSD2項目1〜13を「1-13正常」と報告された。依頼したドクターマリオのOSD2項目を合格とし、同じ依頼に含めたその他の操作は個別に述べられていないため合格へ追加しない。残る試験後のSD不変は、次のS4b用の新しい退避時に照合し、追加のSNES起動を避ける。
