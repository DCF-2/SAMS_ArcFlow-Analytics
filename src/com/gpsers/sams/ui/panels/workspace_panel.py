import customtkinter as ctk
import os
from pathlib import Path
from PIL import Image, ImageTk
import threading
import time
import wave
import pygame

try:
    from moviepy.editor import VideoFileClip
except ImportError:
    try:
        from moviepy import VideoFileClip
    except ImportError:
        VideoFileClip = None

class WorkspacePanel(ctk.CTkFrame):
    def __init__(self, master, controller):
        super().__init__(master, fg_color="transparent")
        self.controller = controller
        
        try:
            pygame.mixer.init()
        except Exception as e:
            print(f"Erro ao inicializar PyGame Mixer: {e}")
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Frames do Workspace
        self.frame_welcome = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_welcome.grid(row=0, column=0, sticky="nsew")
        self.frame_welcome.grid_rowconfigure(0, weight=1)
        self.frame_welcome.grid_columnconfigure(0, weight=1)
        
        self.frame_player = ctk.CTkFrame(self, fg_color="#181818", corner_radius=10)
        
        # ==========================================
        # WELCOME SCREEN (VSCode Style)
        # ==========================================
        icons_dir = Path(__file__).parent.parent.parent / 'assets' / 'img'
        try:
            pil_logo = Image.open(icons_dir / "SAMS.png").convert("RGBA")
            orig_w, orig_h = pil_logo.size
            target_h = 250
            target_w = int(orig_w * (target_h / orig_h))
            
            logo_img = pil_logo.resize((target_w, target_h), Image.LANCZOS)
            # Aplica 80% de transparencia (alpha = 50 de 255)
            logo_img.putalpha(50)
            self.welcome_image = ctk.CTkImage(light_image=logo_img, dark_image=logo_img, size=(target_w, target_h))
        except:
            self.welcome_image = None
            
        welcome_lbl = ctk.CTkLabel(self.frame_welcome, text="SAMS ArcFlow Analytics", image=self.welcome_image, compound="top", font=ctk.CTkFont(size=24, weight="bold", family="Segoe UI"), text_color="#555555")
        welcome_lbl.grid(row=0, column=0)
        
        # ==========================================
        # MEDIA PLAYER
        # ==========================================
        self.frame_player.grid_rowconfigure(0, weight=1)
        self.frame_player.grid_columnconfigure(0, weight=1)
        
        self.video_lbl = ctk.CTkLabel(self.frame_player, text="")
        self.video_lbl.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        self.controls_frame = ctk.CTkFrame(self.frame_player, fg_color="transparent", height=40)
        self.controls_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        self.controls_frame.grid_propagate(False)
        
        self.btn_play_pause = ctk.CTkButton(self.controls_frame, text="▶ Play", command=self.toggle_playback, width=80)
        self.btn_play_pause.pack(side="left")
        
        self.lbl_time = ctk.CTkLabel(self.controls_frame, text="00:00 / 00:00", text_color="#A0A0A0")
        self.lbl_time.pack(side="left", padx=15)
        
        self.scrubber = ctk.CTkSlider(self.controls_frame, from_=0, to=1, command=self.on_scrub)
        self.scrubber.set(0)
        self.scrubber.pack(side="left", fill="x", expand=True, padx=10)
        
        self.speed_combo = ctk.CTkComboBox(self.controls_frame, values=["1.0x", "1.5x", "2.0x", "0.5x"], width=70)
        self.speed_combo.set("1.0x")
        self.speed_combo.pack(side="left", padx=5)
        
        self.btn_fullscreen = ctk.CTkButton(self.controls_frame, text="⛶ F.S.", command=self.toggle_fullscreen, width=60)
        self.btn_fullscreen.pack(side="right", padx=10)
        
        # Carregar imagem de loading animada uma unica vez
        self.loading_frames = []
        self.loading_idx = 0
        self.is_loading = False
        icons_dir = Path(__file__).parent.parent.parent / 'assets' / 'icons'
        if (icons_dir / "carregando.png").exists():
            pil_img = Image.open(icons_dir / "carregando.png").convert("RGBA")
            for i in range(0, 360, 45):
                rotated = pil_img.rotate(-i, resample=Image.BICUBIC)
                self.loading_frames.append(ctk.CTkImage(light_image=rotated, dark_image=rotated, size=(64, 64)))
                
        # Carregar ícone padrão de áudio
        self.audio_icon = None
        if (icons_dir / "audio.png").exists():
            pil_audio = Image.open(icons_dir / "audio.png").convert("RGBA")
            self.audio_icon = ctk.CTkImage(light_image=pil_audio, dark_image=pil_audio, size=(128, 128))
        
        # Variaveis de Estado do Player
        self.clip = None
        self.playing = False
        self.current_frame_idx = 0
        self.video_frames = []
        self.fps = 30
        self.playback_thread = None
        self.double_clicked = False
        self.osd_lbl = ctk.CTkLabel(self.frame_player, text="", fg_color="transparent", text_color="white", font=ctk.CTkFont(size=40, weight="bold"))
        self.osd_lbl.place(relx=0.5, rely=0.5, anchor="center")
        self.video_lbl.bind("<Button-1>", self.on_video_click)
        self.video_lbl.bind("<Double-Button-1>", self.on_video_double_click)

    def show_welcome(self):
        self.stop_video()
        self.frame_player.grid_forget()
        self.frame_welcome.grid(row=0, column=0, sticky="nsew")

    def show_player(self, filepath):
        self.frame_welcome.grid_forget()
        self.frame_player.grid(row=0, column=0, sticky="nsew")
        self.load_media(filepath)
        self.is_fullscreen = False

    def toggle_fullscreen(self):
        if not self.is_fullscreen:
            self.controller.attributes("-fullscreen", True)
            self.is_fullscreen = True
        else:
            self.controller.attributes("-fullscreen", False)
            self.is_fullscreen = False

    def show_osd(self, text):
        self.osd_lbl.configure(text=text)
        self.osd_lbl.lift()
        self.after(600, lambda: self.osd_lbl.configure(text=""))

    def on_video_click(self, event):
        self.after(250, self._handle_single_click)

    def _handle_single_click(self):
        if not self.double_clicked and (self.video_frames or getattr(self, 'audio_duration', 0) > 0):
            self.toggle_playback()
        self.double_clicked = False

    def on_video_double_click(self, event):
        self.double_clicked = True
        if self.video_frames:
            self.current_frame_idx = min(len(self.video_frames) - 1, self.current_frame_idx + int(5 * self.fps))
            self.show_osd("▶▶ +5s")
            self._sync_audio()
        elif getattr(self, 'audio_duration', 0) > 0:
            self.current_audio_time = min(self.audio_duration, getattr(self, 'current_audio_time', 0) + 5.0)
            self.show_osd("▶▶ +5s")
            self._sync_audio()

    def on_scrub(self, value):
        if self.video_frames:
            self.current_frame_idx = int(value * (len(self.video_frames) - 1))
            self.video_lbl.configure(image=self.video_frames[self.current_frame_idx])
            self._sync_audio()
        elif getattr(self, 'audio_duration', 0) > 0:
            self.current_audio_time = value * self.audio_duration
            self._sync_audio()

    def _sync_audio(self):
        if not self.audio_path or not os.path.exists(self.audio_path): return
        try:
            if self.video_frames:
                pos = self.current_frame_idx / self.fps
            else:
                pos = getattr(self, 'current_audio_time', 0)
            
            if self.playing:
                pygame.mixer.music.load(self.audio_path)
                pygame.mixer.music.play(start=pos)
        except Exception as e:
            print(f"Erro Sync Áudio: {e}")

    def _animate_loading(self):
        if self.is_loading and self.loading_frames:
            self.loading_idx = (self.loading_idx + 1) % len(self.loading_frames)
            self.video_lbl.configure(image=self.loading_frames[self.loading_idx])
            self.after(100, self._animate_loading)

    def load_media(self, filepath):
        self.stop_video()
        self.video_frames = []
        self.current_frame_idx = 0
        self.current_audio_time = 0.0
        self.audio_path = None
        self.scrubber.set(0)
        self.osd_lbl.configure(text="")
        
        # Previne recarregamento desnecessario
        if filepath == getattr(self, 'current_loaded_filepath', None):
            self._on_frames_loaded()
            return
            
        self.current_loaded_filepath = filepath
        self.is_loading = True
        self.video_lbl.configure(text="Carregando Mídia...", compound="top")
        if self.loading_frames:
            self.video_lbl.configure(image=self.loading_frames[0])
            self._animate_loading()
            
        self.btn_play_pause.configure(state="disabled")
        
        ext = Path(filepath).suffix.lower()
        if ext == '.mp4' and VideoFileClip:
            self.audio_path = os.path.join(os.path.dirname(filepath), Path(filepath).stem + "_audio.wav")
            threading.Thread(target=self._extract_frames, args=(filepath,), daemon=True).start()
        elif ext == '.wav':
            self.is_loading = False
            self.audio_path = filepath
            self.video_lbl.configure(text=f"Áudio Carregado: {os.path.basename(filepath)}\n(Ondas Sonoras Prontas)", image=self.audio_icon)
            self.btn_play_pause.configure(state="normal", text="▶ Play")
            
            try:
                with wave.open(filepath, 'rb') as w:
                    self.audio_duration = w.getnframes() / float(w.getframerate())
            except:
                self.audio_duration = 0.0
                
            self.lbl_time.configure(text=f"00:00 / {int(self.audio_duration//60):02d}:{int(self.audio_duration%60):02d}")

    def _extract_frames(self, filepath):
        try:
            self.clip = VideoFileClip(filepath)
            self.fps = self.clip.fps
            if self.fps == 0 or self.fps is None: self.fps = 30
            
            for frame in self.clip.iter_frames():
                # Convert Numpy Array (RGB) to PIL Image
                pil_img = Image.fromarray(frame)
                pil_img.thumbnail((600, 400), Image.Resampling.LANCZOS)
                w, h = pil_img.size
                ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(w, h))
                self.video_frames.append(ctk_img)
                
            self.after(0, self._on_frames_loaded)
        except Exception as e:
            self.after(0, lambda err=e: self.video_lbl.configure(text=f"Erro ao carregar mídia: {err}", image=None))

    def _on_frames_loaded(self):
        self.is_loading = False
        self.video_lbl.configure(text="")
        self.btn_play_pause.configure(state="normal", text="▶ Play")
        if self.video_frames:
            self.video_lbl.configure(image=self.video_frames[0])
            total_time = len(self.video_frames) / self.fps
            self.lbl_time.configure(text=f"00:00 / {int(total_time//60):02d}:{int(total_time%60):02d}")

    def toggle_playback(self):
        if self.playing:
            self.playing = False
            self.btn_play_pause.configure(text="▶ Play")
            self.show_osd("⏸")
            try: pygame.mixer.music.pause()
            except: pass
        else:
            self.playing = True
            self.btn_play_pause.configure(text="⏸ Pause")
            self.show_osd("▶")
            
            if self.audio_path and os.path.exists(self.audio_path):
                try:
                    if not pygame.mixer.music.get_busy():
                        pos = self.current_frame_idx / self.fps if self.video_frames else getattr(self, 'current_audio_time', 0)
                        pygame.mixer.music.load(self.audio_path)
                        pygame.mixer.music.play(start=pos)
                    else:
                        pygame.mixer.music.unpause()
                except Exception as e:
                    print(f"Erro ao tocar audio: {e}")
                
            if self.video_frames:
                self.playback_thread = threading.Thread(target=self._play_loop, daemon=True)
                self.playback_thread.start()
            elif self.audio_path and getattr(self, 'audio_duration', 0) > 0:
                self.playback_thread = threading.Thread(target=self._play_audio_loop, daemon=True)
                self.playback_thread.start()

    def _play_audio_loop(self):
        start = time.time() - self.current_audio_time
        while self.playing:
            self.current_audio_time = time.time() - start
            if self.current_audio_time >= self.audio_duration:
                break
                
            self.after(0, lambda c=self.current_audio_time, t=self.audio_duration: self.lbl_time.configure(text=f"{int(c//60):02d}:{int(c%60):02d} / {int(t//60):02d}:{int(t%60):02d}"))
            
            # Atualiza Scrubber
            if self.audio_duration > 0:
                self.after(0, lambda p=self.current_audio_time/self.audio_duration: self.scrubber.set(p))
                
            time.sleep(0.1)
            
        if self.current_audio_time >= self.audio_duration:
            self.playing = False
            self.current_audio_time = 0.0
            self.scrubber.set(0)
            self.after(0, lambda: self.btn_play_pause.configure(text="▶ Play"))

    def _play_loop(self):
        while self.playing and self.current_frame_idx < len(self.video_frames):
            start = time.time()
            
            try: speed = float(self.speed_combo.get().replace("x", ""))
            except: speed = 1.0
            frame_time = 1.0 / (self.fps * speed)
            
            frame_img = self.video_frames[self.current_frame_idx]
            self.after(0, lambda img=frame_img: self.video_lbl.configure(image=img))
            
            # Atualiza label de tempo e scrubber
            cur_sec = self.current_frame_idx / self.fps
            tot_sec = len(self.video_frames) / self.fps
            self.after(0, lambda c=cur_sec, t=tot_sec: self.lbl_time.configure(text=f"{int(c//60):02d}:{int(c%60):02d} / {int(t//60):02d}:{int(t%60):02d}"))
            self.after(0, lambda p=(self.current_frame_idx/(len(self.video_frames)-1) if len(self.video_frames)>1 else 0): self.scrubber.set(p))
            
            self.current_frame_idx += 1
            
            elapsed = time.time() - start
            if elapsed < frame_time:
                time.sleep(frame_time - elapsed)
                
        if self.current_frame_idx >= len(self.video_frames):
            self.playing = False
            self.current_frame_idx = 0
            self.scrubber.set(0)
            self.after(0, lambda: self.btn_play_pause.configure(text="▶ Play"))

    def stop_video(self):
        self.is_loading = False
        self.playing = False
        try: pygame.mixer.music.stop()
        except: pass
        if self.clip:
            try: self.clip.close()
            except: pass
            self.clip = None

    # Esses metodos ficam aqui apenas pra evitar erro no main_window que chamava eles
    def append_dataset_row(self, filename, pred, f_df):
        if hasattr(self.controller, 'dashboard_window') and self.controller.dashboard_window:
            self.controller.dashboard_window.append_dataset_row(filename, pred, f_df)

    def update_plots(self, results, title_suffix):
        if hasattr(self.controller, 'dashboard_window') and self.controller.dashboard_window:
            self.controller.dashboard_window.update_plots(results, title_suffix)
