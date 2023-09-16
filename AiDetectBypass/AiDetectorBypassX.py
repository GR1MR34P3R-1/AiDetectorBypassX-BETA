import tkinter as tk
from tkinter import scrolledtext, messagebox
import nltk
import random
import re
import threading
from tkinter import ttk
from nltk.corpus import wordnet, words as nltk_words
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.tag import pos_tag
import language_tool_python

nltk.download("punkt")
nltk.download("wordnet")
nltk.download("words")
nltk.download("averaged_perceptron_tagger")

common_words_set = set(nltk_words.words())
emphasis_words = ["very", "quite", "so", "too", "really"]

# Create a LanguageTool object for grammar and spelling checking
language_tool = language_tool_python.LanguageTool('en-US')

# Function to get synonyms of a word using NLTK's WordNet
def get_synonyms(word):
    synonyms = []
    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            synonym = lemma.name()
            if synonym in common_words_set and synonym != word:
                synonyms.append(synonym)
    return synonyms

# Function to paraphrase a sentence while avoiding plagiarism
def paraphrase_sentence(sentence):
    words = word_tokenize(sentence)
    paraphrased_words = []

    for word in words:
        synonyms = get_synonyms(word)
        if synonyms and random.randint(0, 100) < 20:
            context_synonyms = [syn for syn in synonyms if syn in sentence]
            if context_synonyms:
                synonym = random.choice(context_synonyms)
            else:
                synonym = random.choice(synonyms)
            if word.isupper():
                synonym = synonym.upper()
            paraphrased_words.append(synonym)
        else:
            paraphrased_words.append(word)

    paraphrased_sentence = " ".join(paraphrased_words)
    return paraphrased_sentence

# Function to emphasize adjectives in the text
def emphasize_adjectives(text, percent_to_change_adj):
    words = word_tokenize(text)
    tagged_words = pos_tag(words)
    output_words = []
    dont_change = False

    for word, pos in tagged_words:
        if pos.startswith('JJ') and not dont_change and random.randint(0, 100) < percent_to_change_adj:
            emp_word = random.choice(emphasis_words)
            output_words.append(emp_word)
            output_words.append(word)
            dont_change = True
        else:
            output_words.append(word)
            dont_change = False

    emphasized_sentence = " ".join(output_words)

    original_adjectives = [word for word, pos in tagged_words if pos.startswith('JJ')]
    emphasized_adjectives = [word for word, pos in pos_tag(emphasized_sentence.split()) if pos.startswith('JJ')]
    if original_adjectives and emphasized_adjectives:
        emphasized_sentence = emphasized_sentence.replace(emphasized_adjectives[0], original_adjectives[0], 1)

    return emphasized_sentence

# Function to automatically calculate the percentage based on character count
def calculate_percentage(char_count):
    if char_count <= 500:
        return random.uniform(20, 40)  # Adjusted percentage range for better results
    elif char_count <= 1000:
        return random.uniform(15, 30)  # Adjusted percentage range
    elif char_count <= 2000:
        return random.uniform(10, 20)  # Adjusted percentage range
    else:
        return random.uniform(5, 15)   # Adjusted percentage range

# Function to handle text modification while avoiding plagiarism
def modify_text():
    input_text = input_text_widget.get("1.0", tk.END)
    input_text = input_text.strip()
    if not input_text:
        messagebox.showinfo("Warning", "Input text is empty.")
        return

    try:
        # Perform spelling and grammar checking
        corrected_text = language_tool.correct(input_text)

        char_count = len(corrected_text)
        percent_to_change_syn = calculate_percentage(char_count)
        percent_to_change_adj = calculate_percentage(char_count)

        paragraphs = sent_tokenize(corrected_text)
        modified_paragraphs = []

        for paragraph in paragraphs:
            # Preserve formatting elements (numbers, abbreviations, and bold text)
            preserved_paragraph = re.sub(r'(\d+\.)|([A-Z]+\.)', r' \1\2 ', paragraph)
            preserved_paragraph = re.sub(r'"(.*?)"', r'"\1"', preserved_paragraph)  # Replace double quotes

            # Paraphrase the sentence while avoiding plagiarism
            paraphrased_sentence = paraphrase_sentence(preserved_paragraph)

            # Emphasize adjectives in the paraphrased sentence
            emphasized_sentence = emphasize_adjectives(paraphrased_sentence, percent_to_change_adj)

            # Remove extra spaces before punctuation
            emphasized_sentence = re.sub(r'\s+([.,;!?])', r'\1', emphasized_sentence)

            modified_paragraphs.append(emphasized_sentence)

        modified_text = '\n'.join(modified_paragraphs)

        # Replace double quotes with straight quotes
        modified_text = modified_text.replace("“", '"').replace("”", '"')

        output_text_widget.delete("1.0", tk.END)
        output_text_widget.insert(tk.END, modified_text)

        messagebox.showinfo("Success", "Text modification completed successfully.")

    except Exception as e:
        messagebox.showinfo("Error", f"An error occurred: {str(e)}")

# Function to perform text modification in a separate thread
def modify_text_thread():
    modify_button.config(state=tk.DISABLED)

    try:
        modify_text()

        modify_button.config(state=tk.NORMAL)
        progress_bar.stop()
    except Exception as e:
        messagebox.showinfo("Error", f"An error occurred: {str(e)}")

# Function to trigger text modification using threading
def start_modification_thread():
    modification_thread = threading.Thread(target=modify_text_thread)
    modification_thread.start()
    progress_bar.start()

window = tk.Tk()
window.title("Text Modifier")

input_label = tk.Label(window, text="Input Text:")
input_label.pack()

# Set focus to the input text box when the window opens
input_text_widget = scrolledtext.ScrolledText(window, wrap=tk.WORD, width=40, height=10)
input_text_widget.pack()
input_text_widget.focus_set()  # Set focus here

percent_adj_label = tk.Label(window, text="Auto-Calculated Percentage of Adjective Emphasis:")
percent_adj_label.pack()

modify_button = tk.Button(window, text="Modify Text", command=start_modification_thread)
modify_button.pack()

output_label = tk.Label(window, text="Modified Text:")
output_label.pack()

output_text_widget = scrolledtext.ScrolledText(window, wrap=tk.WORD, width=40, height=10)
output_text_widget.pack()

progress_bar = ttk.Progressbar(window, mode="indeterminate")
progress_bar.pack()

window.mainloop()
