# app.py
import streamlit as st
import sqlite3
import uuid
import os
from datetime import datetime, date, time
import pandas as pd
import altair as alt

# ---------- CONFIG ----------
DB_PATH = "mh_app.db"
UPLOAD_DIR = "uploads"
ADMIN_PASS = "admin123"  # CHANGE this before production

# Ensure upload dir
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ---------- DB SETUP ----------
def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    c = conn.cursor()
    # anon tokens
    c.execute("""CREATE TABLE IF NOT EXISTS anon_tokens (
                    token TEXT PRIMARY KEY,
                    created_at TEXT
                )""")
    # screenings
    c.execute("""CREATE TABLE IF NOT EXISTS screenings (
                    id TEXT PRIMARY KEY,
                    token TEXT,
                    tool TEXT,
                    answers TEXT,
                    score INTEGER,
                    created_at TEXT
                )""")
    # chats (general chatbot + peer chats)
    c.execute("""CREATE TABLE IF NOT EXISTS chats (
                    id TEXT PRIMARY KEY,
                    token TEXT,
                    session_id TEXT,
                    peer_id TEXT,
                    message TEXT,
                    sender TEXT,
                    created_at TEXT
                )""")
    # bookings
    c.execute("""CREATE TABLE IF NOT EXISTS bookings (
                    id TEXT PRIMARY KEY,
                    token TEXT,
                    counselor TEXT,
                    date TEXT,
                    time TEXT,
                    status TEXT,
                    created_at TEXT
                )""")
    # resources
    c.execute("""CREATE TABLE IF NOT EXISTS resources (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    filename TEXT,
                    language TEXT,
                    type TEXT,
                    description TEXT,
                    created_at TEXT
                )""")
    # plays (resource plays)
    c.execute("""CREATE TABLE IF NOT EXISTS plays (
                    id TEXT PRIMARY KEY,
                    resource_id TEXT,
                    at TEXT
                )""")
    # peers (6 preset)
    c.execute("""CREATE TABLE IF NOT EXISTS peers (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    bio TEXT,
                    active INTEGER
                )""")
    conn.commit()

    # populate six peers if empty
    c.execute("SELECT COUNT(*) FROM peers")
    if c.fetchone()[0] == 0:
        peers = [(f"peer{i}", f"Peer Volunteer {i}", "Trained volunteer", 1) for i in range(1,7)]
        c.executemany("INSERT INTO peers (id,name,bio,active) VALUES (?,?,?,?)", peers)
        conn.commit()
    return conn

conn = init_db()

# ---------- Utilities ----------
def get_or_create_anon():
    if 'anon_token' in st.session_state:
        return st.session_state['anon_token']
    token = str(uuid.uuid4())
    st.session_state['anon_token'] = token
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO anon_tokens(token, created_at) VALUES (?,?)", (token, datetime.utcnow().isoformat()))
    conn.commit()
    return token

def save_chat(token, session_id, peer_id, message, sender):
    c = conn.cursor()
    c.execute("INSERT INTO chats (id,token,session_id,peer_id,message,sender,created_at) VALUES (?,?,?,?,?,?,?)",
              (str(uuid.uuid4()), token, session_id, peer_id, message, sender, datetime.utcnow().isoformat()))
    conn.commit()

def fetch_peer_chats(peer_id, limit=200):
    c = conn.cursor()
    c.execute("SELECT message, sender, created_at FROM chats WHERE peer_id=? ORDER BY created_at ASC LIMIT ?", (peer_id, limit))
    return c.fetchall()

def compute_phq9(answers):
    # answers: dict q1..q9 numeric 0-3
    score = sum(int(answers.get(f"q{i}",0)) for i in range(1,10))
    return score

def screening_action(tool, score):
    action = "self-help"
    if tool == "PHQ-9":
        if score >= 20:
            action = "immediate-escalation"
        elif score >= 15:
            action = "priority-booking"
        elif score >= 10:
            action = "recommend-booking"
    return action

