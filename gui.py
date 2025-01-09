import tkinter as tk
from tkinter import ttk, messagebox
from cli import add_user_to_db, get_users, scan_qr, export_absensi_to_excel, delete_user
import os

# Function to handle login page
def login_page(root):
    def login():
        username = username_entry.get()
        password = password_entry.get()
        if username == "admin" and password == "staffbp1":
            messagebox.showinfo("Login Berhasil", "Selamat datang, Admin!")
            main_menu(root)
        else:
            messagebox.showerror("Login Gagal", "Username atau password salah.")
    clear_frame(root)
    tk.Label(root, text="Login Admin", font=("Arial", 20)).pack(pady=20)
    tk.Label(root, text="Username:").pack(pady=5)
    username_entry = ttk.Entry(root, width=30)
    username_entry.pack(pady=5)
    tk.Label(root, text="Password:").pack(pady=5)
    password_entry = ttk.Entry(root, show="*", width=30)
    password_entry.pack(pady=5)
    ttk.Button(root, text="Login", command=login).pack(pady=20)

def main_menu(root):
    def go_to_add_user():
        add_user_page(root)
    def go_to_user_list():
        user_list_page(root)
    clear_frame(root)
    def run_text():
        try:
            current_text = running_text_label["text"]
            running_text_label["text"] = current_text[1:] + current_text[0]
            root.after(200, run_text)
        except Exception as e:
            messagebox.showerror("Error", f"Terjadi kesalahan: {e}")
    # Dalam fungsi main_menu
    running_text_label = tk.Label(
        root, 
        text="| SELAMAT DATANG DI APLIKASI ABSENSI SMKS BINA PEMBANGUNAN 1 | DIBUAT OLEH KIIDIMITRY | MASIH TAHAP PENGEMBANGAN " * 2, 
        font=("Arial", 12), 
        fg="black"
    )
    running_text_label.pack(pady=10)
    run_text()
    tk.Label(root, text="ABSENSI SMKS BINA PEMBANGUNAN 1", font=("Arial", 20)).pack(pady=20)
    ttk.Button(root, text="Tambah Pengguna", width=30, command=go_to_add_user).pack(pady=10)
    ttk.Button(root, text="Daftar Pengguna", width=30, command=go_to_user_list).pack(pady=10)
    ttk.Button(root, text="Scan QR Code", width=30, command=scan_qr_gui).pack(pady=10)
    ttk.Button(root, text="Rekap Absensi ke Excel", width=30, command=export_absensi_gui).pack(pady=10)
    ttk.Button(root, text="Keluar", width=30, command=root.quit).pack(pady=20)

# Add user page
def add_user_page(root):
    def submit():
        name = name_entry.get()
        dob = dob_entry.get()
        role = role_entry.get()
        qr_color = qr_color_entry.get() or 'black'
        bg_color = bg_color_entry.get() or 'white'
        if name and dob and role:
            try:
                add_user_to_db(name, dob, role, qr_color, bg_color)
                messagebox.showinfo("Sukses", "Pengguna berhasil ditambahkan!")
                main_menu(root)
            except Exception as e:
                messagebox.showerror("Error", f"Gagal menambahkan pengguna: {e}")
        else:
            messagebox.showwarning("Peringatan", "Semua kolom wajib diisi!")
    clear_frame(root)
    tk.Label(root, text="Tambah Pengguna", font=("Arial", 18)).pack(pady=10)
    tk.Label(root, text="Nama:").pack(pady=5)
    name_entry = ttk.Entry(root, width=30)
    name_entry.pack(pady=5)
    tk.Label(root, text="Tanggal Lahir (YYYY-MM-DD):").pack(pady=5)
    dob_entry = ttk.Entry(root, width=30)
    dob_entry.pack(pady=5)
    tk.Label(root, text="Role (Siswa/Guru/Staff/Karyawan):").pack(pady=5)
    role_entry = ttk.Entry(root, width=30)
    role_entry.pack(pady=5)
    tk.Label(root, text="Warna QR Code (default: black):").pack(pady=5)
    qr_color_entry = ttk.Entry(root, width=30)
    qr_color_entry.pack(pady=5)
    tk.Label(root, text="Warna Background (default: white):").pack(pady=5)
    bg_color_entry = ttk.Entry(root, width=30)
    bg_color_entry.pack(pady=5)
    ttk.Button(root, text="Submit", command=submit).pack(pady=20)
    ttk.Button(root, text="Kembali", command=lambda: main_menu(root)).pack(pady=20)

