import streamlit as st
from streamlit_chat import message
import google.generativeai as genai
import base64
from pathlib import Path

# 상수 정의
SYSTEM_ROLE = """당신은 친근하고 편안한 영양 전문가이자 식단 컨설턴트입니다. 
사용자와의 대화를 다음과 같이 진행해주세요:

1단계 - 최근 식사 분석:
- 사용자가 오늘 먹은 식사를 입력하면:
  • 대략적인 영양소 균형을 설명 (어떤 영양소가 부족해 보이는지 언급)
  • 부족한 영양소 보충을 위한 간단한 조언
  • 마지막에 다음 질문 중 하나를 빨간색으로 물어보기:
    "<span style='color: red'>오늘은 어떤 음식을 드시고 싶으신가요?</span>" 또는
    "<span style='color: red'>혹시 오늘 저녁으로 드시고 싶은 메뉴가 있으신가요?</span>"

2단계 - 메뉴 추천:
- 사용자가 먹고 싶은 음식들을 말하면:
  • 사용자의 건강 상태와 부족한 영양소를 함께 고려하여 추천
    (예: 빈혈이 있다면 철분이 풍부한 메뉴 우선 추천)
  • 사용자가 언급한 음식들 중에서만 선택하여 추천
  • 추천 이유를 다음과 같은 형식으로 설명:
    "~님의 (건강상태)를 고려했을 때, 말씀하신 메뉴들 중 ~메뉴가 가장 좋을 것 같아요"
  • 가장 추천하는 메뉴는 <span style='color: red'>메뉴이름</span> 형식으로 표시
  • 마지막에 건강 상태와 관련된 간단한 한 줄 조언 추가
    예시) "고혈압이 있으신 경우 된장찌개는 조금 싱겁게 드시는 게 좋아요 😊"
    예시) "빈혈이 있으시니 시금치는 레몬즙을 뿌려 드시면 철분 흡수가 더 잘될 거예요 👍"

주의사항:
- 절대로 사용자가 언급하지 않은 메뉴는 추천하지 않기
- 정확한 수치 대신 "~이 부족해 보여요", "~이 더 필요해 보여요" 같은 표현 사용
- 부담스럽지 않게 친근한 톤으로 대화하기
- 반드시 사용자가 말한 메뉴들 중에서만 선택하여 추천하기
- 건강 상태를 고려한 조언은 실용적이고 구체적으로, 하지만 부담스럽지 않게 하기"""

PAGE_ICON = "🐽"
PAGE_TITLE = "헬핏잇 - 부족한 영양소를 채우는 메뉴 추천 AI"
MODEL_NAME = "gemini-1.5-flash"

def get_base64_of_bin_file(bin_file):
    """이미지 파일을 base64로 인코딩"""
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_background(png_file):
    """배경 이미지 설정"""
    bin_str = get_base64_of_bin_file(png_file)
    page_bg_img = f'''
    <style>
    .stApp {{
        background-image: url("data:image/png;base64,{bin_str}");
        background-size: 90%;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
        background-color: #fff5f5;  /* 연한 분홍빛 배경색 */
    }}
    </style>
    '''
    st.markdown(page_bg_img, unsafe_allow_html=True)

