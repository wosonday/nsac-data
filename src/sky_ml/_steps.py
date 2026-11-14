"""Hỗ trợ (ngoài luồng): nạp các bước pipeline đánh số.

Tên module bắt đầu bằng chữ số (`1_load_data`) không dùng được với câu lệnh `import` thông thường,
nên mọi nơi lấy các bước qua importlib tại đây. Thứ tự bên dưới chính là thứ tự chạy pipeline.
"""
import importlib

STEPS = {
    1: ("1_load_data", "load-data | check", "copy dữ liệu cần thiết từ NASA-cl → data/, kiểm SHA-256"),
    2: ("2_build_features", "build-features <task>", "dữ liệu → bảng đặc trưng theo configs/tasks.yaml"),
    3: ("3_train", "train <task>", "chia fold, huấn luyện, dự đoán OOF, lưu mô hình"),
    4: ("4_evaluate", "evaluate <task>", "metric theo người, CI95, so baseline, độ bao phủ"),
    5: ("5_predict", "predict <task>", "nạp mô hình đã lưu, dự báo cho dữ liệu mới + khoảng 90%"),
}


def step(number: int):
    return importlib.import_module(f"sky_ml.{STEPS[number][0]}")


load_data, build_features, train, evaluate, predict = (step(n) for n in range(1, 6))
