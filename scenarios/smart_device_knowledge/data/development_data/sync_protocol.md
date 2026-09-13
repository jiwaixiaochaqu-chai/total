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

# 演示同步协议说明

> 本资料为虚构脱敏样例，仅用于 RAG 场景演示。

技术知识主要给研发和测试使用，用于查询底层协议、接口字段、版本兼容和错误码含义。

## 会话流程

1. App 调用 `openSyncSession(device_id)` 创建同步会话。
2. 设备返回 `session_id`，有效期为 60 秒。
3. App 调用 `readRecords(session_id)` 读取步数和睡眠摘要。
4. 如果超过有效期继续读取，接口返回错误码 E103。

## 字段要求

每次排查同步问题时必须记录产品型号、硬件版本、固件版本、App 版本和移动端系统。
