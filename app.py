import streamlit as st
from streamlit_chat import message
import google.generativeai as genai

# 상수 정의
DEFAULT_ROLE = ""
PAGE_ICON = "💬"
PAGE_TITLE = "나만의 프롬프트 기반 Gemini 챗봇"
MODEL_NAME = "gemini-1.5-flash"

def initialize_session_state():
    """세션 상태 초기화"""
    default_values = {
        'chat_history': [],
        'active_role': DEFAULT_ROLE
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
        
        # 역할 설정 적용
        if st.session_state['active_role']:
            try:
                chat.send_message(st.session_state['active_role'])
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

def update_role(new_role):
    """역할 업데이트 및 대화 초기화"""
    st.session_state['active_role'] = new_role
    st.session_state['chat_history'] = []  # 대화 기록 초기화

def display_chat_history():
    """채팅 히스토리 표시"""
    for i, chat in enumerate(st.session_state['chat_history']):
        message(
            chat["content"],
            is_user=chat["is_user"],
            key=f"chat_{i}"
        )

def display_role_status():
    """현재 설정된 역할 상태 표시"""
    if st.session_state['active_role']:
        st.markdown("---")
        st.markdown(f"🧠 **현재 역할:** {st.session_state['active_role']}")
        st.markdown("---")

def main():
    # 페이지 설정
    st.set_page_config(
        page_title=PAGE_TITLE,
        page_icon=PAGE_ICON,
        layout="wide"
    )
    
    # 세션 상태 초기화
    initialize_session_state()
    
    # Gemini 초기화
    if not initialize_gemini():
        st.warning("채팅 기능이 비활성화되었습니다. API 키를 확인해주세요.")
        st.stop()

    # 메인 타이틀
    st.title(f"{PAGE_ICON} {PAGE_TITLE}")
    st.markdown("이 챗봇은 사용자가 정한 역할에 따라 문맥을 기억하고 대화합니다.")
    
    # 현재 역할 표시
    display_role_status()
    
    # 사이드바 설정
    with st.sidebar:
        role_prompt = st.text_area(
            "챗봇의 역할을 입력하세요",
            placeholder="예: 당신은 영양학 전문가입니다. 사용자의 건강과 식단에 대해 조언해주세요.",
            height=200,
            key="role_input"
        )
        
        if st.button("프롬프트 적용"):
            if role_prompt:
                update_role(role_prompt)
                st.success("✅ 새로운 역할이 적용되었습니다!")
                st.info("💫 대화 기록이 초기화되었습니다.")
            else:
                st.warning("⚠️ 역할을 입력해주세요!")
    
    # 채팅 인터페이스
    chat_container = st.container()
    with chat_container:
        display_chat_history()
    
    # 사용자 입력 처리
    user_input = st.chat_input("메시지를 입력하세요")
    if user_input:
        try:
            # 사용자 메시지 추가
            st.session_state['chat_history'].append({
                "content": user_input,
                "is_user": True
            })
            
            # AI 응답 생성
            with st.spinner('답변을 생성하고 있습니다...'):
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

if __name__ == "__main__":
    main()
