import logging
import sys
import datetime
from pathlib import Path

class GUILogHandler(logging.Handler):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

    def emit(self, record):
        try:
            msg = self.format(record)
            level = record.levelname
            
            # Checa se veio do logger de libs externas (via sys.stdout/stderr redirecionado)
            if hasattr(record, 'is_external') and record.is_external:
                level = "EXTERNAL"
                
            if hasattr(record, 'gui_level'):
                level = record.gui_level
                
            if hasattr(self.main_window, 'settings_window') and self.main_window.settings_window and self.main_window.settings_window.winfo_exists():
                self.main_window.after(0, lambda: self.main_window.settings_window.append_log(level, msg))
            else:
                self.main_window.log_history.append((level, msg))
        except Exception:
            self.handleError(record)

def setup_logger(main_window=None):
    data_dir = Path(__file__).parent.parent / "data"
    log_dir = data_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Arquivo de log com a data de hoje (ex: sams_app_2026-07-28.log)
    hoje = datetime.datetime.now().strftime("%Y-%m-%d")
    log_file = log_dir / f"sams_app_{hoje}.log"
    
    logger = logging.getLogger("SAMS")
    logger.setLevel(logging.DEBUG)
    
    # Limpa handlers anteriores (caso haja recarregamento)
    logger.handlers = []
    
    # Formato do Log
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    
    # Handler para Salvar em Arquivo
    fh = logging.FileHandler(log_file, encoding='utf-8')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    # Handler para o Console Padrão (Python)
    ch = logging.StreamHandler(sys.__stdout__)
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    # Handler para a GUI (Janela de Configurações)
    if main_window:
        gui_h = GUILogHandler(main_window)
        gui_h.setLevel(logging.INFO)
        gui_h.setFormatter(logging.Formatter('%(message)s'))
        logger.addHandler(gui_h)
        
    # Interceptador de Exceções Globais (Crashes)
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logger.error("ERRO CRÍTICO (Uncaught exception)", exc_info=(exc_type, exc_value, exc_traceback))
        
    def handle_thread_exception(args):
        logger.error(f"ERRO DE THREAD ({args.thread.name if args.thread else 'Unknown'}): {args.exc_value}", exc_info=(args.exc_type, args.exc_value, args.exc_traceback))

    sys.excepthook = handle_exception
    import threading
    threading.excepthook = handle_thread_exception
    
    # Redirecionador do print() e bibliotecas terceiras
    class StreamToLogger:
        def __init__(self, logger, log_level=logging.INFO):
            self.logger = logger
            self.log_level = log_level
            self.linebuf = ''
            
        def write(self, buf):
            for line in buf.rstrip().splitlines():
                if line.strip():
                    self.logger.log(self.log_level, line.rstrip(), extra={'is_external': True})
                    
        def flush(self):
            pass
            
    # Redireciona tudo que iria pro console para o nosso logger
    sys.stdout = StreamToLogger(logger, logging.INFO)
    sys.stderr = StreamToLogger(logger, logging.ERROR)
    
    return logger
