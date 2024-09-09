from flask import (
    jsonify,
    render_template,
    request,
    Blueprint,
    redirect,
    url_for,
    flash,
    session,
    make_response
)
from werkzeug.security import check_password_hash
from .models import Question, Participant, Quiz, Admin, Visitor
from .database import db
import plotly.express as px
import pandas as pd
import plotly
import json
from sqlalchemy import func
import plotly.graph_objs as go
from plotly.offline import plot
from datetime import datetime
import uuid

main = Blueprint("main", __name__)
admin = Blueprint("admin", __name__, url_prefix="/admin/")

def track_visitor():
    visitor_id = request.cookies.get('visitor_id')
    if not visitor_id:
        visitor_id = str(uuid.uuid4())
    
    visitor = Visitor.query.filter_by(id=visitor_id).first()
    if not visitor:
        visitor = Visitor(id=visitor_id, last_visit=datetime.utcnow())
        db.session.add(visitor)
    else:
        visitor.last_visit = datetime.utcnow()
    
    db.session.commit()
    return visitor_id

@main.route("/", methods=["GET"])
def home():
    visitor_id = track_visitor()
    response = make_response(render_template("index.html"))
    response.set_cookie('visitor_id', visitor_id, max_age=31536000)  # 1년 유효
    return response

@main.route("/participants", methods=["POST"])
def add_participant():
    data = request.get_json()
    new_participant = Participant(
        name=data["name"], age=data["age"], gender=data["gender"], created_at=datetime.utcnow()
    )
    db.session.add(new_participant)
    db.session.commit()
    return jsonify(
        {"redirect": url_for("main.quiz"), "participant_id": new_participant.id}
    )

@main.route("/quiz")
def quiz():
    try:
        participant_id = request.cookies.get("participant_id")
        if not participant_id:
            return redirect(url_for("main.home"))
        questions = Question.query.filter(Question.is_active == True).order_by(Question.order_num).all()
        return render_template("quiz.html", questions=questions)
    except Exception as e:
        print(f"Error in quiz route: {str(e)}")
        return "An error occurred", 500

@main.route("/submit", methods=["POST"])
def submit():
    participant_id = request.cookies.get("participant_id")
    if not participant_id:
        return jsonify({"error": "Participant ID not found"}), 400
    data = request.json
    quizzes = data.get("quizzes", [])
    for quiz in quizzes:
        new_quiz_entry = Quiz(
            participant_id=participant_id,
            question_id=quiz.get("question_id"),
            chosen_answer=quiz.get("chosen_answer"),
        )
        db.session.add(new_quiz_entry)
    db.session.commit()
    return jsonify({
        "message": "Quiz answers submitted successfully.",
        "redirect": url_for("main.show_results"),
    })

@main.route("/questions")
def get_questions():
    questions = Question.query.filter(Question.is_active == True).order_by(Question.order_num).all()
    questions_list = [{
        "id": question.id,
        "content": question.content,
        "option_1": question.option_1,
        "option_2": question.option_2,
        "type": question.type,
    } for question in questions]
    print(f"Returning {len(questions_list)} questions: {questions_list}")  # 디버그 출력
    return jsonify(questions=questions_list)

