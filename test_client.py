# AI 수학 튜터 백엔드 테스트 코드 - backend/test_client.py
# 11) 테스트코드 작성

import requests
import json
import time
import sys
import os
from typing import Optional

class MathTutorTestClient:
    """AI 수학 튜터 백엔드 테스트 클라이언트"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.auth_token: Optional[str] = None
        self.username: Optional[str] = None

    def test_server_status(self):
        """서버 상태 확인 테스트"""
        print("🔍 서버 상태 확인 중...")
        
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            if response.status_code == 200:
                print("✅ 서버 상태 확인 성공")
                result = response.json()
                print(f"   📝 응답: {result.get('message', 'No message')}")
                return True
            else:
                print(f"❌ 서버 상태 확인 실패: HTTP {response.status_code}")
                print(f"   📝 응답: {response.text}")
                return False
        except requests.exceptions.ConnectionError:
            print("❌ 서버에 연결할 수 없습니다")
            print("   💡 backend/main.py가 실행 중인지 확인하세요")
            print("   💡 실행 명령어: cd backend && python main.py")
            return False
        except requests.exceptions.Timeout:
            print("❌ 서버 응답 시간 초과")
            return False
        except Exception as e:
            print(f"❌ 서버 연결 오류: {e}")
            return False

    def test_register(self, username: str = None, email: str = None, password: str = "testpass123"):
        """9) 회원가입 테스트"""
        print(f"\n📝 회원가입 테스트")
        
        # 고유한 사용자명과 이메일 생성
        timestamp = int(time.time())
        if username is None:
            username = f"testuser_{timestamp}"
        if email is None:
            email = f"test_{timestamp}@example.com"
        
        data = {
            "username": username,
            "email": email,
            "password": password
        }
        
        print(f"   👤 사용자명: {username}")
        print(f"   📧 이메일: {email}")
        
        try:
            response = requests.post(f"{self.base_url}/register", json=data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                self.auth_token = result["access_token"]
                self.username = username
                print("✅ 회원가입 성공")
                print(f"   🔑 토큰 타입: {result['token_type']}")
                return True
            else:
                print(f"❌ 회원가입 실패: HTTP {response.status_code}")
                try:
                    error_detail = response.json().get('detail', 'Unknown error')
                except:
                    error_detail = response.text
                print(f"   📝 오류: {error_detail}")
                return False
                
        except requests.exceptions.Timeout:
            print("❌ 회원가입 요청 시간 초과")
            return False
        except Exception as e:
            print(f"❌ 회원가입 오류: {e}")
            return False

    def test_login(self, username: str = None, password: str = "testpass123"):
        """9) 로그인 테스트"""
        print(f"\n🔐 로그인 테스트")
        
        if username is None:
            username = self.username or "testuser"
        
        data = {
            "username": username,
            "password": password
        }
        
        print(f"   👤 사용자명: {username}")
        
        try:
            response = requests.post(f"{self.base_url}/login", json=data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                self.auth_token = result["access_token"]
                self.username = username
                print("✅ 로그인 성공")
                return True
            else:
                print(f"❌ 로그인 실패: HTTP {response.status_code}")
                try:
                    error_detail = response.json().get('detail', 'Unknown error')
                except:
                    error_detail = response.text
                print(f"   📝 오류: {error_detail}")
                return False
                
        except Exception as e:
            print(f"❌ 로그인 오류: {e}")
            return False

    def test_exam_question(self, question_number: int = 5):
        """4) 수능 기출문제 테스트"""
        print(f"\n📚 수능 기출문제 테스트")
        
        if not self.auth_token:
            print("❌ 인증 토큰이 필요합니다. 먼저 로그인하세요.")
            return False
        
        data = {"question_number": question_number}
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        print(f"   🔢 문제 번호: {question_number}")
        
        try:
            response = requests.post(f"{self.base_url}/exam-question", json=data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                print("✅ 수능 문제 조회 성공")
                print(f"   📋 문제: {result['question_text'][:50]}...")
                print(f"   💬 안내: {result['message'][:50]}...")
                return True
            else:
                print(f"❌ 수능 문제 조회 실패: HTTP {response.status_code}")
                try:
                    error_detail = response.json().get('detail', 'Unknown error')
                except:
                    error_detail = response.text
                print(f"   📝 오류: {error_detail}")
                return False
                
        except Exception as e:
            print(f"❌ 수능 문제 조회 오류: {e}")
            return False

    def test_invalid_exam_question(self, question_number: int = 50):
        """4) 잘못된 수능 문제 번호 테스트"""
        print(f"\n🚫 잘못된 수능 문제 번호 테스트")
        
        if not self.auth_token:
            print("❌ 인증 토큰이 필요합니다. 먼저 로그인하세요.")
            return False
        
        data = {"question_number": question_number}
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        print(f"   🔢 잘못된 번호: {question_number}")
        
        try:
            response = requests.post(f"{self.base_url}/exam-question", json=data, headers=headers, timeout=10)
            
            if response.status_code == 422:  # Validation Error 예상
                print("✅ 잘못된 문제 번호 검증 성공")
                return True
            else:
                print(f"❌ 검증 실패: HTTP {response.status_code}")
                print(f"   📝 응답: {response.text[:100]}...")
                return False
                
        except Exception as e:
            print(f"❌ 테스트 오류: {e}")
            return False

    def test_chat(self, message: str = "2x + 3 = 7을 풀어주세요"):
        """7) 채팅 기능 테스트"""
        print(f"\n💬 채팅 기능 테스트")
        
        if not self.auth_token:
            print("❌ 인증 토큰이 필요합니다. 먼저 로그인하세요.")
            return False
        
        data = {"message": message}
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        print(f"   📤 질문: {message}")
        print("   ⏳ AI 응답 대기 중...")
        
        try:
            response = requests.post(f"{self.base_url}/chat", json=data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                print("✅ 채팅 성공")
                ai_response = result['response']
                print(f"   🤖 AI 응답: {ai_response[:100]}{'...' if len(ai_response) > 100 else ''}")
                
                if result.get('usage'):
                    usage = result['usage']
                    print(f"   📊 토큰 사용량: {usage.get('total_tokens', 'N/A')}개")
                
                return True
            else:
                print(f"❌ 채팅 실패: HTTP {response.status_code}")
                try:
                    error_detail = response.json().get('detail', 'Unknown error')
                except:
                    error_detail = response.text
                print(f"   📝 오류: {error_detail}")
                return False
                
        except requests.exceptions.Timeout:
            print("❌ 채팅 요청 시간 초과 (30초)")
            print("   💡 ChatGPT API 응답이 지연되었을 수 있습니다")
            return False
        except Exception as e:
            print(f"❌ 채팅 오류: {e}")
            return False

    def test_multiple_chat(self):
        """대화 맥락 유지 테스트"""
        print(f"\n🔄 대화 맥락 유지 테스트")
        
        if not self.auth_token:
            print("❌ 인증 토큰이 필요합니다. 먼저 로그인하세요.")
            return False
        
        messages = [
            "제 이름은 김수학입니다.",
            "2x + 5 = 15 방정식을 풀고 싶어요.",
            "제 이름이 뭐라고 했죠?"  # 맥락 유지 확인
        ]
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        for i, message in enumerate(messages, 1):
            print(f"   💬 대화 {i}: {message}")
            
            try:
                data = {"message": message}
                response = requests.post(f"{self.base_url}/chat", json=data, headers=headers, timeout=25)
                
                if response.status_code == 200:
                    result = response.json()
                    ai_response = result['response']
                    print(f"   🤖 응답 {i}: {ai_response[:60]}{'...' if len(ai_response) > 60 else ''}")
                    
                    # 대화 간 간격
                    if i < len(messages):
                        time.sleep(1)
                else:
                    print(f"   ❌ 대화 {i} 실패: HTTP {response.status_code}")
                    return False
                    
            except Exception as e:
                print(f"   ❌ 대화 {i} 오류: {e}")
                return False
        
        print("✅ 대화 맥락 유지 테스트 완료")
        return True

    def test_chat_history(self):
        """10) 채팅 기록 조회 테스트"""
        print(f"\n📜 채팅 기록 조회 테스트")
        
        if not self.auth_token:
            print("❌ 인증 토큰이 필요합니다. 먼저 로그인하세요.")
            return False
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        try:
            response = requests.get(f"{self.base_url}/chat-history", headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                chat_history = result.get('chat_history', [])
                print("✅ 채팅 기록 조회 성공")
                print(f"   📊 총 세션 수: {len(chat_history)}개")
                
                for i, session in enumerate(chat_history[:2]):  # 최근 2개 세션만 출력
                    message_count = len(session.get('messages', []))
                    created_at = session.get('created_at', 'Unknown')
                    print(f"   📝 세션 {i+1}: {message_count}개 메시지 (생성: {created_at[:19]})")
                
                return True
            else:
                print(f"❌ 채팅 기록 조회 실패: HTTP {response.status_code}")
                try:
                    error_detail = response.json().get('detail', 'Unknown error')
                except:
                    error_detail = response.text
                print(f"   📝 오류: {error_detail}")
                return False
                
        except Exception as e:
            print(f"❌ 채팅 기록 조회 오류: {e}")
            return False

    def test_unauthorized_access(self):
        """11) 인증 없이 접근 테스트"""
        print(f"\n🚫 비인증 접근 차단 테스트")
        
        # 토큰 없이 채팅 시도
        data = {"message": "안녕하세요"}
        
        try:
            response = requests.post(f"{self.base_url}/chat", json=data, timeout=10)
            
            if response.status_code == 403:  # Forbidden 예상
                print("✅ 비인증 접근 차단 성공")
                return True
            else:
                print(f"❌ 비인증 접근 차단 실패: HTTP {response.status_code}")
                print("   💡 인증 없이도 접근 가능한 상태입니다")
                return False
                
        except Exception as e:
            print(f"❌ 테스트 오류: {e}")
            return False

    def test_input_validation(self):
        """11) 입력 데이터 검증 테스트"""
        print(f"\n✅ 입력 데이터 검증 테스트")
        
        # 잘못된 회원가입 데이터
        invalid_data = [
            {
                "data": {"username": "ab", "email": "test@test.com", "password": "123456"},
                "name": "짧은 사용자명 (2자)"
            },
            {
                "data": {"username": "testuser", "email": "invalid-email", "password": "123456"},
                "name": "잘못된 이메일 형식"
            },
            {
                "data": {"username": "testuser", "email": "test@test.com", "password": "123"},
                "name": "짧은 비밀번호 (3자)"
            }
        ]
        
        for test_case in invalid_data:
            data = test_case["data"]
            test_name = test_case["name"]
            
            print(f"   🧪 테스트: {test_name}")
            
            try:
                response = requests.post(f"{self.base_url}/register", json=data, timeout=10)
                
                if response.status_code in [400, 422]:  # Bad Request 또는 Validation Error 예상
                    print(f"   ✅ {test_name} 검증 성공")
                else:
                    print(f"   ❌ {test_name} 검증 실패: HTTP {response.status_code}")
                    return False
                    
            except Exception as e:
                print(f"   ❌ {test_name} 테스트 오류: {e}")
                return False
        
        return True

    def run_all_tests(self):
        """모든 테스트 실행"""
        print("🚀 AI 수학 튜터 백엔드 전체 테스트 시작")
        print("=" * 60)
        
        test_results = []
        
        # 테스트 순서대로 실행
        tests = [
            ("서버 상태 확인", self.test_server_status),
            ("입력 데이터 검증", self.test_input_validation),
            ("회원가입", self.test_register),
            ("로그인", lambda: self.test_login(self.username)),
            ("수능 문제 조회", self.test_exam_question),
            ("잘못된 수능 문제 번호", self.test_invalid_exam_question),
            ("기본 채팅", self.test_chat),
            ("대화 맥락 유지", self.test_multiple_chat),
            ("채팅 기록 조회", self.test_chat_history),
            ("비인증 접근 차단", self.test_unauthorized_access),
        ]
        
        for test_name, test_func in tests:
            print(f"\n🔍 실행 중: {test_name}")
            
            try:
                start_time = time.time()
                result = test_func()
                end_time = time.time()
                duration = end_time - start_time
                
                test_results.append((test_name, result, duration))
                
                if result:
                    print(f"   ⏱️  소요 시간: {duration:.2f}초")
                else:
                    print(f"   ⚠️  {test_name} 테스트 실패")
                    break
                    
            except Exception as e:
                print(f"   ❌ {test_name} 테스트 실행 중 오류: {e}")
                test_results.append((test_name, False, 0))
                break
        
        # 결과 요약
        self.print_test_summary(test_results)
        
        passed = sum(1 for _, result, _ in test_results if result)
        total = len(test_results)
        
        return passed == total

    def print_test_summary(self, test_results):
        """테스트 결과 요약 출력"""
        print("\n" + "=" * 60)
        print("🏁 테스트 결과 요약")
        print("=" * 60)
        
        passed = sum(1 for _, result, _ in test_results if result)
        total = len(test_results)
        total_time = sum(duration for _, _, duration in test_results)
        
        for test_name, result, duration in test_results:
            status = "✅ 통과" if result else "❌ 실패"
            time_info = f" ({duration:.2f}초)" if duration > 0 else ""
            print(f"{test_name}: {status}{time_info}")
        
        print(f"\n📊 전체 통계:")
        print(f"   총 테스트: {total}개")
        print(f"   통과: {passed}개")
        print(f"   실패: {total - passed}개")
        print(f"   성공률: {passed/total*100:.1f}%")
        print(f"   총 소요 시간: {total_time:.2f}초")
        
        if passed == total:
            print("\n🎉 모든 테스트가 성공적으로 완료되었습니다!")
        else:
            print(f"\n⚠️  {total - passed}개의 테스트가 실패했습니다.")


def run_quick_test():
    """빠른 테스트 실행"""
    client = MathTutorTestClient()
    
    print("⚡ 백엔드 빠른 테스트 실행")
    print("=" * 40)
    
    # 서버 상태만 확인
    if client.test_server_status():
        print("\n🎉 백엔드 서버가 정상적으로 실행 중입니다!")
        
        # 간단한 기능 테스트
        if client.test_register():
            client.test_chat("간단한 수학 문제: 5 + 3 = ?")
    else:
        print("\n❌ 백엔드 서버가 실행되지 않았습니다.")
        print("💡 backend/main.py를 먼저 실행하세요:")
        print("   cd backend")
        print("   python main.py")


def run_performance_test():
    """11) 성능 테스트"""
    print("⚡ 백엔드 성능 테스트 실행")
    print("=" * 40)
    
    client = MathTutorTestClient()
    
    # 서버 상태 확인
    if not client.test_server_status():
        return
    
    # 로그인
    if not client.test_register():
        return
    
    # 연속 채팅 테스트
    messages = [
        "2x + 1 = 5를 풀어주세요",
        "3y - 2 = 10은 어떻게 풀까요?",
        "x^2 - 4 = 0을 인수분해해주세요",
        "피타고라스 정리를 설명해주세요",
        "일차함수의 기울기란 무엇인가요?"
    ]
    
    print(f"\n📊 연속 채팅 테스트 ({len(messages)}개 메시지)")
    
    start_time = time.time()
    success_count = 0
    
    for i, message in enumerate(messages, 1):
        print(f"   💬 메시지 {i}/{len(messages)}: {message[:30]}...")
        
        if client.test_chat(message):
            success_count += 1
        else:
            print("   ❌ 성능 테스트 중단")
            break
        
        # 서버 부하 방지를 위한 간격
        time.sleep(0.5)
    
    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"\n📈 성능 테스트 결과:")
    print(f"   성공한 메시지: {success_count}/{len(messages)}개")
    print(f"   총 처리 시간: {total_time:.2f}초")
    if success_count > 0:
        print(f"   평균 응답 시간: {total_time/success_count:.2f}초")
    print(f"   성공률: {success_count/len(messages)*100:.1f}%")


if __name__ == "__main__":
    # 환경 변수 확인
    if os.path.exists('.env'):
        print("💡 .env 파일이 감지되었습니다.")
    else:
        print("⚠️  .env 파일이 없습니다. backend/.env 파일을 생성하세요.")
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        if command == "quick":
            run_quick_test()
        elif command == "performance":
            run_performance_test()
        elif command in ["help", "-h", "--help"]:
            print("사용법:")
            print("  python test_client.py         - 전체 테스트 실행")
            print("  python test_client.py quick   - 빠른 테스트 (서버 상태만)")
            print("  python test_client.py performance - 성능 테스트")
            print("  python test_client.py help    - 도움말 표시")
        else:
            print(f"❌ 알 수 없는 명령어: {command}")
            print("help 명령어로 사용법을 확인하세요.")
    else:
        # 전체 테스트 실행
        client = MathTutorTestClient()
        success = client.run_all_tests()
        
        if success:
            print("\n🎉 모든 테스트가 성공적으로 완료되었습니다!")
            sys.exit(0)
        else:
            print("\n⚠️  일부 테스트가 실패했습니다. 로그를 확인해주세요.")
            sys.exit(1)