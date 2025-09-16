// AI 수학 튜터 프론트엔드 JavaScript - 수정된 버전
// LaTeX 제거 및 수능 문제 처리 개선

// API 기본 URL (환경별로 변경 필요)
const API_BASE_URL = 'http://localhost:8000';

// 전역 변수
let authToken = localStorage.getItem('authToken');
let currentUser = localStorage.getItem('currentUser');
let uploadedImageData = null;
let uploadedImageUrl = null;

/**
 * 페이지 로드 시 초기화
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('AI 수학 튜터 초기화 시작');
    
    // Enter키 입력 지원
    const chatInput = document.getElementById('chatInput');
    if (chatInput) {
        chatInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        // 자동 높이 조절
        chatInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = this.scrollHeight + 'px';
        });
    }

    // 로그인 상태 확인
    if (authToken && currentUser) {
        showChatInterface();
        loadChatHistory();
    }
    
    // 수학 기호 애니메이션 시작
    startMathSymbolsAnimation();
    
    console.log('초기화 완료');
});

/**
 * 수학 기호 애니메이션
 */
function startMathSymbolsAnimation() {
    const symbols = ['∑', '∫', 'π', '∞', '√', '±', '×', '÷', '∆', 'α', 'β', 'θ', 'λ', 'μ', 'σ', 'Ω'];
    const container = document.querySelector('.chat-messages');
    
    if (!container) return;
    
    setInterval(() => {
        // 랜덤 수학 기호 선택
        const symbol = symbols[Math.floor(Math.random() * symbols.length)];
        
        // 기호 요소 생성
        const symbolEl = document.createElement('div');
        symbolEl.textContent = symbol;
        symbolEl.className = 'floating-symbol';
        symbolEl.style.cssText = `
            position: absolute;
            font-size: ${20 + Math.random() * 30}px;
            color: rgba(253, 203, 110, 0.3);
            pointer-events: none;
            z-index: 1;
            left: ${Math.random() * 90}%;
            top: ${Math.random() * 90}%;
            animation: float-symbol 4s ease-in-out forwards;
        `;
        
        container.appendChild(symbolEl);
        
        // 4초 후 제거
        setTimeout(() => {
            if (symbolEl.parentNode) {
                symbolEl.parentNode.removeChild(symbolEl);
            }
        }, 4000);
    }, 3000); // 3초마다 새 기호 생성
}

/**
 * LaTeX 수식을 일반 텍스트로 변환
 */
function convertLatexToText(text) {
    // LaTeX 수식 패턴들을 일반 텍스트로 변환
    let converted = text;
    
    // 인라인 수식 \\( ... \\) 제거
    converted = converted.replace(/\\\((.*?)\\\)/g, '$1');
    
    // 블록 수식 \\[ ... \\] 제거
    converted = converted.replace(/\\\[(.*?)\\\]/g, '$1');
    
    // $$ ... $$ 제거
    converted = converted.replace(/\$\$(.*?)\$\$/g, '$1');
    
    // $ ... $ 제거
    converted = converted.replace(/\$(.*?)\$/g, '$1');
    
    // 일반적인 LaTeX 명령어들을 텍스트로 변환
    const latexReplacements = {
        '\\frac{(.+?)}{(.+?)}': '($1)/($2)',
        '\\sqrt{(.+?)}': 'sqrt($1)',
        '\\left\\(': '(',
        '\\right\\)': ')',
        '\\left\\[': '[',
        '\\right\\]': ']',
        '\\times': '×',
        '\\div': '÷',
        '\\pm': '±',
        '\\infty': '∞',
        '\\pi': 'π',
        '\\alpha': 'α',
        '\\beta': 'β',
        '\\theta': 'θ',
        '\\lambda': 'λ',
        '\\mu': 'μ',
        '\\sigma': 'σ',
        '\\Omega': 'Ω',
        '\\Delta': '∆',
        '\\ ': ' ',
    };
    
    for (let [latex, replacement] of Object.entries(latexReplacements)) {
        const regex = new RegExp(latex, 'g');
        converted = converted.replace(regex, replacement);
    }
    
    return converted;
}

