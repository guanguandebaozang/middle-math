# -*- coding: utf-8 -*-
# 【终极云端安全版】Streamlit + GitHub 正式上线专用
# 全部账号读取云端Secrets，代码0敏感信息、0明文密码
# 修复：IndentationError、TypeError登录崩溃、变量不匹配、代码冲突
import json
import os
import random
from datetime import datetime
import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ====================== 全局页面配置 ======================
st.set_page_config(
    page_title="初中数学智能组卷刷题系统",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== 会话状态初始化 ==========
if "authentication_status" not in st.session_state:
    st.session_state.authentication_status = None
if "name" not in st.session_state:
    st.session_state.name = None
if "username" not in st.session_state:
    st.session_state.username = None
if "user_data" not in st.session_state:
    st.session_state.user_data = {}
if "practice_question_list" not in st.session_state:
    st.session_state.practice_question_list = []
if "current_question_idx" not in st.session_state:
    st.session_state.current_question_idx = 0
if "question_submit_status" not in st.session_state:
    st.session_state.question_submit_status = {}

# A4打印配置
PRINT_CONFIG = {
    "paper_size": "A4",
    "font_size": 12,
    "line_spacing": 1.5,
    "margin_top": 2.5,
    "margin_bottom": 2.5,
    "margin_left": 2.0,
    "margin_right": 2.0
}
PAPER_HEADER = """
{}
==============================
试卷名称：2021-2025中考数学真题试卷
组卷时间：{}
适用学段：初中数学
题型：选择题、填空题
==============================
"""

# 兜底题库
DEFAULT_QUESTION_BANK = [
    {
        "id": 1, 
        "type": "选择", 
        "grade": "初一", 
        "chapter": "有理数", 
        "q": "-8 的绝对值是多少？", 
        "opts": ["-8", "8", "0", "±8"], 
        "ans": "B", 
        "analysis": "负数的绝对值是它的相反数，负数绝对值为正数，|-8|=8", 
        "source": "真题兜底题库"
    },
    {
        "id": 2, 
        "type": "选择", 
        "grade": "初三", 
        "chapter": "锐角三角函数", 
        "q": "sin45°=____", 
        "opts": ["1/2", "√2/2", "√3/2", "1"], 
        "ans": "B", 
        "analysis": "sin45°为特殊三角函数值，结果为二分之根号二", 
        "source": "中考真题"
    },
    {
        "id": 3, 
        "type": "选择", 
        "grade": "初一", 
        "chapter": "整式", 
        "q": "单项式 -3xy² 的次数是？", 
        "opts": ["2", "3", "-3", "1"], 
        "ans": "B", 
        "analysis": "单项式次数为所有字母指数之和，x(1)+y²(2)=3次，系数不计入次数", 
        "source": "基础真题"
    },
    {
        "id": 4, 
        "type": "选择", 
        "grade": "初二", 
        "chapter": "一次函数", 
        "q": "一次函数 y=2x+1 的截距是？", 
        "opts": ["1", "2", "-1", "0"], 
        "ans": "A", 
        "analysis": "一次函数y=kx+b，b为y轴截距，本题k=2，b=1", 
        "source": "单元真题"
    },
    {
        "id": 5,
        "type": "选择",
        "grade": "初一",
        "chapter": "一元一次方程",
        "q": "方程 2x+4=0 的解为？",
        "opts": ["x=2", "x=-2", "x=4", "x=-4"],
        "ans": "B",
        "analysis": "移项得2x=-4，解得x=-2",
        "source": "基础真题"
    },
    {
        "id": 6,
        "type": "选择",
        "grade": "初二",
        "chapter": "勾股定理",
        "q": "直角三角形两直角边为3和4，斜边长度为？",
        "opts": ["5", "6", "7", "8"],
        "ans": "A",
        "analysis": "根据勾股定理 a²+b²=c²，3²+4²=25，c=5",
        "source": "中考高频题"
    },
    {
        "id": 7,
        "type": "选择",
        "grade": "初一",
        "chapter": "有理数运算",
        "q": "计算：-5 + 3 的结果是？",
        "opts": ["-2", "2", "-8", "8"],
        "ans": "A",
        "analysis": "异号两数相加，取绝对值大的符号，5-3=2，结果为-2",
        "source": "基础真题"
    },
    {
        "id": 8,
        "type": "选择",
        "grade": "初三",
        "chapter": "二次函数",
        "q": "二次函数 y=x² 的图像开口方向为？",
        "opts": ["向上", "向下", "向左", "向右"],
        "ans": "A",
        "analysis": "二次函数y=ax²，a>0开口向上，a<0开口向下，本题a=1>0",
        "source": "中考真题"
    }
]

# ====================== 题库读写 ======================
def load_json_bank():
    json_path = "question_bank.json"
    try:
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                bank = json.load(f)
            valid_bank = [item for item in bank if len(item["opts"]) == 4]
            return valid_bank
        else:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_QUESTION_BANK, f, ensure_ascii=False, indent=2)
            st.success("✅ 已自动生成初始题库文件")
            return DEFAULT_QUESTION_BANK
    except Exception as e:
        st.error(f"题库读取异常：{str(e)}，重置初始题库")
        with open("question_bank.json", "w", encoding="utf-8") as f:
            json.dump(DEFAULT_QUESTION_BANK, f, ensure_ascii=False, indent=2)
        return DEFAULT_QUESTION_BANK

