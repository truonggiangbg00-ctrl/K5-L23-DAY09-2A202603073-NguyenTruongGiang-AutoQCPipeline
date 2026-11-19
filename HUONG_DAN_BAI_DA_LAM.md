# Hướng dẫn đọc và chạy bài đã hoàn thiện

Học viên: Nguyễn Trường Giang — 2A202603073.

## 1. Chạy trên Windows
Mở Terminal PowerShell tại thư mục repo. Môi trường `.venv` đã được tạo.

```powershell
$env:PYTHONUTF8 = "1"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pipeline.run
$LASTEXITCODE
.\.venv\Scripts\python.exe scripts/check_submission_windows.py
```

Khi clone sang máy khác: `python -m venv .venv`, rồi
`.\.venv\Scripts\python.exe -X utf8 -m pip install -r requirements.txt`.
Không cần GPU cho phần lõi. Phần train bổ sung chạy trên RTX 3050 4 GB, cùng batch 4 cho raw và clean.

## 2. Bốn module đã làm

### label_format: kiểm quy tắc
File `pipeline/checks/label_format.py` trả danh sách Issue, không sửa nhãn.
Duyệt file đã sắp thứ tự, đọc `(số dòng gốc, nội dung)` và parse 5 cột YOLO.
Sai định dạng, sai lớp, rộng/cao không dương thì báo lỗi rồi chuyển dòng tiếp theo.
Với box hợp lệ, tính bốn mép từ tâm và kích thước. Mức tràn là max của
0, -left, -top, right-1, bottom-1. So mức tràn với overflow_tol.
So IoU với các box cùng lớp trước đó; chỉ báo trùng ở dòng sau.
Box nhỏ tính bằng `min(w*W,h*H)`, box lớn dùng diện tích chuẩn hóa `w*h`.
Một dòng có thể vừa tràn vừa trùng; các kiểm tra hình học độc lập.
Dòng trống không làm lệch số dòng gốc. Bắt cả OverflowError khi ID lớp là inf.

### gate: kết luận bằng số liệu
File `pipeline/steps/gate.py` đếm ERROR trước; lỗi bắt buộc luôn gây Rework,
kể cả ảnh đã được người duyệt. WARN được gom bằng set tên ảnh để một ảnh
nhiều cảnh báo không bị đếm nhiều lần. Chỉ tính ảnh còn trong dataset và chưa duyệt.
Tỷ lệ = ảnh cảnh báo / tổng ảnh; chia cho 0 trả tỷ lệ 0 theo đặc tả đề.
So tỷ lệ chưa làm tròn với 10%; chỉ làm tròn khi xuất kết quả.

### autofix: sửa và ghi dấu vết
File `pipeline/steps/autofix.py` chỉ nhận ERROR để sửa bản sao mà pipeline truyền vào.
Loại ảnh trước, bỏ qua lỗi dòng của ảnh đã loại. Chuẩn hóa tên lớp nhưng giữ
các trường YAML khác. Thiếu nhãn chỉ ghi needs_label, tuyệt đối không tạo file rỗng.
Gom lỗi theo ảnh và số dòng GỐC; đọc mỗi file một lần, tạo danh sách dòng mới.
Nếu có mã yêu cầu xóa, xóa thắng cắt box và chỉ ghi một log.
Cắt box bằng giao hai góc với [0,1], đổi lại tâm/rộng/cao; nếu mất diện tích thì xóa.
Mỗi thay đổi ghi image, line, action, before, after. Quét lại rồi sửa lần hai
không làm gì thêm nếu đã sạch; needs_label có thể lặp khi chưa có nhãn.

### second_opinion: model chỉ cảnh báo
File `pipeline/checks/second_opinion.py` lấy dự đoán cache nếu không truyền preds.
Giữ số dòng gốc của nhãn hợp lệ. Nhóm dự đoán mạnh lọc conf >= 0.6 và diện tích >= 600 px².
Tìm nhãn giao với dự đoán ở IoU >= 0.3: không có là MISSING; có cùng lớp nhưng
IoU tốt nhất < 0.5 là LOOSE_BOX; không có cùng lớp và IoU khác lớp >= 0.5 là WRONG_CLASS.
Nếu cùng lớp đã phủ đủ, không báo WRONG_CLASS chỉ vì còn một nhãn khác lớp chồng lên.
Một dự đoán sinh tối đa một cảnh báo trong ba nhóm, theo đúng thứ tự cache.
Sau đó xét từng nhãn với nhóm dự đoán conf >= fp_conf (0.1), KHÔNG lọc diện tích:
không khớp ở IoU >= 0.3 thì FALSE_POS, kèm số dòng gốc. Mọi kết quả đều WARN.

## 3. Tại sao chọn ngưỡng này?

```powershell
.\.venv\Scripts\python.exe -X utf8 -m pipeline.calibrate --sweep "duplicates.phash_dist=2,4,6,8,10,12,14,16,20" --sweep "second_opinion.conf=0.1,0.25,0.4,0.5,0.6,0.7,0.8" --out submission/calibration
```

pHash 4 là ngưỡng nhỏ nhất cải thiện recall gần-trùng từ 3/6 lên 4/6, precision calib vẫn 1.
Ngưỡng 16 có recall calib cao hơn nhưng báo nhầm hai cảnh hoàn toàn khác nhau trên raw.
Chọn conf 0.6 giảm FP sai lớp và thiếu nhãn, giữ recall tương ứng 5/6 và 8/8;
đổi lại recall box lỏng chỉ còn 1/5. Xem đầy đủ bảng và hạn chế trong REPORT.md.
Không có ngưỡng nào ở đây được xem là bảo đảm dữ liệu hoàn toàn đúng.