def upload_resource(file, title, language, rtype, desc):
    # file is UploadedFile object from streamlit.file_uploader
    fname = f"{uuid.uuid4()}_{file.name}"
    path = os.path.join(UPLOAD_DIR, fname)
    with open(path, "wb") as f:
        f.write(file.getbuffer())
    c = conn.cursor()
    c.execute("INSERT INTO resources (id,title,filename,language,type,description,created_at) VALUES (?,?,?,?,?,?,?)",
              (str(uuid.uuid4()), title, fname, language, rtype, desc, datetime.utcnow().isoformat()))
    conn.commit()

def list_resources():
    c = conn.cursor()
    c.execute("SELECT id,title,filename,language,type,description,created_at FROM resources ORDER BY created_at DESC")
    return c.fetchall()

def record_play(resource_id):
    c = conn.cursor()
    c.execute("INSERT INTO plays (id, resource_id, at) VALUES (?,?,?)", (str(uuid.uuid4()), resource_id, datetime.utcnow().isoformat()))
    conn.commit()

def get_analytics():
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM screenings")
    total_screenings = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM bookings")
    total_bookings = c.fetchone()[0]
    c.execute("SELECT id, title FROM resources")
    resources = c.fetchall()
    resource_data = []
    for rid, title in resources:
        c.execute("SELECT COUNT(*) FROM plays WHERE resource_id=?", (rid,))
        plays = c.fetchone()[0]
        resource_data.append((title, plays))
    return total_screenings, total_bookings, resource_data

def create_booking(token, counselor, date_str, time_str):
    # conflict check
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM bookings WHERE counselor=? AND date=? AND time=? AND status='confirmed'", (counselor, date_str, time_str))
    if c.fetchone()[0] > 0:
        return None, "Timeslot already booked"
    bid = str(uuid.uuid4())
    c.execute("INSERT INTO bookings (id,token,counselor,date,time,status,created_at) VALUES (?,?,?,?,?,?,?)",
              (bid, token, counselor, date_str, time_str, 'confirmed', datetime.utcnow().isoformat()))
    conn.commit()
    return bid, None

# ---------- UI ----------
st.set_page_config(page_title="College Mental Health", layout="wide")
st.title("College Mental Health — Streamlit MVP")
token = get_or_create_anon()

menu = st.sidebar.radio("Go to", ["Chatbot", "Booking", "Resources", "Peer Support", "Admin"])

