# AI 수학 튜터 백엔드 - backend/main.py (수정된 버전)
# 필요한 라이브러리들을 가져옵니다
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, ForeignKey, LargeBinary
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from passlib.context import CryptContext
from jose import JWTError, jwt
import httpx
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv
import base64

# OCR 관련 import 추가
import easyocr
from PIL import Image
import io

# 환경변수 로드
load_dotenv()

# API 키 환경변수 처리 및 민감한 정보 노출 방지
SECRET_KEY = os.getenv("SECRET_KEY", "change_this_to_a_secure_random_string")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# 부트캠프 API 엔드포인트 URL (환경변수로 관리)
BOOTCAMP_API_URL = os.getenv("BOOTCAMP_API_URL", "https://dev.wenivops.co.kr/services/openai-api")

# 데이터베이스 URL (환경변수로 관리)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./chatgpt_math_tutor.db")

# CORS 설정 (환경변수로 관리)
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

# 서버 설정
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# 로그 레벨 설정
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# 로그 시스템 설정 (환경변수 반영)
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# OCR 리더 전역 변수
ocr_reader = None

# FastAPI 애플리케이션 인스턴스 생성
app = FastAPI(title="AI 수학 튜터 API 서버", version="1.0.0")

# FastAPI 시작 이벤트에 OCR 초기화 추가
@app.on_event("startup")
async def startup_event():
    logger.info("서버 시작 이벤트: OCR 초기화...")
    initialize_ocr()
    # 수능 문제 초기 데이터 로드
    initialize_exam_questions()

# CORS 설정 (프론트엔드와 통신을 위해, 환경변수 반영)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 데이터베이스 스키마 설계 (SQLite와 SQLAlchemy 사용)
SQLALCHEMY_DATABASE_URL = DATABASE_URL
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 비밀번호 해싱
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 인증 스키마
security = HTTPBearer()

# 사용자 모델 및 테이블 생성
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계 설정
    chat_sessions = relationship("ChatSession", back_populates="user")

# 수능 기출문제 모델 추가
class ExamQuestion(Base):
    __tablename__ = "exam_questions"
    
    id = Column(Integer, primary_key=True, index=True)
    question_number = Column(Integer, unique=True, index=True)  # 1-30
    question_text = Column(Text)  # 문제 설명
    question_image = Column(LargeBinary)  # 이미지 데이터 (Base64)
    difficulty = Column(Integer)  # 난이도 (1-5)
    topic = Column(String)  # 주제 (대수, 기하, 확률 등)
    created_at = Column(DateTime, default=datetime.utcnow)

# 대화 기록 모델
class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"))
    role = Column(String)  # "user" 또는 "assistant"
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    session = relationship("ChatSession", back_populates="messages")

# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)

# 수능 문제 초기 데이터 로드 함수
def initialize_exam_questions():
    """수능 기출문제 초기 데이터 생성"""
    db = SessionLocal()
    try:
        # 이미 데이터가 있는지 확인
        existing_count = db.query(ExamQuestion).count()
        if existing_count > 0:
            logger.info(f"수능 문제 데이터 이미 존재: {existing_count}개")
            return

        logger.info("수능 기출문제 초기 데이터 생성 중...")
        
        # 샘플 수능 문제 데이터 (실제로는 이미지 파일이나 실제 문제로 교체)
        sample_questions = [
            {
                "question_text": "다음 방정식을 풀어보세요: 2x + 3 = 11",
                "difficulty": 1,
                "topic": "일차방정식"
            },
            {
                "question_text": "다음 이차방정식의 해를 구하세요: x² - 5x + 6 = 0",
                "difficulty": 2,
                "topic": "이차방정식"
            },
            {
                "question_text": "삼각형 ABC에서 AB = 3, BC = 4, 각 B = 90°일 때, AC의 길이를 구하세요.",
                "difficulty": 2,
                "topic": "기하"
            },
            {
                "question_text": "주사위를 두 번 던질 때, 나온 수의 합이 7이 될 확률을 구하세요.",
                "difficulty": 3,
                "topic": "확률"
            },
            {
                "question_text": "함수 f(x) = x² - 2x + 1의 최솟값을 구하세요.",
                "difficulty": 3,
                "topic": "함수"
            }
        ]
        
        # 5개 문제를 30개로 확장 (실제로는 각각 다른 문제여야 함)
        for i in range(30):
            base_question = sample_questions[i % 5]
            question = ExamQuestion(
                question_number=i + 1,
                question_text=f"{i + 1}번. " + base_question["question_text"],
                question_image=None,  # 실제로는 이미지 데이터 저장
                difficulty=base_question["difficulty"],
                topic=base_question["topic"]
            )
            db.add(question)
        
        db.commit()
        logger.info("수능 기출문제 30개 초기 데이터 생성 완료")
        
    except Exception as e:
        logger.error(f"수능 문제 초기화 실패: {e}")
        db.rollback()
    finally:
        db.close()

