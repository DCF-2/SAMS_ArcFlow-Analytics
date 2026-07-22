"""
worker_thread.py
================
Módulo de gerenciamento de threads para processamento em background
Evita travamento da interface gráfica durante operações pesadas

Autor: Sistema de Monitoramento de Soldagem
Versão: 2.0
"""

import threading
import traceback
from typing import Callable, Any, Optional


class WorkerThread(threading.Thread):
    """
    Thread customizada para processamento em background
    
    Executa funções pesadas sem bloquear a UI e retorna resultados
    via callback thread-safe.
    
    Uso:
        def minha_funcao(x, y):
            return x + y
        
        def callback(resultado, erro):
            if erro:
                print(f"Erro: {erro}")
            else:
                print(f"Resultado: {resultado}")
        
        worker = WorkerThread(callback, minha_funcao, 10, 20)
        worker.start()
    """
    
    def __init__(
        self, 
        callback: Callable[[Any, Optional[str]], None],
        target_func: Callable,
        *args,
        **kwargs
    ):
        """
        Inicializa a thread de trabalho
        
        Args:
            callback: Função chamada ao finalizar (resultado, erro)
            target_func: Função a ser executada em background
            *args: Argumentos posicionais para target_func
            **kwargs: Argumentos nomeados para target_func
        """
        super().__init__()
        self.callback = callback
        self.target_func = target_func
        self.args = args
        self.kwargs = kwargs
        self.result = None
        self.error = None
        self.daemon = True  # Thread morre quando programa principal termina
        
    def run(self):
        """
        Executa a função alvo e captura resultados/erros
        Chamado automaticamente por thread.start()
        """
        try:
            print(f"[WORKER] Iniciando: {self.target_func.__name__}")
            self.result = self.target_func(*self.args, **self.kwargs)
            print(f"[WORKER] Concluído: {self.target_func.__name__}")
            self.callback(self.result, None)
            
        except Exception as e:
            self.error = f"{type(e).__name__}: {str(e)}"
            print(f"[WORKER ERROR] {self.error}")
            print(traceback.format_exc())
            self.callback(None, self.error)


class ThreadPool:
    """
    Gerenciador de múltiplas threads (para uso futuro)
    
    Exemplo de uso:
        pool = ThreadPool(max_workers=3)
        pool.submit(funcao1, arg1, arg2)
        pool.submit(funcao2, arg3)
        pool.wait_all()
    """
    
    def __init__(self, max_workers: int = 3):
        """
        Inicializa o pool de threads
        
        Args:
            max_workers: Número máximo de threads simultâneas
        """
        self.max_workers = max_workers
        self.threads = []
        self.lock = threading.Lock()
        
    def submit(
        self, 
        callback: Callable,
        target_func: Callable,
        *args,
        **kwargs
    ):
        """
        Submete uma nova tarefa ao pool
        
        Args:
            callback: Função de callback
            target_func: Função a executar
            *args, **kwargs: Argumentos para target_func
        """
        # Aguarda se atingiu limite
        while len([t for t in self.threads if t.is_alive()]) >= self.max_workers:
            threading.Event().wait(0.1)
        
        # Cria e inicia thread
        worker = WorkerThread(callback, target_func, *args, **kwargs)
        
        with self.lock:
            self.threads.append(worker)
        
        worker.start()
        
    def wait_all(self):
        """Aguarda todas as threads terminarem"""
        for thread in self.threads:
            if thread.is_alive():
                thread.join()
        
        print(f"[POOL] Todas as {len(self.threads)} threads concluídas")
        
    def get_active_count(self) -> int:
        """Retorna número de threads ativas"""
        return len([t for t in self.threads if t.is_alive()])