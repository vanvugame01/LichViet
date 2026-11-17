# Lịch Việt

Ứng dụng xem lịch âm–dương và lưu nhắc việc theo ngày âm. Giao diện PC và Android dùng nền sáng, chữ slate và màu nhấn hổ phách theo mockup đã duyệt. Trong ô lịch chỉ hiển thị số ngày/tháng âm, không thêm tiền tố “âm”.

## PC

Yêu cầu Python 3.10 trở lên. Từ thư mục dự án trên Windows:

```powershell
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -r requirements.txt
./.venv/Scripts/python.exe -B main.py
```

Màn hình có lịch tháng, nút Hôm nay, chi tiết ngày, nhắc việc trong ngày và nút thêm/quản lý lịch. Dùng phím mũi tên để đổi ngày; Enter hoặc Space để chọn. Cửa sổ có thể thay đổi kích thước. Nút đóng ẩn ứng dụng xuống khay khi hệ thống hỗ trợ; dùng menu Thoát để kết thúc.

Nhắc việc được lưu trong `lunar_reminders.json`. Dữ liệu cũ mặc định là tháng thường. Thêm lịch có thể chọn tháng nhuận, nhắc một lần theo năm hoặc lặp hằng năm. Ngày 30 và tháng nhuận chỉ được nhắc trong năm có ngày đó. Khi lỗi lưu, giao diện giữ biểu mẫu và báo lỗi. Xóa có thể hoàn tác trong hộp thoại quản lý.

### Bản portable Windows x64

Bản chạy nằm tại `output/portable/LichViet.exe`; gói mang sang máy khác là `output/LichViet-Portable-Windows-x64.zip`. Giải nén rồi chạy EXE, không cần cài Python. Đặt trong thư mục có quyền ghi. Khi chuyển máy, chép cả thư mục để giữ dữ liệu.

Bản đóng gói lưu `lunar_reminders.json` cạnh EXE, độc lập với thư mục làm việc và thư mục giải nén tạm của PyInstaller. Lần build đầu sao chép lịch hiện có của dự án sang thư mục portable; các lần build sau giữ dữ liệu portable đã tồn tại. ZIP chứa chương trình, hướng dẫn và bản sao dữ liệu trong thư mục portable.

Build lại trên Windows:

```powershell
./.venv/Scripts/python.exe -m pip install -r requirements-build.txt
./.venv/Scripts/python.exe -B tools/build_portable.py
./.venv/Scripts/python.exe -B tools/verify_portable.py
```