# OCR 관련 함수들
def initialize_ocr():
    """OCR 리더 초기화"""
    global ocr_reader
    try:
        logger.info("OCR 리더 초기화 중...")
        ocr_reader = easyocr.Reader(['ko', 'en'], gpu=False)
        logger.info("OCR 리더 초기화 성공")
        return True
    except Exception as e:
        logger.error(f"OCR 리더 초기화 실패: {e}")
        logger.warning("이미지 업로드 기능이 제한됩니다.")
        ocr_reader = None
        return False

def extract_text_from_image(image_data: str) -> str:
    """Base64 이미지에서 텍스트 추출"""
    global ocr_reader
    
    if not ocr_reader:
        return "OCR 기능을 사용할 수 없습니다. 텍스트로 문제를 입력해주세요."
    
    try:
        # Base64 디코딩
        image_bytes = base64.b64decode(image_data)
        
        # OCR에 바이트 데이터 직접 전달
        results = ocr_reader.readtext(image_bytes)
        
        if not results:
            return "이미지에서 텍스트를 찾을 수 없습니다. 더 선명한 이미지를 업로드하거나 텍스트로 문제를 입력해주세요."
        
        # 신뢰도 순으로 정렬하고 텍스트 추출
        texts = []
        for result in results:
            text = result[1].strip()
            confidence = result[2]
            
            # 신뢰도가 0.3 이상인 텍스트만 사용
            if confidence > 0.3 and text:
                texts.append(text)
        
        if not texts:
            return "이미지에서 명확한 텍스트를 찾을 수 없습니다. 더 선명한 이미지를 업로드해주세요."
        
        # 텍스트 합치기 및 정리
        extracted_text = " ".join(texts)
        
        # 수학 기호 정리
        extracted_text = clean_math_text(extracted_text)
        
        logger.info(f"OCR 텍스트 추출 성공: {extracted_text[:50]}...")
        return extracted_text
        
    except Exception as e:
        logger.error(f"OCR 텍스트 추출 실패: {e}")
        return f"이미지 처리 중 오류가 발생했습니다. 텍스트로 문제를 입력해주세요."

