import os 

folder = ''
file_names = []
index = 1
with open(f"{folder}\list.txt", "w", encoding="utf-8") as file:
    for f in os.listdir(folder):
        title = f.replace('.pdf','')
        title = f'{title}\n'
        index += 1
        file.write(title)
    file.close() 

     
      