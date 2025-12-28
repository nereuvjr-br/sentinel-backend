
import os

def update_env():
    # Itens para adicionar
    new_item = "Improved_Wooden_Chest"
    
    with open('.env', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    new_lines = []
    found = False
    for line in lines:
        if line.startswith("EXCLUDED_ITEMS="):
            found = True
            current_val = line.strip().split("=", 1)[1]
            if new_item not in current_val:
                new_line = f"EXCLUDED_ITEMS={current_val},{new_item}\n"
                new_lines.append(new_line)
                print(f"Adicionado {new_item}")
            else:
                new_lines.append(line)
                print("Item já existe")
        else:
            new_lines.append(line)
            
    if not found:
        print("EXCLUDED_ITEMS não encontrado!")

    with open('.env', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

if __name__ == "__main__":
    update_env()
