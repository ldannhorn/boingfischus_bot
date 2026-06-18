with open('words_de.txt', 'r', encoding='utf-8') as src, \
     open('res.txt', 'x', encoding='utf-8') as  res:
    
    for line in src.readlines():
        res.write(line.casefold())
