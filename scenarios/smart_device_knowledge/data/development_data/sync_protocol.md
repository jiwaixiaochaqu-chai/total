+++
product_model = "SW-H8"
product_line = "smartwatch"
hardware_version = "V2.0"
firmware_version = "1.3.6"
app_version = "2.8.1"
mobile_os = "Android 14"
error_codes = ["E103"]
document_type = "protocol"
effective_status = "active"
+++
# 智能健康设备技术知识

## 同步会话

App 调用 openSyncSession 创建设备同步会话，服务端返回 session_id。session_id 有效期为 60 秒，超过有效期继续读取会返回 E103。

## 数据读取

readRecords 接口按分页返回步数、睡眠摘要和设备电量。客户端请求必须携带 product_model、firmware_version、app_version 和 mobile_os。

## 异常处理

E103 表示同步会话过期，客户端应重新创建 session 后再读取。连续三次出现 E103 时，需要同时保留蓝牙状态和设备端日志。
