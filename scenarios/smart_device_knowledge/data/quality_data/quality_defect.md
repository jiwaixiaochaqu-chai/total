+++
product_model = "SW-H8"
product_line = "smartwatch"
hardware_version = "V2.0"
firmware_version = "1.3.6"
app_version = "2.8.1"
mobile_os = "Android 14"
error_codes = ["E103"]
document_type = "known_issue"
effective_status = "active"
+++
# 智能健康设备测试与缺陷知识

## 历史缺陷

E103 曾在 App 2.8.1 与固件 1.3.6 的同步链路中出现。复现条件为创建 session 后等待超过 60 秒，再继续使用旧 session_id 读取数据。

## 复现记录

测试人员记录缺陷时必须包含产品型号、硬件版本、固件版本、App 版本、移动端系统、前置条件、复现步骤、实际结果和期望结果。

## 提交边界

知识库辅助查询历史问题和生成缺陷单草稿。是否提交到禅道或 Jira 需要测试人员人工确认，缺陷生命周期仍由原缺陷系统管理。
