import pyttsx3
import threading
import queue
import time

class VoiceEngine:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VoiceEngine, cls).__new__(cls)
            cls._instance._init_engine()
        return cls._instance

    def _init_engine(self):
        self.enabled = True
        self.q = queue.Queue()
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()

    def _worker(self):
        # O pyttsx3 deve ser instanciado dentro da thread onde será usado no Windows
        try:
            self.engine = pyttsx3.init()
            
            # Ajuste de propriedades (velocidade e voz)
            self.engine.setProperty('rate', 160)
            
            # Tentar selecionar uma voz feminina ou em pt-br se disponível
            voices = self.engine.getProperty('voices')
            for voice in voices:
                if 'brazil' in voice.name.lower() or 'pt-br' in voice.id.lower():
                    self.engine.setProperty('voice', voice.id)
                    break
        except Exception as e:
            print(f"[VoiceEngine] Erro ao iniciar TTS: {e}")
            return
            
        while True:
            text = self.q.get()
            if text is None:
                break
            try:
                self.engine.say(text)
                self.engine.runAndWait()
            except Exception as e:
                print(f"[VoiceEngine] Erro ao falar: {e}")
            self.q.task_done()
            time.sleep(0.1)

    def speak(self, text):
        """Adiciona um texto à fila para ser falado"""
        if self.enabled:
            self.q.put(text)
        
    def stop(self):
        """Tenta interromper a fala limpando a fila"""
        with self.q.mutex:
            self.q.queue.clear()

# Instância global Singleton
voice = VoiceEngine()

def speak(text):
    voice.speak(text)