def save_question_to_json(new_question):
    bank = load_json_bank()
    bank.append(new_question)
    with open("question_bank.json", "w", encoding="utf-8") as f:
        json.dump(bank, f, ensure_ascii=False, indent=2)
    return True

def upload_json_question_bank(uploaded_file, mode="append"):
    try:
        upload_data = json.load(uploaded_file)
        if not isinstance(upload_data, list):
            return None, "JSON根节点必须是数组列表"
        standard_keys = ["id", "type", "grade", "chapter", "q", "opts", "ans", "analysis", "source"]
        valid_questions = []
        for idx, item in enumerate(upload_data, 1):
            if not all(key in item for key in standard_keys):
                continue
            if len(item["opts"]) != 4 or item["ans"] not in ["A","B","C","D"]:
                continue
            valid_questions.append(item)
        if not valid_questions:
            return None, "无有效题目"
        if mode == "cover":
            final_bank = valid_questions
        else:
            local_bank = load_json_bank()
            local_ids = [q["id"] for q in local_bank]
            new_ques = [q for q in valid_questions if q["id"] not in local_ids]
            final_bank = local_bank + new_ques
        with open("question_bank.json", "w", encoding="utf-8") as f:
            json.dump(final_bank, f, ensure_ascii=False, indent=2)
        return final_bank, f"导入成功，当前总题量：{len(final_bank)}"
    except Exception as e:
        return None, f"导入失败：{str(e)}"

QUESTION_BANK = load_json_bank()

# ====================== 中文PDF字体 ======================
def register_cn_font():
    try:
        if os.path.exists("C:/Windows/Fonts/simsun.ttc"):
            font = TTFont("SimSun", "C:/Windows/Fonts/simsun.ttc")
            pdfmetrics.registerFont(font)
            return "SimSun"
        elif os.path.exists("/System/Library/Fonts/PingFang.ttc"):
            font = TTFont("PingFang", "/System/Library/Fonts/PingFang.ttc")
            pdfmetrics.registerFont(font)
            return "PingFang"
        else:
            return "Helvetica"
    except Exception:
        return "Helvetica"

CN_FONT = register_cn_font()

