# app.py
import streamlit as st
import sqlite3
import pandas as pd
import altair as alt
import os
import datetime
import json
import random
import hashlib
from pathlib import Path

# Optional OpenAI usage (only if OPENAI_API_KEY set)
USE_OPENAI = bool(os.getenv("OPENAI_API_KEY"))
if USE_OPENAI:
    import openai

# ---------- CONFIG ----------
DB_PATH = "mental_platform.db"
FERNET_KEY = os.getenv("FERNET_KEY")  # optional — base64 key from Fernet.generate_key()
MOD_PASSWORD = os.getenv("MOD_PASSWORD", "modpass123")  # Change in deployment
EMERGENCY_HELPLINE = "If you are in immediate danger or crisis, call your local emergency number or the college emergency helpline."

# Screening thresholds (PHQ-9)
PHQ9_THRESHOLDS = {
    "none_mild": range(0, 10),
    "moderate": range(10, 15),
    "moderately_severe": range(15, 20),
    "severe": range(20, 100)
}
# GAD-7 thresholds
GAD7_THRESHOLDS = {
    "none_mild": range(0, 10),
    "moderate": range(10, 15),
    "severe": range(15, 100)
}

# ---------- UTILS ----------
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()
    # Students table (anonymized)
    c.execute("""
    CREATE TABLE IF NOT EXISTS screenings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        anon_id TEXT,
        phq9_score INTEGER,
        gad7_score INTEGER,
        meta JSON,
        timestamp TEXT
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        anon_id TEXT,
        preferred_date TEXT,
        preferred_time TEXT,
        notes TEXT,
        contact_encrypted TEXT,
        status TEXT,
        timestamp TEXT
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS resources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        type TEXT,
        language TEXT,
        url TEXT,
        description TEXT
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        anon_id TEXT,
        content TEXT,
        flagged INTEGER DEFAULT 0,
        approved INTEGER DEFAULT 0,
        timestamp TEXT
    )
    """)
    conn.commit()
    conn.close()

def seed_sample_resources():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT count(*) FROM resources")
    if c.fetchone()[0] == 0:
        sample = [
            ("Understanding Anxiety (Guide)", "article", "English", "https://example.edu/anxiety.html", "A simple guide to anxiety and coping."),
            ("PHQ-9 Explained (Video)", "video", "Hindi", "https://example.edu/phq9_hi.mp4", "Short video on PHQ-9 meaning (regional language)"),
            ("Relaxation Audio (10 min)", "audio", "Tamil", "https://example.edu/relax_ta.mp3", "A 10-minute guided relaxation"),
            ("On-campus Counsellors", "article", "English", "", "List of counsellors and timings")
        ]
        c.executemany("INSERT INTO resources (title, type, language, url, description) VALUES (?, ?, ?, ?, ?)", sample)
        conn.commit()
    conn.close()

def anonymize_id(raw_id: str):
    # deterministic pseudonymization (not reversible)
    h = hashlib.sha256(raw_id.encode()).hexdigest()[:8]
    return f"anon_{h}"

def encrypt_contact(plain: str):
    if not FERNET_KEY:
        return None
    try:
        f = Fernet(FERNET_KEY.encode())
        return f.encrypt(plain.encode()).decode()
    except Exception:
        return None

def decrypt_contact(token: str):
    if not FERNET_KEY:
        return None
    try:
        f = Fernet(FERNET_KEY.encode())
        return f.decrypt(token.encode()).decode()
    except InvalidToken:
        return None
    except Exception:
        return None

def score_phq9(answers):
    return sum(int(x) for x in answers)

def score_gad7(answers):
    return sum(int(x) for x in answers)

def risk_level_from_scores(phq9, gad7):
    # Simple mapping
    phq9_level = "none/mild"
    for k, r in PHQ9_THRESHOLDS.items():
        if phq9 in r:
            phq9_level = k
            break
    gad7_level = "none/mild"
    for k, r in GAD7_THRESHOLDS.items():
        if gad7 in r:
            gad7_level = k
            break
    return phq9_level, gad7_level

