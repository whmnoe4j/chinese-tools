# Situation: I want to pair the keywords of a Chariman's Bao article with the article's text.
# I inspected the HTML to find the keywords and article text and saved them to separate files.
# Make a tab separated text file that I can import into a (modified) Anki cloze deletion note type.
# The modification replaces the "extra" field with a "word" and a "definition" field.

import codecs
from collections import defaultdict
from csv import reader, writer

# These are the script's parameters. Changing the last one lets you control the size of your sentences.
# You could add "，", "：", "；" to isolate smaller segments of text than full (often run-on) sentences.
keyFileName = "bao-key-words.txt"
textFileName = "bao-text.txt"
clozeFileName = "bao-cloze.txt"
clauseBoundaries = ["。", "？", "！"]

#
# Write a class for convenience. KeywordClozer will process the data that I extract from keyFileName and textFileName.
#

class KeywordClozer:
    """Extract sample sentences from a body of text that contains the given keywords."""

    def __init__(self, keywords, text, clause_boundaries):
        """Set up the keywords, text, and boundaries between "sentences"

        Keyword arguments:
        __keywords -- a list of dictionaries of strings. The dictionaries each contain a word, a pronunciation, and a definition.
        __text -- a list of strings from which sentences will be extracted. There should be no newlines.
        clause_boundaries -- a list of strings: the sentence-ending punctuation marks of the text.
        """
        self.__keywords = keywords
        self.__text = text
        self.clause_boundaries = clause_boundaries
        self.sentences = []
        self.clozed_sentences = []

    def delimeter_split(self):
        """Split the lines of text in self.text into "sentences" using self.clause_boundaries as punctuation marks."""
        self.sentences = []

        for line in self.__text:
            partial_text = ""
            for char in line:
                if char in self.clause_boundaries:
                    # We've found a sentence ender, so push the sentence with its ender onto self.sentences
                    self.sentences.append(partial_text + char)
                    line = line[1:]
                    partial_text = ""
                else:
                    # We're still looking for a sentence ender, so continue accumulating characters
                    partial_text = partial_text + char
                    line = line[1:]

            # If a line ends without a punctuation mark, assume it's a sentence anyway.
            # Sometimes people are lax about punctuation.
            if partial_text != "":
                self.sentences.append(partial_text)

        return (self)

    def keyword_cloze(self):
        """Given that sentences have been generated from the text, surround all occurrences of the keywords with Anki cloze tags"""

        # Split a sentnece into an array, where the "split" occurs on a keyword.
        # The join of the array is the same as the original sentence
        def isolate_keyword(sentence, word, ary):
            word_length = len(word)
            next_match = sentence.find(word)

            if next_match == -1:
                return (ary + [sentence])
            else:
                ary.append(sentence[0:next_match])
                ary.append(sentence[next_match: next_match + word_length])
                sentence = sentence[next_match + word_length:]
                return (isolate_keyword(sentence, word, ary) )

        # Given an array where some of the entries are keywords, wrap the keywords in
        # cloze strings for anki.
        def cloze_a_word(ary, word):
            clozed = []
            count = 1
            for term in ary:
                if term == word:
                    clozed.append("{{c" + str(count) + "::" + term + "}}")
                    count += 1
                else:
                    clozed.append(term)
            return (clozed)

        # Isolate the keywords in each sentence by splitting it into an array.
        clozed = []
        count = 1

        for dic in self.__keywords:
            word = dic["word"]
            for sent in self.sentences:
                if word in sent:
                    clozed.append({"sentence": "".join(cloze_a_word(isolate_keyword(sent, word, []), word)), "dictionary": dic})


        self.clozed_sentences = clozed

        return (self)




#
# Begin the program:
# We're going to process a Chairman's Bao article to extract example sentences from keywords.
#


# Fill this using a keywords file.
raw_keywords = []

# Open the keyword file.
with codecs.open(keyFileName, "rb", "utf-8") as csvFile:
  csvReader = reader((line.replace(" - ", '\t') for line in csvFile), delimiter='\t')

  # Store its contents without alteration.
  for row in csvReader:
      raw_keywords.append(row)

  # Close the keyword file.
  csvFile.close()


# Create the list of dictionaries from the raw input.
keyword_dicts = []

# The "word" entry is a tuple, since the same characters can have multiple pronunciations.
for row in raw_keywords:
    keyword_dicts.append({"word": row[0],  "pronunciation": row[1], "definition": row[2] })


# Get the lines of text.
lines = []

# Open the text file and store its lines
with codecs.open(textFileName, "rb", "utf-8") as textFile:
  text = textFile.read()
  for line in text.split("\r\n"):
      if line != "":
          lines.append(line)
  textFile.close()

# Set up the keyword clozer
clozer = KeywordClozer(keyword_dicts, lines, clauseBoundaries)

# Generate the data for cloze-delection Anki cards
clozer.delimeter_split().keyword_cloze()

# Write the cards to file.
anki_cards = []

# Convert the dictionary entry and the clozed sentence into a row in a CSV file
for sent in clozer.clozed_sentences:
    anki_cards.append([sent["dictionary"]["word"], sent["dictionary"]["definition"], sent["sentence"]])

# Open the target file for writing card data
with codecs.open(clozeFileName, "wb", "utf-8") as csvCloze:
  csvWriter = writer(csvCloze, delimiter='\t')

  # Write the card data to file
  for card in anki_cards:
      csvWriter.writerow(card)

  # Close the file
  csvCloze.close
