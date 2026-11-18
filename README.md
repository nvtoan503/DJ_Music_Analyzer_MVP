# DJ Music Analyzer — MVP desktop

App desktop chạy cục bộ trên Windows/macOS. Mã nguồn Python + PySide6.

## Chức năng
- Nhập 1 hoặc nhiều bài nhạc / quét cả thư mục (có thư mục con).
- Phân tích waveform (đường biên âm lượng), BPM và thời lượng.
- Gợi ý thể loại **Vinahouse**, **House Lắc**, **EDM** theo **quy tắc âm thanh**.
- Nghe thử bài, nhấn waveform/timeline để tua.
- Sửa nhãn thể loại và lọc thư viện.
- Sao chép bài nhạc ra các thư mục phân theo thể loại. **Không di chuyển hay xóa file gốc.**
- Tự lưu thư viện JSON trong thư mục dữ liệu ứng dụng của người dùng.

## Cài đặt và chạy

Yêu cầu: **Python 3.11 hoặc 3.12**, máy có Internet để cài thư viện lần đầu.

### Windows (PowerShell)
```powershell
cd DJ_Music_Analyzer_MVP
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```
Nếu chỉ có Python 3.11, thay `-3.12` bằng `-3.11`. Nếu PowerShell chặn Activate, dùng trực tiếp `.\.venv\Scripts\python.exe -m pip install -r requirements.txt` rồi `.\.venv\Scripts\python.exe main.py`.

### macOS (Terminal)
```bash
cd DJ_Music_Analyzer_MVP
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```
Nếu dùng `python3` và đã cài Python 3.11–3.12, có thể thay `python3.12` bằng `python3`.

## Đóng gói app (tùy chọn)
Tạo app *trên chính hệ điều hành cần xuất* (Windows để tạo .exe, macOS để tạo .app):
```bash
pip install pyinstaller
pyinstaller --noconfirm --clean --windowed --onedir --name DJMusicAnalyzer --collect-all librosa --collect-all soundfile main.py
```
Thư mục `dist/DJMusicAnalyzer` chứa bản chạy được. Bản này chưa ký mã/code signing, chưa notarize macOS, và chưa kiểm thử trên nhiều loại máy. Không thể cross-compile .exe trên Mac hoặc .app trên Windows bằng cách này.

## Giới hạn đã biết
- **Không phải AI nhận diện genre đã huấn luyện**: gợi ý thể loại là heuristic dựa trên BPM, bass, spectral centroid, onset và độ động. Ranh giới House Lắc/Vinahouse/EDM mang tính cộng đồng, nên **bắt buộc nghe kiểm tra**. Chưa có phần học từ nhãn DJ sửa.
- BPM có thể sai x2 hoặc /2 do half/double tempo; app lưu BPM gốc và BPM đã chuẩn hóa, nhưng không đảm bảo chính xác.
- Phân tích tối đa **180 giây đầu** mỗi bài để tăng tốc; thời lượng hiển thị là toàn bộ bài. Waveform là mẫu của đoạn phân tích, không phải toàn bộ bài nếu dài hơn 180 giây. Vị trí tua trên waveform vì vậy chỉ là minh họa cho bài dài; timeline tua theo toàn bài.
- Bộ codec phụ thuộc môi trường: MP3/WAV/FLAC thường hoạt động; M4A/AAC/AIFF/OGG có thể không đọc/phát trên một số hệ. Cài ffmpeg trên máy nếu định dạng không giải mã được; backend librosa vẫn có thể cần decoder tương thích.
- Chưa có key Camelot, sync Rekordbox, mô hình AI học nhãn, beat grid thủ công, hay kéo-thả.
- Phần mềm xử lý file của người dùng, không tải bài hát lên server.

## Thử nhanh
1. Chạy `python main.py`.
2. Nhấn **Thêm file nhạc** và chọn một file WAV/MP3 hợp lệ.
3. Đợi tiến trình phân tích kết thúc, chọn bài trong bảng.
4. Xem BPM, sóng nhạc, nhấn **Phát** và thử tua.
5. Chỉnh nhãn trong dropdown, lọc theo thể loại và thử **Xuất thư mục**.

## Kiến trúc
- `main.py`: UI Qt, phát audio với QtMultimedia, thư viện JSON, xuất file.
- `analyzer.py`: librosa phân tích nhịp/sóng và quy tắc gợi ý thể loại.
- `requirements.txt`: các thư viện Python.

**Không cung cấp nhạc có bản quyền trong project.**

## Script mở nhanh
- Windows có Python 3.12: chạy `run_windows.bat` (lần đầu tự cài thư viện).
- macOS có Python 3.11/3.12: chạy từ Terminal `bash run_mac.command` (lần đầu tự cài thư viện).

## Dành riêng cho Windows 11: tạo EXE

1. Cài **Python 3.12 bản 64-bit** từ python.org, bật tùy chọn thêm Python vào PATH nếu được hỏi. Máy cần có Internet để tải thư viện.
2. Giải nén toàn bộ ZIP, nhấp đúp **`build_windows_exe.bat`**.
3. Nếu quá trình thành công, mở **`dist/DJMusicAnalyzer/DJMusicAnalyzer.exe`**.
4. Giữ nguyên cả thư mục `dist/DJMusicAnalyzer` khi di chuyển sang máy khác; đây là bản **one-folder**, không phải một file EXE độc lập.

Script đóng gói chỉ có thể chạy **trên máy Windows**, không được kiểm thử trực tiếp trong môi trường tạo mã nguồn. Windows SmartScreen hoặc phần mềm bảo mật có thể cảnh báo với app chưa ký số. Không tắt bảo vệ hệ thống; chỉ mở file nếu bạn tin cậy mã nguồn và đã kiểm tra nội dung.

## Không muốn cài Python lên máy Windows 11?
Xem `HUONG_DAN_WIN11_KHONG_CAN_CAI_PYTHON.md` để dùng GitHub Actions đóng gói ứng dụng thành thư mục EXE portable trên máy chủ Windows của GitHub. File nguồn workflow: `.github/workflows/build-windows.yml`.
