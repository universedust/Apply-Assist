import traceback  # 用于捕获和处理异常堆栈信息

from flask import Flask, request, jsonify, send_from_directory, Response, stream_with_context  # 导入Flask相关模块和函数
from flask_cors import CORS  # 导入CORS工具，用于处理跨域请求
from openai import OpenAI  # 导入OpenAI客户端库
import os  # 导入操作系统接口模块
from dotenv import load_dotenv  # 导入环境变量加载工具
import json  # 导入JSON处理模块
import time  # 导入时间处理模块
import pdfplumber  # 导入PDF文件解析库
import docx2txt  # 导入Word文件解析库
import io  # 导入IO流处理模块

from werkzeug.utils import secure_filename  # 导入安全文件名处理函数
from datetime import datetime  # 导入日期时间模块

# 加载环境变量
load_dotenv()

# 初始化Flask应用
app = Flask(__name__)
CORS(app)  # 启用CORS跨域支持

# 配置应用，设置上传文件大小限制为20MB，上传目录为'uploads'
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = 'uploads'

# 初始化OpenAI客户端，使用环境变量中的API密钥和自定义API端点
client = OpenAI(
    api_key=os.getenv("ARK_API_KEY"),
    base_url="https://ark.cn-beijing.volces.com/api/v3/bots"
)

# 定义选校系统提示词，用于构造发送给AI模型的请求内容
SCHOOL_PROMPT = """作为顶级留学顾问，请按以下规则处理用户信息：
1. 核心背景分析：
   - 院校档次：{school_tier}
   - 学业成绩：
     * 输入类型：{score_type}（GPA/百分制）
     * 原始输入：{original_score}
   - 所学专业：{major}
   - 语言成绩：{language_score}
   - 目标地区：{region}
   - 预算：{budget}万/年

2. 推荐逻辑：
   (1) 优先匹配专业排名前20的院校,一定不要包含中国大陆学校
   (2) 结合用户背景突出3个专业相关优势
   (3) 标注要求专业背景（例如：用户申请CS则标注AI/算法课程资源）

3. 输出要求：
   | 学校排名 | 项目名称 | 专业匹配度 | 优势分析 | 官网链接 |
   注意：学校排名用QS2025；项目名称要加上校名；官网链接只需要学校官网，不用精确到项目，并放在项目名称的超链接中；专业匹配度用五星等级表示；文案最后不需要让用户继续问你，
   所以不要说”如果有其他问题请问我“这样的话；建议部分只需要给选校建议，不需要别的方面的"""

# 定义选校系统API路由，处理POST请求
@app.route('/api/school-selection', methods=['POST'])
def school_selection():
    try:
        data = request.json  # 获取请求中的JSON数据
        score_type = data.get('score_type', 'gpa')  # 获取成绩类型，默认为GPA
        original_score = data.get('original_score')  # 获取原始成绩值

        # 调用OpenAI接口，发送构造好的提示词和用户请求
        response = client.chat.completions.create(
            model="bot-20250303140321-b8ms2",
            messages=[
                {"role": "system", "content": SCHOOL_PROMPT.format(**data)},  # 格式化提示词内容
                {"role": "user", "content": "请根据我的背景推荐院校"}
            ],
            temperature=0.3  # 设置结果随机性，值越低结果越确定
        )
        # 返回AI模型的响应内容，封装为JSON格式
        return jsonify({"result": response.choices[0].message.content})
    except Exception as e:
        # 捕获异常，返回错误信息
        return jsonify({"error": str(e)}), 300

# 定义文书优化系统提示词
DOC_OPTIMIZE_PROMPT = """作为职业发展顾问，请根据以下信息生成结构化简历优化建议：
1. 教育背景分析：
   - 院校专业：{education}

2. 职业经历评估：
   - 工作经历：{experience}
   - 项目经验：{projects}

3. 技能匹配度：
   - 技能证书：{skills}

输出要求：
1. 按【教育背景优化】【职业经历优化】【技能提升建议】分章节
2. 每章节包含3-5条具体建议
3. 使用Markdown表格对比原始内容与优化方案
4. 最后提供完整优化示例"""