def clean_math_text(text: str) -> str:
    """수학 텍스트 정리"""
    replacements = {
        'X': 'x',
        '×': '*',
        '÷': '/',
        '—': '-',
        '–': '-',
        '²': '^2',
        '³': '^3',
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    return text.strip()

# 데이터베이스 세션 의존성
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic 모델들
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class ChatRequest(BaseModel):
    message: str = Field(..., max_length=2000)
    image_data: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    usage: Optional[Dict] = None

class ExamQuestionRequest(BaseModel):
    question_number: int = Field(..., ge=1, le=30)

class ExamQuestionResponse(BaseModel):
    question_number: int
    question_text: str
    question_image: Optional[str] = None
    difficulty: int
    topic: str
    message: str = "문제를 확인하신 후, 어떤 부분부터 시작하면 좋을지 물어보세요!"

# 유틸리티 함수들
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

# API 엔드포인트들
@app.get("/")
async def root():
    """서버 상태 확인"""
    logger.info("서버 상태 확인 요청")
    ocr_status = "사용 가능" if ocr_reader else "사용 불가"
    return {
        "message": "AI 수학 튜터 서버가 실행 중입니다",
        "ocr_status": ocr_status
    }

@app.post("/register", response_model=Token)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """회원가입 기능을 구현합니다."""
    logger.info(f"회원가입 요청: {user.username}")
    
    if get_user_by_username(db, user.username):
        raise HTTPException(status_code=400, detail="이미 존재하는 사용자명입니다")
    
    if get_user_by_email(db, user.email):
        raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다")
    
    hashed_password = get_password_hash(user.password)
    
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    logger.info(f"회원가입 성공: {user.username}")
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/login", response_model=Token)
async def login(user: UserLogin, db: Session = Depends(get_db)):
    """로그인 기능을 구현합니다."""
    logger.info(f"로그인 요청: {user.username}")
    
    db_user = get_user_by_username(db, user.username)
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        logger.warning(f"로그인 실패: {user.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="잘못된 사용자명 또는 비밀번호",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    logger.info(f"로그인 성공: {user.username}")
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/exam-question", response_model=ExamQuestionResponse)
async def get_exam_question(
    request: ExamQuestionRequest, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """DB에서 수능 기출문제를 조회합니다."""
    question_number = request.question_number
    
    logger.info(f"수능 문제 요청: 사용자 {current_user.username}, 문제 {question_number}번")
    
    # 데이터베이스에서 문제 조회
    exam_question = db.query(ExamQuestion).filter(
        ExamQuestion.question_number == question_number
    ).first()
    
    if not exam_question:
        raise HTTPException(status_code=404, detail=f"{question_number}번 문제를 찾을 수 없습니다")
    
    # 이미지 데이터가 있으면 Base64로 인코딩
    question_image_base64 = None
    if exam_question.question_image:
        question_image_base64 = base64.b64encode(exam_question.question_image).decode('utf-8')
    
    return ExamQuestionResponse(
        question_number=exam_question.question_number,
        question_text=exam_question.question_text,
        question_image=question_image_base64,
        difficulty=exam_question.difficulty,
        topic=exam_question.topic,
        message="문제를 확인하신 후, 어떤 부분부터 시작하면 좋을지 물어보세요!"
    )

@app.post("/chat", response_model=ChatResponse)
async def chat_with_ai(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """채팅 기능 구현"""
    logger.info(f"채팅 요청: 사용자 {current_user.username}, 이미지 포함: {bool(request.image_data)}")
    
    try:
        # 사용자별 채팅 세션 가져오기 또는 생성
        chat_session = db.query(ChatSession).filter(
            ChatSession.user_id == current_user.id
        ).order_by(ChatSession.created_at.desc()).first()
        
        if not chat_session:
            chat_session = ChatSession(user_id=current_user.id)
            db.add(chat_session)
            db.commit()
            db.refresh(chat_session)
        
        # 이전 대화 맥락 가져오기
        previous_messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == chat_session.id
        ).order_by(ChatMessage.timestamp.desc()).limit(10).all()
        
        # 대화 맥락 구성
        system_content = """당신은 AI 수학 튜터입니다. 다음 규칙을 반드시 지켜주세요.

**절대 규칙:**
1. 한 번에 최대 2-3문장만 말하세요
2. 설명 후 반드시 "이해했나요?" 또는 "여기까지 괜찮나요?" 물어보세요
3. 학생이 "네" 또는 "이해했어요"라고 답할 때까지 다음 단계로 넘어가지 마세요
4. 절대 여러 단계를 한 번에 설명하지 마세요
5. LaTeX 수식을 사용하지 마세요 (\\(, \\[, $ 등 금지)
6. # 기호로 제목을 만들지 마세요
7. 수학 기호는 일반 텍스트로 작성하세요 (예: x^2, 1/2, sqrt(x))

**응답 패턴:**
- 첫 질문: "이 문제에서 가장 먼저 무엇을 파악해야 할까요?"
- 설명 후: "[2-3문장 설명]. 이해했나요?"
- 이해함: "좋습니다! 다음으로 [한 가지만] 생각해보세요."
- 이해 못함: "어떤 부분이 어려운가요? 다시 설명해드릴게요."

**수학 표현 예시:**
- 올바름: "2x - 4 = 0", "x^2 + 3x + 2", "(1/2)^16"
- 금지: "\\( 2x - 4 = 0 \\)", "$2x - 4 = 0$", "\\[ x^2 \\]"

**금지사항:**
- LaTeX 수식 표현 절대 금지
- 긴 설명 금지 (3문장 초과)
- 여러 단계 동시 설명 금지
- ### 1단계, # 제목 같은 마크다운 제목 금지
- 이해도 확인 없이 계속 설명하기 금지

예시: "이 방정식은 2x - 4 = 0 이네요. 여기서 x의 값을 찾는 것이 목표입니다. 이해했나요?"

이렇게 짧게, 한 번에 하나씩만 확인하며 진행하세요."""

        messages = [
            {
                "role": "system", 
                "content": system_content
            }
        ]
        
        # 이전 대화 추가 (최신 순서를 역순으로)
        for msg in reversed(previous_messages):
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # 현재 사용자 메시지 추가 - OCR 처리 통합
        if request.image_data:
            # 이미지에서 텍스트 추출
            extracted_text = extract_text_from_image(request.image_data)
            
            # 추출된 텍스트로 메시지 구성
            if request.message:
                user_content = f"{request.message}\n\n[이미지에서 추출된 수학 문제: {extracted_text}]"
            else:
                user_content = f"다음 수학 문제를 단계별로 풀이해주세요:\n\n{extracted_text}"
            
            user_message = {
                "role": "user",
                "content": user_content
            }
            
            db_user_content = f"{request.message or '이미지 업로드'} [OCR 추출: {extracted_text[:50]}...]"
            
            logger.info(f"OCR 추출 텍스트: {extracted_text[:100]}...")
        else:
            user_message = {
                "role": "user",
                "content": request.message
            }
            db_user_content = request.message

        messages.append(user_message)
        
        logger.info(f"API 요청 메시지 수: {len(messages)}")
        
        # ChatGPT API 호출
        async with httpx.AsyncClient() as client:
            response = await client.post(
                BOOTCAMP_API_URL,
                json=messages,
                timeout=30.0
            )
            
            response.raise_for_status()
            response_data = response.json()
            
            logger.info(f"API 응답 상태: {response.status_code}")
            
            if 'error' in response_data:
                error_msg = response_data['error'].get('message', 'Unknown API error')
                logger.error(f"API 에러: {error_msg}")
                raise HTTPException(status_code=500, detail=f"AI 서비스 오류: {error_msg}")
            
            ai_message = response_data["choices"][0]["message"]["content"]
            usage_info = response_data.get("usage", {})
            
            logger.info(f"AI 응답 길이: {len(ai_message)} characters")
        
        # 채팅 기록 저장
        user_message_db = ChatMessage(
            session_id=chat_session.id,
            role="user",
            content=db_user_content
        )
        db.add(user_message_db)
        
        ai_response_message = ChatMessage(
            session_id=chat_session.id,
            role="assistant",
            content=ai_message
        )
        db.add(ai_response_message)
        
        db.commit()
        
        logger.info(f"채팅 응답 성공: 사용자 {current_user.username}")
        
        return ChatResponse(
            response=ai_message,
            usage=usage_info
        )
        
    except httpx.TimeoutException:
        logger.error("API 요청 시간 초과")
        raise HTTPException(status_code=408, detail="AI 응답 시간이 초과되었습니다")
    except httpx.HTTPStatusError as e:
        logger.error(f"API HTTP 오류: {e.response.status_code}")
        raise HTTPException(status_code=e.response.status_code, detail=f"AI 서비스 오류: {e}")
    except Exception as e:
        logger.error(f"채팅 처리 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")

@app.get("/chat-history")
async def get_chat_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """사용자별 채팅 기록 조회 기능"""
    logger.info(f"채팅 기록 조회: 사용자 {current_user.username}")
    
    chat_sessions = db.query(ChatSession).filter(
        ChatSession.user_id == current_user.id
    ).order_by(ChatSession.created_at.desc()).all()
    
    history = []
    for session in chat_sessions:
        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session.id
        ).order_by(ChatMessage.timestamp.asc()).all()
        
        session_data = {
            "session_id": session.id,
            "created_at": session.created_at,
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp
                }
                for msg in messages
            ]
        }
        history.append(session_data)
    
    return {"chat_history": history}

