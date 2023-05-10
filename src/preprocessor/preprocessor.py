import logging
import nltk
import re


class Preprocessor:
    def __init__(self):
        # Download & apply indonesian stopword database
        nltk.download('stopwords')
        self.stop_words = set(nltk.corpus.stopwords.words('indonesian'))

        self.store_replacement_words()

    # Store additional words to be replaced
    def store_replacement_words(self):
        file_path = 'src/preprocessor/replacement_word_list.txt'

        self.replacement_words = {}
        with open(file_path, 'r') as file:
            for line in file.readlines():
                word = line.strip().split(',')
                before_replace = word[0].strip()
                after_replace = word[1].strip()

                self.replacement_words[before_replace] = after_replace

    def run(self, text):
        logging.debug("text: %s", text)
        text = text.lower()
        
        logging.debug("lowered text: %s", text)

        # Remove http(s), hashtags, username, RT
        text = re.sub(r'http\S+', ' ', text)
        text = re.sub(r'#\S+', ' ', text)
        text = re.sub(r'@[a-zA-Z0-9_]+', ' ', text)
        text = re.sub(r'RT\s', ' ', text)
        text = re.sub(r'[^a-zA-Z0-9]', ' ', text)

        logging.debug("cleaned text: %s", text)

        # Change abbreviations
        new_text = ""
        for word in text.split():
            expanded_word = self.replacement_words.get(word, word)

            # Don't include stopwords
            if expanded_word in self.stop_words:
                continue

            new_text += " " + expanded_word
            
        logging.debug("expanded text: %s", text)

        return new_text.strip()


preprocessor = Preprocessor()