/**
 * 마크다운 스타일을 HTML로 변환 (# 제목 대신 CSS 스타일 사용)
 */
function convertMarkdownToHtml(text) {
    let converted = convertLatexToText(text);
    
    // ### 제목을 강조 텍스트로 변환
    converted = converted.replace(/^### (.+)$/gm, '<div class="section-title">$1</div>');
    converted = converted.replace(/^## (.+)$/gm, '<div class="main-title">$1</div>');
    converted = converted.replace(/^# (.+)$/gm, '<div class="main-title">$1</div>');
    
    // **볼드** 텍스트
    converted = converted.replace(/\*\*(.+?)\*\*/g, '<span class="bold-text">$1</span>');
    
    // *이탤릭* 텍스트
    converted = converted.replace(/\*(.+?)\*/g, '<span class="italic-text">$1</span>');
    
    // 줄바꿈 처리
    converted = converted.replace(/\n/g, '<br>');
    
    return converted;
}

/**
 * 회원가입 함수
 */
async function register() {
    console.log('회원가입 함수 호출됨');
    
    const username = document.getElementById('registerUsername').value.trim();
    const email = document.getElementById('registerEmail').value.trim();
    const password = document.getElementById('registerPassword').value;

    console.log('회원가입 시도:', username);

    if (!username || username.length < 3) {
        showError('사용자명은 3자 이상이어야 합니다.');
        return;
    }

    if (!email || !email.includes('@')) {
        showError('올바른 이메일 주소를 입력해주세요.');
        return;
    }

    if (!password || password.length < 6) {
        showError('비밀번호는 6자 이상이어야 합니다.');
        return;
    }

    try {
        console.log('API 요청 전송 중...');
        
        const response = await fetch(`${API_BASE_URL}/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: username,
                email: email,
                password: password
            })
        });

        console.log('API 응답 상태:', response.status);
        const data = await response.json();

        if (response.ok) {
            authToken = data.access_token;
            currentUser = username;
            
            localStorage.setItem('authToken', authToken);
            localStorage.setItem('currentUser', currentUser);
            
            showChatInterface();
            clearAuthForms();
            showError('회원가입이 완료되었습니다!', 'success');
            console.log('회원가입 성공:', username);
        } else {
            showError(data.detail || '회원가입에 실패했습니다.');
            console.error('회원가입 실패:', data.detail);
        }
    } catch (error) {
        console.error('Register error:', error);
        showError('네트워크 오류가 발생했습니다. 서버가 실행 중인지 확인해주세요.');
    }
}

/**
 * 로그인 함수
 */
async function login() {
    const username = document.getElementById('loginUsername').value.trim();
    const password = document.getElementById('loginPassword').value;

    console.log('로그인 시도:', username);

    if (!username || !password) {
        showError('사용자명과 비밀번호를 입력해주세요.');
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: username,
                password: password
            })
        });

        const data = await response.json();

        if (response.ok) {
            authToken = data.access_token;
            currentUser = username;
            
            localStorage.setItem('authToken', authToken);
            localStorage.setItem('currentUser', currentUser);
            
            showChatInterface();
            clearAuthForms();
            loadChatHistory();
            showError('로그인되었습니다!', 'success');
            console.log('로그인 성공:', username);
        } else {
            showError(data.detail || '로그인에 실패했습니다.');
            console.error('로그인 실패:', data.detail);
        }
    } catch (error) {
        console.error('Login error:', error);
        showError('네트워크 오류가 발생했습니다. 서버가 실행 중인지 확인해주세요.');
    }
}

/**
 * 로그아웃 함수
 */
function logout() {
    console.log('로그아웃:', currentUser);
    
    authToken = null;
    currentUser = null;
    uploadedImageData = null;
    uploadedImageUrl = null;
    localStorage.removeItem('authToken');
    localStorage.removeItem('currentUser');
    
    showAuthInterface();
    clearChatMessages();
    showError('로그아웃되었습니다.', 'success');
}

/**
 * 인터페이스 표시/숨김 함수들
 */
function showChatInterface() {
    const authSection = document.getElementById('authSection');
    const examButton = document.getElementById('examButton');
    const chatContainer = document.getElementById('chatContainer');
    const userInfo = document.getElementById('userInfo');
    const welcomeUser = document.getElementById('welcomeUser');

    if (authSection) authSection.classList.add('hidden');
    if (examButton) examButton.classList.remove('hidden');
    if (chatContainer) chatContainer.style.display = 'block';
    if (userInfo) userInfo.style.display = 'block';
    if (welcomeUser) welcomeUser.textContent = `환영합니다, ${currentUser}님!`;
}

function showAuthInterface() {
    const authSection = document.getElementById('authSection');
    const examButton = document.getElementById('examButton');
    const chatContainer = document.getElementById('chatContainer');
    const userInfo = document.getElementById('userInfo');

    if (authSection) authSection.classList.remove('hidden');
    if (examButton) examButton.classList.add('hidden');
    if (chatContainer) chatContainer.style.display = 'none';
    if (userInfo) userInfo.style.display = 'none';
}

/**
 * '2025년 수능 기출문제' 버튼 기능
 */
function showExamPrompt() {
    console.log('수능 기출문제 버튼 클릭');
    
    const message = "2025년 수능 수학 기출문제 중 풀이가 궁금한 문제의 번호를 입력하세요.(1~30 사이 자연수 한 개)";
    addMessage('assistant', message);
    
    const chatInput = document.getElementById('chatInput');
    if (chatInput) {
        chatInput.setAttribute('data-exam-mode', 'true');
        chatInput.focus();
    }
}

/**
 * 메시지 전송 함수
 */
async function sendMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();

    if (!message && !uploadedImageData) {
        return;
    }

    if (!authToken) {
        showError('로그인이 필요합니다.');
        return;
    }

    console.log('메시지 전송:', message.substring(0, 50) + '...');

    const sendBtn = document.getElementById('sendBtn');
    input.disabled = true;
    sendBtn.disabled = true;

    const isExamMode = input.getAttribute('data-exam-mode') === 'true';
    
    if (isExamMode) {
        await handleExamQuestion(message, input, sendBtn);
        return;
    }

    // 이미지와 메시지 함께 표시
    if (uploadedImageData) {
        addMessageWithImage('user', message, uploadedImageUrl);
    } else {
        addMessage('user', message);
    }

    input.value = '';
    input.style.height = 'auto';
    showLoading(true);

    try {
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({
                message: message || "이 수학 문제를 단계별로 풀어주세요.",
                image_data: uploadedImageData
            })
        });

        const data = await response.json();

        if (response.ok) {
            addMessage('assistant', data.response);
            console.log('AI 응답 받음');
        } else {
            if (response.status === 401) {
                logout();
                showError('로그인이 만료되었습니다. 다시 로그인해주세요.');
            } else {
                showError(data.detail || '메시지 전송에 실패했습니다.');
            }
        }
    } catch (error) {
        console.error('Send message error:', error);
        showError('네트워크 오류가 발생했습니다. 서버 연결을 확인해주세요.');
    } finally {
        showLoading(false);
        input.disabled = false;
        sendBtn.disabled = false;
        // 이미지 데이터 초기화
        uploadedImageData = null;
        uploadedImageUrl = null;
    }
}

/**
 * 이미지만으로 자동 전송
 */
async function sendImageMessage() {
    if (!uploadedImageData || !authToken) {
        return;
    }

    console.log('이미지 자동 전송 시작');
    
    showLoading(true);

    try {
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({
                message: "이 수학 문제를 단계별로 풀어주세요.",
                image_data: uploadedImageData
            })
        });

        const data = await response.json();

        if (response.ok) {
            addMessage('assistant', data.response);
            console.log('이미지 기반 AI 응답 받음');
        } else {
            if (response.status === 401) {
                logout();
                showError('로그인이 만료되었습니다. 다시 로그인해주세요.');
            } else {
                showError(data.detail || '이미지 분석에 실패했습니다.');
            }
        }
    } catch (error) {
        console.error('Image message error:', error);
        showError('네트워크 오류가 발생했습니다.');
    } finally {
        showLoading(false);
        // 이미지 데이터 초기화
        uploadedImageData = null;
        uploadedImageUrl = null;
    }
}

/**
 * 수능 기출문제 처리 (수정된 버전)
 */
async function handleExamQuestion(message, input, sendBtn) {
    const questionNumber = parseInt(message);
    
    console.log('수능 문제 번호:', questionNumber);
    
    if (isNaN(questionNumber) || questionNumber < 1 || questionNumber > 30) {
        addMessage('assistant', "1~30 사이 자연수 한 개를 입력하세요.");
        input.disabled = false;
        sendBtn.disabled = false;
        return;
    }

    addMessage('user', message);
    showLoading(true);

    try {
        const response = await fetch(`${API_BASE_URL}/exam-question`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({
                question_number: questionNumber
            })
        });

        const data = await response.json();

        if (response.ok) {
            // 문제 정보를 포맷팅하여 표시
            let questionDisplay = `📚 ${questionNumber}번 수능 문제\n\n`;
            questionDisplay += `🔗 주제: ${data.topic || '수학'}\n`;
            questionDisplay += `⭐ 난이도: ${data.difficulty || 1}/5\n\n`;
            questionDisplay += `📝 문제:\n${data.question_text}\n\n`;
            
            // 이미지가 있다면 추가 처리
            if (data.question_image) {
                const imageUrl = `data:image/png;base64,${data.question_image}`;
                addMessageWithImage('assistant', questionDisplay, imageUrl);
            } else {
                addMessage('assistant', questionDisplay);
            }
            
            // 안내 메시지 추가
            setTimeout(() => {
                const guideMessage = data.message || "문제를 확인하신 후, 어떤 부분부터 시작하면 좋을지 물어보세요!";
                addMessage('assistant', guideMessage);
            }, 500);
            
        } else {
            showError(data.detail || '문제를 불러오는데 실패했습니다.');
        }
    } catch (error) {
        console.error('Exam question error:', error);
        showError('네트워크 오류가 발생했습니다.');
    }

    showLoading(false);
    input.removeAttribute('data-exam-mode');
    input.value = '';
    input.disabled = false;
    sendBtn.disabled = false;
}

/**
 * 메시지 화면 출력 기능 (개선된 버전)
 */
function addMessage(role, content) {
    const messagesContainer = document.getElementById('chatMessages');
    
    if (!messagesContainer) {
        console.error('Messages container not found');
        return;
    }

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    const bubbleDiv = document.createElement('div');
    bubbleDiv.className = 'message-bubble';
    
    // LaTeX 제거 및 마크다운을 HTML로 변환
    const processedContent = convertMarkdownToHtml(content);
    bubbleDiv.innerHTML = processedContent;

    messageDiv.appendChild(bubbleDiv);
    messagesContainer.appendChild(messageDiv);

    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    console.log(`메시지 추가됨: ${role} - ${content.substring(0, 30)}...`);
    
    // 메시지 애니메이션
    messageDiv.style.opacity = '0';
    messageDiv.style.transform = 'translateY(20px)';
    
    setTimeout(() => {
        messageDiv.style.transition = 'all 0.3s ease';
        messageDiv.style.opacity = '1';
        messageDiv.style.transform = 'translateY(0)';
    }, 100);
}

/**
 * 이미지와 함께 메시지 표시
 */
function addMessageWithImage(role, content, imageUrl) {
    const messagesContainer = document.getElementById('chatMessages');
    
    if (!messagesContainer) {
        console.error('Messages container not found');
        return;
    }

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    const bubbleDiv = document.createElement('div');
    bubbleDiv.className = 'message-bubble';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    // 이미지 추가
    if (imageUrl) {
        const img = document.createElement('img');
        img.src = imageUrl;
        img.className = 'message-image';
        img.alt = '업로드된 수학 문제 이미지';
        img.onclick = () => openImageModal(imageUrl);
        contentDiv.appendChild(img);
    }

    // 텍스트 추가
    if (content) {
        const textDiv = document.createElement('div');
        const processedContent = convertMarkdownToHtml(content);
        textDiv.innerHTML = processedContent;
        contentDiv.appendChild(textDiv);
    }

    bubbleDiv.appendChild(contentDiv);
    messageDiv.appendChild(bubbleDiv);
    messagesContainer.appendChild(messageDiv);

    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    console.log(`이미지 메시지 추가됨: ${role}`);
}

/**
 * 이미지 모달 열기 (클릭시 확대)
 */
function openImageModal(imageUrl) {
    const modal = document.createElement('div');
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.8);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 1000;
        cursor: pointer;
    `;

    const img = document.createElement('img');
    img.src = imageUrl;
    img.style.cssText = `
        max-width: 90%;
        max-height: 90%;
        border-radius: 10px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
    `;

    modal.appendChild(img);
    document.body.appendChild(modal);

    modal.onclick = () => {
        document.body.removeChild(modal);
    };
}

/**
 * 이미지 업로드 처리
 */
function handleImageUpload() {
    const input = document.getElementById('imageUpload');
    const file = input.files[0];

    if (file) {
        console.log('수학 문제 이미지 업로드:', file.name);
        
        // 파일 크기 검증 (5MB 제한)
        if (file.size > 5 * 1024 * 1024) {
            showError('이미지 파일 크기는 5MB 이하여야 합니다.');
            input.value = '';
            return;
        }

        // 파일 타입 검증
        if (!file.type.startsWith('image/')) {
            showError('이미지 파일만 업로드 가능합니다.');
            input.value = '';
            return;
        }

        const reader = new FileReader();
        reader.onload = function(e) {
            uploadedImageData = e.target.result.split(',')[1]; // base64 데이터
            uploadedImageUrl = e.target.result; // 전체 data URL
            
            // 즉시 대화창에 이미지 표시
            addMessageWithImage('user', '', uploadedImageUrl);
            
            // 성공 메시지 표시
            showError(`수학 문제 이미지를 분석하고 있습니다...`, 'success');
            
            // 자동으로 AI에게 전송
            setTimeout(() => {
                sendImageMessage();
            }, 1000);
            
            console.log('이미지 업로드 및 표시 완료');
        };
        
        reader.onerror = function() {
            showError('이미지 읽기에 실패했습니다.');
            input.value = '';
        };
        
        reader.readAsDataURL(file);
        
        // 파일 입력 초기화
        input.value = '';
    }
}

/**
 * 채팅 기록 불러오기
 */
async function loadChatHistory() {
    if (!authToken) return;

    console.log('채팅 기록 로드 중...');

    try {
        const response = await fetch(`${API_BASE_URL}/chat-history`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        const data = await response.json();

        if (response.ok && data.chat_history.length > 0) {
            clearChatMessages();
            
            const latestSession = data.chat_history[0];
            const recentMessages = latestSession.messages.slice(-20);
            
            recentMessages.forEach(msg => {
                addMessage(msg.role, msg.content);
            });
            
            console.log(`채팅 기록 로드 완료: ${recentMessages.length}개 메시지`);
        }
    } catch (error) {
        console.error('Load chat history error:', error);
    }
}

/**
 * 로딩 상태 표시/숨김
 */
function showLoading(show) {
    const loadingIndicator = document.getElementById('loadingIndicator');
    if (loadingIndicator) {
        loadingIndicator.style.display = show ? 'block' : 'none';
    }
}

/**
 * 에러 메시지 표시
 */
function showError(message, type = 'error') {
    const errorDiv = document.getElementById('errorMessage');
    if (!errorDiv) return;

    errorDiv.textContent = message;
    errorDiv.className = `error-message ${type === 'success' ? 'success-message' : ''}`;
    errorDiv.classList.remove('hidden');
    
    console.log(`${type.toUpperCase()}: ${message}`);

    setTimeout(() => {
        errorDiv.classList.add('hidden');
    }, 3000);
}

/**
 * 폼 초기화
 */
function clearAuthForms() {
    const fields = [
        'loginUsername', 'loginPassword',
        'registerUsername', 'registerEmail', 'registerPassword'
    ];
    
    fields.forEach(fieldId => {
        const field = document.getElementById(fieldId);
        if (field) field.value = '';
    });
}

/**
 * 채팅 메시지 초기화
 */
function clearChatMessages() {
    const messagesContainer = document.getElementById('chatMessages');
    if (messagesContainer) {
        messagesContainer.innerHTML = '';
    }
}

console.log('AI 수학 튜터 JavaScript 로드 완료');