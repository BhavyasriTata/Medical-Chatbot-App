# import streamlit as st
# import datetime
# import requests
# import altair as alt
# import pandas as pd

# # ------------------------------
# # CONFIG
# # ------------------------------
# st.set_page_config(page_title="Digital Mental Health Support", layout="wide")

# API_URL = "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta"  # 🔑 Get it from https://huggingface.co/settings/tokens
# headers = {"Authorization": "Bearer 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"}

# def query(payload):
#     response = requests.post(API_URL, headers=headers, json=payload)
#     return response.json()

# # In chatbot section
# context = """
# Stress is a state of mental or emotional strain caused by challenging situations.
# It can affect both mind and body, leading to anxiety, sleep problems, or health issues.
# """
# output = query({
#     "inputs": {
#         "question": user_text,
#         "context": context
#     }
# })

# bot_reply = output.get("answer", "I'm here to listen. Could you share more?")


# # ------------------------------
# # APP SECTIONS
# # ------------------------------
# menu = ["AI Chatbot", "Book a Session", "Resources", "Peer Support Forum", "Admin Dashboard"]
# choice = st.sidebar.radio("Navigate", menu)

# # ------------------------------
# # 1. AI CHATBOT
# # ------------------------------
# if choice == "AI Chatbot":
#     st.title("🤖 AI-Guided First Aid Chatbot")
#     st.write("Confidential mental health support. Please note this is **not a substitute for professional therapy**.")

#     if 'chat_history' not in st.session_state:
#         st.session_state['chat_history'] = []

#     user_input = st.text_input("Say something to the bot")
#     send = st.button("Send")

#     if send and user_input.strip():
#         user_text = user_input.strip()
#         st.session_state['chat_history'].append({'role':'user','text':user_text})

#         # Rule-based check first (safety-critical)
#         if any(word in user_text.lower() for word in ["suicide", "kill myself", "end life", "die"]):
#             bot_reply = "⚠️ It sounds like you might be in crisis. Please reach out immediately:\n\n📞 24x7 Helpline: 9152987821 (India)\n📞 1800-599-0019 (KIRAN Helpline)\n\nYou are not alone."
#         else:
#             try:
#                 output = query({"inputs": user_text})
#                 if isinstance(output, list) and "generated_text" in output[0]:
#                     bot_reply = output[0]["generated_text"]
#                 elif "generated_text" in output:
#                     bot_reply = output["generated_text"]
#                 else:
#                     bot_reply = "I'm here to listen. Could you share more?"
#             except Exception as e:
#                 bot_reply = "Sorry, I couldn’t process that right now."

#         # Always append bot reply
#         st.session_state['chat_history'].append({'role': 'bot', 'text': bot_reply})


#             #     output = query({"inputs": user_text})
#             #     bot_reply = output.get("generated_text", "I'm here to listen, could you tell me more?")
#             # except:
#             #     bot_reply = "Sorry, I couldn’t process that right now."

        
#     # Display chat
#     for msg in st.session_state['chat_history']:
#         if msg['role'] == 'user':
#             st.markdown(f"👤 **You:** {msg['text']}")
#         else:
#             st.markdown(f"🤖 **Bot:** {msg['text']}")

# # ------------------------------
# # 2. BOOKING SYSTEM
# # ------------------------------
# elif choice == "Book a Session":
#     st.title("📅 Confidential Counselling Booking")

#     name = st.text_input("Your Name (Confidential - not shown to admin)")
#     date = st.date_input("Choose a Date", min_value=datetime.date.today())
#     time = st.time_input("Choose a Time", datetime.time(15,0))
#     if st.button("Book Appointment"):
#         st.success(f"✅ Appointment booked for {name} on {date} at {time}")

# # ------------------------------
# # 3. RESOURCES HUB
# # ------------------------------
# elif choice == "Resources":
#     st.title("🎧 Mental Health Resources")

