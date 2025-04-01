import os
from supabase import create_client, Client

# Configuração do Supabase (SUA URL E KEY AQUI)
SUPABASE_URL = "https://brehfssbmphoqgmmckrr.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJyZWhmc3NibXBob3FnbW1ja3JyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDI5NDIxMzgsImV4cCI6MjA1ODUxODEzOH0.g7EPcTSKw5froygzwKFKGh7ktYaEcBVFotK5MJMp0Qo"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def test_connection():
    """Testa a conexão com o Supabase"""
    try:
        response = supabase.table("departamento").select("*").execute()
        print("✅ Conexão bem-sucedida!")
        print("Dados iniciais:", response.data)
    except Exception as e:
        print(f"❌ Falha na conexão: {str(e)}")

if __name__ == "__main__":
    test_connection()