def make_anon_tag():
    return "anon_" + "".join(random.choice("0123456789ABCDEF") for i in range(6))

# ---------- AI Chat helpers ----------
def rule_based_response(user_text, last_screening=None):
    """
    Simple rule-based replies for fallback AI.
    Escalation if suicidal keywords or high screening risk.
    """
    text = user_text.lower()
    suicidal_keywords = ["suicide", "kill myself", "i want to die", "ending", "hurt myself"]
    urgent = any(k in text for k in suicidal_keywords)
    if urgent:
        return {
            "message": (
                "I’m really sorry you’re feeling this way. If you are in immediate danger, please call your local emergency services now. "
                + EMERGENCY_HELPLINE
            ),
            "escalate": True
        }
    if last_screening:
        phq9, gad7 = last_screening
        if phq9 >= 15 or gad7 >= 15:
            return {
                "message": "I see your screening scores indicate moderate-to-severe symptoms. I recommend booking with a counsellor. Would you like to book an appointment now? You can also reach immediate support via the helpline.",
                "escalate": False
            }
    # generic coping tips
    tips = [
        "Take slow deep breaths for a minute — breathe in for 4, hold 2, out for 6.",
        "Try grounding: name 5 things you can see, 4 you can touch, 3 you can hear.",
        "A short walk, even 5–10 minutes, can reduce stress.",
        "If you're comfortable, talking to a trusted friend or a counsellor often helps."
    ]
    return {"message": random.choice(tips), "escalate": False}

def call_openai_chat(prompt):
    """
    Example OpenAI call. Only used if OPENAI_API_KEY is set.
    IMPORTANT: This function is a minimal example. For production, handle rate limits and errors robustly.
    """
    openai.api_key = os.getenv("OPENAI_API_KEY")
    resp = openai.ChatCompletion.create(
        model="gpt-4o-mini",  # replace with available model in your account
        messages=[{"role":"system","content":"You are a supportive mental health first-aid assistant. Provide coping tips and encourage professional help when needed. Don't provide medical or legal advice."},
                  {"role":"user","content":prompt}],
        temperature=0.7,
        max_tokens=400
    )
    return resp.choices[0].message.content.strip()

# ---------- UI PAGES ----------
def page_home():
    st.title("Digital Psychological Intervention System — College Pilot")
    st.markdown("""
    This platform provides:
    - **AI-guided first-aid chat** (optional OpenAI or rule-based fallback),
    - **Screening (PHQ-9 / GAD-7)**,
    - **Confidential appointment booking**,
    - **Psychoeducational resource hub (regional languages)**,
    - **Peer support forum**,
    - **Admin dashboard** (anonymous analytics).
    """)
    st.info("This is a prototype. For emergencies see the helpline at the top-right or contact local emergency services.")
    st.sidebar.markdown("## Quick actions\n- Take screening\n- Chat with First Aid\n- Book Counsellor")