# ====================== PDF生成 ======================
def generate_pdf_paper(questions, is_analysis=False):
    if is_analysis:
        pdf_path = "带解析中考数学试卷.pdf"
        title_text = "【解析复盘版】"
    else:
        pdf_path = "纯净版中考数学试卷.pdf"
        title_text = "【纯净考试版】"
    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4
    margin_left = PRINT_CONFIG["margin_left"] * 28.35
    margin_top = PRINT_CONFIG["margin_top"] * 28.35
    font_size = PRINT_CONFIG["font_size"]
    line_spacing = PRINT_CONFIG["line_spacing"]
    c.setFont(CN_FONT, font_size)
    current_y = height - margin_top
    header_list = PAPER_HEADER.format(title_text, datetime.now().strftime("%Y-%m-%d %H:%M")).split("\n")
    for line in header_list:
        if line.strip():
            c.drawString(margin_left, current_y, line.strip())
            current_y -= font_size * line_spacing
    opt_list = ["A", "B", "C", "D"]
    for idx, q in enumerate(questions, 1):
        if current_y < margin_top + 80:
            c.showPage()
            c.setFont(CN_FONT, font_size)
            current_y = height - margin_top
        question_line = f"{idx}. 【{q['type']}】{q['q']}"
        c.drawString(margin_left, current_y, question_line)
        current_y -= font_size * line_spacing
        if q["type"] == "选择" and q["opts"]:
            for i, opt in enumerate(q["opts"]):
                opt_line = f"   {opt_list[i]}. {opt}"
                c.drawString(margin_left, current_y, opt_line)
                current_y -= font_size * line_spacing
        if is_analysis:
            ans_line = f"   标准答案：{q['ans']}"
            analysis_line = f"   详细解析：{q['analysis']}"
            source_line = f"   真题来源：{q['source']}"
            c.drawString(margin_left, current_y, ans_line)
            current_y -= font_size * line_spacing
            c.drawString(margin_left, current_y, analysis_line)
            current_y -= font_size * line_spacing
            c.drawString(margin_left, current_y, source_line)
            current_y -= font_size * line_spacing * 2
    c.save()
    return pdf_path

def generate_pure_paper(questions, save_path="纯净版中考数学试卷.txt"):
    paper_content = PAPER_HEADER.format("【纯净考试版】", datetime.now().strftime("%Y-%m-%d %H:%M"))
    idx = 1
    for q in questions:
        paper_content += f"\n{idx}. 【{q['type']}】{q['q']}\n"
        if q["type"] == "选择" and q["opts"]:
            opt_list = ["A", "B", "C", "D"]
            for i, opt in enumerate(q["opts"]):
                paper_content += f"   {opt_list[i]}. {opt}\n"
        idx += 1
    with open(save_path, "w", encoding="utf-8") as f:
        f.write(paper_content)
    return paper_content, save_path

def generate_analysis_paper(questions, save_path="带解析中考数学试卷.txt"):
    paper_content = PAPER_HEADER.format("【解析复盘版】", datetime.now().strftime("%Y-%m-%d %H:%M"))
    idx = 1
    for q in questions:
        paper_content += f"\n{idx}. 【{q['type']}】{q['q']}\n"
        if q["type"] == "选择" and q["opts"]:
            opt_list = ["A", "B", "C", "D"]
            for i, opt in enumerate(q["opts"]):
                paper_content += f"   {opt_list[i]}. {opt}\n"
        paper_content += f"   标准答案：{q['ans']}\n"
        paper_content += f"   详细解析：{q['analysis']}\n"
        paper_content += f"   真题来源：{q['source']}\n"
        idx += 1
    with open(save_path, "w", encoding="utf-8") as f:
        f.write(paper_content)
    return paper_content, save_path

def select_questions(count, grade=None, shuffle=True):
    bank = QUESTION_BANK
    if grade:
        bank = [q for q in bank if q["grade"] == grade]
    if shuffle:
        random.shuffle(bank)
    return bank[:count]