#     resource_type = st.radio("Choose Resource Type", ["Videos", "Audios", "Texts"])
    
#     if resource_type == "Videos":
#         st.video("https://www.youtube.com/watch?v=1vx8iUvfyCY")  # Example meditation video
#     elif resource_type == "Audios":
#         st.audio("https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3")
#     elif resource_type == "Texts":
#         st.download_button("📥 Download Wellness Guide (PDF)", data="This is a sample guide.", file_name="guide.pdf")

#     if "plays" not in st.session_state:
#         st.session_state["plays"] = 0
#     if st.button("Mark as Viewed/Played"):
#         st.session_state["plays"] += 1
#         st.success("Thank you for using this resource 🙏")

# # ------------------------------
# # 4. PEER SUPPORT FORUM
# # ------------------------------
# elif choice == "Peer Support Forum":
#     st.title("💬 Peer Support Forum")
#     st.write("Talk to trained student volunteers. 6 profiles are available.")

#     profiles = [f"Student Volunteer {i}" for i in range(1,7)]
#     selected_profile = st.selectbox("Choose a volunteer to chat with:", profiles)

#     if 'peer_chat' not in st.session_state:
#         st.session_state['peer_chat'] = {p: [] for p in profiles}

#     user_msg = st.text_input(f"Message to {selected_profile}")
#     if st.button("Send Message"):
#         st.session_state['peer_chat'][selected_profile].append(("You", user_msg))
#         st.session_state['peer_chat'][selected_profile].append((selected_profile, "Thanks for sharing, I hear you."))

#     for sender, msg in st.session_state['peer_chat'][selected_profile]:
#         st.markdown(f"**{sender}:** {msg}")

# # ------------------------------
# # 5. ADMIN DASHBOARD
# # ------------------------------
# elif choice == "Admin Dashboard":
#     st.title("📊 Admin Dashboard (Anonymous Analytics)")
#     st.write("No personal student data shown. Only trends are visible.")

#     plays = st.session_state.get("plays", 0)
#     data = pd.DataFrame({"Resources": ["Videos/Audio/Text"], "Plays": [plays]})

#     chart = alt.Chart(data).mark_bar().encode(
#         x="Resources",
#         y="Plays",
#         tooltip=["Resources","Plays"]
#     )
#     st.altair_chart(chart, use_container_width=True)

#     st.metric("Total Resources Played", plays)



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

# Use env var or Streamlit secrets for the Hugging Face key.
# DO NOT hard-code your key in this file if you will publish it.
HF_API_KEY = os.environ.get("HF_API_KEY") or st.secrets.get("HF_API_KEY", None)
if not HF_API_KEY:
    st.warning("HuggingFace API key not set. Set HF_API_KEY in environment or Streamlit secrets for AI responses.")
# Choose a stable inference model for Q&A (works well for definitions)
API_URL = "https://huggingface.co/settings/tokens/new?tokenType=fineGrained"
headers = {"Authorization": "Bearer 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"}

def query_hf(payload):
    """
    Send payload to the HF Inference API and return JSON.
    Payload format depends on the model. For SQuAD-style models:
      {"inputs": {"question": "...", "context": "..."}}
    """
    try:
        resp = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        # Do not leak exception details to UI; return None to fallback
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
        "**not a substitute for professional therapy**."
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
                "⚠️ It sounds like you might be in crisis. Please reach out immediately:\n\n"
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
                output = query_hf(payload)
                # deepset/roberta-base-squad2 returns dict like {"answer": "...", "score": ...}
                if isinstance(output, dict) and "answer" in output and output["answer"]:
                    bot_reply = output["answer"]
                else:
                    # fallback conversational reply
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
            st.markdown(f"👤 **You:** {msg['text']}")
        else:
            st.markdown(f"🤖 **Bot:** {msg['text']}")

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
            data="This is a sample guide.",
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
        st.markdown(f"**{sender}:** {msg}")

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