def page_screening():
    st.header("1) Screening — PHQ-9 (depression) and GAD-7 (anxiety)")
    with st.form("screen_form"):
        st.write("Optional: enter a personal identifier (we will anonymize/encrypt it). Leave blank for anonymous.")
        raw_id = st.text_input("Student ID / Roll no / Email (optional)")
        st.markdown("### PHQ-9 questions (0=Not at all ... 3=Nearly every day)")
        phq9_q = [
            "Little interest or pleasure in doing things",
            "Feeling down, depressed, or hopeless",
            "Trouble falling or staying asleep",
            "Feeling tired or little energy",
            "Poor appetite or overeating",
            "Feeling bad about yourself",
            "Trouble concentrating",
            "Moving or speaking slowly / restless",
            "Thoughts of being better off dead or hurting yourself"
        ]
        phq9_answers = [st.selectbox(f"PHQ-9 Q{i+1}: {q}", ["0","1","2","3"], key=f"p{i}") for i,q in enumerate(phq9_q)]

        st.markdown("### GAD-7 questions (0=Not at all ... 3=Nearly every day)")
        gad7_q = [
            "Feeling nervous, anxious or on edge",
            "Not being able to stop worrying",
            "Worrying too much about different things",
            "Trouble relaxing",
            "Being restless",
            "Becoming easily annoyed",
            "Feeling afraid as if something awful might happen"
        ]
        gad7_answers = [st.selectbox(f"GAD-7 Q{i+1}: {q}", ["0","1","2","3"], key=f"g{i}") for i,q in enumerate(gad7_q)]

        submitted = st.form_submit_button("Submit screening")
        if submitted:
            anon = anonymize_id(raw_id) if raw_id else make_anon_tag()
            phq9_score = score_phq9(phq9_answers)
            gad7_score = score_gad7(gad7_answers)
            level = risk_level_from_scores(phq9_score, gad7_score)
            conn = get_conn()
            c = conn.cursor()
            meta = {"phq9_answers": phq9_answers, "gad7_answers": gad7_answers}
            c.execute("INSERT INTO screenings (anon_id, phq9_score, gad7_score, meta, timestamp) VALUES (?, ?, ?, ?, ?)",
                      (anon, phq9_score, gad7_score, json.dumps(meta), datetime.datetime.utcnow().isoformat()))
            conn.commit()
            conn.close()
            st.success(f"Screening saved (anon id: {anon}). PHQ-9: {phq9_score}  |  GAD-7: {gad7_score}")
            phq9_level, gad7_level = level
            st.info(f"PHQ-9 level: **{phq9_level}**, GAD-7 level: **{gad7_level}**")
            # brief actionable suggestions
            if phq9_score >= 15 or gad7_score >= 15 or int(phq9_answers[-1])>0:
                st.warning("Your responses suggest moderate-to-severe symptoms or suicidal thoughts — we recommend contacting a professional immediately.")
                st.write(EMERGENCY_HELPLINE)
                if st.form_submit_button("Book counsellor now"):
                    st.session_state.get("book_now", True)
                else:
                    st.write("Here are some immediate coping suggestions:")
                    st.write("- Try breathing exercises, grounding, or a short walk.")
                    st.write("- If you'd like, talk to a counsellor. You can book an appointment below.")

def page_first_aid_chat():
    st.header("2) AI-guided First-Aid Chat (Supportive, not a replacement for professional care)")
    st.markdown("**Privacy note:** Chat logs are only stored temporarily in your browser session and not saved to the DB by default for privacy.")
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    # Optionally fetch recent screening to guide escalation
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT phq9_score, gad7_score FROM screenings ORDER BY id DESC LIMIT 1")
    row = c.fetchone()
    last_screening = (row[0], row[1]) if row else None

    user_input = st.text_input("How can I help today? (type feelings, problems or 'help')", key="chat_input")
    if st.button("Send"):
        st.session_state.chat_history.append(("user", user_input))
        if USE_OPENAI:
            try:
                prompt = f"User says: {user_input}\nProvide supportive, non-judgmental, practical coping tips. If suicidal or high-risk, instruct the user to seek emergency help and encourage booking. Keep brief."
                ai_resp = call_openai_chat(prompt)
                st.session_state.chat_history.append(("bot", ai_resp))
            except Exception as e:
                st.error("AI service error — falling back to rule-based response.")
                rb = rule_based_response(user_input, last_screening)
                st.session_state.chat_history.append(("bot", rb["message"]))
                if rb.get("escalate"):
                    st.warning(EMERGENCY_HELPLINE)
        else:
            rb = rule_based_response(user_input, last_screening)
            st.session_state.chat_history.append(("bot", rb["message"]))
            if rb.get("escalate"):
                st.warning(EMERGENCY_HELPLINE)

    # show chat
    for role, msg in st.session_state.chat_history[::-1]:
        if role == "bot":
            st.markdown(f"**Support Bot:** {msg}")
        else:
            st.markdown(f"**You:** {msg}")

