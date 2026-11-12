# TangCore - FPGA Gaming Distribution for Sipeed Tang

<p align="right">
  <a title="Documentation" href="https://nand2mario.github.io/tangcore"><img src="https://img.shields.io/website.svg?label=nand2mario.github.io%2Ftangcore&longCache=true&style=flat-square&url=http%3A%2F%2Fnand2mario.github.io%2Ftangcore%2F&logo=GitHub"></a><!--
  -->
  <a title="Releases" href="https://github.com/nand2mario/tangcore/releases"><img src="https://img.shields.io/github/commits-since/nand2mario/tangcore/latest.svg?longCache=true&style=flat-square&logo=git&logoColor=fff"></a>
</p>

TangCore is a comprehensive FPGA gaming distribution that brings classic gaming systems to Sipeed Tang FPGA boards. It combines multiple high-quality gaming cores into a single package with an easy-to-use menu system.

Please [file an issue](https://github.com/nand2mario/tangcore/issues) if you run into any problems, like game compatibility and display glitches.

## 開発branch（ak188571版）

`tangcore-integrated`があるrepositoryでは、このbranchを今後の変更の基準にします。対象一覧とsubmoduleの扱いは[開発branchの方針](docs/DEVELOPMENT_BRANCHES.md)を参照してください。

## Console138K JTAG 20 MHzの実機確認

BL616の通常版で、FPGA bitstreamをSPI0＋DMAの20 MHz JTAGで送信します。従来のGPIO JTAGに比べ、ゲーム選択受理からROM転送開始まで約2.10秒、OSDからの一覧復帰まで約2.03秒短縮しました。[構成・時間比較・通常版の確認結果](docs/rom/JTAG20_20261112.md)

## Console138K SNES ROM転送の実機確認（SPI 32 MHz）

共通tag `spi32-continuous-hw-20261112`。DMA連続送信と150 MHzのFPGA受信回路を使用した通常版です。[構成・測定結果・build設定](docs/rom/SPI32_20261112.md)を参照してください。

## Console138K UART8 CPU重ね合わせの実機確認

共通tag `uart8-cpu-overlap-hw-20261108`。通常版は軽量計測・詳細計測ともOFFです。
[実装・比較・確認範囲](docs/rom/UART8_CPU_OVERLAP_20261108.md)、[通常版の配布ZIP](verification/uart8-cpu-overlap-20261108/verified-normal-pair.zip)を参照してください。

## Console138K UART8並行化の実機確認

共通tag `uart8-overlap-hw-20261108` で、通常版firmwareとSNES coreの対応する組を公開しています。
[実装・測定・確認範囲](docs/rom/UART8_OVERLAP_20261108.md)、[通常版の配布ZIP](verification/uart8-overlap-20261108/verified-normal-pair.zip)を参照してください。

## 🎮 Supported Systems

<div align="center">
  <img src="doc/tangcore-nes.png" width="300" />
  <img src="doc/tangcore-snes.png" width="300" />
  <img src="doc/tangcore-gba.png" width="300" />
  <img src="doc/tangcore-genesis.png" width="300" />
</div>

- **[NESTang](https://github.com/nand2mario/nestang/)** - Nintendo Entertainment System
  - Cycle-accurate NES emulation
  - Extensive mapper support
  - 720p HDMI output

- **[SNESTang](https://github.com/nand2mario/snestang/)** - Super Nintendo Entertainment System
  - Support for LoROM, HiROM and ExHiROM
  - DSP-1/2/3/4, S-RTC, OBC-1 extension chips

- **[GBATang](https://github.com/nand2mario/gbatang/)** - Game Boy Advance
  - High compatibility
  - Open source BIOS included
  - Full 32MB gamepak support

- **[MDTang](https://github.com/nand2mario/mdtang/)** - Sega Genesis/Mega Drive
  - Accurate Genesis/Mega Drive emulation

- **[SMSTang](https://github.com/nand2mario/smstang/)** - Sega Master System

- 🌟🌟 **Try the new [486Tang](https://github.com/nand2mario/486tang)**

## 💻 Supported Hardware

| Board Model | Status | Notes |
|------------|--------|-------|
| [Tang Console 60K](https://sipeed.com/tangconsole) | ✅ Recommended | Best overall experience |
| Tang Console 138K | ✅ Experimental | Supported since April 2025 |
| Tang Primer 25K | ✅ Experimental | NES/SNES only |

<img src="doc/tangcore-boards.jpg" width=450> 

## 🚀 Quick Start

For detailed setup instructions, please refer to our [Installation Guide](https://nand2mario.github.io/tangcore/user-guide/installation/). Here's a quick overview:

1. Download the latest [TangCore release](https://github.com/nand2mario/tangcore/releases)
2. Flash the firmware using Bouffalo Lab Dev Cube
3. Prepare a USB drive with FPGA cores and your game ROMs
4. Connect required peripherals (HDMI and controller)
5. Power on and enjoy!

## 🛠️ Documentation

TangCore uses a different architecture compared to individual cores (NESTang/SNESTang):
- Firmware runs on BL616 MCU instead of FPGA
- Fast core switching via JTAG
- USB storage support
- SOM-connector debugging interface

For detailed development information, see an introduction to [TangCore archtecture](https://nand2mario.github.io/tangcore/dev-guide/architecture/), [building from sources](https://nand2mario.github.io/tangcore/dev-guide/building/), how to [develop a new core](https://nand2mario.github.io/tangcore/dev-guide/core-development/), and [core debugging guide](https://nand2mario.github.io/tangcore/dev-guide/core-debugging/).

My blog post on TangCore,

* [MCU for Better FPGA Gaming on Tang Console](https://nand2mario.github.io/posts/2025/mcu_for_better_fpga_gaming/)

## 📝 License

TangCore firmware is licensed under Apache 2.0. Each core maintains its original license - please check individual core directories for details.

## 🙏 Acknowledgments

- MiSTer FPGA cores and their developers
- openFPGALoader by Gwenhael Goavec-Merou


## 📫 Contact

For updates and announcements, follow [@nand2mario](https://x.com/nand2mario) on X.

For support, please use the [GitHub Issues](https://github.com/nand2mario/tangcore/issues) page.  
