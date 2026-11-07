# 小型OSD2：START後の全解放待ち修正

2026年11月7日。小型表示の実機報告と、最終SD照合で見つかった保存更新を分けて扱う。

## 観測と原因の未確定

SNESは通常動作、小型表示1〜8、補助表示1〜9とA〜Cを正常と報告された。NESも通常表示1〜8・補助表示1〜9を正常と報告された。一方、最終SDの読取り退避では、SNES .aがReset generation 7・値0、.bがUSER generation 6・値1となっていた。導入前は.aがUSER generation 3・値27、.bがReset generation 4・値0だった。他の63fileと全属性は不変。

実recordは退避して保持し、書戻しや削除は行っていない。利用者へSAVE回数・その時の値・START保持中の追加入力を確認中。今回の保存更新が利用者の明示SAVEか入力経路に起因するかは、操作履歴なしに断定しない。旧版を「無変更SAVE後もSD不変」とする合格tagは付けない。

後続の利用者回答で、保存更新は実際に利用者が行ったものでsoftwareに起因しないと確認された。この差分を意図したSAVEによる正常な更新へ訂正し、現物のReset .a generation 7とUSER .b generation 6を次の退避基準として保持する。無変更SAVEの実機不変は今回の試験条件では判定しない。以下のSTART入力経路は独立してhostで再現した改善点であり、今回の保存差分の原因とは扱わない。

## 独立して再現した入力経路

旧版はSTART初回押下と同時に存在する複合入力を遮断していたが、STARTを保持した後に追加したA/B・方向は通常のSAVE・編集へ到達した。SAVEを選び、未保存変更がある状態でSTART→STARTを保持したままAという入力を与えると、意図した全解放前に保存callbackが呼ばれた。実入力loopのhost再現試験は修正前に失敗した。

修正はSTARTが処理された時点で常に全解放待ちへ入ること。START単独でも後から追加されたbuttonを全解放まで遮断する。補助情報のpoll・ACK・描画更新は待機中も続く。全解放後の新しいA/B操作は通常どおり受け付ける。

## PC確認と成果物

firmware commitは`a1b6755a271e8dfc29f388e85bb3aef772862f18`。再現試験が修正後に合格し、解放後の意図したSAVE、USER/Reset双方の同値SAVE省略も実入力loopで確認した。関連host試験15組が合格した。通常16×10・補助24×17のgeometry、短縮名、font、保存engine、CRT効果は変更していない。

firmwareは230,960byte、SHA256 `943f883476aa57d49367c0b19992553c42ee36e68b36938d5f80f626cf1ec622`。production 99fileとcommit/build入力の一致、実ELFのSDH wrapper接続、保持するNES/SNES/monitorのsourceも照合した。証拠は`verification/osd2-compact-start-release-20261107/`。

修正版はPC検証までで、実機へはまだ導入していない。実機は旧小型版`8bf3c70`のまま。操作履歴の回答を待ち、保存更新の解釈と修正版の最小実機確認を整理する。現在の有効な実recordは保持し、旧generationへ戻して差分を消さない。

利用者回答後は、現在の有効な保存値を保全したままfirmwareだけを更新し、SNES 1回・NES 1回の起動中にSTART保持後の追加入力遮断と、全解放後の通常操作を確認する。変更値の保存は試験に含めず、最後に新しい退避と全file・属性の不変を照合する。
