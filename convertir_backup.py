with open("backup.json", "r", encoding="latin-1") as f:
    data = f.read()

with open("backup_utf8.json", "w", encoding="utf-8") as f:
    f.write(data)

print("Archivo convertido a UTF-8: backup_utf8.json")