Đã kiểm tra EXE riêng trong một thư mục tên tiếng Việt, khởi động từ thư mục làm việc khác: cửa sổ Lịch Việt 460×720 khởi tạo và kết thúc với mã 0. Bài kiểm tra không đưa Python, QSS hoặc dữ liệu thật vào thư mục thử. Báo cáo nằm tại `output/portable-verification.json`. Tổng 15 bài Python đạt, bao gồm xác định vị trí dữ liệu ở chế độ source/portable. Đóng gói dùng [cơ chế đường dẫn runtime của PyInstaller](https://pyinstaller.org/en/stable/runtime-information.html).

Ứng dụng kiểm tra lịch mỗi 30 giây và cần đang chạy để thông báo. Một lịch chỉ được nhắc một lần mỗi ngày. Tệp dữ liệu hỏng được giữ nguyên và chặn ghi tiếp; cần sao lưu rồi khôi phục JSON hợp lệ trước khi sử dụng tiếp.

## Android

Thư mục `android/` là dự án Compose Material 3, gồm hai màn hình Lịch và Nhắc việc. Lịch lưu bằng Room; migration phiên bản 1 sang 2 giữ dữ liệu cũ và bổ sung trường tháng nhuận. Không dùng dữ liệu mẫu khi chạy ứng dụng.

Mở `android/` trong Android Studio. Cần JDK 17, Android SDK Platform 35 và Build Tools tương thích. Gradle Wrapper 8.11.1 có kiểm tra SHA-256 bản phân phối. Sau khi SDK và giấy phép SDK đã được thiết lập:

```powershell
cd android
./gradlew.bat :app:assembleDebug :app:testDebugUnitTest
```

APK cài thử đã ký nằm tại `output/android/LichViet-Android-debug.apk`. Bản này có `applicationId=com.lichviet`, phiên bản 1.0.0, hỗ trợ từ Android API 26. Chưa nghiệm thu cài đặt hoặc thao tác trên điện thoại thật.

Máy phát triển đã có SDK/JDK cục bộ của dự án `ShareManHinhDT` tại `.tools/`; nhận định trước đó rằng máy thiếu SDK là do bỏ sót đường dẫn này. Đã dùng công cụ SDK hiện có để chuẩn bị SDK Platform 35 và Build Tools 35.0.0 riêng tại `.tools/android-sdk` của LichViet, không thay đổi mã hoặc khóa ký của ShareManHinhDT.

Build, chạy kiểm thử, kiểm tra lint và xuất APK kèm báo cáo bằng một lệnh từ thư mục gốc:

```powershell
./.venv/Scripts/python.exe -B tools/build_android.py
```

Script tự tìm JDK trong `.tools/jdk`, SDK trong `.tools/android-sdk`, hoặc nhận `--java-home` và `--sdk`. Báo cáo chữ ký, manifest, SHA-256 và kiểm thử nằm tại `output/android/verification.json`. APK dùng chữ ký Debug để cài thử. Không dùng khóa ký của dự án khác.

Android hiện hỗ trợ xem lịch, thêm, bật/tắt, xóa và hoàn tác nhắc việc. **Chưa có bộ lập lịch/thông báo nền Android.** Giao diện có thông báo giới hạn này. PC và Android lưu dữ liệu riêng, chưa đồng bộ.

Hai nền tảng dùng cùng quy tắc tính sóc và tiết khí UTC+7 cho âm lịch Việt Nam. Android đã bỏ giá trị ngày cố định trong mã cũ; PC đã thay bảng LunarCalendar để tránh sai khác múi giờ. Bộ kiểm thử có các mốc Tết, tháng nhuận, ngày biên 17/02/2007 và kiểm tra đổi khứ hồi.

## Kiểm tra và ảnh giao diện

Các kiểm tra PC dùng tệp tạm và không thay dữ liệu thật:

```powershell
./.venv/Scripts/python.exe -B -m unittest discover -s tests -v
./.venv/Scripts/python.exe -B tools/render_desktop.py
```

Ảnh dựng từ giao diện thật nằm trong `output/desktop/`, gồm lịch, cửa sổ nhỏ nhất, thêm lịch và quản lý. Đây là ảnh kiểm tra với dữ liệu mẫu riêng trong tệp tạm.

Kết quả kiểm tra lần triển khai này:

- 15 bài kiểm tra Python đạt: thao tác bàn phím, biểu mẫu, lưu lỗi, hoàn tác xóa, tiêu đề dài, chống nhắc trùng, bảo vệ JSON hỏng, đường dẫn portable và đổi âm lịch.
- 4 bài JUnit Kotlin đạt cả khi chạy riêng và qua Gradle; phép đổi ngày được kiểm tra hằng ngày trong giai đoạn 1900–2199.
- Đối chiếu độc lập hai bản Python/Kotlin trên 109.573 ngày: không có sai khác.
- Đã dựng và xem ảnh PC ở kích thước mặc định và nhỏ nhất, cùng hai hộp thoại.
- APK Debug đã build, kiểm tra chữ ký và manifest; Android lint không còn lỗi. Đã sửa cấu hình thanh điều hướng cho API 26/27 và bổ sung biểu tượng ứng dụng.
- Chưa chạy emulator/thiết bị Android hoặc kiểm tra thông báo/khay Windows trực tiếp.

JDK, SDK và cache Gradle nằm trong `.tools/`, không cài công cụ hệ thống. Build và kiểm thử tự động không thay thế việc nghiệm thu ứng dụng trên thiết bị Android thật.

Tham khảo cấu hình: [AGP 8.9](https://developer.android.com/build/releases/agp-8-9-0-release-notes), [Compose Compiler](https://developer.android.com/develop/ui/compose/setup-compose-dependencies-and-compiler), [Room](https://developer.android.com/jetpack/androidx/releases/room).