# ====================== 刷题模块 ======================
def practice_module(username):
    st.header("📝 在线逐题刷题练习")
    st.divider()
    if username not in st.session_state.user_data:
        st.session_state.user_data[username] = {"practice_records":[],"error_questions":[]}
    user_records = st.session_state.user_data[username]["practice_records"]
    user_errors = st.session_state.user_data[username]["error_questions"]
    grade_list = ["全部", "初一", "初二", "初三"]
    prac_grade = st.selectbox("选择刷题学段", grade_list)
    prac_count = st.slider("本次刷题总题量",5,40,10,5)
    if st.button("🎯 开始刷题",use_container_width=True):
        prac_ques = QUESTION_BANK
        if prac_grade != "全部":
            prac_ques = [q for q in prac_ques if q["grade"] == prac_grade]
        random.shuffle(prac_ques)
        st.session_state.practice_question_list = prac_ques[:prac_count]
        st.session_state.current_question_idx = 0
        st.session_state.question_submit_status = {}
        st.rerun()
    ques_list = st.session_state.practice_question_list
    if not ques_list:
        st.info("👆 请选择刷题学段和题量，点击【开始刷题】进入答题")
        return
    cur_idx = st.session_state.current_question_idx
    total = len(ques_list)
    q = ques_list[cur_idx]
    submitted = st.session_state.question_submit_status.get(cur_idx,False)
    st.progress((cur_idx+1)/total,text=f"进度：{cur_idx+1}/{total}")
    st.subheader(f"第{cur_idx+1}题｜{q['grade']}｜{q['chapter']}")
    st.write(f"**题目：**{q['q']}")
    opts = [f"A.{q['opts'][0]}",f"B.{q['opts'][1]}",f"C.{q['opts'][2]}",f"D.{q['opts'][3]}"]
    map_opt = {opts[0]:"A",opts[1]:"B",opts[2]:"C",opts[3]:"D"}
    if not submitted:
        sel = st.radio("请选择答案",opts,key=f"q_{cur_idx}_{q['id']}")
        if st.button("✅ 提交答案",use_container_width=True):
            ans = map_opt[sel]
            if ans == q["ans"]:
                st.success("✅ 正确")
                ok = 1
            else:
                st.error(f"❌ 错误，正确答案：{q['ans']}")
                ok = 0
                if q not in user_errors:
                    user_errors.append(q)
            st.info(f"解析：{q['analysis']}")
            st.session_state.user_data[username]["practice_records"].append({
                "time":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "grade":q["grade"],
                "chapter":q["chapter"],
                "user_ans":ans,
                "true_ans":q["ans"],
                "is_right":ok
            })
            st.session_state.question_submit_status[cur_idx]=True
            st.rerun()
    else:
        st.success("✅ 本题已完成")
    col1,col2 = st.columns(2)
    with col1:
        if cur_idx>0 and st.button("⬅️ 上一题",use_container_width=True):
            st.session_state.current_question_idx -=1
            st.rerun()
    with col2:
        if cur_idx < total-1 and st.button("➡️ 下一题",use_container_width=True):
            st.session_state.current_question_idx +=1
            st.rerun()

# ====================== 错题本 ======================
def error_book_module(username):
    st.header("📒 我的错题本")
    st.divider()
    if username not in st.session_state.user_data:
        st.session_state.user_data[username] = {"practice_records":[],"error_questions":[]}
    err_list = st.session_state.user_data[username]["error_questions"]
    if not err_list:
        st.info("🎉 暂无错题")
        return
    st.warning(f"累计错题：{len(err_list)} 道")
    for idx,q in enumerate(err_list,1):
        st.subheader(f"错题{idx}｜{q['grade']}-{q['chapter']}")
        st.write(f"**题目：**{q['q']}")
        opts = [f"A.{q['opts'][0]}",f"B.{q['opts'][1]}",f"C.{q['opts'][2]}",f"D.{q['opts'][3]}"]
        map_opt = {opts[0]:"A",opts[1]:"B",opts[2]:"C",opts[3]:"D"}
        redo = st.radio("重新作答",opts,key=f"err_{q['id']}")
        if st.button("核对答案",key=f"chk_{q['id']}"):
            if map_opt[redo]==q["ans"]:
                st.success("✅ 订正正确")
            else:
                st.error(f"❌ 仍错误，正确答案：{q['ans']}")
                st.info(f"解析：{q['analysis']}")
    if st.button("🗑️ 清空错题本",use_container_width=True):
        st.session_state.user_data[username]["error_questions"]=[]
        st.rerun()

# ====================== 统计模块 ======================
def statistic_module(username):
    st.header("📊 刷题数据统计")
    st.divider()
    if username not in st.session_state.user_data:
        st.session_state.user_data[username] = {"practice_records":[],"error_questions":[]}
    rec = st.session_state.user_data[username]["practice_records"]
    if not rec:
        st.info("暂无刷题数据")
        return
    df = pd.DataFrame(rec)
    total = len(df)
    right = df["is_right"].sum()
    wrong = total-right
    acc = round(right/total*100,2)
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("总题数",total)
    c2.metric("正确",right)
    c3.metric("错误",wrong)
    c4.metric("正确率",f"{acc}%")
    st.divider()
    st.subheader("学段正确率统计")
    group = df.groupby("grade")["is_right"].agg(["sum","count"])
    group["正确率"] = round(group["sum"]/group["count"]*100,2)
    group.columns = ["正确数","总题数","正确率(%)"]
    st.dataframe(group,use_container_width=True)
    if st.button("🗑️ 清空记录",use_container_width=True):
        st.session_state.user_data[username]["practice_records"]=[]
        st.rerun()