# View user list page with tabs for roles
def user_list_page(root):
    def delete_user_gui(user_id):
        """Menghapus pengguna dengan dialog konfirmasi."""
        confirm = messagebox.askyesno("Konfirmasi", "Apakah Anda yakin ingin menghapus pengguna ini?")
        if confirm:
            success, error = delete_user(user_id)
            if success:
                messagebox.showinfo("Sukses", "Pengguna berhasil dihapus.")
                user_list_page(root)  # Refresh halaman
            else:
                messagebox.showerror("Error", f"Gagal menghapus pengguna: {error}")

    def show_qr(qr_data):
        """Menampilkan QR Code dalam jendela baru."""
        qr_file = f"qr_codes/{qr_data}.png"
        if os.path.exists(qr_file):
            qr_window = tk.Toplevel(root)
            qr_window.title("QR Code")
            qr_img = tk.PhotoImage(file=qr_file)
            tk.Label(qr_window, image=qr_img).pack()
            qr_window.mainloop()
        else:
            messagebox.showerror("Error", "QR Code tidak ditemukan!")

    def search_users():
        """Memperbarui tampilan berdasarkan hasil pencarian."""
        query = search_entry.get().lower()
        filtered_users = [user for user in all_users if query in user[1].lower()]
        display_users(filtered_users)

    def sort_users_by_role(users):
        """Mengelompokkan pengguna berdasarkan role."""
        sorted_roles = {"Siswa": [], "Guru": [], "Staff": [], "Karyawan": []}
        for user in users:
            role = user[3]
            if role in sorted_roles:
                sorted_roles[role].append(user)
            else:
                sorted_roles["Lainnya"].append(user)
        return sorted_roles

    def display_users(users):
        """Menampilkan pengguna dalam tab berdasarkan daftar yang diberikan."""
        sorted_roles = sort_users_by_role(users)

        for tab in tabs:
            # Bersihkan konten pada setiap tab
            for widget in tabs[tab].winfo_children():
                widget.destroy()
            if sorted_roles[tab]:  # Jika ada pengguna pada role ini
                for user in sorted_roles[tab]:
                    user_frame = tk.Frame(tabs[tab], relief="solid", borderwidth=1, padx=5, pady=5)
                    user_frame.pack(fill="x", padx=10, pady=5)
                    user_info = f"Nama: {user[1]}, Tanggal Lahir: {user[2]}"
                    tk.Label(user_frame, text=user_info, anchor="w").pack(side="left", padx=5)
                    ttk.Button(user_frame, text="Lihat QR", command=lambda qr=user[4]: show_qr(qr)).pack(side="right", padx=5)
                    ttk.Button(user_frame, text="Hapus Data", command=lambda uid=user[0]: delete_user_gui(uid)).pack(side="right", padx=5)
            else:
                # Tampilkan pesan jika tidak ada pengguna
                tk.Label(tabs[tab], text="Tidak ada pengguna terdaftar.", fg="gray").pack(pady=10)
    # Ambil data pengguna dari CLI
    all_users = get_users()
    # Bersihkan frame utama
    clear_frame(root)
    tk.Label(root, text="Daftar Pengguna", font=("Arial", 18)).pack(pady=10)
    # Pencarian
    search_frame = tk.Frame(root)
    search_frame.pack(fill="x", padx=10, pady=5)
    tk.Label(search_frame, text="Cari Pengguna:").pack(side="left", padx=5)
    search_entry = ttk.Entry(search_frame, width=30)
    search_entry.pack(side="left", padx=5)
    ttk.Button(search_frame, text="Cari", command=search_users).pack(side="left", padx=5)
    # Notebook untuk tab per role
    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True, padx=10, pady=10)
    # Buat tab untuk setiap role
    tabs = {
        "Siswa": tk.Frame(notebook),
        "Guru": tk.Frame(notebook),
        "Staff": tk.Frame(notebook),
        "Karyawan": tk.Frame(notebook),
    }
    for role, frame in tabs.items():
        notebook.add(frame, text=role)
    # Tampilkan semua pengguna
    display_users(all_users)
    ttk.Button(root, text="Kembali", command=lambda: main_menu(root)).pack(pady=20)

def scan_qr_gui():
    messagebox.showinfo("Info", "Pemindai QR Code akan dimulai. Tekan 'q' untuk keluar.")
    scan_qr()

def export_absensi_gui():
    try:
        export_absensi_to_excel()
        messagebox.showinfo("Sukses", "Rekap absensi berhasil diekspor ke 'rekap_absensi.xlsx'!")
    except Exception as e:
        messagebox.showerror("Error", f"Gagal mengekspor absensi: {e}")

def clear_frame(root):
    for widget in root.winfo_children():
        widget.destroy()

# Main function
def main_gui():
    root = tk.Tk()
    root.title("Absensi SMKS Bina Pembangunan 1")
    root.geometry("700x500")
    login_page(root)
    root.mainloop()
if __name__ == "__main__":
    main_gui()