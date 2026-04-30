import smtplib
from email.message import EmailMessage
from tkinter import *
from tkinter import ttk, messagebox
import json, os, sys
from datetime import datetime

CONFIG_FILE = "smtpconfig.log"
LOG_FILE = "sends.log"

# ---------------- PATH EXE SAFE ----------------
def resource_path(path):
    try:
        base = sys._MEIPASS
    except AttributeError:
        base = os.path.abspath(".")
    return os.path.join(base, path)

# ---------------- ICON FIX (ICO + PNG) ----------------
def apply_icon(win):
    try:
        ico = resource_path("icon.ico")
        png = resource_path("icon.png")

        if os.path.exists(ico):
            win.iconbitmap(ico)

        if os.path.exists(png):
            icon = PhotoImage(file=png)
            win.iconphoto(True, icon)
            win._icon = icon  # éviter GC

    except Exception as e:
        print("Icon error:", e)

# ---------------- THEME ----------------
def setup_theme(root):
    style = ttk.Style(root)
    style.theme_use("default")

    root.configure(bg="#1e1e1e")

    style.configure("TLabel", background="#1e1e1e", foreground="white")
    style.configure("TButton", background="#333", foreground="white")
    style.map("TButton", background=[("active", "#555")])
    style.configure("TEntry", fieldbackground="#2b2b2b", foreground="white")

# ---------------- SMTP CONFIG ----------------
class SMTPConfig:
    def __init__(self, root):
        self.win = Toplevel(root)
        apply_icon(self.win)

        self.win.title("SMTP Configuration")
        self.win.geometry("400x300")
        self.win.configure(bg="#1e1e1e")

        ttk.Label(self.win, text="SMTP Host").pack(pady=5)
        self.host = ttk.Entry(self.win)
        self.host.pack(fill=X, padx=10)

        ttk.Label(self.win, text="Port").pack(pady=5)
        self.port = ttk.Entry(self.win)
        self.port.pack(fill=X, padx=10)
        self.port.insert(0, "587")

        ttk.Label(self.win, text="Security").pack(pady=5)
        self.security = StringVar(value="TLS")
        ttk.OptionMenu(self.win, self.security, "TLS", "TLS", "SSL").pack()

        ttk.Button(self.win, text="Save", command=self.save).pack(pady=10)

        self.load()

    def save(self):
        data = {
            "host": self.host.get(),
            "port": int(self.port.get()),
            "security": self.security.get()
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f)
        messagebox.showinfo("Saved", "SMTP config saved!")

    def load(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE) as f:
                data = json.load(f)
                self.host.insert(0, data.get("host", ""))
                self.port.delete(0, END)
                self.port.insert(0, data.get("port", 587))
                self.security.set(data.get("security", "TLS"))

# ---------------- SEND EMAIL ----------------
class SendEmail:
    def __init__(self, root, log_box):
        self.log_box = log_box

        self.win = Toplevel(root)
        apply_icon(self.win)

        self.win.title("New Email")
        self.win.geometry("500x450")
        self.win.configure(bg="#1e1e1e")

        ttk.Label(self.win, text="Your Email").pack()
        self.sender = ttk.Entry(self.win)
        self.sender.pack(fill=X, padx=10)

        ttk.Label(self.win, text="Password").pack()
        self.password = ttk.Entry(self.win, show="*")
        self.password.pack(fill=X, padx=10)

        ttk.Label(self.win, text="Recipient").pack()
        self.to = ttk.Entry(self.win)
        self.to.pack(fill=X, padx=10)

        ttk.Label(self.win, text="Message").pack()
        self.msg = Text(self.win, bg="#2b2b2b", fg="white")
        self.msg.pack(fill=BOTH, expand=True, padx=10, pady=5)

        ttk.Button(self.win, text="Send", command=self.send).pack(pady=10)

    def log(self, txt):
        self.log_box.insert(END, txt + "\n")
        self.log_box.see(END)

    def save_file_log(self, sender, to, status):
        t = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{t} | {sender} -> {to} | {status}\n")

    def send(self):
        sender = self.sender.get().strip()
        pwd = self.password.get().strip()
        to = self.to.get().strip()
        msgtxt = self.msg.get("1.0", END).strip()

        if not os.path.exists(CONFIG_FILE):
            messagebox.showerror("Error", "No SMTP config")
            return

        config = json.load(open(CONFIG_FILE))
        host = config["host"]
        port = int(config["port"])
        sec = config["security"]

        try:
            msg = EmailMessage()
            msg["From"] = sender
            msg["To"] = to
            msg["Subject"] = "SMTP Box"
            msg.set_content(msgtxt)

            if sec == "SSL":
                smtp = smtplib.SMTP_SSL(host, port)
            else:
                smtp = smtplib.SMTP(host, port)
                smtp.ehlo()
                smtp.starttls()
                smtp.ehlo()

            smtp.login(sender, pwd)
            smtp.send_message(msg)
            smtp.quit()

            self.log(f"SUCCESS → {sender} -> {to}")
            self.save_file_log(sender, to, "SUCCESS")

        except Exception as e:
            self.log(f"FAIL → {e}")
            self.save_file_log(sender, to, f"FAIL ({e})")
            messagebox.showerror("Error", str(e))

# ---------------- MAIN UI ----------------
root = Tk()
root.title("SMTP Box")
root.geometry("900x600")

apply_icon(root)
setup_theme(root)

main_frame = Frame(root, bg="#1e1e1e")
main_frame.pack(fill=BOTH, expand=True)

sidebar = Frame(main_frame, bg="#252526", width=150)
sidebar.pack(side=LEFT, fill=Y)

content = Frame(main_frame, bg="#1e1e1e")
content.pack(side=RIGHT, fill=BOTH, expand=True)

log_box = Text(content, bg="#111", fg="lime")
log_box.pack(fill=BOTH, expand=True, padx=10, pady=10)

Button(sidebar, text="New Email", bg="#333", fg="white",
       command=lambda: SendEmail(root, log_box)).pack(fill=X, pady=5)

Button(sidebar, text="SMTP Config", bg="#333", fg="white",
       command=lambda: SMTPConfig(root)).pack(fill=X, pady=5)

Button(sidebar, text="Quit", bg="#900", fg="white",
       command=root.quit).pack(fill=X, pady=5)

root.mainloop()