@app.delete("/chat-session/{session_id}")
async def delete_chat_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """채팅방 삭제 기능"""
    logger.info(f"채팅 세션 삭제 요청: 사용자 {current_user.username}, 세션 {session_id}")
    
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="채팅 세션을 찾을 수 없습니다")
    
    # 관련 메시지들 삭제
    db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
    
    # 세션 삭제
    db.delete(session)
    db.commit()
    
    logger.info(f"채팅 세션 삭제 완료: 세션 {session_id}")
    return {"message": "채팅 세션이 삭제되었습니다"}

# 서버 실행 코드
if __name__ == "__main__":
    import uvicorn
    
    # 개발 모드 감지
    is_development = (
        LOG_LEVEL.upper() == "DEBUG" or 
        HOST in ["127.0.0.1", "localhost"] or
        os.getenv("ENVIRONMENT", "development") == "development"
    )
    
    logger.info("AI 수학 튜터 서버 시작")
    logger.info(f"서버 주소: http://{HOST}:{PORT}")
    logger.info(f"API 문서: http://{HOST}:{PORT}/docs")
    logger.info(f"모드: {'개발' if is_development else '배포'}")
    
    if is_development:
        # 개발 모드: reload를 위해 import string 사용
        logger.info("개발 모드: 파일 변경 감지 활성화")
        uvicorn.run(
            "main:app",
            host=HOST,
            port=PORT,
            reload=True,
            log_level=LOG_LEVEL.lower()
        )
    else:
        # 배포 모드: 직접 앱 객체 사용
        uvicorn.run(
            app,
            host=HOST,
            port=PORT,
            log_level=LOG_LEVEL.lower()
        )