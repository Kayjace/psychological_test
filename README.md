# 심리 테스트 프로젝트

이 프로젝트는 Flask를 사용한 연습용 미니 프로젝트로, MBTI 성격 유형 테스트 웹 애플리케이션입니다.

## 주요 기능

### 사용자 기능
- 홈페이지에서 사용자 정보 입력
- MBTI 질문에 답변
- 개인 MBTI 결과 및 통계 시각화 확인

### 관리자 기능
- 관리자 대시보드
- 질문 관리 (추가, 수정, 활성화/비활성화)
- 참가자 퀴즈 결과 조회

## 프로젝트 구조
```text
psychological_test/
│
├── app/
│ ├── static/
│ ├── images/
│ │    └── background.png
│ ├──templates/
│ │ ├── index.html
│ │ ├── quiz.html
│ │ ├── results.html
│ │ ├── admin.html
│ │ ├── dashboard.html
│ │ └── manage_questions.html
│ ├── init.py
│ ├── models.py
│ ├── database.py
│ ├── main.py
│ └── admin.py
├── db.sqlite
├── wsgi.py
└── run.py
```

## 주요 라우트

### 메인 라우트 (`main.py`)
- `/`: 홈페이지
- `/participants`: 새 참가자 추가 (POST)
- `/quiz`: MBTI 질문 표시
- `/submit`: 퀴즈 응답 제출 (POST)
- `/results`: MBTI 결과 및 통계 표시

### 관리자 라우트 (`admin.py`)
- `/admin`: 관리자 로그인
- `/admin/dashboard`: 전체 통계 및 그래프
- `/admin/dashboard/question`: 질문 관리 (질문 추가 및 수정, 활성화 및 비활성화)
- `/admin/dashboard/list`: 개별 참여자 퀴즈 응답 조회

## 데이터 모델

- **Participant**: 참가자 정보
- **Question**: MBTI 질문 정보
- **Quiz**: 참가자의 질문별 응답
- **Admin**: 관리자 계정 정보
- **Visitor**: 페이지 접속자 정보

## 사용된 기술

- **백엔드**: Python, Flask
- **데이터베이스**: SQLAlchemy (ORM), SQLite
- **프론트엔드**: HTML, JavaScript
- **데이터 시각화**: Plotly
- **기타 라이브러리**: pandas, werkzeug.security

## 설치 및 실행 방법

1. 저장소 클론:
```git
git clone https://github.com/Kayjace/psychological_test.git
```
2. 가상 환경 설정 및 의존성 설치:
```python
python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate
pip install -r requirements.txt
```
3. 애플리케이션 실행:
   
개발환경 실행 시 (기본값 localhost:5000)
```terminal
flask run
```
    
gunicorn 사용 시 (기본값 localhost:8000)
```terminal
gunicorn wsgi:application
```
