import tkinter as tk
from huggingface_hub import InferenceClient
import ctypes
import threading
import time

# Hugging Face setup
HF_TOKEN = "your hf token here"
MODEL_ID = "HuggingFaceH4/zephyr-7b-beta"
client = InferenceClient(model=MODEL_ID, token=HF_TOKEN)

# calling llm
def call_llm(client, prompt):
    formatted_prompt = f"<|system|>\nYou are a helpful assistant.\n<|user|>\n{prompt}\n<|assistant|>\n"
    response_text = client.text_generation(
        prompt=formatted_prompt,
        max_new_tokens=150,
        temperature=0.7,
        top_p=0.95,
        repetition_penalty=1.1,
        stop=["<|user|>", "<|system|>"]
    )
    return response_text.strip()

# GUI Setup
root = tk.Tk()
root.geometry("420x540")
root.overrideredirect(True)
root.config(bg="#fcd6e6")

# Aesthetic window shell (tkinter) setup
if ctypes.windll.shell32.IsUserAnAdmin():
    hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
    ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 2, ctypes.pointer(ctypes.c_int(1)), 4)

# Move window
def move_window(event):
    root.geometry(f'+{event.x_root}+{event.y_root}')

# Auto-close on focus out when inactive
def click_outside(event):
    if not root.winfo_containing(event.x_root, event.y_root):
        root.destroy()

# Top title bar
title_bar = tk.Frame(root, bg="#fbb1cc", relief="flat", height=30)
title_bar.pack(fill=tk.X)
title_bar.bind("<B1-Motion>", move_window)

btn_close = tk.Button(title_bar, text="✖", command=root.destroy, font=("Helvetica", 10),
                      bg="#fbb1cc", fg="white", bd=0)
btn_close.pack(side=tk.RIGHT, padx=5)

btn_min = tk.Button(title_bar, text="—", command=lambda: root.iconify(),
                    font=("Helvetica", 10), bg="#fbb1cc", fg="white", bd=0)
btn_min.pack(side=tk.RIGHT)

# Chat display
chat_text = tk.Text(root, bg="#fff0f5", fg="#333", font=("Helvetica", 11),
                    wrap="word", bd=0, padx=10, pady=10)
chat_text.pack(padx=20, pady=(10, 0), fill=tk.BOTH, expand=True)
chat_text.insert(tk.END, "🤖 Bot: Hello! Ask me anything 💬\n\n", "bot")
chat_text.tag_config("user", foreground="#d81b60", font=("Helvetica", 11, "bold"))
chat_text.tag_config("bot", foreground="#6a1b9a", font=("Helvetica", 11))
chat_text.config(state="disabled")

# Input box with scrollbar
input_frame = tk.Frame(root, bg="#fcd6e6")
input_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=20, pady=10)

input_text = tk.Text(input_frame, height=3, width=30, wrap="word",
                     font=("Helvetica", 12), bg="#ffe4ec", fg="#000",
                     bd=0, relief=tk.FLAT)
input_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

scrollbar = tk.Scrollbar(input_frame, command=input_text.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
input_text.config(yscrollcommand=scrollbar.set)

# Typing animation
typing_id = None
typing_running = False
typing_states = ["typing.", "typing..", "typing..."]
typing_line_index = None

def start_typing_animation():
    global typing_id, typing_running, typing_line_index
    typing_running = True
    state = [0]

    chat_text.config(state="normal")
    typing_line_index = chat_text.index("end-1c")
    chat_text.insert(tk.END, "🤖 Bot: typing.\n\n", "bot")
    chat_text.config(state="disabled")

    def animate():
        if not typing_running:
            return
        chat_text.config(state="normal")
        chat_text.delete(typing_line_index, f"{typing_line_index} lineend")
        chat_text.insert(typing_line_index, f"🤖 Bot: {typing_states[state[0]]}")
        chat_text.config(state="disabled")
        state[0] = (state[0] + 1) % 3
        global typing_id
        typing_id = root.after(500, animate)

    animate()

def stop_typing_animation():
    global typing_id, typing_running
    typing_running = False
    if typing_id:
        root.after_cancel(typing_id)

# Send message
def send_message():
    user_input = input_text.get("1.0", "end-1c").strip()
    if not user_input:
        return

    chat_text.config(state="normal")
    chat_text.insert(tk.END, f"🧑 You: {user_input}\n\n", "user")
    chat_text.config(state="disabled")
    input_text.delete("1.0", tk.END)
    chat_text.yview(tk.END)

    start_typing_animation()

    # Use threading to avoid freezing UI and gitching out
    def get_response():
        response = call_llm(client, user_input)
        root.after(0, lambda: display_bot_response(response))

    threading.Thread(target=get_response).start()

# Show bot replies to our texts and saving them below the binding
def display_bot_response(response):
    stop_typing_animation()
    chat_text.config(state="normal")
    chat_text.delete(typing_line_index, f"{typing_line_index} lineend")
    chat_text.insert(tk.END, f"🤖 Bot: {response}\n\n", "bot")
    chat_text.config(state="disabled")
    chat_text.yview(tk.END)

# Bindings
root.bind("<Return>", lambda e: send_message())
root.bind("<Button-1>", click_outside)

root.mainloop()