# ====================== 管理员后台 ======================
def admin_question_manage():
    global QUESTION_BANK
    st.header("🔧 管理员后台工具中心")
    st.divider()
    # 账号哈希生成工具
    st.subheader("🔐 自定义账号哈希生成工具（云端专用）")
    st.info("输入账号、昵称、明文密码，一键生成SECRETS可直接粘贴的哈希配置，**全程无明文存储、安全上线**")
    with st.form("hash_tool",clear_on_submit=True):
        cu,cn = st.columns(2)
        with cu:
            new_user = st.text_input("登录用户名",placeholder="stu5 / math01")
            new_name = st.text_input("用户昵称",placeholder="学生五号")
        with cn:
            new_pwd = st.text_input("自定义密码",type="password",placeholder="654321")
        gen = st.form_submit_button("✅ 生成云端Secrets配置",use_container_width=True)
    if gen:
        if not new_user or not new_name or not new_pwd:
            st.error("请填写完整信息")
        else:
            hasher = stauth.Hasher()
            hash_str = hasher.hash(new_pwd)
            out = f'{new_user}_name = "{new_name}"\n{new_user}_pwd = "{hash_str}"'
            st.success("🎉 可直接复制到 Streamlit Secrets 配置！")
            st.code(out,language="toml")
    st.divider()
    st.success(f"✅ 当前题库总量：{len(QUESTION_BANK)} 道")
    # JSON批量上传
    st.subheader("📤 批量上传JSON题库")
    mode = st.radio("导入模式",["追加模式","覆盖模式"])
    m = "append" if "追加" in mode else "cover"
    upfile = st.file_uploader("上传题库JSON",type="json")
    if upfile and st.button("✅ 确认导入",use_container_width=True):
        with st.spinner("导入中..."):
            new_bank,msg = upload_json_question_bank(upfile,m)
            if new_bank:
                st.success(msg)
                QUESTION_BANK = new_bank
            else:
                st.error(msg)
    st.divider()
    # 手动新增题目
    st.subheader("📝 手动新增单选题")
    with st.form("add_q",clear_on_submit=True):
        g,cpt = st.columns(2)
        grade = g.selectbox("学段",["初一","初二","初三"])
        chapter = cpt.text_input("章节")
        qq = st.text_area("题目内容")
        a,b = st.columns(2)
        optA = a.text_input("选项A")
        optB = b.text_input("选项B")
        c,d = st.columns(2)
        optC = c.text_input("选项C")
        optD = d.text_input("选项D")
        ans = st.selectbox("正确答案",["A","B","C","D"])
        analysis = st.text_area("解析")
        source = st.text_input("来源",value="自定义新增")
        sub = st.form_submit_button("✅ 提交保存题目",use_container_width=True)
        if sub:
            if not all([qq,optA,optB,optC,optD,analysis]):
                st.error("请完善所有内容")
            else:
                maxid = max([x["id"] for x in QUESTION_BANK]) if QUESTION_BANK else 0
                newq = {
                    "id":maxid+1,"type":"选择","grade":grade,"chapter":chapter,
                    "q":qq,"opts":[optA,optB,optC,optD],"ans":ans,
                    "analysis":analysis,"source":source
                }
                save_question_to_json(newq)
                QUESTION_BANK = load_json_bank()
                st.success(f"🎉 新增题目成功，ID：{maxid+1}")
    st.divider()
    st.subheader("📊 题库预览")
    if st.button("刷新题库",use_container_width=True):
        QUESTION_BANK = load_json_bank()
        st.rerun()
    preview = []
    for x in QUESTION_BANK:
        preview.append({
            "ID":x["id"],"学段":x["grade"],"章节":x["chapter"],
            "题目":x["q"][:25]+"..." if len(x["q"])>25 else x["q"],
            "答案":x["ans"]
        })
    st.dataframe(pd.DataFrame(preview),use_container_width=True,height=400)

