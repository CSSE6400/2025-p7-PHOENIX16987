from flask import Blueprint, jsonify, request 
from todo.models import db 
from todo.models.todo import Todo 
from datetime import datetime, timedelta
from celery.result import AsyncResult
from todo.tasks import ical


# 创建API蓝图，设置URL前缀为/api/v1
api = Blueprint('api', __name__, url_prefix='/api/v1') 


@api.route('/health') 
def health():
    """返回服务器运行状态，如果服务器正在运行则返回'ok'"""
    return jsonify({"status": "ok"})


@api.route('/todos', methods=['GET'])
def get_todos():
    """获取待办事项列表，支持按完成状态和时间窗口筛选"""
    # 获取URL查询参数
    completed = request.args.get('completed')  # 完成状态筛选
    window = request.args.get('window')        # 时间窗口筛选（天数）

    # 查询所有待办事项，按创建时间降序排列
    todos = Todo.query.order_by(Todo.created_at.desc()).all()
    result = []
    
    for todo in todos:
        # 按完成状态筛选
        if completed is not None:
            if str(todo.completed).lower() != completed:
                continue

        # 按截止日期时间窗口筛选
        if window is not None:
            date_limit = datetime.utcnow() + timedelta(days=int(window))
            if todo.deadline_at > date_limit:
                continue

        # 将符合条件的待办事项添加到结果列表
        result.append(todo.to_dict())
    
    return jsonify(result)


@api.route('/todos/<int:todo_id>', methods=['GET'])
def get_todo(todo_id):
    """根据ID获取特定待办事项的详细信息"""
    # 查询指定ID的待办事项
    todo = Todo.query.get(todo_id) 
    
    # 如果未找到，返回404错误
    if todo is None: 
        return jsonify({'error': 'Todo not found'}), 404 
    
    # 返回待办事项详情
    return jsonify(todo.to_dict())


@api.route('/todos', methods=['POST'])
def create_todo():
    """创建新的待办事项并返回创建的项目"""
    # 验证请求字段是否合法，不允许有额外字段
    if not set(request.json.keys()).issubset(set(('title', 'description', 'completed', 'deadline_at'))):
        return jsonify({'error': 'extra fields'}), 400

    # 标题字段是必需的
    if "title" not in request.json:
        return jsonify({'error': 'missing title'}), 400

    # 创建新的待办事项
    todo = Todo( 
        title=request.json.get('title'), 
        description=request.json.get('description'), 
        completed=request.json.get('completed', False), 
    ) 
    
    # 如果提供了截止日期，转换为datetime对象
    if 'deadline_at' in request.json: 
        todo.deadline_at = datetime.fromisoformat(request.json.get('deadline_at')) 

    # 将新记录添加到数据库 
    db.session.add(todo) 
    # 提交更改到数据库
    db.session.commit() 
    
    # 返回创建的待办事项，状态码201表示创建成功
    return jsonify(todo.to_dict()), 201


@api.route('/todos/<int:todo_id>', methods=['PUT'])
def update_todo(todo_id):
    """更新指定的待办事项并返回更新后的项目"""
    # 验证请求字段是否合法，不允许有额外字段
    if not set(request.json.keys()).issubset(set(('title', 'description', 'completed', 'deadline_at'))):
        return jsonify({'error': 'extra fields'}), 400

    # 查询指定ID的待办事项
    todo = Todo.query.get(todo_id) 
    
    # 如果未找到，返回404错误
    if todo is None: 
        return jsonify({'error': 'Todo not found'}), 404 
    
    # 更新待办事项字段，使用请求中的值或保留原值
    todo.title = request.json.get('title', todo.title) 
    todo.description = request.json.get('description', todo.description) 
    todo.completed = request.json.get('completed', todo.completed) 
    todo.deadline_at = request.json.get('deadline_at', todo.deadline_at) 
    
    # 提交更改到数据库
    db.session.commit() 
    
    # 返回更新后的待办事项
    return jsonify(todo.to_dict())


@api.route('/todos/<int:todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    """删除指定的待办事项并返回删除的项目"""
    # 查询指定ID的待办事项
    todo = Todo.query.get(todo_id) 
    
    # 如果未找到，返回空对象和200状态码（幂等性）
    if todo is None: 
        return jsonify({}), 200 

    # 从数据库中删除待办事项
    db.session.delete(todo) 
    db.session.commit() 
    
    # 返回删除的待办事项
    return jsonify(todo.to_dict()), 200


@api.route('/todos/ical', methods=['POST'])
def create_ical():
    """创建iCal日历文件的异步任务并返回任务ID"""
    # 获取所有待办事项，按创建时间降序排列
    todos = Todo.query.order_by(Todo.created_at.desc()).all()
    todo_input = []
    
    # 将待办事项转换为字典列表
    for todo in todos:
        todo_input.append(todo.to_dict())
    
    # 创建异步任务生成iCal文件
    task = ical.create_ical.delay(todo_input)
    
    # 构建结果对象，包含任务ID和状态URL
    result = {
        'task_id': task.id,
        'task_url': f'{request.host_url}api/v1/todos/ical/{task.id}/status'
    }
    
    # 返回结果，状态码202表示请求已接受但处理尚未完成
    return jsonify(result), 202


@api.route('/todos/ical/<task_id>/status', methods=['GET'])
def get_task(task_id):
    """获取指定任务ID的iCal生成状态"""
    # 获取异步任务结果
    task_result = AsyncResult(task_id)
    
    # 构建结果对象，包含任务ID、状态和结果URL
    result = {
        "task_id": task_id,
        "task_status": task_result.status,
        "result_url": f'{request.host_url}api/v1/todos/ical/{task_id}/result'
    }
    
    # 返回任务状态
    return jsonify(result), 200


@api.route('/todos/ical/<task_id>/result', methods=['GET'])
def get_calendar(task_id):
    """获取指定任务ID的iCal文件内容"""
    # 获取异步任务结果
    task_result = AsyncResult(task_id)
    
    # 如果任务成功完成，返回iCal内容
    if task_result.status == 'SUCCESS':
        return task_result.result, 200, {'Content-Type': 'text/calendar'}
    else:
        # 如果任务未完成，返回404错误
        return jsonify({'error': 'Task not finished'}), 404

 
