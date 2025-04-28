# 定义Terraform配置
terraform {
 # 指定所需的提供商
 required_providers {
   aws = {
     source = "hashicorp/aws"  # 使用AWS提供商
     version = "~> 5.0"        # 使用5.x版本的AWS提供商
   }
 }
}

# 配置AWS提供商
provider "aws" {
 region = "us-east-1"                          # 在us-east-1区域创建资源
 shared_credentials_files = ["./credentials"]  # 使用本地credentials文件中的AWS凭证
}

# 创建标准SQS队列
resource "aws_sqs_queue" "our_first_mailbox" {
 name = "csse6400_prac"  # 队列名称
}

# 创建FIFO SQS队列
resource "aws_sqs_queue" "our_first_fifo" {
 name = "csse6400_prac.fifo"     # 队列名称，必须以.fifo结尾
 fifo_queue = true               # 启用FIFO（先进先出）功能
 content_based_deduplication = true  # 启用基于内容的重复数据删除功能，防止重复消息
}

# 输出标准队列的ARN（Amazon资源名称）
output "mailbox" {
 value = aws_sqs_queue.our_first_mailbox.arn
}

# 输出FIFO队列的ARN
output "fifo" {
 value = aws_sqs_queue.our_first_fifo.arn
}