# 定义文书优化API路由，处理POST请求
@app.route('/api/document-optimize', methods=['POST'])
def document_optimize():
    try:
        form_data = request.json  # 获取请求中的表单数据
        attachments = json.loads(form_data.get('attachments', '[]'))  # 获取附件数据

        # 构建附件内容提示信息
        attachment_prompt = ""
        for att in attachments:
            attachment_prompt += f"### {att['filename']}\n{att['content'][:1000]}...\n"

        # 格式化提示词，构造发送给AI模型的内容
        full_prompt = DOC_OPTIMIZE_PROMPT.format(**form_data) + f"\n\n附件内容：\n{attachment_prompt}"

        # 调用OpenAI接口
        response = client.chat.completions.create(
            model="bot-20250303140321-b8ms2",
            messages=[
                {"role": "system", "content": full_prompt},
                {"role": "user", "content": "请结合我的材料生成优化建议"}
            ],
            temperature=0.3
        )
        # 返回AI模型的优化建议内容
        return jsonify({"content": response.choices[0].message.content})
    except Exception as e:
        # 记录错误日志，返回错误响应
        app.logger.error(f"优化失败: {traceback.format_exc()}")
        return jsonify({"error": "服务暂时不可用"}), 500

# 定义DeepSeek智能建议接口路由，处理POST请求
@app.route('/api/ask-deepseek', methods=['POST'])
def ask_deepseek():
    try:
        data = request.get_json()  # 获取请求中的JSON数据
        question = data.get('question', '')  # 获取用户问题
        timeline_data = data.get('timeline', [])  # 获取时间线数据

        # 构造发送给AI模型的提示词内容
        prompt = f"""## 留学申请时间线分析
**当前时间线：**
{json.dumps(timeline_data, indent=2, ensure_ascii=False)}

**用户问题：** {question}

请用Markdown格式给出专业建议，要求：
1. 分阶段说明优化方案
2. 使用有序列表排列建议
3. 关键时间节点用**加粗**标出
4. 包含具体实施步骤"""

        # 初始化OpenAI客户端
        client = OpenAI(
            api_key=os.getenv("ARK_API_KEY"),
            base_url="https://ark.cn-beijing.volces.com/api/v3/bots"
        )

        # 调用AI模型获取建议
        response = client.chat.completions.create(
            model="bot-20250303140321-b8ms2",
            messages=[
                {"role": "system", "content": "你是资深留学申请规划专家"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )

        # 返回AI模型的建议内容
        return jsonify({
            "answer": response.choices[0].message.content.strip()
        })
    except Exception as e:
        # 记录错误日志，返回错误响应
        app.logger.error(f"DeepSeek请求失败: {traceback.format_exc()}")
        return jsonify({
            "error": f"服务暂时不可用: {str(e)}"
        }), 500

# 配置允许的文件扩展名和上传文件夹路径
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'doc', 'docx', 'txt'}
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')

# 定义检查文件扩展名的函数
def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# 定义文件上传API路由，处理POST请求
@app.route('/api/upload', methods=['POST'])
def upload_file():
    # 检查请求中是否包含文件
    if 'file' not in request.files:
        return jsonify({"error": "未选择文件"}), 400

    file = request.files['file']  # 获取上传的文件
    # 检查文件名是否为空
    if file.filename == '':
        return jsonify({"error": "无效文件"}), 400

    # 检查文件扩展名是否允许
    if not allowed_file(file.filename):
        return jsonify({"error": "不支持的文件格式"}), 400

    try:
        # 安全保存文件，避免文件名中的特殊字符
        filename = secure_filename(file.filename)
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)  # 确保上传目录存在
        file.save(save_path)  # 保存文件

        # 根据文件类型解析文件内容
        content = ""
        if filename.lower().endswith('.pdf'):
            with pdfplumber.open(save_path) as pdf:
                content = '\n'.join([p.extract_text() for p in pdf.pages])
        elif filename.lower().endswith(('.docx', '.doc')):
            content = docx2txt.process(save_path)
        elif filename.lower().endswith('.txt'):
            with open(save_path, 'r', encoding='utf-8') as f:
                content = f.read()

        # 返回文件的访问URL、内容和文件名
        return jsonify({
            "url": f"/uploads/{filename}",
            "content": content,
            "filename": filename
        })
    except Exception as e:
        # 记录错误日志，返回错误响应
        app.logger.error(f"文件处理失败: {str(e)}")
        return jsonify({"error": "文件处理失败"}), 500

# 定义文件下载API路由
@app.route('/uploads/<filename>')
def download_file(filename):
    # 发送文件给客户端，允许用户下载
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# 应用入口，启动Flask服务
if __name__ == '__main__':
    app.run(port=5000, debug=True)  # 在5000端口启动服务，开启调试模式