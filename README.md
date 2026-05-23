```markdown
# Second Stage Repacker for Huawei Balong USB Loaders

**Version:** 23.5  
**Based on:** [satyamisme/balong-usbdload](balong-usbdload)  
**Original authors:** forth32, rust3028, 4pda community  
**License:** GNU GPLv3

---

## English

### Description

`SecondstageRepacker(23.5).bat` is a batch wrapper for the `usbloader-packer` tool from the [balong-usbdload](https://github.com/satyamisme/balong-usbdload) repository. It allows you to modify the **second stage (initramfs)** inside Huawei Balong USB loaders.

The second stage is the initial root filesystem that runs when the loader boots. By modifying it, you can:
- Add persistent backdoor scripts (like `doall.sh`)
- Modify startup behavior
- Inject custom binaries
- Bypass carrier restrictions

### Where to Get USB Loader Files

**DO NOT ask the repository maintainers for loader files.** They are clear about this.

USB loader files are often found in Huawei **technologic firmware** releases with **99** in the version number (e.g., `21.170.99.03.00`).

This repository already includes many loaders in the root directory:

| Loader File | Compatible Devices |
|-------------|--------------------|
| `usblsafe-b525.bin` | B525, B528 |
| `usblsafe-e5573cs-322.bin` | E5573Cs-322 |
| `usblsafe-e5785.bin` | E5785 |
| `usblsafe-e5885.bin` | E5885 |
| `usblsafe_b315.bin` | B315s |
| `usblsafe-3372h.bin` | E3372h |
| `usblsafe-3372s.bin` | E3372s |
| And many more... | See repository root |

Place the appropriate `.bin` file for your device in the same folder as the batch file.

### Requirements

- Python 3.x installed and added to PATH
- The following Python scripts from the repository in `bin/` folder:
  - `usbloader-packer.c` (compile to .exe or use .py version)
  - `extract_second.py` (custom script for second stage extraction)
  - `repack_inject.py` (custom script for repacking)
- Or simply use the pre-compiled `usbloader-packer.exe` from the `winbuild/` folder

### Directory Structure

***
YourFolder/
│
├── SecondstageRepacker(23.5).bat    # Main batch file
├── usblsafe-*.bin                    # Your USB loader file (from repo)
│
├── bin/                              # Tools (from repository)
│   ├── usbloader-packer.exe          # From winbuild/ or compiled
│   ├── extract_second.py             # Custom script
│   ├── repack_inject.py              # Custom script
│   ├── ptable-list.exe               # View partition table
│   ├── ptable-injector.exe           # Modify partition table
│   ├── loader-patch.exe              # Create safe loader
│   ├── balong-usbdload.exe           # Flash to device
│   └── patchblocked.sh               # Optional script to inject
│
├── work/                             # Working directory (auto-created)
└── output/                           # Patched loaders (auto-created)
***

### Quick Start

1. **Get the correct loader** for your device from the repository (e.g., `usblsafe-b525.bin`)
2. **Copy it** to the same folder as the batch file
3. **Run `SecondstageRepacker(23.5).bat`** as Administrator
4. **Select option 90** (Full workflow)
5. **Add/modify files** in the opened `work\second_out\` folder
6. **Press any key** when done
7. **Find your patched loader** in `output\` folder

### Menu Options

| Option | Description |
|--------|-------------|
| **1** | Load source (auto-detect .bin file in folder) |
| **2** | Load source (manual file selection) |
| **3** | Unpack USB loader (using usbloader-packer) |
| **40** | Extract second stage only |
| **41** | Open second stage folder for editing |
| **42** | Repack second stage (after manual edits) |
| **11** | Build final patched loader |
| **34** | Clean work folder |
| **36** | Exit |
| **80** | Show loader info (without unpacking) |
| **81** | Verify repack (compare original vs patched) |
| **82** | Create safe loader (disable flash erase) - uses `loader-patch` |
| **83** | Test all loaders in folder for compatibility |
| **90** | **FULL WORKFLOW** - Unpack → Extract → Open → Wait → Repack → Build |
| **91** | **FAST WORKFLOW** - Repack existing second stage → Build |
| **92** | **PATCH WORKFLOW** - Add patchblocked.sh → Repack → Build |
| **95** | Check files (verify all scripts exist) |
| **96** | Show flash instructions |
| **97** | View log |

### Flashing the Patched Loader

After building the patched loader, use `balong-usbdload` from the repository:

```bash
# For Balong V7R22 (B525, B535, E5785, E5885)
bin\balong-usbdload.exe -p COM3 -x3 output\your_loader_patched.bin

