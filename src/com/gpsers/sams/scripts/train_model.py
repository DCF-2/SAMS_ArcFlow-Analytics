"""
SAMS - Script de Treinamento de Inteligência Artificial (Machine Learning)
Fase 2 - Lê os dados extraídos, aplica a separação de 80/20% por modo,
e treina um classificador Random Forest.
"""

import os
import sys
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
# pyrefly: ignore [missing-import]
import joblib

# Configurações de pastas (MVC SAMS)
diretorio_atual = os.path.dirname(os.path.abspath(__file__))
diretorio_pai = os.path.dirname(diretorio_atual)

caminho_csv = os.path.join(diretorio_pai, "data", "dataset_features.csv")
caminho_modelo = os.path.join(diretorio_pai, "core", "rf_model_sams.pkl")

def train_sams_model():
    print("="*65)
    print("🤖 SAMS - Treinamento de Inteligência Artificial (Random Forest)")
    print("="*65)
    
    if not os.path.exists(caminho_csv):
        print(f"\n[ERRO] O dataset não foi encontrado no caminho esperado:\n{caminho_csv}")
        return
        
    print(f"\n1. Carregando dados acústicos de: {os.path.basename(caminho_csv)}")
    try:
        df = pd.read_csv(caminho_csv)
    except Exception as e:
        print(f"[ERRO] Falha ao ler arquivo CSV: {e}")
        return
        
    # Limpeza básica (Ignora arquivos que ainda não foram classificados manualmente)
    df = df[df['modo_transferencia'] != 'A_DEFINIR']
    
    if df.empty:
        print("[ERRO] O dataset está vazio ou não possui ensaios com modos preenchidos.")
        return
        
    print(f"   -> Encontradas {len(df)} amostras de áudio válidas.")
    print("   -> Distribuição atual de classes (Modos de Soldagem):")
    # Imprime quantas amostras de Spray, Globular e CC existem
    distribuicao = df['modo_transferencia'].value_counts()
    for classe, count in distribuicao.items():
        print(f"      * {classe}: {count} amostras")
        
    # Preparando as Features (Matemática: X) e o Label/Alvo (Resposta: y)
    colunas_ignoradas = ['id_ensaio', 'nome_arquivo', 'modo_transferencia']
    features_matematicas = [col for col in df.columns if col not in colunas_ignoradas]
    
    X = df[features_matematicas]
    y = df['modo_transferencia']
    
    # ==========================================================
    # SEPARAÇÃO 80% TREINO / 20% TESTE (ESTRATIFICADO)
    # ==========================================================
    # A mágica que você pediu: O parâmetro 'stratify=y' garante que 
    # o algoritmo pegará EXATAMENTE 80% de Curtos, 80% de Spray, etc,
    # para que nenhuma classe fique em desvantagem no treinamento.
    print("\n2. Separando os dados em 80% (Estudo) e 20% (Prova Final)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"   -> Dados para Treinamento da IA: {len(X_train)} amostras")
    print(f"   -> Dados para o Teste Final:     {len(X_test)} amostras escondidas")
    
    # ==========================================================
    # TREINAMENTO DO MODELO
    # ==========================================================
    print("\n3. Criando e treinando a Floresta Aleatória (Random Forest)...")
    modelo_rf = RandomForestClassifier(n_estimators=100, random_state=42)
    modelo_rf.fit(X_train, y_train)
    print("   -> Treinamento concluído com sucesso!")
    
    # ==========================================================
    # AVALIAÇÃO DO MODELO (O "Boletim" da IA)
    # ==========================================================
    print("\n4. Aplicando a 'Prova Final' (Testando com dados que a IA nunca viu)...")
    y_pred = modelo_rf.predict(X_test)
    
    acuracia = accuracy_score(y_test, y_pred)
    print(f"\n🏆 PRECISÃO GERAL DA IA: {acuracia * 100:.2f}% de acertos!\n")
    
    print("📊 Detalhes de Precisão por Modo de Transferência:")
    # classification_report imprime uma tabela linda de precisão, recall e f1-score
    print(classification_report(y_test, y_pred))
    
    print("\n🧠 O que a IA achou mais importante? (Peso de cada característica):")
    importancias = modelo_rf.feature_importances_
    # Combina a coluna e o peso para exibir
    feature_importances = sorted(zip(features_matematicas, importancias), key=lambda x: x[1], reverse=True)
    for col, imp in feature_importances:
        print(f"   - {col}: {imp * 100:.1f}% de influência na decisão")
        
    # ==========================================================
    # SALVAR O CÉREBRO (Para uso no Gêmeo Digital depois)
    # ==========================================================
    joblib.dump(modelo_rf, caminho_modelo)
    print(f"\n💾 O Cérebro treinado foi exportado e salvo com sucesso em:\n   {caminho_modelo}")
    print("\nA Fase 2 está completa! O SAMS agora tem a sua própria Inteligência Artificial.")

if __name__ == "__main__":
    train_sams_model()
