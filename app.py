import streamlit as st
from streamlit_chat import message
import google.generativeai as genai

def initialize_gemini():
    """Gemini API 초기화 및 설정을 수행합니다."""
    try:
        if "GEMINI_API_KEY" not in st.secrets:
            st.error("❌ API 키가 설정되지 않았습니다.")
            st.markdown("""
            1. `.streamlit/secrets.toml` 파일을 열어주세요.
            2. `GEMINI_API_KEY = "your-api-key"` 형식으로 API 키를 추가해주세요.
            """)
            return None
            
        # Gemini API 설정
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        
        # 모델 초기화
        try:
            model = genai.GenerativeModel('gemini-1.5-pro')
            return model
        except Exception as e:
            st.error("❌ 모델 초기화 중 오류가 발생했습니다.")
            st.error(f"상세 오류: {str(e)}")
            return None
        
    except Exception as e:
        st.error("❌ API 설정 중 오류가 발생했습니다.")
        st.error(f"상세 오류: {str(e)}")
        return None

def initialize_session_state():
    """세션 상태 변수를 초기화합니다."""
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    if "current_role" not in st.session_state:
        st.session_state.current_role = None

def update_role(new_role):
    """챗봇의 역할을 업데이트하고 대화 기록을 초기화합니다."""
    if new_role:
        st.session_state.current_role = new_role
        st.session_state.chat_history = []  # 대화 기록 초기화
        return True
    return False

def get_gemini_response(model, role_prompt, messages):
    """Gemini API를 사용하여 응답을 생성합니다."""
    try:
        # 채팅 세션 시작
        chat = model.start_chat(history=[])
        
        # 역할 프롬프트를 시스템 메시지로 전송
        chat.send_message(f"당신은 다음과 같은 역할을 수행해야 합니다: {role_prompt}")
        
        # 이전 대화 기록 전송
        for msg in messages:
            content = msg["content"]
            # 사용자 메시지만 전송하여 컨텍스트 유지
            if msg["is_user"]:
                chat.send_message(content)
                
        # 최종 응답 생성
        response = chat.send_message(messages[-1]["content"])
        return response.text
        
    except Exception as e:
        st.error("❌ 답변 중 오류가 발생했습니다.")
        st.error(f"상세 오류: {str(e)}")
        return None

def display_chat_history():
    """채팅 기록을 화면에 표시합니다."""
    for i, chat in enumerate(st.session_state.chat_history):
        message(
            chat["content"],
            is_user=chat["is_user"],
            key=f"chat_{i}"
        )

def main():
    # 페이지 설정
    st.set_page_config(
        page_title="Gemini 챗봇",
        page_icon="💬",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # 제목과 설명
    st.title("💬 나만의 프롬프트 기반 Gemini 챗봇")
    st.markdown("이 챗봇은 사용자가 정한 역할에 따라 문맥을 기억하고 대화합니다.")

    # 세션 상태 초기화
    initialize_session_state()
    
    # Gemini 모델 초기화
    model = initialize_gemini()
    if not model:
        st.stop()

    # 사이드바 구성
    with st.sidebar:
        st.title("챗봇 설정")
        
        # 역할 입력
        role_input = st.text_area(
            "챗봇의 역할을 입력하세요",
            height=100,
            placeholder="예시: 당신은 친절한 영어 선생님입니다. 학생들의 질문에 자세히 답변해주세요.",
            key="role_input"
        )
        
        # 역할 적용 버튼
        if st.button("프롬프트 적용", type="primary"):
            if update_role(role_input):
                st.success("✅ 새로운 역할이 적용되었습니다!")
            else:
                st.error("❌ 역할을 입력해주세요!")

    # 메인 화면
    if st.session_state.current_role:
        # 현재 설정된 역할 표시
        st.markdown(f"🧠 **현재 역할:** {st.session_state.current_role}")
        
        # 채팅 기록 표시
        display_chat_history()
        
        # 채팅 입력
        user_input = st.chat_input("메시지를 입력하세요")
        
        if user_input:
            try:
                # 사용자 메시지를 채팅 기록에 추가
                st.session_state.chat_history.append({
                    "content": user_input,
                    "is_user": True
                })
                
                # Gemini API로 응답 생성
                with st.spinner("응답을 생성하고 있습니다..."):
                    ai_response = get_gemini_response(
                        model,
                        st.session_state.current_role,
                        st.session_state.chat_history
                    )
                    
                    if ai_response:
                        # AI 응답을 채팅 기록에 추가
                        st.session_state.chat_history.append({
                            "content": ai_response,
                            "is_user": False
                        })
                        
                # 채팅 기록이 업데이트되면 페이지 새로고침
                st.rerun()
                    
            except Exception as e:
                st.error("❌ 예상치 못한 오류가 발생했습니다.")
                st.error(f"상세 오류: {str(e)}")

    else:
        st.warning("👈 사이드바에서 챗봇의 역할을 설정해주세요.")

if __name__ == "__main__":
    main() 
