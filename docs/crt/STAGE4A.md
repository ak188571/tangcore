# 4a 水平ぼかし

対象はConsole138K／NES。実機確認済みの `crt-osd2-stage1-hw-20261103` を基準に、水平ぼかしと、その操作に必要なOSD2・能力通知だけを追加する。走査線と保存は別段階とする。

## 演算と接続

既存の色変換・拡大後のRGB888に、左右対称の3-tap処理を適用する。OSDはその後に合成する。処理半径はHDMI出力の1画素であり、NES元画像の1画素ではない。拡大された輪郭に対する変化は比較的小さい。

各色成分の左・中央・右の値をL、C、Rとすると、演算は次のとおり。小数は最近整数へ丸め、ちょうど半分は切り上げる。

| H BLUR | 演算 | 基本の1:2:1処理との関係 |
| --- | --- | --- |
| OFF | C | 完全なbypass |
| WEAK | floor((L + 14C + R + 8) / 16) | 元画像へ1/4の割合で混合 |
| STANDARD | floor((L + 6C + R + 4) / 8) | 元画像へ1/2の割合で混合 |
| STRONG | floor((L + 2C + R + 2) / 4) | 基本処理そのもの |

中間和は12 bitで保持し、黒・白を含む8 bit全範囲で範囲超過を起こさない。gamma変換は追加しない。左右のゲーム表示端では端画素を複製し、余白や次の行の画素を混ぜない。

ぼかし有効時だけ既存frame bufferの読み出しを1 pixel clock先行させ、filter内で中央画素を1 clock保持して補う。scalerの状態遷移と最終RGB・OSD・HDMIの位置関係は維持する。追加する画素memoryはRGBの2画素分のregisterであり、新しいframe bufferや行bufferは設けない。

CRT ENABLEがOFF、またはH BLURがOFFのときは、先読みと演算をbypassして従来の読み出し時刻・RGB経路を使う。無効時にも先読みする案は、NESが同じmemoryを書き換える瞬間に元の映像との差を生むため採用しない。

有効時には各画素のmemory参照時刻が最大1 pixel clock早くなる。動作中のdual-clock frame bufferで書き込みと重なる場合の見え方は実機確認対象とする。OSD表示中もゲーム映像と音声は継続する。

## 設定とOSD2

設定は既存のbit割当を維持する。bit 16をCRT ENABLE、bit 18:17を水平ぼかし強度0〜3として使う。frame境界反映とFRAME ACKの経路は前段階のものを継続する。scanline用bitはこの段階では映像に影響しない。

NES coreは既存の `OSDWIN1;CRTSTG1` に `CRTBLR1` を追加して通知する。firmwareは3つの通知がそろった場合だけ、実際のぼかし用画面を表示する。旧bypass coreでは従来の要求値画面を維持し、ぼかし対応とは表示しない。能力情報はcore切替時に破棄する。

対応coreのOSD2には次を表示する。

- `H BLUR READY - STAGE4A`
- `SESSION ONLY / NO SAVE`
- `CRT ENABLE`、`H BLUR`
- `SCANLINE NOT YET`（選択・変更の対象外）
- `APPLY: WAITING` または `APPLY: FRAME ACK`
- `CLOSE`、`POS`

CRT ENABLEがONでも、H BLURがOFFならbypassとなる。新しいゲームを起動すると要求値はすべてOFFへ初期化し、同じゲームで開き直したときは値と位置を保持する。保存はまだ行わない。firmwareとNES imageは、同じ配布物内の組合せで使用する。

## 自動検証

- `nestang/tests/crt/test_blur.sh`：独立した整数式と29,568画素を比較。3強度、2種類のbypass、色成分ごとの丸め、単色、白黒、単一画素、交互画素、ramp、乱数、幅1〜32、両端とresetを確認。
- `nestang/tests/crt/test_config.sh`：異なるclock間の転送、frame境界の一括反映、連続変更の収束、reset、65,536組のbypassを確認。
- `nestang/tests/crt/test_integration.sh`：実UARTの要求・適用済み値の返信・能力通知を確認。変更前の固定commitの映像変換部と比較し、900万画素で従来の座標と各強度の演算を確認。そのうち5,287,496画素でbypassのRGBと出力時刻が一致。
- 有効時の空間演算比較ではframe bufferへの書き込みを一時的に止め、従来実装から取得した隣接画素を参照値に使う。bypassは書き込み継続中も比較する。この試験上の停止を製品コードへ追加してはいない。
- firmwareの `test_crt.sh`、`test_osd.sh`、`test_launch.sh`：新旧能力判定、実装済み項目だけの選択、FRAME ACK、既存の描画維持、入力制御、起動経路を確認。

Console138K向けfirmwareとNES imageのbuildが成功した。FPGAのsetup違反・hold違反はともに0件で、report掲載の最小pulse幅にも負の余裕はなかった。clockと制約は基準版から変更していない。既存のPLL VCO等の警告は残る。16 bitのframe buffer addressへ切り詰める幅の警告も出るが、従来と同じaddress bus幅であり、表示範囲内のaddressはframe bufferに収まる。警告と資源量の詳細はbuild記録へ保存する。

firmwareは220,912 byte、NES imageは4,627,550 byte。buildと試験の記録は `verification/crt-stage4a/` に保存する。実機での画質・音声・操作の確認は未実施。

## 実機試験

1. 今回のfirmwareとNES imageを導入し、通常起動、日本語メニュー、一覧順序、NESの映像・音声・操作を確認する。
2. SELECT＋左でOSD2を開き、今回の対応表示を確認する。
3. CRT ENABLEをONにし、H BLURをOFF／WEAK／STANDARD／STRONGと変える。実画面の輪郭が段階的に変化し、変更後にFRAME ACKとなることを確認する。
4. H BLURをSTRONGにしてCRT ENABLEをON／OFFと変え、OFF時の映像へ戻り、画像が左右に移動しないことを確認する。
5. ゲーム表示端へ余白や別の行の色が混ざらず、動く場面でも異常な筋やちらつきが増えないことを確認する。
6. OSD文字にぼかしが掛からず、項目・値変更時にOSDが消えないこと、5位置の表示、入力遮断・解放待ちを確認する。
7. 同じゲームでの値保持と、別のゲームでOFFへ初期化されることを確認する。

試験結果は実機で確認した範囲だけを追記し、次の走査線実装とcommitを分ける。
