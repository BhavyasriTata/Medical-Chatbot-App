import os
import streamlit as st
import datetime
import requests
import altair as alt
import pandas as pd

# ------------------------------
# CONFIG
# ------------------------------

st.set_page_config(page_title="Digital Mental Health Support", layout="wide")

# IMPORTANT: Replace with your actual Hugging Face API Key
# You can get one here: https://huggingface.co/settings/tokens
HF_API_KEY = "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" 

headers = {"Authorization": f"Bearer {HF_API_KEY}"}

# ------------------------------
# APP SECTIONS
# ------------------------------
menu = ["AI Chatbot", "Book a Session", "Resources", "Peer Support Forum", "Admin Dashboard"]
choice = st.sidebar.radio("Navigate", menu)

# ------------------------------
# 1. AI CHATBOT (UPGRADED)
# ------------------------------
# if choice == "AI Chatbot":
#     st.title("🤖 AI-Guided First Aid Chatbot")
#     st.write(
#         "A confidential space to explore your feelings. Please note this is "
#         "*not a substitute for professional therapy*."
#     )

#     # Use a better, conversational model
#     API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"

#     # Define the chatbot's persona and instructions
#     SYSTEM_PROMPT = """You are 'Aura', a caring and empathetic AI mental health companion. Your purpose is to provide a safe, non-judgmental space for users to express their feelings.

# Your core principles are:
# 1.  *Empathy and Validation:* Always validate the user's feelings. Use phrases like "That sounds incredibly difficult," "It makes sense that you would feel that way," or "Thank you for sharing that with me."
# 2.  *Active Listening:* Ask thoughtful, open-ended questions to encourage the user to explore their feelings. For example, "How has that been affecting you?" or "What's on your mind when you feel that way?"
# 3.  *Gentle Guidance:* You can suggest simple, evidence-based coping strategies (like deep breathing, grounding, or journaling) but NEVER present them as a cure. Introduce them gently.
# 4.  *Safety First:* You are NOT a therapist. Do not give medical advice.
# 5.  *Maintain Persona:* Always be calm, supportive, and kind. Keep your responses concise.
# """
    
    # Updated query function for conversational models
    #
# REPLACE the old query_hf_conversational function with this one
#
if choice == "AI Chatbot":
    st.title("🤖 AI-Guided First Aid Chatbot")
    st.write(
        "A confidential space to explore your feelings. Please note this is "
        "*not a substitute for professional therapy*."
    )

    API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"

    SYSTEM_PROMPT = """You are 'Aura', a caring and empathetic AI mental health companion..."""

    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    user_input = st.chat_input("How are you feeling today?")

    if user_input:
        ...
    # Display chat history
    for msg in st.session_state.chat_history:
        ...
        
# ------------------------------
# Place the function OUTSIDE the if-block
# ------------------------------
def query_hf_conversational(history):
    prompt_messages = []
    for msg in history:
        role = "user" if msg["role"] == "user" else "assistant"
        prompt_messages.append({"role": role, "content": msg["text"]})
    
    formatted_prompt = ""
    for message in prompt_messages:
        if message["role"] == "user":
            formatted_prompt += f"[INST] {message['content']} [/INST]"
        else:
            formatted_prompt += f"{message['content']} "

    payload = {
        "inputs": formatted_prompt,
        "parameters": {"max_new_tokens": 250, "temperature": 0.7, "return_full_text": False}
    }

    try:
        resp = requests.post(API_URL, headers=headers, json=payload, timeout=45)
        resp.raise_for_status()
        return resp.json()[0]['generated_text']
    except Exception as e:
        st.error(f"API error: {e}")
        return None

    #




    # Initialize chat history
    # if "chat_history" not in st.session_state:
    #     st.session_state["chat_history"] = []

    # user_input = st.chat_input("How are you feeling today?")

    # if user_input:
    #     user_text = user_input.strip()
    #     st.session_state.chat_history.append({"role": "user", "text": user_text})

    #     # Safety-first rule-based check
    #     lowered = user_text.lower()
    #     crisis_terms = ["suicide", "kill myself", "end my life", "want to die", "hurt myself"]
    #     if any(term in lowered for term in crisis_terms):
    #         bot_reply = (
    #             "⚠ It sounds like you are in significant distress. Your safety is the most important thing. "
    #             "Please reach out for immediate help. You are not alone.\n\n"
    #             "📞 *National Suicide Prevention Lifeline (India):* 9152987821\n"
    #             "📞 *KIRAN Mental Health Helpline:* 1800-599-0019\n\n"
    #             "If you are in immediate danger, please call your local emergency services."
    #         )
    #     else:
    #         history_for_api = [{"role": "user", "text": SYSTEM_PROMPT}] + st.session_state.chat_history
            
    #         with st.spinner("Aura is thinking..."):

    #             bot_reply_text = query_hf_conversational(history_for_api)

    #         if bot_reply_text:
    #             bot_reply = bot_reply_text
    #         else:
    #             bot_reply = "I'm sorry, I'm having a little trouble connecting right now. Please know that I'm here to listen."

    #     st.session_state.chat_history.append({"role": "bot", "text": bot_reply})

    # # Display chat history
    # for msg in st.session_state.chat_history:
    #     with st.chat_message("user" if msg["role"] == "user" else "assistant", avatar="👤" if msg["role"] == "user" else "🤖"):
    #         st.markdown(msg["text"])