# ---------- CHATBOT ----------
if menu == "Chatbot":
    st.header("AI-guided First-Aid Chat")
    st.write("This is a rule-based first-aid bot. Type how you feel, or start PHQ-9 screening with the button.")
    session_id = st.session_state.get("chat_session_id", str(uuid.uuid4()))
    st.session_state["chat_session_id"] = session_id

    if 'chat_history' not in st.session_state:
        st.session_state['chat_history'] = []

    col1, col2 = st.columns([3,1])
    with col1:
        for i, msg in enumerate(st.session_state['chat_history']):
            role = msg['role']
            content = msg['text']
            if role == 'user':
                st.markdown(f"**You:** {content}")
            else:
                st.markdown(f"**Bot:** {content}")

        user_input = st.text_input("Say something to the bot", key="chat_input")
        send = st.button("Send")
        from transformers import pipeline
        if "qa_model" not in st.session_state:
            st.session_state.qa_model = pipeline("text-generation", model="gpt2")  # light model
            if send and user_input.strip():
                user_text = user_input.strip()
                st.session_state['chat_history'].append({'role':'user','text':user_text})
                save_chat(token, session_id, None, user_text, 'user')
                try:
                    result = st.session_state.qa_model(user_text, max_length=80, num_return_sequences=1, do_sample=True)
                    bot_reply = result[0]['generated_text']
                    bot_reply = bot_reply[len(user_text):].strip() if bot_reply.startswith(user_text) else bot_reply
                    if not bot_reply:
                        bot_reply = "I'm here to listen. Could you tell me more about how you're feeling?"
                except Exception as e:
                    bot_reply = "Sorry, I couldn't process that right now."
                    st.session_state['chat_history'].append({'role':'bot','text':bot_reply})
                    save_chat(token, session_id, None, bot_reply, 'bot')

        # if send and user_input.strip():
        #     # rule-based reply
        #     lower = user_input.lower()
        #     if 'phq' in lower or 'screen' in lower:
        #         st.session_state['chat_history'].append({'role':'bot','text':"Starting PHQ-9 screening. Click the 'Start PHQ-9' button below."})
        #     elif any(x in lower for x in ['suicide','kill myself','hurt myself','immediate danger']):
        #         st.session_state['chat_history'].append({'role':'bot','text':"If you are in immediate danger, please call local emergency services. Would you like me to help you book a counsellor?"})
        #     elif any(x in lower for x in ['anxiety','stress','depressed','sad','sleep']):
        #         st.session_state['chat_history'].append({'role':'bot','text':"I'm sorry you're feeling that way. Try 4-4-4 breathing (inhale 4s, hold 4s, exhale 4s). Would you like an audio relaxation resource?"})
        #     else:
        #         st.session_state['chat_history'].append({'role':'bot','text':"Thanks for sharing. If you'd like, run the PHQ-9 screening or book a counsellor."})
        #     st.session_state['chat_history'].append({'role':'user','text':user_input})
        #     save_chat(token, session_id, None, user_input, 'user')
    

    with col2:
        st.markdown("### Quick actions")
        if st.button("Start PHQ-9"):
            st.session_state['start_phq'] = True
        if st.session_state.get('start_phq', False):
            st.markdown("#### PHQ-9 (0=Not at all, 1=Several days, 2=More than half the days, 3=Nearly every day)")
            answers = {}
            for i in range(1,10):
                answers[f"q{i}"] = st.radio(f"Q{i}", options=[0,1,2,3], index=0, key=f"phq_q{i}")
            if st.button("Submit PHQ-9"):
                score = compute_phq9({k:v for k,v in answers.items()})
                c = conn.cursor()
                sid = str(uuid.uuid4())
                c.execute("INSERT INTO screenings (id,token,tool,answers,score,created_at) VALUES (?,?,?,?,?,?)",
                          (sid, token, "PHQ-9", str(answers), score, datetime.utcnow().isoformat()))
                conn.commit()
                action = screening_action("PHQ-9", score)
                st.success(f"Your PHQ-9 score is {score}. Suggested action: {action}")
                save_chat(token, session_id, None, f"PHQ-9 score {score}", 'bot')
                st.session_state['start_phq'] = False

# ---------- BOOKING ----------
elif menu == "Booking":
    st.header("Confidential Booking System")
    st.write("Book an appointment with campus counsellor. No names required — booking is anonymous.")
    c1, c2 = st.columns(2)
    with c1:
        d = st.date_input("Choose date", date.today())
        t = st.time_input("Choose time", time(hour=15, minute=0))
        counselor = st.selectbox("Counsellor", ["campus-counsellor"])
        if st.button("Book slot"):
            date_str = d.isoformat()
            time_str = t.strftime("%H:%M")
            bid, err = create_booking(token, counselor, date_str, time_str)
            if err:
                st.error(err)
            else:
                st.success(f"Booked {date_str} at {time_str}")
    with c2:
        st.markdown("### Existing bookings (anonymous)")
        c = conn.cursor()
        c.execute("SELECT date,time,created_at,status FROM bookings ORDER BY created_at DESC LIMIT 20")
        rows = c.fetchall()
        if rows:
            df = pd.DataFrame(rows, columns=["date","time","created_at","status"])
            st.dataframe(df)
        else:
            st.write("No bookings yet.")