@main.route("/results")
def show_results():
    participant_id = request.cookies.get("participant_id")
    if not participant_id:
        return redirect(url_for("main.home"))

    # MBTI 결과 계산
    quizzes = Quiz.query.filter_by(participant_id=participant_id).all()
    type_scores = {'I': 0, 'E': 0, 'S': 0, 'N': 0, 'T': 0, 'F': 0, 'J': 0, 'P': 0}
    for quiz in quizzes:
        question = Question.query.get(quiz.question_id)
        if quiz.chosen_answer == '1':
            type_scores[question.type[0]] += 1
        else:
            type_scores[question.type[1]] += 1
    
    mbti_type = ''
    mbti_type += 'I' if type_scores['I'] > type_scores['E'] else 'E'
    mbti_type += 'S' if type_scores['S'] > type_scores['N'] else 'N'
    mbti_type += 'T' if type_scores['T'] > type_scores['F'] else 'F'
    mbti_type += 'J' if type_scores['J'] > type_scores['P'] else 'P'

    mbti_descriptions = {
        'ISTP': '[탐험가형] 백과사전형, 만능 재주꾼',
        'ISFP': '[탐험가형] 성인군자형, 호기심 많은 예술가',
        'ESFP': '[탐험가형] 사교적인 유형, 자유로운 영혼의 연예인',
        'ESTP': '[탐험가형] 수완좋은 활동가형, 모험을 즐기는 사업가',
        'ISTJ': '[관리자형] 세상의 소금형, 청렴결백한 논리주의자',
        'ISFJ': '[관리자형] 임금 뒷편의 권력형, 용감한 수호자',
        'ESFJ': '[관리자형] 친선도모형, 사교적인 외교관',
        'ESTJ': '[관리자형] 사업가형, 엄격한 관리자',
        'INFJ': '[외교형] 예언자형, 선의의 옹호자',
        'INFP': '[외교형] 잔다르크형, 열정적인 중재자',
        'ENFP': '[외교형] 스파크형, 재기발랄한 활동가',
        'ENFJ': '[외교형] 언변능숙형, 정의로운 사회운동가',
        'INTJ': '[분석형] 과학자형, 용의주도한 전략가',
        'INTP': '[분석형] 아이디어 뱅크형, 논리적인 사색가',
        'ENTP': '[분석형] 발명가형, 뜨거운 논쟁을 즐기는 변론가',
        'ENTJ': '[분석형] 지도자형, 대담한 통솔자'
    }

    mbti_description = mbti_descriptions.get(mbti_type, '')

    # 모든 참가자의 MBTI 유형 계산
    all_participants = Participant.query.all()
    mbti_types = []
    for participant in all_participants:
        p_quizzes = Quiz.query.filter_by(participant_id=participant.id).all()
        p_type_scores = {'I': 0, 'E': 0, 'S': 0, 'N': 0, 'T': 0, 'F': 0, 'J': 0, 'P': 0}
        for quiz in p_quizzes:
            question = Question.query.get(quiz.question_id)
            if quiz.chosen_answer == '1':
                p_type_scores[question.type[0]] += 1
            else:
                p_type_scores[question.type[1]] += 1
        p_mbti_type = ''
        p_mbti_type += 'I' if p_type_scores['I'] > p_type_scores['E'] else 'E'
        p_mbti_type += 'S' if p_type_scores['S'] > p_type_scores['N'] else 'N'
        p_mbti_type += 'T' if p_type_scores['T'] > p_type_scores['F'] else 'F'
        p_mbti_type += 'J' if p_type_scores['J'] > p_type_scores['P'] else 'P'
        mbti_types.append({'mbti': p_mbti_type, 'age': participant.age, 'gender': participant.gender})


    mbti_df = pd.DataFrame(mbti_types)


    # MBTI 유형별 도넛 차트 생성
    mbti_types = ['ISTJ', 'ISFJ', 'INFJ', 'INTJ', 'ISTP', 'ISFP', 'INFP', 'INTP', 
                  'ESTP', 'ESFP', 'ENFP', 'ENTP', 'ESTJ', 'ESFJ', 'ENFJ', 'ENTJ']
    
    mbti_charts = {}
    for mbti_type in mbti_types:
        type_data = mbti_df[mbti_df['mbti'] == mbti_type]
        
        # 연령 도넛 차트
        age_counts = type_data['age'].value_counts()
        fig_age = px.pie(values=age_counts.values, names=age_counts.index, hole=0.3,
                         title=f"{mbti_type} Age Distribution")
        fig_age.update_traces(textposition="inside", textinfo="percent+label")
        
        # 성별 도넛 차트
        gender_counts = type_data['gender'].value_counts()
        fig_gender = px.pie(values=gender_counts.values, names=gender_counts.index, hole=0.3,
                            title=f"{mbti_type} Gender Distribution")
        fig_gender.update_traces(textposition="inside", textinfo="percent+label")
        
        mbti_charts[mbti_type] = {
        'age': fig_age.to_dict(),
        'gender': fig_gender.to_dict()
        }

    # MBTI 유형 분포 도넛 차트
    mbti_counts = mbti_df['mbti'].value_counts()
    fig_mbti = px.pie(values=mbti_counts.values, names=mbti_counts.index, hole=0.3,
                      title="MBTI Type Distribution")
    fig_mbti.update_traces(textposition="inside", textinfo="percent+label")

    # 연령별 MBTI 분포
    age_mbti = pd.crosstab(mbti_df['age'], mbti_df['mbti'])
    fig_age_mbti = px.bar(age_mbti, title="Age Distribution by MBTI Type")
    fig_age_mbti.update_layout(xaxis_title="Age Group", yaxis_title="Count")

    # 성별별 MBTI 분포
    gender_mbti = pd.crosstab(mbti_df['gender'], mbti_df['mbti'])
    fig_gender_mbti = px.bar(gender_mbti, title="Gender Distribution by MBTI Type")
    fig_gender_mbti.update_layout(xaxis_title="Gender", yaxis_title="Count")

    # 기존 시각화 생성
    fig_age = px.pie(
        mbti_df,
        names="age",
        hole=0.3,
        title="Age Distribution",
        color_discrete_sequence=px.colors.sequential.RdBu,
        labels={"age": "Age Group"},
    )
    fig_age.update_traces(textposition="inside", textinfo="percent+label")

    fig_gender = px.pie(
        mbti_df,
        names="gender",
        hole=0.3,
        title="Gender Distribution",
        color_discrete_sequence=px.colors.sequential.Purp,
        labels={"gender": "Gender"},
    )
    fig_gender.update_traces(textposition="inside", textinfo="percent+label")

    graphs_json = json.dumps({
        'mbti_charts': mbti_charts,
        "mbti_distribution": fig_mbti.to_dict(),
        "age_mbti_distribution": fig_age_mbti.to_dict(),
        "gender_mbti_distribution": fig_gender_mbti.to_dict(),
        "age_distribution": fig_age.to_dict(),
        "gender_distribution": fig_gender.to_dict(),
    }, cls=plotly.utils.PlotlyJSONEncoder)

    return render_template("results.html", graphs_json=graphs_json, mbti_type=mbti_type, mbti_description=mbti_description)