## 4. Đọc kết quả theo thứ tự
1. `submission/reports/08_summary.json`: kết luận Hold, 38/205 ảnh (18,54%).
2. `07_error_list_v3.csv`: 0 ERROR, 71 WARN; gate không đếm WARN trên ảnh đã duyệt.
3. `02_error_list_v1.csv`: 208 bản ghi, gồm 19 intake và 189 QC.
4. `03_fixes.csv`: 35 mục hành động; 6 mục chuyển người không phải sửa nhãn.
5. `05_review_queue.csv`: 125 ảnh; `06_review_log.csv`: 80 ảnh đã duyệt mô phỏng.
6. `submission/export/clean_v1/manifest.json`: bản NHÁP 205 ảnh; export chứa nhãn,
   danh sách ảnh và checksum, không nhân đôi ảnh gốc.

## 5. Bằng chứng cửa chặn và ca khó

```powershell
.\.venv\Scripts\python.exe -X utf8 -m pipeline.run --budget 0 --work work/run_nb --reports submission/evidence/no_review --export-dir work/exp_nb
$LASTEXITCODE
Test-Path .\work\exp_nb\clean_v1\manifest.json
.\.venv\Scripts\python.exe -X utf8 submission/evidence/edge_cases.py
```

Kỳ vọng đã xác minh: Rework, mã 20, Test-Path False; ba ca bổ sung với 6 assert đạt.
Các test e2e của đề đã so kết quả hai lần chạy để kiểm tính lặp lại.

## 6. Ghi chú checker gốc trên Windows
`check_submission.py` so `str(relative_path)` với danh sách tên file POSIX.
Trên Windows, dấu phân cách khác nhau khiến file mẫu `pipeline/calibrate.py`
bị quét nhầm và báo hai lỗi đọc MANIFEST/data/calib. Không sửa file đề.
`check_submission_windows.py` đọc checker gốc, thay duy nhất biểu thức nhận diện
đường dẫn bằng `.as_posix()` trong bộ nhớ rồi chạy nguyên các kiểm tra còn lại.
Đọc mã launcher để đối chiếu; nó không bỏ kiểm hash, test, cấu hình hay báo cáo.

## 7. Trước khi nộp
Đọc `submission/REPORT.md` và tự giải thích được code; báo cáo ghi rõ có AI hỗ trợ.
Repo hiện có remote origin của lớp. Tạo repo public cá nhân tên
`K5-L23-DAY09-2A202603073-AutoQCPipeline`, trỏ remote về repo cá nhân rồi push.
Không đưa work/, .venv/, trọng số model hoặc token lên GitHub.
Phần train raw/clean đã được bổ sung theo yêu cầu học viên; CVAT/thưởng không thuộc phần bắt buộc.


## 8. Tái lập phần train GPU trên Windows
Môi trường đã dùng: Python 3.10.11, Ultralytics 8.4.214, PyTorch 2.11.0+cu128,
TorchVision 0.26.0+cu128. Danh sách đầy đủ ở `submission/evidence/environment.txt`.
Khi cài mới, cài requirements-train.txt rồi cài bản PyTorch CUDA chính thức:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m pip install -r requirements-train.txt
.\.venv\Scripts\python.exe -X utf8 -m pip install torch==2.11.0 torchvision==0.26.0 --index-url https://download.pytorch.org/whl/cu128
$env:PYTHONUTF8 = "1"
New-Item -ItemType Directory -Force work/models,work/ultralytics,work/matplotlib | Out-Null
$env:YOLO_CONFIG_DIR = (Join-Path $PWD "work/ultralytics")
$env:MPLCONFIGDIR = (Join-Path $PWD "work/matplotlib")
.\.venv\Scripts\python.exe scripts/normalize_export_manifest.py
.\.venv\Scripts\python.exe scripts/train_compare.py --variants raw clean --seeds 0 1 --epochs 20 --imgsz 640 --batch 4 --device 0 --model work/models/yolo26n.pt --skip-existing
.\.venv\Scripts\python.exe scripts/summarize_results.py
.\.venv\Scripts\python.exe scripts/check_submission_windows.py
```

`--skip-existing` chỉ dùng khi dữ liệu, cấu hình và siêu tham số không đổi;
nó bỏ qua lượt đã có JSON, không tự xác nhận JSON cũ có cùng cấu hình.
Bốn file `*_seed*.json` và `comparison.*` phải do script sinh, không sửa số bằng tay.
Trọng số ở `work/train/runs/<variant>_seed<seed>/weights/best.pt`, không commit vào Git.
Bảng `train_images` đếm ảnh đã copy: raw 224, clean 205. Loader thực tế sử dụng
raw 213 và clean 205; xem hai file `*_loader_audit.json` trong evidence.
Báo cáo cuối vẫn phải giữ Hold nếu gate chưa đạt, dù metric train có tăng.


### Checksum manifest trên Windows
`train_compare.py` hash byte thực của manifest, trong khi checker gốc hash sau khi
đổi CRLF thành LF. Vì vậy chạy `scripts/normalize_export_manifest.py` **trước train**:
helper chỉ chuẩn hóa xuống dòng, kiểm nội dung JSON không thay đổi, không sửa nhãn.
Hai lượt clean cuối đã được train lại sau chuẩn hóa để JSON kết quả do script gốc tự sinh.
`.gitattributes` giữ nguyên byte trong export/results/evidence để checksum không đổi
khi commit/clone. Checker gốc không bị sửa; launcher Windows vẫn chỉ sửa phép so đường dẫn.