# ------------------------------
# 2. BOOKING SYSTEM
# ------------------------------
elif choice == "Book a Session":
    st.title("📅 Confidential Counselling Booking")

    name = st.text_input("Your Name (Optional — kept confidential)")
    date = st.date_input("Choose a Date", min_value=datetime.date.today())
    time_selected = st.time_input("Choose a Time", datetime.time(15, 0))
    if st.button("Book Appointment"):
        st.success(f"✅ Appointment booked for {name or 'Anonymous'} on {date} at {time_selected}")

# ------------------------------
# 3. RESOURCES HUB
# ------------------------------
elif choice == "Resources":
    st.title("🎧 Mental Health Resources")

    resource_type = st.radio("Choose Resource Type", ["Videos", "Audios", "Texts"])

    if resource_type == "Videos":
        st.video("https://www.youtube.com/watch?v=1vx8iUvfyCY")  # Example meditation video
    elif resource_type == "Audios":
        st.audio("https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3")
    elif resource_type == "Texts":
        st.download_button(
            "📥 Download Wellness Guide (TXT)",
            data="""  Self-care means taking the time to do things that help you live well and improve both your physical health and mental health. This can help you manage stress, lower your risk of illness, and increase your energy. Even small acts of self-care in your daily life can have a big impact.

Here are some self-care tips:

⦁	Get regular exercise. Just 30 minutes of walking every day can boost your mood and improve your health.
⦁	Small amounts of exercise add up, so do not be discouraged if you can not do 30 minutes at one time.
⦁	Eat healthy, regular meals and stay hydrated.
⦁	A balanced diet and plenty of water can improve your energy and focus throughout the day.
⦁	Pay attention to your intake of caffeine and alcohol and how they affect your mood and well-being—for some, decreasing caffeine and alcohol consumption can be helpful.
⦁	Make sleep a priority.
⦁	Stick to a schedule, and make sure you are getting enough sleep.
⦁	Blue light from devices and screens can make it harder to fall asleep, so reduce blue light exposure from your phone or computer before bedtime.
⦁	Try a relaxing activity.
⦁	Explore relaxation or wellness programs or apps, which may incorporate meditation, muscle relaxation, or breathing exercises.
⦁	Schedule regular times for these and other healthy activities you enjoy, such as listening to music, reading, spending time in nature, and engaging in low-stress hobbies.
⦁	Set goals and priorities.
⦁	Decide what must get done now and what can wait. Learn to say NO to new tasks if you start to feel like you are taking on too much.
⦁	Try to appreciate what you have accomplished at the end of the day.
⦁	Practice gratitude.
⦁	Remind yourself daily of things you are grateful for.
⦁	Be specific.
⦁	Write them down or replay them in your mind.
⦁	Focus on positivity.
⦁	Identify and challenge your negative and unhelpful thoughts.
⦁	Stay connected.
⦁	Reach out to friends or family members who can provide emotional support and practical help.
⦁	Self-care looks different for everyone, and it is important to find what you need and enjoy.
⦁	It may take trial and error to discover what works best for you.  """,
            file_name="wellness_guide.txt",
        )

    if "plays" not in st.session_state:
        st.session_state["plays"] = 0
    if st.button("Mark as Viewed/Played"):
        st.session_state["plays"] += 1
        st.success("Thank you for using this resource 🙏")

# ------------------------------
# 4. PEER SUPPORT FORUM
# ------------------------------
elif choice == "Peer Support Forum":
    st.title("💬 Peer Support Forum")
    st.write("Talk to trained student volunteers. 6 profiles are available.")

    profiles = [f"Student Volunteer {i}" for i in range(1, 7)]
    selected_profile = st.selectbox("Choose a volunteer to chat with:", profiles)

    if "peer_chat" not in st.session_state:
        st.session_state["peer_chat"] = {p: [] for p in profiles}

    user_msg = st.text_input(f"Message to {selected_profile}", key=f"peer_input_{selected_profile}")
    if st.button("Send Message", key=f"peer_send_{selected_profile}") and user_msg.strip():
        st.session_state["peer_chat"][selected_profile].append(("You", user_msg.strip()))
        st.session_state["peer_chat"][selected_profile].append(
            (selected_profile, "Thank you for sharing. I'm here to listen.")
        )

    for sender, msg in st.session_state["peer_chat"][selected_profile]:
        st.markdown(f"{sender}:** {msg}")

# ------------------------------
# 5. ADMIN DASHBOARD
# ------------------------------
elif choice == "Admin Dashboard":
    st.title("📊 Admin Dashboard (Anonymous Analytics)")
    st.write("No personal student data shown. Only trends are visible.")

    plays = st.session_state.get("plays", 0)
    data = pd.DataFrame({"Resource Type": ["Videos/Audio/Text"], "Views": [plays]})

    chart = alt.Chart(data).mark_bar().encode(x="Resource Type", y="Views", tooltip=["Resource Type", "Views"])
    st.altair_chart(chart, use_container_width=True)

    st.metric("Total Resource Views", plays)



















