import sqlite3
import qrcode
import cv2
from pyzbar.pyzbar import decode
import numpy as np
import os
import time
import os
import pandas as pd
from playsound import playsound
from datetime import datetime 

# Membuat folder qr_codes jika tidak ada
os.makedirs('qr_codes', exist_ok=True)

# Fungsi untuk menginisialisasi database
def init_db():
    with sqlite3.connect('absen.db') as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            dob TEXT,
            role TEXT,
            qr_data TEXT UNIQUE
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS absensi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            qr_data TEXT,
            date TEXT
        )
        """)
        conn.commit()

# Fungsi untuk menambahkan pengguna ke database
def add_user_to_db(name, dob, role, qr_color, bg_color):
    qr_data = f"{name}_{dob}_{role}"
    with sqlite3.connect('absen.db') as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (name, dob, role, qr_data) VALUES (?, ?, ?, ?)",
                       (name, dob, role, qr_data))
        conn.commit()
    generate_qr(qr_data, qr_color, bg_color)

# Fungsi untuk membuat QR code
def generate_qr(data, qr_color='black', bg_color='white'):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color=qr_color, back_color=bg_color)
    img = img.convert("RGB")
    img.save(f"qr_codes/{data}.png")

# Fungsi untuk mengambil daftar pengguna dari database
def get_users():
    with sqlite3.connect('absen.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        return cursor.fetchall()

def delete_user(user_id):
    """Menghapus pengguna berdasarkan ID."""
    try:
        with sqlite3.connect('absen.db') as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
        return True, None  # Berhasil, tanpa kesalahan
    except Exception as e:
        return False, str(e)  # Gagal, dengan pesan kesalahan

# Fungsi untuk memindai QR code
def play_notification_sound():
    playsound("notif.mp3")  # Ganti dengan path file mp3 Anda

def scan_qr():
    cap = cv2.VideoCapture(0)
    # Membuat window fullscreen
    cv2.namedWindow("QR Code Scanner", cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty("QR Code Scanner", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    
    # Variabel untuk menyimpan notifikasi
    notification = ""
    notification_time = None
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Menambahkan jam real-time
        current_time = datetime.now().strftime('%Y-%m-%d | %H:%M:%S')
        cv2.putText(frame, f"SMK BP 1 | {current_time}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                    1, (255, 255, 255), 2, cv2.LINE_AA)
        
        # Decode QR code dari frame
        for barcode in decode(frame):
            qr_data = barcode.data.decode('utf-8')
            if qr_data_exists(qr_data):  # Cek apakah data QR ada di database
                name = qr_data.split('_')[0]
                if check_absensi_today(qr_data):  # Cek apakah sudah absen hari ini
                    notification = f"{name} Sudah absen hari ini!"
                    play_notification_sound()
                else:
                    record_absensi(qr_data)  # Rekam absensi
                    notification = f"{name} Berhasil absen!"
                    play_notification_sound()  # Putar suara notifikasi
                notification_time = time.time()  # Catat waktu notifikasi
                
                # Tambahkan marker di sekitar QR code
                points = barcode.polygon
                if len(points) == 4:
                    pts = np.array([[point.x, point.y] for point in points], np.int32)
                    pts = pts.reshape((-1, 1, 2))
                    cv2.polylines(frame, [pts], True, (0, 255, 0), 3)
                
                # Tambahkan notifikasi text di atas marker
                rect = barcode.rect
                cv2.putText(frame, notification, (rect.left, rect.top - 10), cv2.FONT_HERSHEY_SIMPLEX, 
                            0.7, (0, 255, 0), 2)
        
        # Tampilkan notifikasi (maksimal 3 detik)
        if notification and notification_time and (time.time() - notification_time < 3):
            cv2.putText(frame, notification, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 
                        1, (0, 255, 0), 2, cv2.LINE_AA)
        elif notification_time and (time.time() - notification_time >= 3):
            notification = ""  # Reset notifikasi setelah 3 detik
        
        # Tampilkan frame di window fullscreen
        cv2.imshow("QR Code Scanner", frame)
        
        # Tombol 'q' untuk keluar
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()

# Fungsi untuk memeriksa apakah QR code sudah ada di database
def qr_data_exists(qr_data):
    with sqlite3.connect('absen.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE qr_data = ?", (qr_data,))
        return cursor.fetchone() is not None

# Fungsi untuk memeriksa apakah pengguna sudah absen hari ini
def check_absensi_today(qr_data):
    today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with sqlite3.connect('absen.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM absensi WHERE qr_data = ? AND date = ?", (qr_data, today))
        return cursor.fetchone() is not None

# Fungsi untuk mencatat absensi
def record_absensi(qr_data):
    today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with sqlite3.connect('absen.db') as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO absensi (qr_data, date) VALUES (?, ?)", (qr_data, today))
        conn.commit()

def export_absensi_to_excel():
    with sqlite3.connect('absen.db') as conn:
        df = pd.read_sql_query("""
            SELECT users.name AS Nama, absensi.date AS TanggalWaktu
            FROM users
            JOIN absensi ON users.qr_data = absensi.qr_data
        """, conn)
    try:
        # Cobalah berbagai format datetime
        possible_formats = ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d']      
        # Cobalah semua format, jika gagal, pakai ISO8601 sebagai fallback
        for fmt in possible_formats:
            try:
                df['TanggalWaktu'] = pd.to_datetime(df['TanggalWaktu'], format=fmt, errors='coerce')
                break
            except ValueError:
                continue    
        # Jika semua format gagal, gunakan ISO8601
        if not pd.api.types.is_datetime64_any_dtype(df['TanggalWaktu']):
            df['TanggalWaktu'] = pd.to_datetime(df['TanggalWaktu'], errors='coerce')
        df['Tanggal'] = df['TanggalWaktu'].dt.date
        df['Hari'] = df['TanggalWaktu'].dt.day_name()
        df['Jam'] = df['TanggalWaktu'].dt.time   
        df = df[['Nama', 'Tanggal', 'Hari', 'Jam']]
        df.to_excel('rekap_absensi.xlsx', index=False)
        print("Rekap absensi berhasil diekspor ke file 'rekap_absensi.xlsx'")
    except Exception as e:
        print(f"Terjadi kesalahan saat mengubah data ke dalam format datetime: {e}")

# Fungsi utama yang akan memanggil semua fungsi
def main():
    init_db()
    main_menu()

# Fungsi menu utama (pilihan admin)
def main_menu():
    while True:
        # Bersihkan layar di setiap iterasi
        os.system('cls' if os.name == 'nt' else 'clear')
        print("ABSENSI SMKS BINA PEMBANGUNAN 1")
        print("Menu:")
        print("1. Tambah Pengguna")
        print("2. Lihat Daftar Pengguna")
        print("3. Scan QR Code")
        print("4. Rekap Absensi ke Excel")
        print("5. Keluar")
        pilihan = input("Pilih: ")
        if pilihan == '1':
            name = input("Nama: ")
            dob = input("Tanggal Lahir (YYYY-MM-DD): ")
            role = input("Role (Siswa/Guru/Staff/Karyawan): ")
            qr_color = input("Warna QR Code (nama warna atau kode HEX, default 'black'): ") or 'black'
            bg_color = input("Warna Background QR Code (nama warna atau kode HEX, default 'white'): ") or 'white'
            add_user_to_db(name, dob, role, qr_color, bg_color)
            print("Pengguna berhasil ditambahkan.")
            input("Tekan Enter untuk kembali ke menu utama...")
        elif pilihan == '2':
            users = get_users()
            os.system('cls' if os.name == 'nt' else 'clear')
            print("Daftar Pengguna:")
            for user in users:
                print(user)
            input("Tekan Enter untuk kembali ke menu utama...")
        elif pilihan == '3':
            scan_qr()
            input("Pemindaian selesai. Tekan Enter untuk kembali ke menu utama...")
        elif pilihan == '4':
            export_absensi_to_excel()
            print("Rekap absensi berhasil disimpan ke Excel.")
            input("Tekan Enter untuk kembali ke menu utama...")
        elif pilihan == '5':
            print("Dibuat oleh Qii Dimitry SMK Bina Pembangunan 1")
            break
        else:
            print("Pilihan tidak valid!")
            input("Tekan Enter untuk mencoba lagi...")
if __name__ == '__main__':
    main()