@admin.route("", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        admin = Admin.query.filter_by(username=username).first()

        if admin and check_password_hash(admin.password, password):
            session["admin_logged_in"] = True
            return redirect(url_for("admin.dashboard"))
        else:
            flash("Invalid username or password")

    return render_template("admin.html")


@admin.route("/logout")
def logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("admin.login"))


from functools import wraps
from flask import redirect, url_for, session


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "admin_logged_in" not in session:
            return redirect(url_for("admin.login", next=request.url))
        return f(*args, **kwargs)

    return decorated_function

@admin.route("/dashboard")
@login_required
def dashboard():
    # 유니크 방문자 수 계산
    unique_visitors = db.session.query(func.count(func.distinct(Visitor.id))).scalar()
    
    # 총 참여자 수 계산
    total_participants = db.session.query(func.count(Participant.id)).scalar()
    
    # 날짜별 참가자 수를 계산
    participant_counts = (
        db.session.query(
            func.date(Participant.created_at).label("date"),
            func.count(Participant.id).label("count"),
        )
        .group_by(func.date(Participant.created_at))
        .order_by(func.date(Participant.created_at))
        .all()
    )

    # 데이터프레임 생성
    df = pd.DataFrame(participant_counts, columns=['date', 'count'])
    df['date'] = pd.to_datetime(df['date'])

    # Plotly Express를 사용하여 그래프 생성
    fig = px.line(df, x='date', y='count', title='일자별 참가자 수', markers=True)
    fig.update_layout(
    xaxis_title="날짜",
    yaxis_title="참가자 수",
    xaxis=dict(tickformat='%Y-%m-%d'),
    yaxis=dict(rangemode='tozero')
    )
    
    # Plotly 그래프를 HTML로 변환
    graph_div = fig.to_html(full_html=False, config={'displayModeBar': False})

    # 성별 분포 계산
    gender_counts = db.session.query(Participant.gender, func.count(Participant.id)).group_by(Participant.gender).all()
    df_gender = pd.DataFrame(gender_counts, columns=['gender', 'count'])
    
    # 성별 분포 그래프
    fig_gender = px.pie(df_gender, values='count', names='gender', title='성별 분포')
    gender_distribution_div = fig_gender.to_html(full_html=False)

    # 연령대 분포 계산
    age_counts = db.session.query(Participant.age, func.count(Participant.id)).group_by(Participant.age).all()
    df_age = pd.DataFrame(age_counts, columns=['age', 'count'])
    
    # 연령대 분포 그래프
    fig_age = px.bar(df_age, x='age', y='count', title='연령대 분포')
    age_distribution_div = fig_age.to_html(full_html=False)

    return render_template(
        "dashboard.html",
        unique_visitors=unique_visitors,
        total_participants=total_participants,
        graph_div=graph_div,
        gender_distribution_div=gender_distribution_div,
        age_distribution_div=age_distribution_div
    )


@admin.route("/dashboard/question", methods=["GET", "POST"])
@login_required
def manage_questions():
    if request.method == "POST":
        if "new_question" in request.form:
            # 새 질문 추가
            is_active = (
                "is_active" in request.form and request.form["is_active"] == "on"
            )
            new_question = Question(
                content=request.form["content"],
                order_num=request.form["order_num"],
                is_active=is_active,
            )
            db.session.add(new_question)
            db.session.commit()
        else:
            # 기존 질문 수정
            question_id = request.form["question_id"]
            question = Question.query.get(question_id)
            if question:
                is_active = (
                    "is_active" in request.form and request.form["is_active"] == "on"
                )
                question.content = request.form["content"]
                question.order_num = request.form["order_num"]
                question.is_active = is_active
                db.session.commit()

    questions = Question.query.order_by(Question.order_num).all()
    return render_template("manage_questions.html", questions=questions)


@admin.route("/dashboard/list", methods=["GET", "POST"])
@login_required
def quiz_list():
    participants = Participant.query.all()
    selected_participant_id = request.form.get("participant_id")
    quizzes = []

    if selected_participant_id:
        quizzes = Quiz.query.filter_by(participant_id=selected_participant_id).all()

    return render_template("quiz_list.html", participants=participants, quizzes=quizzes)