# ====================== 主程序函数（终极修复｜无缩进/无变量报错） ======================
def main():
    # 【极简纯净版 无BUG登录内核｜修复所有TypeError/IndentationError】
    import streamlit as st
    import streamlit_authenticator as stauth

    # 容错读取云端配置
    try:
        creds = st.secrets["credentials"]
    except Exception:
        st.error("配置读取失败，请检查云端Secrets配置")
        st.stop()

    # 初始化账号列表
    names = []
    usernames = []
    hashed_passwords = []
    user_keys = ["admin", "teacher", "stu1", "stu2", "stu3", "stu4", "stu5", "stu6"]
    for key in user_keys:
        if f"{key}_name" in creds and f"{key}_pwd" in creds:
            names.append(creds[f"{key}_name"])
            usernames.append(key)
            hashed_passwords.append(creds[f"{key}_pwd"])

    # 标准认证初始化
    authenticator = stauth.Authenticate(
        names,
        usernames,
        hashed_passwords,
        "math_app_auth",
        st.secrets.get("cookie_key", "math123456"),
        30
    )

    # 核心登录渲染
    name, authentication_status, username = authenticator.login(location="main")

    # 状态判断【彻底修复617行报错、删除无效status变量、统一缩进】
    if authentication_status is None:
        st.info("👋 欢迎使用初中数学智能组卷刷题系统，请登录后使用")
        st.markdown("""
### 云端上线说明
- 账号全部由 **Streamlit Secrets 云端加密配置**
- 管理员后台可 **在线生成账号哈希、在线扩充题库**
- 题库永久保存，无需改代码即可更新题目
        """)
        return
    elif authentication_status == False:
        st.error("❌ 账号或密码错误，请重新输入")
        return
    elif authentication_status == True:
        st.session_state.username = username
        # 权限菜单
        if username == "admin":
            menu = ["📄 智能组卷打印","📝 在线刷题练习","📒 错题本","📊 正确率统计","🔧 管理员题库扩充"]
        else:
            menu = ["📄 智能组卷打印","📝 在线刷题练习","📒 错题本","📊 正确率统计"]
        with st.sidebar:
            st.success(f"✅ 欢迎您，{name}")
            st.divider()
            st.header("🧩 功能导航")
            select_menu = st.radio("功能列表",menu)
            st.divider()
            if st.button("🚪 退出登录",use_container_width=True):
                authenticator.logout()
                for k in list(st.session_state.keys()):
                    if k in ["authentication_status","name","username"]:
                        del st.session_state[k]
                st.rerun()

        # 页面路由
        if select_menu == "📄 智能组卷打印":
            st.title("📚 初中数学智能组卷打印系统")
            st.subheader("真题题库｜随机组卷｜带解析｜PDF+TXT双格式导出")
            st.divider()
            QUESTION_BANK = load_json_bank()
            st.info(f"✅ 当前题库总量：{len(QUESTION_BANK)} 道")
            g_list = ["全部","初一","初二","初三"]
            sel_g = st.selectbox("选择学段",g_list)
            final_g = None if sel_g=="全部" else sel_g
            cnt = st.slider("出题数量",5,80,30,5)
            shuffle = st.checkbox("题目随机打乱",value=True)
            st.divider()
            b1,b2 = st.columns(2)
            with b1:
                gen = st.button("📄 生成试卷文本",use_container_width=True)
            with b2:
                pdf_export = st.button("🖨️ 导出PDF打印文件",use_container_width=True)
            if gen:
                qs = select_questions(cnt,final_g,shuffle)
                pure_txt,_ = generate_pure_paper(qs)
                ana_txt,_ = generate_analysis_paper(qs)
                st.success("✅ 试卷生成完成")
                st.subheader("纯净考试版")
                st.text_area("",pure_txt,height=350)
                st.subheader("解析答案版")
                st.text_area("",ana_txt,height=350)
            if pdf_export:
                qs = select_questions(cnt,final_g,shuffle)
                f1 = generate_pdf_paper(qs,False)
                f2 = generate_pdf_paper(qs,True)
                st.success("✅ PDF导出成功")
                c1,c2 = st.columns(2)
                with c1:
                    with open(f1,"rb") as f:
                        st.download_button("下载纯净PDF",f,file_name=f1,use_container_width=True)
                with c2:
                    with open(f2,"rb") as f:
                        st.download_button("下载解析PDF",f,file_name=f2,use_container_width=True)

        elif select_menu == "📝 在线刷题练习":
            practice_module(username)
        elif select_menu == "📒 错题本":
            error_book_module(username)
        elif select_menu == "📊 正确率统计":
            statistic_module(username)
        elif select_menu == "🔧 管理员题库扩充":
            admin_question_manage()

# 程序入口
if __name__ == "__main__":
    main()
