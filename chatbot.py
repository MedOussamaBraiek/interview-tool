import streamlit as st
import ollama
from streamlit_js_eval import streamlit_js_eval

st.set_page_config(page_title="Ollama Streaming Chat", page_icon=":speech_balloon:")
st.title("Chatbot")

if "setup_complete" not in st.session_state:
    st.session_state.setup_complete = False
if "user_message_count" not in st.session_state:
    st.session_state.user_message_count = 0
if "feedback_shown" not in st.session_state:
    st.session_state.feedback_shown = False
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_complete" not in st.session_state:
    st.session_state.chat_complete = False

def complete_setup():
    st.session_state.setup_complete = True

def show_feedback():
    st.session_state.feedback_shown = True

if not st.session_state.setup_complete:

    st.subheader("Personal Information", divider="rainbow")

    if "name" not in st.session_state:
        st.session_state["name"] = ""
    if "experience" not in st.session_state:
        st.session_state["experience"] = ""
    if "skills" not in st.session_state:
        st.session_state["skills"] = ""

    st.session_state["name"] = st.text_input(label="Name", placeholder="Enter your name", max_chars=40)

    st.session_state["experience"] = st.text_area(label="Experience", value = "", placeholder="Describe your experience", max_chars=200)

    st.session_state["skills"] = st.text_area(label="Skills", value = "", placeholder="List your skills", max_chars=200)


    st.subheader("Company and Position", divider="rainbow")

    if "level" not in st.session_state:
        st.session_state["level"] = "Junior"
    if "position" not in st.session_state:
        st.session_state["position"] = "Software Engineer"
    if "company" not in st.session_state:
        st.session_state["company"] = "Amazon"

    col1, col2 = st.columns(2)

    with col1:
        st.session_state["level"] = st.radio(
            label="Choose level",
            key="visibility",
            options=["Junior", "Mid-level", "Senior"],
        )

    with col2:
        st.session_state["position"] = st.selectbox(
            label="Choose position",
            options=["Software Engineer", "Data Scientist", "Data Engineer", "ML Engineer", "BI Analyst", "Financial Analyst"],
        )

    st.session_state["company"] = st.selectbox(
        "Choose company",
        options=[
            "Google",
            "Amazon",
            "Facebook",
            "Apple",
            "Microsoft",
            "Netflix",
        ],
    )


    if st.button("Start Interview", on_click=complete_setup):
        st.write("Setup complete! You can now start the interview.")

if  st.session_state.setup_complete and not st.session_state.feedback_shown and not st.session_state.chat_complete:

    st.info(
        """
        Start by introducing yourself.
        """,
        icon="👋",
    )

    if not st.session_state.messages: # Initialize messages with system prompt only once, when messages is empty
        st.session_state.messages = [{"role": "system", "content": f"You are an HR executive that interviews an interviewee called {st.session_state['name']} with experience {st.session_state['experience']} and skills {st.session_state['skills']}. You should interview them for the position {st.session_state['level']} {st.session_state['position']} at the company {st.session_state['company']}. "}]

    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.write(message["content"])

    if st.session_state.user_message_count < 5:
        if prompt := st.chat_input("Ask something...", max_chars=1000):
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            with st.chat_message("user"):
                st.write(prompt)

            if st.session_state.user_message_count < 4:
                with st.chat_message("assistant"):
                    message_placeholder = st.empty()
                    full_response = ""

                    stream = ollama.chat(
                        model="phi3",
                        messages=st.session_state.messages,
                        stream=True,
                    )

                    for chunk in stream:
                        content = chunk["message"]["content"]
                        full_response += content
                        message_placeholder.markdown(full_response)

                st.session_state.messages.append(
                    {"role": "assistant", "content": full_response}
                )
            
            st.session_state.user_message_count += 1

    if st.session_state.user_message_count >= 5:
        st.session_state.chat_complete = True
        

if st.session_state.chat_complete and not st.session_state.feedback_shown:
    if st.button("Get Feedback", on_click=show_feedback):
        st.write("Feedback shown!")

if st.session_state.feedback_shown:
    st.subheader("Feedback", divider="rainbow")
    
    conversation_history = "\n".join([f"{message['role']}: {message['content']}" for message in st.session_state.messages if message["role"] != "system"])

    feedback_prompt = f"""
    You are a helpful tool that provides feedback on an interviewee performance.
    Before the Feedback give a score or 1 to 10.
    Follow this format:
    Overal Score: //Your score
    \nFeedback: //Here you put your feedback
    Give only the feedback do not ask any additional questions.
"""

    feedback_completion = ollama.chat(
        model="phi3",
        messages=[
            {"role": "system", "content": feedback_prompt},
            {"role": "user", "content": f"This is the interview you need to evaluate. You are only a tool and shouldn't engage in conversation: {conversation_history}"},
        ],
    )

    st.write(feedback_completion["message"]["content"])

    if st.button("Restart Interview", type="primary"):
        streamlit_js_eval(js_expressions="parent.window.location.reload()")

  