def page_booking():
    st.header("3) Confidential Booking System")
    st.markdown("Book an appointment with an on-campus counsellor. Contact info is optional.")
    with st.form("booking_form"):
        raw_id = st.text_input("Student ID / Email (optional to help counsellor; will be anonymized/encrypted)")
        preferred_date = st.date_input("Preferred date", min_value=datetime.date.today())
        preferred_time = st.time_input("Preferred time", value=datetime.time(hour=10, minute=0))
        contact = st.text_input("Contact (phone/email) — optional")
        notes = st.text_area("Notes (brief) — optional")
        submitted = st.form_submit_button("Request Booking")
        if submitted:
            anon = anonymize_id(raw_id) if raw_id else make_anon_tag()
            contact_enc = encrypt_contact(contact) if contact else None
            conn = get_conn()
            c = conn.cursor()
            c.execute("INSERT INTO bookings (anon_id, preferred_date, preferred_time, notes, contact_encrypted, status, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
                      (anon, preferred_date.isoformat(), preferred_time.strftime("%H:%M"), notes, contact_enc, "requested", datetime.datetime.utcnow().isoformat()))
            conn.commit()
            conn.close()
            st.success("Booking request saved. Counselors will follow up through provided contact (if given).")

def page_resources():
    st.header("4) Psychoeducational Resource Hub")
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, title, type, language, url, description FROM resources")
    rows = c.fetchall()
    df = pd.DataFrame(rows, columns=["id","title","type","language","url","description"])
    languages = ["All"] + sorted(df["language"].dropna().unique().tolist())
    lang = st.selectbox("Filter by language", languages)
    typ = st.selectbox("Filter by type", ["All","article","video","audio"])
    q = st.text_input("Search title/description")
    filt = df.copy()
    if lang != "All":
        filt = filt[filt["language"]==lang]
    if typ != "All":
        filt = filt[filt["type"]==typ]
    if q:
        filt = filt[filt["title"].str.contains(q, case=False) | filt["description"].str.contains(q, case=False)]
    for _, r in filt.iterrows():
        st.subheader(r["title"])
        st.write(f"Type: {r['type']}  •  Language: {r['language']}")
        st.write(r["description"])
        if r["url"]:
            st.markdown(f"[Open resource]({r['url']})")

def page_forum():
    st.header("5) Peer Support Forum (Anonymous, Moderated)")
    st.markdown("Post anonymously, get supportive replies from peers. Posts are moderated before being public.")
    # new post form
    with st.form("post_form"):
        content = st.text_area("Write your post (be respectful; anonymous):", height=120)
        submit = st.form_submit_button("Post")
        if submit and content.strip():
            anon = make_anon_tag()
            conn = get_conn()
            c = conn.cursor()
            c.execute("INSERT INTO posts (anon_id, content, flagged, approved, timestamp) VALUES (?, ?, ?, ?, ?)",
                      (anon, content.strip(), 0, 0, datetime.datetime.utcnow().isoformat()))
            conn.commit()
            conn.close()
            st.success("Thanks — your post will be reviewed by moderators and published if appropriate.")

    # show approved posts
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT anon_id, content, timestamp FROM posts WHERE approved=1 ORDER BY id DESC LIMIT 30")
    for anon_id, content, ts in c.fetchall():
        st.markdown(f"**{anon_id}** • {ts[:19]}")
        st.write(content)
    st.markdown("---")
    st.markdown("Flag an existing public post by its anon_id (for moderator review):")
    flag_id = st.text_input("Anon id to flag (e.g., anon_AB12CD)")
    if st.button("Flag post"):
        conn = get_conn()
        c = conn.cursor()
        c.execute("UPDATE posts SET flagged=1 WHERE anon_id=? AND approved=1", (flag_id,))
        conn.commit()
        st.success("Marked for moderation.")

    st.markdown("**Moderator login** — click below to moderate (password-protected)")
    if st.button("Moderator panel"):
        pw = st.text_input("Moderator password", type="password")
        if pw == MOD_PASSWORD:
            st.session_state["moderator"] = True
            st.success("Moderator logged in")
        else:
            st.error("Wrong password.")

    if st.session_state.get("moderator"):
        st.subheader("Moderation queue (new/unapproved posts)")
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT id, anon_id, content, flagged, timestamp FROM posts WHERE approved=0 ORDER BY id DESC")
        rows = c.fetchall()
        for id_, anon_id, content, flagged, ts in rows:
            st.markdown(f"**{anon_id}** • {ts[:19]}")
            st.write(content)
            cols = st.columns([1,1,1])
            if cols[0].button(f"Approve {id_}", key=f"ap_{id_}"):
                conn = get_conn(); c = conn.cursor(); c.execute("UPDATE posts SET approved=1 WHERE id=?", (id_,)); conn.commit(); st.experimental_rerun()
            if cols[1].button(f"Delete {id_}", key=f"del_{id_}"):
                conn = get_conn(); c = conn.cursor(); c.execute("DELETE FROM posts WHERE id=?", (id_,)); conn.commit(); st.experimental_rerun()
            if cols[2].button(f"Flag {id_}", key=f"flag_{id_}"):
                conn = get_conn(); c = conn.cursor(); c.execute("UPDATE posts SET flagged=1 WHERE id=?", (id_,)); conn.commit(); st.experimental_rerun()

