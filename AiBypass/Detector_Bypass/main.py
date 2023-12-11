import tkinter as tk
from tkinter import scrolledtext, messagebox, font
from tkinter import ttk
import random
import threading
from tkinter import ttk
from nltk.corpus import wordnet, words as nltk_words
import language_tool_python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import logging
import spacy

# Initialize spaCy and NLTK resources
nlp = spacy.load("en_core_web_sm")
common_words_set = set(nltk_words.words())

# Initialize language tool
language_tool = language_tool_python.LanguageTool('en-US')

# Setup logging
logging.basicConfig(filename='grammarly_checker.log', level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')

def configure_browser():
    options = webdriver.ChromeOptions()
    options.add_argument('--log-level=3')
    browser = webdriver.Chrome(options=options)
    return browser

def extract_grammarly_results_with_bs(browser):
    try:
        wait = WebDriverWait(browser, 600)
        wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "report-summary_reportList__IFgi9")))
        page_source = browser.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        report_content = soup.find_all('li', class_='report-summary_reportListItem__d0QsT')

        for item in report_content:
            content_text = item.text.lower()
            if "significant plagiarism found" in content_text:
                return "Significant Plagiarism Detected"
            elif "no plagiarism found" in content_text:
                return "No Plagiarism Detected"
        return "Unable to determine plagiarism status"
    except Exception as e:
        logging.error(f"Error while extracting results: {str(e)}")
        return None

def check_plagiarism_with_grammarly(text, progress_var):
    browser = configure_browser()
    try:
        browser.get("https://www.grammarly.com/plagiarism-checker")
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "form_textAreaInput__d_XIK"))
        )
        text_area = browser.find_element(By.CSS_SELECTOR, ".form_textAreaInput__d_XIK")
        text_area.clear()
        text_area.send_keys(text)
        submit_button = browser.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()
        plagiarism_result = extract_grammarly_results_with_bs(browser)
        return plagiarism_result
    except Exception as e:
        logging.error(f"Error during plagiarism check: {str(e)}")
        return None
    finally:
        browser.quit()

def convert_passive_to_active(sentence):
    doc = nlp(sentence)
    passive_tokens = [tok for tok in doc if tok.dep_ == "nsubjpass"]
    if passive_tokens:
        return ' '.join([tok.text if tok.dep_ != "nsubjpass" else "" for tok in doc])
    return sentence

def get_synonyms(word):
    synonyms = []
    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            synonym = lemma.name().replace('_', ' ')
            if synonym in common_words_set and synonym != word:
                synonyms.append(synonym)
    return synonyms

def get_better_synonyms(word, sentence):
    synonyms = get_synonyms(word)
    
    # Rank synonyms based on appropriateness for the context (can be enhanced with deep learning models in the future)
    ranked_synonyms = sorted(synonyms, key=lambda x: sentence_similarity(sentence.replace(word, x), sentence), reverse=True)
    
    return ranked_synonyms

def sentence_similarity(sentence1, sentence2):
    # A simple measure of sentence similarity (can be enhanced with embeddings or deep learning in the future)
    doc1 = nlp(sentence1)
    doc2 = nlp(sentence2)
    return doc1.similarity(doc2)

def paraphrase_sentence(sentence):
    doc = nlp(sentence)
    paraphrased_words = []

    named_entities = set([ent.text for ent in doc.ents])
    eligible_words = [token.text for token in doc if token.text not in named_entities and token.tag_ not in ["IN", "CC", "TO", "DT", "MD"] and token.tag_.startswith(('NN', 'VB', 'JJ', 'RB'))]
    
    words_to_paraphrase = random.sample(eligible_words, int(0.7 * len(eligible_words)))

    for token in doc:
        if token.text in words_to_paraphrase:
            synonyms = get_better_synonyms(token.text, sentence)  # Use the enhanced synonym function
            if synonyms:
                synonym = random.choice(synonyms[:3])  # Choose from top-ranked synonyms
                if token.text.istitle():
                    synonym = synonym.capitalize()
                paraphrased_words.append(synonym)
            else:
                paraphrased_words.append(token.text)
        else:
            paraphrased_words.append(token.text)

    paraphrased_sentence = " ".join(paraphrased_words)
    paraphrased_sentence = convert_passive_to_active(paraphrased_sentence)
    corrected_sentence = language_tool.correct(paraphrased_sentence)
    return corrected_sentence