def setup_page_style():
    """페이지 스타일 설정"""
    st.markdown(
        """
        <style>
        /* 최상단 헤더 스타일 */
        header[data-testid="stHeader"],
        .st-emotion-cache-18ni7ap,
        .st-emotion-cache-h5rgaw,
        header.st-emotion-cache-18ni7ap,
        .st-emotion-cache-1avcm0n,
        .st-emotion-cache-1cypcdb,
        .st-emotion-cache-1dp5vir,
        .st-emotion-cache-5rimss,
        .st-emotion-cache-1wbqy5l,
        .st-emotion-cache-pkbazv,
        .st-emotion-cache-1egp75f {
            background-color: transparent !important;
        }

        /* 최상단 데코레이션 라인 제거 */
        .st-emotion-cache-1rtdyuf,
        .st-emotion-cache-19rxjzo {
            display: none !important;
        }

        /* 최상단 메뉴 버튼 */
        .st-emotion-cache-1on073z,
        .st-emotion-cache-1lsqd8v button,
        .st-emotion-cache-pkbazv button {
            background-color: transparent !important;
        }

        /* 채팅 메시지 스타일 */
        .stChatMessage {
            background-color: rgba(255, 255, 255, 0.8) !important;
            border-radius: 15px !important;
            padding: 15px !important;
            margin: 5px 0 !important;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1) !important;
            border: 1px solid #ffe0e0 !important;
        }
        
        /* 사용자 메시지 */
        .stChatMessage[data-testid="user-message"] {
            background-color: rgba(255, 240, 240, 0.8) !important;
        }
        
        /* AI 메시지 */
        .stChatMessage[data-testid="assistant-message"] {
            background-color: rgba(255, 153, 153, 0.6) !important;  /* #ff9999 with higher opacity */
            border: 1px solid #ffcccc !important;
        }
        
        /* 채팅 입력창 스타일 */
        .stChatInputContainer {
            background-color: rgba(255, 255, 255, 0.8) !important;
            border-radius: 15px !important;
            padding: 10px !important;
            margin-top: 10px !important;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1) !important;
            border: 1px solid #ffe0e0 !important;
            backdrop-filter: blur(10px);
        }
        
        /* 타이틀 스타일 */
        .stTitle {
            color: #000000 !important;
            text-shadow: none !important;
        }

        /* 일반 텍스트 스타일 */
        .stMarkdown {
            color: #000000 !important;
            padding: 15px !important;
            border-radius: 10px !important;
            margin-bottom: 20px !important;
            background-color: rgba(255, 255, 255, 0.8) !important;
        }

        /* 버튼 스타일 */
        .stButton > button {
            background-color: #ff9999 !important;
            color: white !important;
            border: none !important;
            padding: 8px 16px !important;
            border-radius: 8px !important;
            font-weight: bold !important;
        }

        .stButton > button:hover {
            background-color: #ff8080 !important;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2) !important;
        }

        /* 커스텀 로딩 스피너 */
        .stSpinner {
            display: none !important;
        }
        
        .custom-spinner {
            display: flex;
            justify-content: center;
            align-items: center;
            margin: 20px 0;
            color: #000000;
            background-color: rgba(255, 255, 255, 0.8) !important;
            padding: 10px;
            border-radius: 10px;
        }
        
        .custom-spinner span {
            font-size: 24px;
            animation: bounce 1s infinite;
        }
        
        @keyframes bounce {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-10px); }
        }

        /* 추가 Streamlit 요소들 */
        div[data-testid="stToolbar"],
        div[data-testid="stDecoration"],
        div[data-testid="stHeader"],
        div[data-testid="stMarkdown"],
        div[data-testid="stBlock"],
        section[data-testid="stSidebar"] {
            background-color: transparent !important;
        }

        /* 스크롤바 영역 */
        ::-webkit-scrollbar-track {
            background-color: transparent !important;
        }

        /* iframe 배경 */
        iframe {
            background-color: transparent !important;
        }

        /* 최상단 햄버거 메뉴 아이콘 */
        button[kind="header"] {
            background-color: transparent !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def initialize_session_state():
    """세션 상태 초기화"""
    default_values = {
        'chat_history': [],
        'active_role': SYSTEM_ROLE,
        'health_condition': None  # 건강 상태를 저장할 변수 추가
    }
    
    for key, value in default_values.items():
        if key not in st.session_state:
            st.session_state[key] = value

def initialize_gemini():
    """Gemini API 초기화 및 설정"""
    try:
        # API 키 검증
        if 'GEMINI_API_KEY' not in st.secrets:
            st.error("❌ API 키가 설정되지 않았습니다. .streamlit/secrets.toml 파일에 GEMINI_API_KEY를 추가해주세요.")
            return False
        
        if not st.secrets['GEMINI_API_KEY']:
            st.error("❌ API 키가 비어 있습니다. 유효한 API 키를 입력해주세요.")
            return False

        # Gemini 설정
        genai.configure(api_key=st.secrets['GEMINI_API_KEY'])
        return True

    except Exception as e:
        st.error(f"❌ Gemini 초기화 중 오류가 발생했습니다: {str(e)}")
        return False

def get_gemini_response(messages):
    """Gemini 모델을 사용하여 응답을 생성하는 함수"""
    try:
        # 모델 인스턴스 생성
        model = genai.GenerativeModel(MODEL_NAME)
        chat = model.start_chat(history=[])
        
        # 시스템 역할 설정
        try:
            chat.send_message(SYSTEM_ROLE)
        except Exception as e:
            st.warning(f"⚠️ 역할 설정 중 오류가 발생했습니다: {str(e)}")
        
        # 대화 기록 전달
        for msg in messages:
            if msg["is_user"]:
                try:
                    chat.send_message(msg["content"])
                except Exception as e:
                    st.warning(f"⚠️ 대화 기록 처리 중 오류가 발생했습니다: {str(e)}")
                    continue
        
        # 응답 생성
        try:
            response = chat.send_message(messages[-1]["content"])
            return response.text
        except Exception as e:
            st.error("❌ 답변 생성 중 오류가 발생했습니다.")
            st.error(f"상세 오류: {str(e)}")
            return "죄송합니다. 답변을 생성하는 중에 문제가 발생했습니다. 다시 시도해 주세요."
        
    except Exception as e:
        st.error("❌ 답변 중 오류가 발생했습니다.")
        st.error(f"상세 오류: {str(e)}")
        return None

def display_chat_history():
    """채팅 히스토리 표시"""
    for i, chat in enumerate(st.session_state['chat_history']):
        message(
            chat["content"],
            is_user=chat["is_user"],
            key=f"chat_{i}",
            allow_html=True  # HTML 태그 허용
        )

def display_welcome_message():
    """시작 안내 메시지 표시"""
    st.markdown("""
    <div style='background-color: #f0f2f6; padding: 20px; border-radius: 10px; border: 1px solid #e0e2e6;'>
        <h3 style='color: #1E1E1E; margin-bottom: 15px;'>👋 안녕하세요!</h3>
        <p style='color: #2c3e50; font-size: 16px;'>먼저 아래에서 해당하는 건강 상태를 선택해주세요.</p>
        <p style='color: #2c3e50; font-size: 16px;'>그 다음 최근 드신 식사를 알려주시면 맞춤 영양 분석을 해드립니다.</p>
        <p style='color: #2c3e50; font-size: 16px;'>예시) 토스트, 김치찌개, 치킨을 먹었어.</p>
    </div>
    """, unsafe_allow_html=True)

def custom_spinner(text="답변을 생성하고 있습니다..."):
    """커스텀 로딩 스피너"""
    return st.markdown(f"""
        <div class="custom-spinner">
            <span>🐽</span>
            <span style="margin-left: 10px;">{text}</span>
        </div>
    """, unsafe_allow_html=True)

def main():
    # 페이지 설정
    st.set_page_config(
        page_title=PAGE_TITLE,
        page_icon=PAGE_ICON,
        layout="wide"
    )
    
    # 배경 이미지 설정
    set_background('bg_pig.png')
    
    # 페이지 스타일 설정
    setup_page_style()
    
    # 세션 상태 초기화
    initialize_session_state()
    
    # Gemini 초기화
    if not initialize_gemini():
        st.warning("채팅 기능이 비활성화되었습니다. API 키를 확인해주세요.")
        st.stop()

    # 메인 타이틀
    st.title(f"{PAGE_ICON} {PAGE_TITLE}")
    
    # 새로운 대화 시작 버튼
    if st.button("새로운 대화 시작"):
        st.session_state['chat_history'] = []
        st.session_state['health_condition'] = None  # 건강 상태도 초기화
        st.rerun()
    
    # 건강 상태 선택
    if not st.session_state['health_condition']:
        health_condition = st.selectbox(
            "현재 해당하는 건강 상태를 선택해주세요:",
            ["선택해주세요", "이상 없음", "당뇨", "빈혈", "고혈압", "비만"],
            index=0
        )
        if health_condition != "선택해주세요":
            st.session_state['health_condition'] = health_condition
            st.rerun()
    else:
        st.info(f"현재 선택된 건강 상태: {st.session_state['health_condition']}")
    
    # 시작 안내 메시지 (채팅 기록이 없을 때만 표시)
    if not st.session_state['chat_history']:
        display_welcome_message()
    
    # 채팅 인터페이스
    chat_container = st.container()
    with chat_container:
        display_chat_history()
    
    # 사용자 입력 처리 (건강 상태가 선택된 경우에만 활성화)
    if st.session_state['health_condition']:
        user_input = st.chat_input("메시지를 입력하세요")
        if user_input:
            try:
                # 사용자 메시지 추가
                st.session_state['chat_history'].append({
                    "content": user_input,
                    "is_user": True
                })
                
                # AI 응답 생성
                with custom_spinner():
                    ai_response = get_gemini_response(st.session_state['chat_history'])
                
                if ai_response:
                    st.session_state['chat_history'].append({
                        "content": ai_response,
                        "is_user": False
                    })
                
                st.rerun()
                
            except Exception as e:
                st.error("❌ 예상치 못한 오류가 발생했습니다.")
                st.error(f"상세 오류: {str(e)}")
    else:
        st.warning("대화를 시작하기 전에 먼저 건강 상태를 선택해주세요.")

if __name__ == "__main__":
    main()
