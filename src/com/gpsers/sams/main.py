"""
main.py
=======
Ponto de Entrada da Aplicação de Monitoramento de Soldagem

Execução:
    python main.py

Estrutura do Projeto:
    .
    ├── main.py                      # <- ESTE ARQUIVO (ponto de entrada)
    ├── config.py                    # Configurações do sistema
    ├── dsp_processor.py             # Módulo DSP (algoritmos matemáticos)
    ├── worker_thread.py             # Gerenciamento de threads
    ├── welding_monitor_app.py       # GUI principal (CustomTkinter)
    └── requirements.txt             # Dependências

Autor: Sistema de Monitoramento de Soldagem
Versão: 2.0
Data: Dezembro 2025
"""

import sys
import traceback


def check_dependencies():
    """Verifica se todas as dependências estão instaladas"""
    missing = []
    
    try:
        import customtkinter
    except ImportError:
        missing.append("customtkinter")
    
    try:
        import numpy
    except ImportError:
        missing.append("numpy")
    
    try:
        import scipy
    except ImportError:
        missing.append("scipy")
    
    try:
        import moviepy
    except ImportError:
        missing.append("moviepy")
    
    try:
        import matplotlib
    except ImportError:
        missing.append("matplotlib")
    
    if missing:
        print("\n[ERRO] Dependências faltando:")
        for lib in missing:
            print(f"  ❌ {lib}")
        print("\nInstale com:")
        print(f"  pip install {' '.join(missing)}")
        print("\nOu use:")
        print("  pip install -r requirements.txt")
        return False
    
    return True


def check_project_files():
    """Verifica se todos os arquivos do projeto existem"""
    import os
    
    required_files = [
        os.path.join('core', 'dsp_processor.py'),
        os.path.join('core', 'worker_thread.py'),
        os.path.join('ui', 'main_window.py')
    ]
    
    missing = []
    for file in required_files:
        if not os.path.exists(file):
            missing.append(file)
    
    if missing:
        print("\n[ERRO] Arquivos do projeto faltando:")
        for file in missing:
            print(f"  ❌ {file}")
        print("\nCertifique-se de que todos os arquivos estão nos diretórios corretos:")
        print("  - main.py (raiz)")
        print("  - utils/config.py (opcional)")
        print("  - core/dsp_processor.py")
        print("  - core/worker_thread.py")
        print("  - ui/main_window.py")
        return False
    
    return True


import os
def main():
    """
    Função principal - Ponto de entrada da aplicação
    """
    print("=" * 70)
    print("  SAMS ARCFLOW ANALYTICS - V1.0")
    print(" Enterprise Dashboard com LLM Local Offline")
    print("=" * 70)
    print()
    
    # Verifica dependências
    print("🔍 Verificando dependências...")
    if not check_dependencies():
        sys.exit(1)
    print("   ✓ Todas as dependências instaladas")
    
    # Verifica arquivos do projeto
    print("\n🔍 Verificando arquivos do projeto...")
    if not check_project_files():
        sys.exit(1)
    print("   ✓ Todos os arquivos presentes")
    
    print("\n📦 Carregando módulos...")
    
    try:
        sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
        
        from ui.main_window import MainWindow
        
        print("   ✓ core.dsp_processor")
        print("   ✓ core.worker_thread")
        print("   ✓ ui.main_window")
        
        # Verifica se config.py existe (opcional)
        try:
            import utils.config as config
            print("   ✓ utils.config (configurações carregadas)")
        except ImportError:
            print("   ⚠️  utils.config não encontrado (usando configurações padrão)")
        
        print("\n🚀 Iniciando aplicação...")
        print()
        
        # Inicializa e executa a aplicação
        app = MainWindow()
        app.mainloop()
        
    except ImportError as e:
        print("\n[ERRO] Erro ao importar módulos!")
        print(f"Detalhes: {e}")
        print("\nVerifique se todos os arquivos estão no diretório correto")
        print(traceback.format_exc())
        sys.exit(1)
        
    except Exception as e:
        print(f"\n[ERRO CRÍTICO] {type(e).__name__}: {e}")
        print("\nStack trace completo:")
        print(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()