# For Balong V7R11 (E5573, E3372h, B310, B315s)
bin\balong-usbdload.exe -p COM2 -x2 output\your_loader_patched.bin

# For Balong V7R1 (E3272, E3276, E5372)
bin\balong-usbdload.exe -p COM1 -x1 output\your_loader_patched.bin

# For Balong V7R5 (B612, B618, B715)
bin\balong-usbdload.exe -p COM4 -x4 output\your_loader_patched.bin

# For Balong V7R65 (B625, B818)
bin\balong-usbdload.exe -p COM5 -x5 output\your_loader_patched.bin
```

### `-x` Flag Reference (Secuboot Bypass)

| Flag | Platform | Example Devices |
|------|----------|-----------------|
| `-x1` | V7R1 | E3272, E3276, E5372 (Hi6920) |
| `-x2` | V7R2 / V7R11 | E3372s, E5373, E5377, E5786, E3372h, E8372h, E5573, B310, B315s |
| `-x3` | V7R22 | E5785, E5885, B316, B525, B528, B535 |
| `-x4` | V7R5 | B612s, B618s, B715s (Hi6950) |
| `-x5` | V7R65 | B625, B818 (Hi6965) |
| `-x6` | 5000 | H112, H122, E6878 (Hi9500) |

### What is usblsafe.bin?

Original Huawei USB loaders **erase NAND flash** when loaded - this would remove IMEI, S/N, and radio calibration.

`usblsafe.bin` files are **patched "safe" loaders** that disable the flash erasure procedure. You can create them using:

```bash
bin\loader-patch.exe -o usblsafe.bin usbloader.bin
```

Or use option **82** in the batch file.

### Troubleshooting

| Problem | Solution |
|---------|----------|
| "python not recognized" | Install Python 3 and add to PATH |
| "ANDROID! not found" | File is not a valid Balong USB loader - get the correct one from repository |
| Repack fails | Ensure `work\second_out\.extract_meta` exists |
| Device not detected when flashing | Device must be in download mode (VID 12d1:PID 1443) |
| Loader not found for your device | Search for **technologic firmware** with **99** in version number |

### Status Indicators

The menu shows current status:

| Indicator | Meaning |
|-----------|---------|
| `[1] [OK] Source` | Loader file is loaded |
| `[2] [OK] Unpacked` | Loader has been unpacked |
| `[S] [OK] Second stage` | Second stage has been extracted |
| `[3] [OK] Repacked` | Second stage has been repacked |
| `[4] [OK] Final output` | Patched loader has been built |

### Credits

- **forth32** - Original balong_flash and balong-usbdload tools
- **rust3028** - Windows port and winbuild binaries
- **satyamisme** - Current maintainer of the [balong-usbdload repository])
- **4pda community** - Reverse engineering and testing
- **Various contributors** - Python repacking scripts

### Links

- **Main repository:** [https://github.com/satyamisme/balong-usbdload](https://github.com/satyamisme/balong-usbdload)
- **Includes:** All loader files, usbloader-packer, ptable tools, loader-patch

### Disclaimer

**USE AT YOUR OWN RISK.** Modifying your device's firmware can permanently brick it. The authors are not responsible for any damage.

---

## Русский

### Описание

`SecondstageRepacker(23.5).bat` - это пакетный wrapper для инструмента `usbloader-packer` из репозитория [balong-usbdload](balong-usbdload). Он позволяет модифицировать **second stage (initramfs)** внутри USB загрузчиков Huawei Balong.

Second stage - это корневая файловая система, которая запускается при загрузке. Модифицируя её, можно:
- Добавлять постоянные бэкдоры (например, `doall.sh`)
- Изменять поведение при загрузке
- Внедрять свои бинарные файлы
- Обходить ограничения оператора

### Где взять файлы загрузчиков?

**НЕ спрашивайте мейнтейнеров репозитория о файлах загрузчиков.** Они ясно дали понять, что такие вопросы не принимаются.

Файлы загрузчиков часто находятся в **технологических** прошивках Huawei с номером версии, содержащим **99** (например, `21.170.99.03.00`).

В корне репозитория уже есть много загрузчиков:

| Файл загрузчика | Совместимые устройства |
|-----------------|------------------------|
| `usblsafe-b525.bin` | B525, B528 |
| `usblsafe-e5573cs-322.bin` | E5573Cs-322 |
| `usblsafe-e5785.bin` | E5785 |
| `usblsafe-e5885.bin` | E5885 |
| `usblsafe_b315.bin` | B315s |
| `usblsafe-3372h.bin` | E3372h |
| `usblsafe-3372s.bin` | E3372s |
| И многие другие... | Смотрите в корне репозитория |

### Быстрый старт

1. **Скопируйте загрузчик** для вашего устройства из репозитория в папку с bat-файлом
2. **Запустите `SecondstageRepacker(23.5).bat`** от имени Администратора
3. **Выберите опцию 90** (Полный процесс)
4. **Отредактируйте файлы** в открывшейся папке `work\second_out\`
5. **Нажмите любую клавишу** после редактирования
6. **Патченый загрузчик** в папке `output\`

### Опции меню

| Опция | Описание |
|-------|----------|
| **1** | Загрузить источник (авто-определение .bin) |
| **2** | Загрузить источник (вручную) |
| **3** | Распаковать USB загрузчик |
| **40** | Извлечь second stage |
| **41** | Открыть папку second stage |
| **42** | Перепаковать second stage |
| **11** | Собрать финальный загрузчик |
| **34** | Очистить work папку |
| **36** | Выход |
| **80** | Показать информацию о загрузчике |
| **81** | Проверить перепаковку |
| **82** | Создать безопасный загрузчик |
| **83** | Тестировать все загрузчики |
| **90** | **ПОЛНЫЙ ПРОЦЕСС** |
| **91** | **БЫСТРЫЙ ПРОЦЕСС** |
| **92** | **ПАТЧ ПРОЦЕСС** |
| **95** | Проверить файлы |
| **96** | Инструкции по прошивке |
| **97** | Просмотреть лог |

### Прошивка патченого загрузчика

```bash
# Для Balong V7R22 (B525, B535, E5785, E5885)
bin\balong-usbdload.exe -p COM3 -x3 output\patched.bin

