import customtkinter as ctk
import threading
from ui.components.tooltip import ToolTip
try:
    from gpt4all import GPT4All
except ImportError:
    GPT4All = None

class AIPanel(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, corner_radius=0, fg_color="#212121", width=420)
        self.controller = controller
        
        self.llm_model = None
        self.cancel_llm = False
        self.is_thinking = False
        self.think_dots = 0
        
        self.grid_rowconfigure(4, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        frame_ai_top = ctk.CTkFrame(self, fg_color="transparent")
        frame_ai_top.grid(row=0, column=0, sticky="ew", padx=15, pady=15)
        frame_ai_top.grid_columnconfigure(1, weight=1)
        
        # Título sem colchetes
        lbl_ai = ctk.CTkLabel(frame_ai_top, text="SAMS IA", font=ctk.CTkFont(size=18, weight="bold"))
        lbl_ai.grid(row=0, column=0, sticky="w")
        self.current_model_name = "Llama-3.2-3B-Instruct-Q4_0.gguf"
        
        # O combobox foi removido daqui e foi para baixo da caixa de texto
        
        frame_ml = ctk.CTkFrame(self, fg_color="#2b2b2b", corner_radius=8)
        frame_ml.grid(row=1, column=0, padx=15, pady=5, sticky="ew")
        ctk.CTkLabel(frame_ml, text="DIAGNÓSTICO TÉCNICO:", font=ctk.CTkFont(size=11, weight="bold")).pack(pady=(5, 0))
        self.lbl_ml_result = ctk.CTkLabel(frame_ml, text="Aguardando...", font=ctk.CTkFont(size=16, weight="bold"), text_color="#F59E0B")
        self.lbl_ml_result.pack(pady=5)
        
        self.lbl_ai_status = ctk.CTkLabel(self, text="Aguardando comandos.", text_color="gray", font=ctk.CTkFont(size=11, slant="italic"))
        self.lbl_ai_status.grid(row=2, column=0, padx=15, sticky="w")
        
        # Histórico de Chat
        self.txt_chat = ctk.CTkTextbox(self, font=("Consolas", 13), text_color="#ffffff", fg_color="#1a1a1a", wrap="word")
        self.txt_chat.grid(row=4, column=0, padx=15, pady=5, sticky="nsew")
        
        # Tags de alinhamento e cores
        self.txt_chat.tag_config("user_label", justify="right", foreground="#58A6FF")
        self.txt_chat.tag_config("user_text", justify="right", foreground="#E6EDF3")
        self.txt_chat.tag_config("ai_label", justify="left", foreground="#10B981")
        self.txt_chat.tag_config("ai_text", justify="left", foreground="#FFFFFF")
        self.txt_chat.tag_config("system", justify="center", foreground="#F59E0B")
        
        self.txt_chat.insert("end", "Bem vindo ao SAMS ArcFlow Analytics.\nSelecione um ensaio no Explorer e me pergunte qualquer coisa.\n\n", "system")
        self.txt_chat.configure(state="disabled")
        
        # Novo design da caixa de entrada do chat (Moderno e esticável)
        frame_input = ctk.CTkFrame(self, fg_color="#2b2b2b", corner_radius=20)
        frame_input.grid(row=5, column=0, padx=15, pady=(5, 15), sticky="ew")
        frame_input.grid_columnconfigure(0, weight=1)
        
        # Row 0: Textbox
        self.entry_chat = ctk.CTkTextbox(frame_input, height=50, font=("Segoe UI", 12), fg_color="transparent", border_width=0)
        self.entry_chat.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 5))
        
        # Row 1: Bottom Bar (Model selector + Button)
        frame_bottom_input = ctk.CTkFrame(frame_input, fg_color="transparent")
        frame_bottom_input.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 5))
        frame_bottom_input.grid_columnconfigure(1, weight=1) # Spacer para empurrar o botão para a direita
        
        # Left side: Model selection
        frame_model = ctk.CTkFrame(frame_bottom_input, fg_color="transparent")
        frame_model.grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(frame_model, text="✨", font=ctk.CTkFont(size=12), text_color="#F59E0B").pack(side="left")
        self.combo_model = ctk.CTkOptionMenu(
            frame_model, values=["Llama-3.2-3B-Instruct-Q4_0.gguf", "Phi-3-mini-4k-instruct.Q4_0.gguf"],
            width=200, height=20, font=ctk.CTkFont(size=11), fg_color="#2b2b2b", button_color="#2b2b2b", button_hover_color="#333333", text_color="gray", command=self._on_model_change
        )
        self.combo_model.pack(side="left", padx=2)
        self.combo_model.set(self.current_model_name)
        
        # Right side: Send/Stop Buttons
        self.btn_container = ctk.CTkFrame(frame_bottom_input, fg_color="transparent", width=34, height=34)
        self.btn_container.grid(row=0, column=2, sticky="e", padx=(0, 5), pady=(0, 5))
        self.btn_container.grid_propagate(False) # Mantém o tamanho fixo
        self.btn_container.grid_rowconfigure(0, weight=1)
        self.btn_container.grid_columnconfigure(0, weight=1)
        
        # O botão agora é APENAS o ícone (fundo transparente)
        self.btn_send = ctk.CTkButton(self.btn_container, text="➤", font=ctk.CTkFont(size=20), width=34, height=34, corner_radius=0, border_spacing=0, text_color="#0078D7", command=self.send_chat_message, fg_color="transparent", hover_color="#333333")
        self.btn_send.grid(row=0, column=0, sticky="nsew")
        
        self.btn_stop = ctk.CTkButton(self.btn_container, text="⏹", font=ctk.CTkFont(size=20), width=34, height=34, corner_radius=0, border_spacing=0, text_color="#d73a49", command=self.stop_llm, fg_color="transparent", hover_color="#333333")

        
        # Inicia modelo padrão
        self._init_local_llm(self.current_model_name)
        
        # Bind do Enter
        self.entry_chat.bind("<Return>", self._on_enter_pressed)
        self.entry_chat.bind("<Shift-Return>", self._on_shift_enter_pressed)

    def _on_enter_pressed(self, event):
        self.send_chat_message()
        return "break" # Impede de pular a linha
        
    def _on_shift_enter_pressed(self, event):
        return # Permite pular a linha se usar Shift+Enter

    def set_ml_result(self, predicao, cor):
        self.lbl_ml_result.configure(text=f"MODO: {predicao.upper()}", text_color=cor)

    def _init_local_llm(self, model_file):
        threading.Thread(target=self._load_llm_thread, args=(model_file,), daemon=True).start()

    def _load_llm_thread(self, model_file):
        self.current_model_name = model_file
        self.after(0, lambda: self.btn_send.configure(state="disabled"))
        self.after(0, lambda: self.lbl_ai_status.configure(text=f"Carregando {model_file} (Baixando se for 1º uso)...", text_color="#F59E0B"))
        
        try:
            if not GPT4All:
                raise Exception("A biblioteca gpt4all não está instalada.")
            
            # Forçando n_threads=4 para evitar erro do llama.cpp no ambiente do usuário
            self.llm_model = GPT4All(model_file, n_threads=4)
            self.after(0, lambda: self.lbl_ai_status.configure(text=f"Modelo {model_file} Ativo (Offline).", text_color="#10B981"))
        except Exception as e:
            self.after(0, lambda: self.lbl_ai_status.configure(text="Erro de Carregamento.", text_color="#d73a49"))
            self.after(0, lambda e=e: self._append_to_chat("ERRO", str(e)))
        finally:
            self.after(0, lambda: self.btn_send.configure(state="normal"))

    def _on_model_change(self, choice):
        self._init_local_llm(choice)

    def _append_to_chat(self, sender, message):
        self.txt_chat.configure(state="normal")
        if sender == "VOCÊ":
            self.txt_chat.insert("end", f"{sender}\n", "user_label")
            self.txt_chat.insert("end", f"{message}\n\n", "user_text")
        elif sender == "SAMS IA":
            self.txt_chat.insert("end", f"{sender}\n", "ai_label")
            self.txt_chat.insert("end", f"{message}\n\n", "ai_text")
        else:
            self.txt_chat.insert("end", f"[{sender}] {message}\n\n", "system")
        self.txt_chat.see("end")
        self.txt_chat.configure(state="disabled")

    def stop_llm(self):
        self.cancel_llm = True
        self.lbl_ai_status.configure(text="Parado pelo usuário.", text_color="#d73a49")
        self.btn_send.configure(state="normal")
        self.btn_stop.grid_forget()
        self.btn_send.grid(row=0, column=0, sticky="nsew")
        self.is_thinking = False

    def send_chat_message(self):
        if self.is_thinking: return # Previne o usuário de spammar ENTER e travar a CPU
        user_msg = self.entry_chat.get("1.0", "end-1c").strip()
        if not user_msg: return
        
        self.entry_chat.delete("1.0", "end")
        self._append_to_chat("VOCÊ", user_msg)
        
        self.btn_send.grid_forget()
        self.btn_stop.grid(row=0, column=0, sticky="nsew")
        self.cancel_llm = False
        self.is_thinking = True
        self.think_dots = 0
        self._animate_thinking()
        
        threading.Thread(target=self._process_llm_chat, args=(user_msg,), daemon=True).start()

    def _animate_thinking(self):
        if not self.is_thinking:
            return
        dots = self.think_dots % 4
        self.lbl_ai_status.configure(text="Pensando" + "." * dots, text_color="#10B981")
        self.think_dots += 1
        self.after(500, self._animate_thinking)

    def _process_llm_chat(self, message):
        try:
            if not self.llm_model:
                self.after(0, lambda: self._append_to_chat("SISTEMA", "Modelo ainda não carregou."))
                return

            f_df = self.controller.current_features_cache
            pred = self.lbl_ml_result.cget('text')
            
            if f_df is not None:
                system_prompt = (
                    "Você é o Assistente SAMS IA, um engenheiro especialista em soldagem MIG/MAG.\n"
                    f"O usuário está analisando um ensaio cujo diagnóstico matemático apontou: {pred}.\n"
                    f"Métricas técnicas extraídas da onda de soldagem:\n"
                    f"- Energia Média: {round(f_df['energia_media'].iloc[0], 2)}\n"
                    f"- Variância: {round(f_df['variancia_sinal'].iloc[0], 2)}\n"
                    f"- Taxa Cruzamento Zero: {round(f_df['taxa_cruzamento_zero'].iloc[0], 2)}\n"
                    f"- Frequência de Pico: {round(f_df['frequencia_pico_hz'].iloc[0], 2)} Hz.\n"
                    "DICA: Ao responder, aja naturalmente como se estivesse observando os gráficos e os resultados. Responda de forma sucinta e direta a pergunta do usuário baseando-se apenas na teoria de soldagem aplicável a esses dados. Não mencione frases esquisitas como 'análise oculta' ou 'dados secretos'."
                )
            else:
                system_prompt = "Você é o SAMS IA, um especialista em soldagem. Responda à pergunta do usuário."

            # Prompt simples, sem formatações confusas que causam alucinação
            prompt = f"{system_prompt}\n\nUsuário: {message}\nSAMS IA: "
            
            self.after(0, lambda: self.txt_chat.configure(state="normal"))
            self.after(0, lambda: self.txt_chat.insert("end", "SAMS IA\n", "ai_label"))
            self.after(0, lambda: self.txt_chat.see("end"))
            
            self.is_thinking = False
            self.after(0, lambda: self.lbl_ai_status.configure(text="Gerando...", text_color="#F59E0B"))

            # Stream response
            for token in self.llm_model.generate(prompt, streaming=True, max_tokens=300):
                if self.cancel_llm: break
                self.after(0, lambda t=token: self._stream_token(t))
            
            self.after(0, lambda: self._stream_token("\n\n"))
            self.after(0, lambda: self.txt_chat.configure(state="disabled"))
            self.after(0, lambda: self.lbl_ai_status.configure(text="Pronto.", text_color="gray"))

        except Exception as e:
            if not self.cancel_llm:
                self.after(0, lambda err=str(e): self._append_to_chat("ERRO IA", err))
        finally:
            self.is_thinking = False
            self.after(0, lambda: self.btn_stop.grid_forget())
            self.after(0, lambda: self.btn_send.grid(row=0, column=0, sticky="nsew"))
            self.after(0, lambda: self.btn_send.configure(state="normal"))

    def _stream_token(self, token):
        self.txt_chat.insert("end", token, "ai_text")
        self.txt_chat.see("end")
