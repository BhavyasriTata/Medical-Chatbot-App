import streamlit as st
import datetime
import requests
import altair as alt
import pandas as pd

# ------------------------------
# CONFIG
# ------------------------------
st.set_page_config(page_title="Digital Mental Health Support", layout="wide")

API_URL = "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta"  # 🔑 Get it from https://huggingface.co/settings/tokens
headers = {"Authorization": "Bearer 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"}

def query(payload):
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.json()

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
    st.write("Confidential mental health support. Please note this is **not a substitute for professional therapy**.")

    if 'chat_history' not in st.session_state:
        st.session_state['chat_history'] = []

    user_input = st.text_input("Say something to the bot")
    send = st.button("Send")

    if send and user_input.strip():
        user_text = user_input.strip()
        st.session_state['chat_history'].append({'role':'user','text':user_text})

        # Rule-based check first (safety-critical)
        if any(word in user_text.lower() for word in ["suicide", "kill myself", "end life", "die"]):
            bot_reply = "⚠️ It sounds like you might be in crisis. Please reach out immediately:\n\n📞 24x7 Helpline: 9152987821 (India)\n📞 1800-599-0019 (KIRAN Helpline)\n\nYou are not alone."
        else:
            try:
                output = query({"inputs": user_text})
                bot_reply = output.get("generated_text", "I'm here to listen, could you tell me more?")
            except:
                bot_reply = "Sorry, I couldn’t process that right now."

        st.session_state['chat_history'].append({'role':'bot','text':bot_reply})

    # Display chat
    for msg in st.session_state['chat_history']:
        if msg['role'] == 'user':
            st.markdown(f"👤 **You:** {msg['text']}")
        else:
            st.markdown(f"🤖 **Bot:** {msg['text']}")

# ------------------------------
# 2. BOOKING SYSTEM
# ------------------------------
elif choice == "Book a Session":
    st.title("📅 Confidential Counselling Booking")

    name = st.text_input("Your Name (Confidential - not shown to admin)")
    date = st.date_input("Choose a Date", min_value=datetime.date.today())
    time = st.time_input("Choose a Time", datetime.time(15,0))
    if st.button("Book Appointment"):
        st.success(f"✅ Appointment booked for {name} on {date} at {time}")

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
        st.download_button("📥 Download Wellness Guide (PDF)", data="This is a sample guide.", file_name="guide.pdf")

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

    profiles = [f"Student Volunteer {i}" for i in range(1,7)]
    selected_profile = st.selectbox("Choose a volunteer to chat with:", profiles)

    if 'peer_chat' not in st.session_state:
        st.session_state['peer_chat'] = {p: [] for p in profiles}

    user_msg = st.text_input(f"Message to {selected_profile}")
    if st.button("Send Message"):
        st.session_state['peer_chat'][selected_profile].append(("You", user_msg))
        st.session_state['peer_chat'][selected_profile].append((selected_profile, "Thanks for sharing, I hear you."))

    for sender, msg in st.session_state['peer_chat'][selected_profile]:
        st.markdown(f"**{sender}:** {msg}")

# ------------------------------
# 5. ADMIN DASHBOARD
# ------------------------------
elif choice == "Admin Dashboard":
    st.title("📊 Admin Dashboard (Anonymous Analytics)")
    st.write("No personal student data shown. Only trends are visible.")

    plays = st.session_state.get("plays", 0)
    data = pd.DataFrame({"Resources": ["Videos/Audio/Text"], "Plays": [plays]})

    chart = alt.Chart(data).mark_bar().encode(
        x="Resources",
        y="Plays",
        tooltip=["Resources","Plays"]
    )
    st.altair_chart(chart, use_container_width=True)

    st.metric("Total Resources Played", plays)
