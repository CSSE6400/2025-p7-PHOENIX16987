terraform {
 required_providers {
   aws = {
     source = "hashicorp/aws"   # 指定使用AWS提供商
     version = "~> 5.0"         # 使用5.x版本的AWS提供商
   }
 }
}

provider "aws" {
 region = "us-east-1"                          # 在美国东部1区域创建资源
 shared_credentials_files = ["./credentials"]  # 使用本地凭证文件进行身份验证
}

# 创建AWS SQS队列资源
# AWS SQS(Simple Queue Service)是一种完全托管的消息队列服务
# SQS队列允许应用程序之间的解耦通信，通过发送、存储和接收消息
# 主要用途:
# - 分布式系统组件之间的异步通信
# - 处理峰值负载而不丢失数据
# - 确保消息至少被处理一次
# - 作为微服务架构中的通信中介
resource "aws_sqs_queue" "ical_queue" {
 name = "ical"   # 队列名称为"ical"
}