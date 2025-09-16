# upload_exam_questions.py - 수능 문제 이미지를 데이터베이스에 업로드 (수정된 버전)
import os
import base64
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import ExamQuestion, Base
import logging
import re

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 데이터베이스 연결 설정
DATABASE_URL = "sqlite:///./chatgpt_math_tutor.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def extract_question_number_from_filename(filename):
    """파일명에서 문제 번호를 정확히 추출"""
    try:
        # 확장자 제거
        name_without_ext = filename.split('.')[0]
        
        # 다양한 패턴 시도
        patterns = [
            r'(\d+)$',           # 끝에 오는 숫자 (예: 2025_26.png -> 26)
            r'_(\d+)',           # 언더스코어 뒤 숫자 (예: 2025_26.png -> 26)
            r'-(\d+)',           # 하이픈 뒤 숫자 (예: 2025-26.png -> 26)
            r'(\d{1,2})(?=\D|$)' # 1-2자리 숫자 (마지막으로 나오는 것)
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, name_without_ext)
            if matches:
                question_num = int(matches[-1])  # 마지막 매치 사용
                if 1 <= question_num <= 30:  # 유효한 범위 확인
                    return question_num
        
        # 패턴이 안 맞으면 전체 숫자에서 마지막 1-2자리 사용
        all_numbers = re.findall(r'\d+', name_without_ext)
        if all_numbers:
            last_number = all_numbers[-1]
            # 마지막 1-2자리만 사용 (예: 202526 -> 26)
            if len(last_number) > 2:
                question_num = int(last_number[-2:])
                if 1 <= question_num <= 30:
                    return question_num
            else:
                question_num = int(last_number)
                if 1 <= question_num <= 30:
                    return question_num
        
        logger.warning(f"파일명에서 문제 번호 추출 실패: {filename}")
        return None
        
    except Exception as e:
        logger.error(f"파일명 처리 오류 ({filename}): {e}")
        return None

