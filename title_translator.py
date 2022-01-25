from googletrans import Translator
import os

translator = Translator()

DIR_PATH = ''

def translate_files_into_korean(DIR_PATH):
    for f in os.listdir(DIR_PATH):
        title = f.replace('.pdf','')
        print(title)
        translated = translator.translate(title, dest='ch')
        print(translated.text)
        dest = os.path.join(DIR_PATH, f'{translated.text}.pdf')
        old = os.path.join(DIR_PATH, f)
        os.rename(old, dest)
    print("DONE")

if __name__ == '__main__':
    translate_files_into_korean(DIR_PATH)