# ---------- RESOURCES ----------
elif menu == "Resources":
    st.header("Psychoeducational Resource Hub")
    st.write("Upload videos, audios, text files in regional languages. Files are downloadable for offline use.")
    st.markdown("#### Upload resource (admin / content team)")
    with st.form("upload_form", clear_on_submit=True):
        file = st.file_uploader("Choose file (video/audio/pdf/text)", accept_multiple_files=False)
        title = st.text_input("Title")
        language = st.selectbox("Language", ["English","Hindi","Tamil","Telugu","Kannada","Marathi","Bengali","Other"])
        rtype = st.selectbox("Type", ["video","audio","document"])
        desc = st.text_area("Short description")
        submit = st.form_submit_button("Upload")
        if submit and file is not None:
            upload_resource(file, title if title else file.name, language, rtype, desc)
            st.success("Uploaded resource.")

    st.markdown("#### Available resources (click to download / open). Plays are tracked anonymously.")
    res = list_resources()
    if res:
        for rid, title, fname, lang, rtype, desc, created in res:
            cols = st.columns([6,2])
            with cols[0]:
                st.markdown(f"**{title}** — {lang} — {rtype}")
                if desc:
                    st.write(desc)
            with cols[1]:
                file_path = os.path.join(UPLOAD_DIR, fname)
                if os.path.exists(file_path):
                    # Download button
                    with open(file_path, "rb") as f:
                        st.download_button("Download / Open", f, file_name=fname)
                    if st.button("Open (record play)", key=f"play_{rid}"):
                        record_play(rid)
                        st.success("Play recorded.")
                else:
                    st.write("File missing")
    else:
        st.write("No resources uploaded yet.")

# ---------- PEER SUPPORT ----------
elif menu == "Peer Support":
    st.header("Peer Support — Anonymous")
    st.write("Chat privately with a trained volunteer (6 preset profiles). Messages are stored anonymously for safety and supervision.")
    c = conn.cursor()
    c.execute("SELECT id,name,bio FROM peers WHERE active=1")
    peers = c.fetchall()
    cols = st.columns(len(peers))
    for i,(pid,name,bio) in enumerate(peers):
        with cols[i]:
            if st.button(name, key=f"peer_{pid}"):
                st.session_state['selected_peer'] = pid
    selected = st.session_state.get('selected_peer', None)
    if selected:
        c.execute("SELECT name,bio FROM peers WHERE id=?", (selected,))
        pr = c.fetchone()
        st.subheader(f"Chat with {pr[0]}")
        chat_rows = fetch_peer_chats(selected)
        for msg, sender, at in chat_rows:
            if sender == 'user':
                st.markdown(f"**You:** {msg}")
            else:
                st.markdown(f"**{pr[0]}:** {msg}")
        new_msg = st.text_input("Type your message", key=f"peer_input_{selected}")
        if st.button("Send", key=f"peer_send_{selected}") and new_msg.strip():
            save_chat(token, str(uuid.uuid4()), selected, new_msg, 'user')
            # a simple auto-reply by peer (simulated)
            save_chat(token, str(uuid.uuid4()), selected, "Thank you for sharing — I'm here to listen. If you want, I can suggest resources.", 'peer')
            st.experimental_rerun()

# ---------- ADMIN ----------
elif menu == "Admin":
    st.header("Admin Dashboard (anonymous analytics)")
    pwd = st.text_input("Enter admin password", type="password")
    if pwd != ADMIN_PASS:
        st.warning("Enter admin password to view analytics. (Change ADMIN_PASS in app.py before production.)")
    else:
        total_screenings, total_bookings, resource_data = get_analytics()
        st.metric("Total screenings", total_screenings)
        st.metric("Total bookings", total_bookings)
        if resource_data:
            df = pd.DataFrame(resource_data, columns=["title","plays"])
            st.subheader("Resource plays (anonymous)")
            st.dataframe(df)
            chart = alt.Chart(df).mark_bar().encode(
                x=alt.X('title', sort='-y', title='Resource'),
                y=alt.Y('plays', title='Plays')
            )
            st.altair_chart(chart, use_container_width=True)
        else:
            st.write("No resource data yet.")

st.sidebar.markdown("---")
st.sidebar.write("Privacy: This app generates an anonymous token in your browser and does not collect names or IDs. Admin sees only aggregated counts (plays/bookings/screenings).")

