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
        'dsp_processor.py',
        'worker_thread.py',
        'welding_monitor_app.py'
    ]
    
    missing = []
    for file in required_files:
        if not os.path.exists(file):
            missing.append(file)
    
    if missing:
        print("\n[ERRO] Arquivos do projeto faltando:")
        for file in missing:
            print(f"  ❌ {file}")
        print("\nCertifique-se de que todos os arquivos estão no mesmo diretório:")
        print("  - main.py")
        print("  - config.py (opcional)")
        print("  - dsp_processor.py")
        print("  - worker_thread.py")
        print("  - welding_monitor_app.py")
        return False
    
    return True


def main():
    """
    Função principal - Ponto de entrada da aplicação
    """
    print("=" * 70)
    print("  SISTEMA DE MONITORAMENTO DE SOLDAGEM - v2.0")
    print("  Análise Espectral de Áudio com DSP Avançado")
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
        # Importa módulos do projeto
        from welding_monitor_app import WeldingMonitorApp
        print("   ✓ dsp_processor.py")
        print("   ✓ worker_thread.py")
        print("   ✓ welding_monitor_app.py")
        
        # Verifica se config.py existe (opcional)
        try:
            import config
            print("   ✓ config.py (configurações carregadas)")
        except ImportError:
            print("   ⚠️  config.py não encontrado (usando configurações padrão)")
        
        print("\n🚀 Iniciando aplicação...")
        print()
        
        # Inicializa e executa a aplicação
        app = WeldingMonitorApp()
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