def modify_and_check_thread():
    try:
        input_text = input_text_widget.get("1.0", tk.END)
        input_text = input_text.strip()
        if not input_text:
            messagebox.showinfo("Warning", "Input text is empty.")
            return
        progress_bar["value"] = 0
        plagiarized = True
        max_attempts = 15
        while plagiarized and max_attempts > 0:
            corrected_text = language_tool.correct(input_text)
            paragraphs = [sent.text for sent in nlp(corrected_text).sents]
            modified_paragraphs = []
            total_paragraphs = len(paragraphs)
            for i, paragraph in enumerate(paragraphs):
                paraphrased_sentence = paraphrase_sentence(paragraph)
                modified_paragraphs.append(paraphrased_sentence)
                progress_value = ((i + 1) / total_paragraphs) * 100
                progress_var.set(progress_value)
            modified_text = "\n".join(modified_paragraphs)
            plagiarism_result = check_plagiarism_with_grammarly(modified_text, progress_var)
            if plagiarism_result == "No Plagiarism Detected":
                plagiarized = False
            else:
                max_attempts -= 1
        if not plagiarized:
            output_text_widget.delete(1.0, tk.END)
            output_text_widget.insert(tk.END, modified_text)
            messagebox.showinfo("Success", "Successfully paraphrased the text!")
        else:
            messagebox.showerror("Failed", "Unable to paraphrase the text without plagiarism.")
    except Exception as e:
        logging.error(f"Error in modifying and checking: {str(e)}")
        messagebox.showerror("Error", f"An unexpected error occurred: {str(e)}")
    finally:
        progress_bar["value"] = 0
        btn_start["state"] = tk.NORMAL

# GUI
root = tk.Tk()
root.title("(BETA-VERSION)")
root.geometry("900x650")
root.configure(bg='#FFFFFF')

# Custom fonts
title_font = font.Font(family="Arial", size=24, weight="bold")
label_font = font.Font(family="Arial", size=16)

# Title
title_label = tk.Label(root, text="AiDetectorBypassX-BETA", font=title_font, bg='#FFFFFF', fg='#333333')
title_label.pack(pady=30)

# Input Frame
frame1 = tk.Frame(root, bg='#FFFFFF')
frame1.pack(pady=10, padx=50, fill="both", expand=True)
input_label = tk.Label(frame1, text="Input Text:", font=label_font, bg='#FFFFFF', fg='#555555')
input_label.pack(anchor="w", padx=10, pady=5)
input_text_widget = scrolledtext.ScrolledText(frame1, wrap=tk.WORD, width=80, height=8, font=('Arial', 12), bd=2, relief="solid", padx=5, pady=5)
input_text_widget.pack(padx=10, pady=10, fill="both", expand=True)

# Output Frame
frame2 = tk.Frame(root, bg='#FFFFFF')
frame2.pack(pady=10, padx=50, fill="both", expand=True)
output_label = tk.Label(frame2, text="Paraphrased Text:", font=label_font, bg='#FFFFFF', fg='#555555')
output_label.pack(anchor="w", padx=10, pady=5)
output_text_widget = scrolledtext.ScrolledText(frame2, wrap=tk.WORD, width=80, height=8, font=('Arial', 12), bd=2, relief="solid", padx=5, pady=5)
output_text_widget.pack(padx=10, pady=10, fill="both", expand=True)

# Start Button
btn_start = tk.Button(root, text="Start Paraphrasing", command=lambda: threading.Thread(target=modify_and_check_thread).start(), font=('Arial', 14), bg='#4CAF50', fg='white', relief=tk.GROOVE, width=20)
btn_start.pack(pady=20)

# Progress bar
progress_var = tk.DoubleVar()
progress_bar = ttk.Progressbar(root, orient="horizontal", length=800, mode="determinate", variable=progress_var, style='TProgressbar')
progress_bar.pack(pady=10)

# Set the focus to the input_text_widget
input_text_widget.focus_set()

root.mainloop()