def upload_exam_images(image_folder_path):
    """이미지 폴더에서 수능 문제 이미지들을 데이터베이스에 업로드 (수정된 버전)"""
    
    if not os.path.exists(image_folder_path):
        logger.error(f"이미지 폴더를 찾을 수 없습니다: {image_folder_path}")
        return False
    
    db = SessionLocal()
    try:
        logger.info(f"이미지 폴더 스캔 중: {image_folder_path}")
        
        # 이미지 파일 목록 가져오기
        image_files = []
        for filename in os.listdir(image_folder_path):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                question_num = extract_question_number_from_filename(filename)
                if question_num:
                    image_files.append((filename, question_num))
                else:
                    logger.warning(f"건너뜀 (문제번호 추출 실패): {filename}")
        
        logger.info(f"처리할 이미지 파일: {len(image_files)}개")
        
        # 문제 번호 순으로 정렬
        image_files.sort(key=lambda x: x[1])
        
        success_count = 0
        update_count = 0
        error_count = 0
        
        for filename, question_number in image_files:
            file_path = os.path.join(image_folder_path, filename)
            
            logger.info(f"처리 중: {filename} -> 문제 {question_number}번")
            
            try:
                # 이미지 파일을 바이너리로 읽기
                with open(file_path, 'rb') as image_file:
                    image_data = image_file.read()
                
                # 기존 문제가 있는지 확인
                existing_question = db.query(ExamQuestion).filter(
                    ExamQuestion.question_number == question_number
                ).first()
                
                if existing_question:
                    # 기존 문제 업데이트
                    existing_question.question_image = image_data
                    existing_question.question_text = f"{question_number}번. 수능 기출문제 (이미지 참조)"
                    update_count += 1
                    logger.info(f"  ✅ 문제 {question_number}번 이미지 업데이트")
                else:
                    # 새 문제 생성
                    new_question = ExamQuestion(
                        question_number=question_number,  # 🎯 수정: 파일명에서 추출한 실제 번호 사용
                        question_text=f"{question_number}번. 수능 기출문제 (이미지 참조)",
                        question_image=image_data,
                        difficulty=3,  # 기본 난이도
                        topic="수능기출"
                    )
                    db.add(new_question)
                    success_count += 1
                    logger.info(f"  ✅ 문제 {question_number}번 신규 추가")
                
            except Exception as e:
                logger.error(f"  ❌ {filename} 처리 실패: {e}")
                error_count += 1
                continue
        
        # 변경사항 저장
        db.commit()
        
        logger.info("=" * 50)
        logger.info("📊 업로드 결과:")
        logger.info(f"   신규 추가: {success_count}개")
        logger.info(f"   업데이트: {update_count}개")
        logger.info(f"   오류: {error_count}개")
        logger.info(f"   총 처리: {success_count + update_count}개")
        logger.info("=" * 50)
        
        return True
        
    except Exception as e:
        logger.error(f"데이터베이스 작업 실패: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def verify_uploaded_images():
    """업로드된 이미지 확인"""
    db = SessionLocal()
    try:
        questions = db.query(ExamQuestion).order_by(ExamQuestion.question_number).all()
        
        logger.info("📋 데이터베이스 문제 현황:")
        logger.info("-" * 50)
        
        for question in questions:
            image_status = "이미지 있음" if question.question_image else "이미지 없음"
            image_size = f"({len(question.question_image)} bytes)" if question.question_image else ""
            logger.info(f"  {question.question_number:2d}번: {image_status} {image_size}")
        
        logger.info("-" * 50)
        logger.info(f"총 {len(questions)}개 문제 등록됨")
        
        # 이미지가 있는 문제 수 계산
        with_images = sum(1 for q in questions if q.question_image)
        logger.info(f"이미지 포함 문제: {with_images}개")
        
        # 누락된 문제 번호 확인
        existing_numbers = {q.question_number for q in questions}
        missing_numbers = set(range(1, 31)) - existing_numbers
        if missing_numbers:
            logger.warning(f"누락된 문제 번호: {sorted(missing_numbers)}")
        else:
            logger.info("✅ 1-30번 문제 모두 등록됨")
        
    except Exception as e:
        logger.error(f"확인 중 오류: {e}")
    finally:
        db.close()

def test_filename_extraction():
    """파일명 추출 테스트"""
    test_files = [
        "2025_1.png",
        "2025_26.png", 
        "수능2025-15.jpg",
        "question_30.png",
        "2025년수능_5번.jpeg",
        "26번문제.png"
    ]
    
    print("🧪 파일명 테스트:")
    print("-" * 30)
    for filename in test_files:
        number = extract_question_number_from_filename(filename)
        print(f"{filename:20} -> {number}")

def clear_all_questions():
    """모든 문제 삭제 (재업로드 전 초기화용)"""
    db = SessionLocal()
    try:
        deleted_count = db.query(ExamQuestion).delete()
        db.commit()
        logger.info(f"🗑️  모든 문제 삭제 완료: {deleted_count}개")
        return True
    except Exception as e:
        logger.error(f"삭제 실패: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def main():
    """메인 함수"""
    print("🎓 수능 문제 이미지 업로드 도구 (수정된 버전)")
    print("=" * 50)
    
    # 사용법 안내
    print("✨ 주요 수정사항:")
    print("- 파일명에서 실제 문제 번호를 추출하여 정확히 매칭")
    print("- 다양한 파일명 패턴 지원")
    print()
    print("📝 지원하는 파일명 패턴:")
    print("  • 2025_26.png -> 26번")
    print("  • 수능-15.jpg -> 15번") 
    print("  • question_30.png -> 30번")
    print("  • 26번문제.png -> 26번")
    print()
    
    while True:
        print("메뉴를 선택하세요:")
        print("1. 이미지 업로드")
        print("2. 업로드된 문제 확인")
        print("3. 파일명 추출 테스트")
        print("4. 모든 문제 삭제 (주의!)")
        print("5. 종료")
        
        choice = input("선택 (1-5): ").strip()
        
        if choice == "1":
            image_folder = input("이미지 폴더 경로를 입력하세요: ").strip()
            if image_folder:
                # 따옴표 제거
                image_folder = image_folder.strip('"\'')
                print(f"📁 폴더: {image_folder}")
                
                if upload_exam_images(image_folder):
                    print("✅ 업로드 완료!")
                else:
                    print("❌ 업로드 실패!")
            else:
                print("❌ 폴더 경로를 입력해주세요.")
                
        elif choice == "2":
            verify_uploaded_images()
            
        elif choice == "3":
            test_filename_extraction()
            
        elif choice == "4":
            confirm = input("⚠️  모든 문제를 삭제하시겠습니까? (yes 입력): ")
            if confirm.lower() == "yes":
                if clear_all_questions():
                    print("✅ 모든 문제 삭제 완료!")
                else:
                    print("❌ 삭제 실패!")
            else:
                print("삭제 취소됨")
                
        elif choice == "5":
            print("👋 프로그램 종료")
            break
            
        else:
            print("❌ 잘못된 선택입니다. 1-5 중 선택해주세요.")
        
        print()

if __name__ == "__main__":
    main()