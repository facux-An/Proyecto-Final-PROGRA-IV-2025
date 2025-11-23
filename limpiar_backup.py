import json

# Abrimos el archivo con latin-1 para rescatar los caracteres originales
with open("backup.json", "r", encoding="latin-1") as f:
    data = f.read()

# Guardamos en UTF-8 puro
with open("backup_utf8.json", "w", encoding="utf-8") as f:
    f.write(data)

print("Archivo convertido correctamente a UTF-8: backup_utf8.json")