def page_admin():
    st.header("6) Admin Dashboard — Anonymous analytics")
    st.markdown("Aggregated analytics only. No personal data is shown in cleartext.")
    conn = get_conn(); c = conn.cursor()
    # screenings aggregation
    c.execute("SELECT phq9_score, gad7_score, timestamp FROM screenings")
    rows = c.fetchall()
    if rows:
        df = pd.DataFrame(rows, columns=["phq9","gad7","ts"])
        df["ts"] = pd.to_datetime(df["ts"])
        df["date"] = df["ts"].dt.date
        st.subheader("Screenings over time (avg scores per day)")
        daily = df.groupby("date").mean().reset_index()
        chart = alt.Chart(daily).transform_fold(["phq9","gad7"], as_=["measure","value"]).mark_line(point=True).encode(
            x="date:T", y="value:Q", color="measure:N"
        )
        st.altair_chart(chart, use_container_width=True)
        # distribution
        st.subheader("Risk distribution (latest)")
        latest = df.tail(200)
        latest["phq9_level"] = latest["phq9"].apply(lambda x: ("severe" if x>=20 else "moderately_severe" if x>=15 else "moderate" if x>=10 else "none/mild"))
        dist = latest["phq9_level"].value_counts().reset_index()
        dist.columns = ["level","count"]
        st.bar_chart(dist.set_index("level"))
    else:
        st.info("No screening data yet.")

    st.subheader("Bookings")
    c.execute("SELECT status, count(*) FROM bookings GROUP BY status")
    b = c.fetchall()
    if b:
        dfb = pd.DataFrame(b, columns=["status","count"]).set_index("status")
        st.table(dfb)
    else:
        st.info("No bookings yet.")

    # export anonymized CSV
    if st.button("Export anonymized CSV (screenings)"):
        c.execute("SELECT anon_id, phq9_score, gad7_score, timestamp FROM screenings")
        outrows = c.fetchall()
        dfa = pd.DataFrame(outrows, columns=["anon_id","phq9","gad7","timestamp"])
        csv = dfa.to_csv(index=False)
        st.download_button("Download CSV", csv, file_name="screenings_anon.csv", mime="text/csv")

# ---------- APP START ----------
def main():
    st.set_page_config(page_title="Digital Psychological Intervention System", layout="wide")
    init_db()
    seed_sample_resources()

    pages = {
        "Home": page_home,
        "Screening": page_screening,
        "First-aid Chat": page_first_aid_chat,
        "Booking": page_booking,
        "Resources": page_resources,
        "Peer Forum": page_forum,
        "Admin": page_admin
    }
    st.sidebar.title("Navigation")
    choice = st.sidebar.radio("Go to", list(pages.keys()))
    # emergency message
    st.sidebar.markdown("### Emergency / Helpline")
    st.sidebar.write(EMERGENCY_HELPLINE)

    # run selected page
    pages[choice]()

if __name__ == "__main__":
    main()



