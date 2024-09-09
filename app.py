from flask import Flask
from flask_migrate import Migrate
from flask.cli import with_appcontext
import os
import click
from app.database import db
from app.models import Question, Admin, Participant
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta

def create_app():
    app = Flask(__name__)
    # 환경 변수에서 SECRET_KEY 가져오기, 없으면 기본값 사용
    app.secret_key = os.environ.get("SECRET_KEY", "oz_coding_secret")

    # Vercel Postgres 데이터베이스 URL 사용
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("POSTGRES_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # 데이터베이스 초기화
    from app.models import db
    db.init_app(app)
    
    # 마이그레이션 설정
    migrate = Migrate(app, db)

    from app.routes import main as main_blueprint
    from app.routes import admin as admin_blueprint

    app.register_blueprint(main_blueprint)
    app.register_blueprint(admin_blueprint)

    def add_initial_questions():
        initial_questions = [
            {
                "content": "수업 시간에 메모한 시험 범위를 잃어버렸다! 당신은",
                "option_1": "같이 수업을 듣는 친구들에게 물어본다",
                "option_2": "학교 페이지에 들어가 시험 범위를 찾아본다",
                "type": "IE"
            },
            {
                "content": "친구들과 술자리에서 나는",
                "option_1": "들어주면서 리액션 많이 하는 타입",
                "option_2": "내가 먼저 화제를 꺼내는 타입",
                "type": "IE"
            },
            {
                "content": "갑자기 생긴 휴일의 당신은",
                "option_1": "하루종일 누워서 유튜브를 본다",
                "option_2": "일단 그날 시간 되는 친구가 있는지 물어본다",
                "type": "IE"
            },
            {
                "content": "여행 계획을 세운다면",
                "option_1": "시간, 장소 단위로 최대한 자세히 세운다",
                "option_2": "그날 뭐할지 정도만 정해둔다",
                "type": "SN"
            },
            {
                "content": "나는 다른 사람보다",
                "option_1": "성실하고 꼼꼼하다",
                "option_2": "창의적이고 유연하다",
                "type": "SN"
            },
            {
                "content": "처음 해보는 일을 할 때",
                "option_1": "다른 사람들이 어떻게 하는지 참고한다",
                "option_2": "일단 부딪혀보고 내 방식대로 한다",
                "type": "SN"
            },
            {
                "content": "일을 하다가 작지만 아리송한 부분이 생겼을 때",
                "option_1": "시간이 걸려도 도움을 청한다",
                "option_2": "일단 할 수 있는 대로 하고 넘어간다",
                "type": "JP"
            },
            {
                "content": "늦은 시간,영화 한 편만 보고 자려했는데 잠이 안 온다. 나는",
                "option_1": "그래도 내일 일정이 있으니 억지로라도 자야 한다.",
                "option_2": "한 편 더 보고 자면 된다.",
                "type": "JP"
            },
            {
                "content": "나는 일을 할 때",
                "option_1": "나만의 계획을 세우고 그대로 실행한다.",
                "option_2": "일단 눈앞에 보이는 일 먼저 처리한다.",
                "type": "JP"
            },
            {
                "content": "드라마나 소설을 볼 때",
                "option_1": "일어난 사건들을 중심으로 본다",
                "option_2": "내가 인물에게 몰입해 공감하며 본다",
                "type": "TF"
            },
            {
                "content": "갑자기 친구가 다른 친구와 생긴 문제를 이야기한다. 우선",
                "option_1": "어쩌다 문제가 생겼는지 알아낸다",
                "option_2": "친구의 기분을 먼저 풀어준다",
                "type": "TF"
            },
            {
                "content": "고급 레스토랑에서 맛있는 음식을 먹고 난 뒤",
                "option_1": "아무리 맛있어도 비싸서 별로인 것 같다",
                "option_2": "좀 비싸도 맛있으니까 만족이다",
                "type": "TF"
            },
        ]

        yesterday = datetime.utcnow() - timedelta(days=1)

        existing_admin = Admin.query.filter_by(username="admin").first()
        if not existing_admin:
            hashed_password = generate_password_hash("0000")
            new_admin = Admin(username="admin", password=hashed_password)
            db.session.add(new_admin)

        participants_without_created_at = Participant.query.filter(Participant.created_at == None).all()
        for participant in participants_without_created_at:
            participant.created_at = yesterday

        for index, question_data in enumerate(initial_questions, start=1):
            existing_question = Question.query.filter_by(content=question_data["content"]).first()
            if not existing_question:
                new_question = Question(
                    content=question_data["content"],
                    option_1=question_data["option_1"],
                    option_2=question_data["option_2"],
                    type=question_data["type"],
                    order_num=index,
                    is_active=True
                )
                db.session.add(new_question)

        db.session.commit()

    @click.command("init-db")
    @with_appcontext
    def init_db_command():
        db.create_all()
        add_initial_questions()
        click.echo("Initialized the database with MBTI questions.")

    app.cli.add_command(init_db_command)

    return app