# app.py
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

# Hard-coded API key
HF_API_KEY = "Secret"

# Use a QA model, not the token URL
API_URL = "https://api-inference.huggingface.co/models/deepset/roberta-base-squad2"
headers = {"Authorization": f"Bearer {HF_API_KEY}"}

def query_hf(question, context):
    payload = {"inputs": {"question": question, "context": context}}
    try:
        resp = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None



# ------------------------------
# APP SECTIONS
# ------------------------------
menu = ["AI Chatbot", "Book a Session", "Resources", "Peer Support Forum", "Admin Dashboard"]
choice = st.sidebar.radio("Navigate", menu)

# ------------------------------
# 1. AI CHATBOT
# ------------------------------
if choice == "AI Chatbot":
    st.title("🤖 AI-Guided First Aid Chatbot")
    st.write(
        "Confidential mental health support. Please note this is "
        "*not a substitute for professional therapy*."
    )

    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    user_input = st.text_input("Say something to the bot")
    send = st.button("Send")

    if send and user_input and user_input.strip():
        user_text = user_input.strip()
        # Save user message
        st.session_state["chat_history"].append({"role": "user", "text": user_text})

        # Safety-first rule-based check (emergency terms)
        lowered = user_text.lower()
        crisis_terms = ["suicide", "kill myself", "end life", "i want to die", "hurt myself"]
        if any(term in lowered for term in crisis_terms):
            bot_reply = (
                "⚠ It sounds like you might be in crisis. Please reach out immediately:\n\n"
                "📞 24x7 Helpline: 9152987821 (India)\n"
                "📞 1800-599-0019 (KIRAN Helpline)\n\n"
                "If you are in immediate danger, call local emergency services now. You are not alone."
            )
        else:
            # Try to get a factual/definition-style answer from the HF Q&A model.
            # Provide a small context to help the model answer common mental-health questions.
            context = (
                "Mental health refers to our emotional, psychological, and social well-being. "
                "Common problems include stress, anxiety, depression, burnout, and sleep problems. "
                "Support includes self-care techniques (breathing, grounding), peer support, counselling, and clinical interventions when required."
            )
            if HF_API_KEY:
                payload = {"inputs": {"question": user_text, "context": context}}
                output = query_hf(user_text, context)
                if output and "answer" in output and output["answer"]:
                        bot_reply = output["answer"]
                else:
                        bot_reply = "I'm here to listen — could you tell me a little more about how you're feeling?"

            else:
                # No API key -> fallback to lightweight replies
                if any(k in lowered for k in ["stress", "anxiety", "burnout", "depressed", "sleep"]):
                    bot_reply = (
                        "It sounds like you are experiencing stress or anxiety. "
                        "Try a 4-4-4 breathing exercise (inhale 4s, hold 4s, exhale 4s), "
                        "and consider short grounding: name 5 things you can see, 4 you can touch, 3 you can hear."
                    )
                else:
                    bot_reply = "I'm here to listen — could you tell me a little more about that?"

        # Append bot reply and continue
        st.session_state["chat_history"].append({"role": "bot", "text": bot_reply})

    # Display chat history
    for msg in st.session_state["chat_history"]:
        if msg["role"] == "user":
            st.markdown(f"👤 *You:* {msg['text']}")
        else:
            st.markdown(f"🤖 *Bot:* {msg['text']}")

# ------------------------------
# 2. BOOKING SYSTEM
# ------------------------------
elif choice == "Book a Session":
    st.title("📅 Confidential Counselling Booking")

    name = st.text_input("Your Name (Optional — kept confidential)")
    date = st.date_input("Choose a Date", min_value=datetime.date.today())
    time_selected = st.time_input("Choose a Time", datetime.time(15, 0))
    if st.button("Book Appointment"):
        # For MVP we simply show confirmation; persist to DB or file in real app
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
            "📥 Download Wellness Guide (PDF)",
            data=""" Self-care means taking the time to do things that help you live well and improve both your physical health and mental health. This can help you manage stress, lower your risk of illness, and increase your energy. Even small acts of self-care in your daily life can have a big impact.

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
⦁	It may take trial and error to discover what works best for you. """,
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
        # Simulated volunteer reply (in real app volunteers log in and reply)
        st.session_state["peer_chat"][selected_profile].append(
            (selected_profile, "Thank you for sharing. I'm here to listen — would you like some self-help resources?")
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
    data = pd.DataFrame({"Resources": ["Videos/Audio/Text"], "Plays": [plays]})

    chart = alt.Chart(data).mark_bar().encode(x="Resources", y="Plays", tooltip=["Resources", "Plays"])
    st.altair_chart(chart, use_container_width=True)

    st.metric("Total Resources Played", plays)