# Для Balong V7R11 (E5573, E3372h, B310, B315s)
bin\balong-usbdload.exe -p COM2 -x2 output\patched.bin

# Для Balong V7R1 (E3272, E3276, E5372)
bin\balong-usbdload.exe -p COM1 -x1 output\patched.bin
```

### Флаги `-x`

| Флаг | Платформа | Примеры устройств |
|------|-----------|-------------------|
| `-x1` | V7R1 | E3272, E3276, E5372 (Hi6920) |
| `-x2` | V7R2 / V7R11 | E3372s, E3372h, E5573, B310 |
| `-x3` | V7R22 | B525, B528, B535, E5785, E5885 |
| `-x4` | V7R5 | B612s, B618s, B715s |
| `-x5` | V7R65 | B625, B818 |
| `-x6` | 5000 | H112, H122, E6878 |

### Что такое usblsafe.bin?

Оригинальные загрузчики Huawei **стирают NAND flash** при загрузке - это удалит IMEI, S/N и калибровку.

`usblsafe.bin` - это **патченые "безопасные" загрузчики**, которые отключают стирание flash. Создать можно командой:

```bash
bin\loader-patch.exe -o usblsafe.bin usbloader.bin
```

Или используйте опцию **82** в bat-файле.

### Устранение проблем

| Проблема | Решение |
|----------|---------|
| "python not recognized" | Установите Python 3 и добавьте в PATH |
| "ANDROID! not found" | Файл не является загрузчиком Balong |
| Перепаковка не удалась | Проверьте `work\second_out\.extract_meta` |
| Устройство не обнаружено | Режим загрузки (VID 12d1:PID 1443) |

### Благодарности

- **forth32** - Оригинальные инструменты
- **rust3028** - Windows порт
- **satyamisme** - Текущий мейнтейнер [репозитория](balong-usbdload)
- **Сообщество 4pda** - Обратная разработка

### Ссылки

- **Репозиторий:** [balong-usbdload)

### Предупреждение

**ИСПОЛЬЗУЙТЕ НА СВОЙ СТРАХ И РИСК.** Авторы не несут ответственности.**

---

## Version History

| Version | Changes |
|---------|---------|
| 23.5 | Initial release based on balong-usbdload |

```
