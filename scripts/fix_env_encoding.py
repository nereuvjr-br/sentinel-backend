
import os

def fix_env_encoding():
    try:
        # Tentar ler com utf-16 (padrão powershell)
        with open('.env', 'r', encoding='utf-16') as f:
            content = f.read()
        print("Lido como UTF-16")
    except:
        try:
            # Tentar utf-8
            with open('.env', 'r', encoding='utf-8') as f:
                content = f.read()
            print("Lido como UTF-8")
        except:
             # Tentar latin-1
            with open('.env', 'r', encoding='latin-1') as f:
                content = f.read()
            print("Lido como Latin-1")

    # Limpar caracteres nulos se houver
    content = content.replace('\x00', '')
    
    # Gravar como UTF-8 limpo
    with open('.env', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Gravado como UTF-8")

if __name__ == "__main__":
    fix_env_encoding()
