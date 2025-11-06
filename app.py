import os
import io
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from supabase import create_client, Client
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

# ---------- CONFIG ----------
load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BUCKET_NAME = os.getenv("BUCKET_NAME")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------- ROUTES ----------
@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

# ----- REGISTER -----
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        if len(password) < 4:
            flash("⚠️ Password minimal 4 karakter!", "warning")
            return redirect(url_for('register'))

        # Cek username di Supabase
        existing = supabase.table('users').select('*').eq('username', username).execute()
        if existing.data and len(existing.data) > 0:
            flash("❌ Username sudah digunakan!", "danger")
            return redirect(url_for('register'))

        # Hash password
        hashed_pw = generate_password_hash(password)
        supabase.table('users').insert({"username": username, "password": hashed_pw}).execute()

        flash("✅ Akun berhasil dibuat! Silakan login.", "success")
        return redirect(url_for('index'))

    return render_template('register.html')

# ----- LOGIN -----
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username'].strip()
    password = request.form['password'].strip()

    result = supabase.table('users').select('*').eq('username', username).execute()

    if result.data and len(result.data) > 0:
        user = result.data[0]
        if check_password_hash(user['password'], password):
            session['user'] = username
            flash("✅ Login berhasil", "success")
            return redirect(url_for('dashboard'))

    flash("❌ Login gagal! Username atau password salah.", "danger")
    return redirect(url_for('index'))

# ----- LOGOUT -----
@app.route('/logout')
def logout():
    session.pop('user', None)
    flash("Anda telah logout", "info")
    return redirect(url_for('index'))

# ----- DASHBOARD -----
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('index'))

    prefix = f"{session['user']}/"
    try:
        files = supabase.storage.from_(BUCKET_NAME).list(prefix)
    except Exception as e:
        print("Error load dashboard:", e)
        files = []

    return render_template('dashboard.html', files=files)

# ----- UPLOAD -----
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'user' not in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        if 'file' not in request.files:
            flash("❌ Tidak ada file yang diunggah!", "danger")
            return redirect(request.url)

        file = request.files['file']
        if file.filename == '':
            flash("⚠️ Tidak ada file yang dipilih!", "warning")
            return redirect(request.url)

        path = f"{session['user']}/{file.filename}"
        try:
            supabase.storage.from_(BUCKET_NAME).upload(path, file.read())
            flash("✅ File berhasil diunggah!", "success")
            return redirect(url_for('dashboard'))
        except Exception as e:
            print("Upload error:", e)
            flash(f"❌ Gagal mengunggah file: {e}", "danger")

    return render_template('upload.html')

# ----- DOWNLOAD -----
@app.route('/download/<filename>')
def download(filename):
    if 'user' not in session:
        return redirect(url_for('index'))

    path = f"{session['user']}/{filename}"
    try:
        data = supabase.storage.from_(BUCKET_NAME).download(path)
        return send_file(io.BytesIO(data), as_attachment=True, download_name=filename)
    except Exception as e:
        print("Download error:", e)
        flash("❌ File tidak ditemukan atau gagal diunduh.", "danger")
        return redirect(url_for('dashboard'))

# ---------- MAIN ----------
if __name__ == '__main__':
    print("🚀 Flask Cloud Arsip berjalan di http://127.0.0.1:5000")
    app.run(debug=True)
