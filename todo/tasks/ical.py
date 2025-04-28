# 导入必要的模块
import os  # 用于读取环境变量
from celery import Celery  # 导入 Celery 任务队列库

# 创建 Celery 应用实例
# __name__ 作为应用的名称，确保每个模块有唯一标识
celery = Celery(__name__)

# 配置 Celery 代理 URL
# 从环境变量获取消息队列的连接地址，通常是 Redis 或 RabbitMQ 的地址
celery.conf.broker_url = os.environ.get("CELERY_BROKER_URL")

# 配置结果后端
# 存储任务执行结果的地方，也是从环境变量读取
celery.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND")

# 设置默认队列名称
# 如果环境变量未设置，默认使用 "ical" 作为队列名
celery.conf.task_default_queue = os.environ.get("CELERY_DEFAULT_QUEUE", "ical")

# 定义一个 Celery 任务
# name="ical" 指定任务的唯一标识符
@celery.task(name="ical")
def create_ical(tasks):
   # 创建iCalendar日历对象
   cal = icalendar.Calendar()
   cal.add("prodid", "-//Taskoverflow Calendar//mxm.dk//")
   cal.add("version", "2.0")
   
   # 模拟长时间处理
   time.sleep(50)
   
   # 为每个任务创建日历事件
   for task in tasks:
       event = icalendar.Event()
       event.add("uid", task["id"])
       event.add("summary", task["title"])
       event.add("description", task["description"])
       event.add("dtstart", datetime.datetime.strptime(task["deadline_at"], "%Y-%m-%dT%H:%M:%S"))
       cal.add_component(event)
   
   # 返回iCalendar格式的日历数据
   return cal.to_ical().decode("utf-8")