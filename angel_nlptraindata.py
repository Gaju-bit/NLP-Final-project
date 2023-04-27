# -*- coding: utf-8 -*-
"""Angel_NLPTraindata.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1LG8tNbFZUFMnEYNrtEgRePAHYNqt2Wvx
"""

#Ibo Dataset
!wget https://github.com/afrisenti-semeval/afrisent-semeval-2023/blob/main/data/ibo/train.tsv
!wget https://github.com/afrisenti-semeval/afrisent-semeval-2023/blob/main/data/ibo/test.tsv


#Hausa Dataset
#!wget https://github.com/afrisenti-semeval/afrisent-semeval-2023/tree/main/data/hau/train.tsv
#!wget https://github.com/afrisenti-semeval/afrisent-semeval-2023/tree/main/data/hau/test.tsv


# #Nigerian Pidgin dataset
#!wget https://github.com/afrisenti-semeval/afrisent-semeval-2023/tree/main/data/pcm/train.tsv
#!wget https://github.com/afrisenti-semeval/afrisent-semeval-2023/tree/main/data/pcm/test.tsv



!pip install -Uqq fastbook
import fastbook
fastbook.setup_book()
from fastai.vision.all import *
from fastbook import *

import pandas as pd
import numpy as np

from bs4 import BeautifulSoup
import requests

from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from keras.regularizers import l2
import tensorflow as tf
from keras import models
from keras import layers
from keras import regularizers
from keras.layers import LSTM


from random import randint
#data_frame_ibo = pd.read_tsv("train.tsv", sep="\t", error_bad_lines=False)

import csv

"""PRE-CLEANING CULTURE:
Setting up libraries and function for process unclean data into clean data
"""

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import string

# Download necessary NLTK resources
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('wordnet')

# Define preprocessing function
def preprocess_text(text):
    # Convert to lowercase
    text = text.lower()
    
    # Remove punctuation
    text = text.translate(str.maketrans("", "", string.punctuation))
    
    # Tokenize text into words
    words = word_tokenize(text)
    
    # Remove stop words
    # stop_words = set(stopwords.words('english'))
    # words = [w for w in words if not w in stop_words]
    
    # Lemmatize words
    lemmatizer = WordNetLemmatizer()
    words = [lemmatizer.lemmatize(w) for w in words]
    
    # Convert list of words back to string
    text = " ".join(words)
    
    return text

"""THE CLEANING PROCESS"""

def clean(filename):
  data = []
  emotion = []
  with open(filename, 'r') as f:
      reader = csv.reader(f, delimiter='\t')
      for row in reader:
          soup = BeautifulSoup(str(row), 'html.parser')
          text = soup.text

          #Cleaning the data
          text = preprocess_text(text)

          if len(text.split(" ")) > 1:  #usernames are skipped
            emo = text[text.rindex(" ")+1:] #identifying the emotion since it is the last word at the end of every sentence
            
            if emo  == 'negative' or emo == 'positive' or emo == 'neutral': #filtering chuff [e.g words about the website which has noting to do with the conversation]
              data.append(text[:text.rindex(" ")])
              emotion.append(emo)
  return data, emotion

data_r = []
emotion = []


data_r, emotion = clean("train.tsv")

emotion_sequence = []
for each_emotion in emotion:
  if each_emotion == 'negative':
    emotion_sequence.append(-1)
  if each_emotion == 'neutral':
    emotion_sequence.append(0)
  if each_emotion == 'positive':
    emotion_sequence.append(1)

#if validation is not part of train uncomment
# val_data, val_emotion = clean("dev.tsv")

"""CLEANED DATA SAMPLE"""

data_r

"""DATA FRAMING"""

data = pd.DataFrame({
    "text": data_r,
    "emotion": emotion
})

data

"""CONVERTING DATASET INTO NUMPY ARRAYS"""

data = np.array(data[["text","emotion"]])

data

"""SETTING HYPER-PARAMETERS"""

VOCAB_SIZE = 1024
BATCH_SIZE = 32
LEARNING_RATE = 0.01
EPOCH = 10
EMBEDDED_DIMENSION = 16
HIDDEN_LAYER = 10

"""SEPARATING TRAIN FROM VALIDATION"""

train_data = []
train_emotion = []

val_data = []
val_emotion = []

selected = []
for i in range(int(len(data_r)*0.2)):
  selected.append(randint(0,len(data_r)))

for j in range(len(data_r)):
  if j in selected:
    val_data.append(data_r[j])
    val_emotion.append(emotion_sequence[j])
  else:
    train_data.append(data_r[j])
    train_emotion.append(emotion_sequence[j])

print("Training size:",len(train_data))
print("Validation size:",len(val_data))
print(len(data_r))

"""TOKENIZATION, SEQUENCING AND EMBEDDING OF TEXTS"""

tokenizer = Tokenizer(num_words=VOCAB_SIZE, oov_token="<OOV>")
tokenizer.fit_on_texts(train_data)

# independent_words = tokenizer.word_index

train_text_sequences = tokenizer.texts_to_sequences(train_data)
padded_train_data = pad_sequences(train_text_sequences, maxlen=100, padding='post', truncating='post')

val_text_sequences = tokenizer.texts_to_sequences(val_data)
padded_val_data = pad_sequences(val_text_sequences, maxlen=100, padding='post', truncating='post')


# padded_train_data = Tensor([train_text_sequences])

# padded_train_data

train_text_sequences

"""CONFIGURING THE MODEL"""

neural = tf.keras.Sequential([
    tf.keras.layers.Embedding(VOCAB_SIZE, EMBEDDED_DIMENSION,input_length=100),

    tf.keras.layers.Bidirectional(LSTM(24)),

    tf.keras.layers.Dense(16, activation='relu', kernel_regularizer=l2(LEARNING_RATE)),

    tf.keras.layers.Dense(3, activation='softmax')
])

neural.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])



neural.summary()

train_emotion = tf.keras.utils.to_categorical(train_emotion, num_classes=3)
val_emotion = tf.keras.utils.to_categorical(val_emotion, num_classes=3)

learned_outputs = neural.fit(
    padded_train_data.tolist(), train_emotion.tolist(), epochs=EPOCH, batch_size = BATCH_SIZE,
    validation_data=(padded_val_data.tolist(), val_emotion.tolist()),
    verbose=2
)

import matplotlib.pyplot as plt

def plot_graphs(history, string):
  plt.plot(history.history[string])
  plt.plot(history.history['val_'+string])
  plt.xlabel("Epochs")
  plt.ylabel(string)
  plt.legend([string, 'val_'+string])
  plt.show()
  
plot_graphs(learned_outputs, "accuracy")
plot_graphs(learned_outputs, "loss")

"""TESTING"""

def cleanTest(filename):
  data = []
  emotion = []
  tweet = False
  with open(filename, 'r') as f:
      reader = csv.reader(f, delimiter='\t')
      for row in reader:
          soup = BeautifulSoup(str(row), 'html.parser')
          text = soup.text
          
          ## Cleaning the data
          text = preprocess_text(text)
          if text == 'tweet':
            tweet = True
            continue

          if tweet:
            if len(text) == 0:
              continue

            if text  == 'negative' or text == 'positive' or text == 'neutral': #filtering chuff [e.g words about the website which has noting to do with the conversation]
              emotion.append(text)
            else:
              data.append(text)
          
          # if len(text.split(" ")) > 1:  #usernames are skipped
          #   emo = text[text.rindex(" ")+1:] #identifying the emotion since it is the last word at the end of every sentence
            
          #   if emo  == 'negative' or emo == 'positive' or emo == 'neutral': #filtering chuff [e.g words about the website which has noting to do with the conversation]
          #     data.append(text[:text.rindex(" ")])
          #     emotion.append(emo)
  return data, emotion

data_t, emotion_t = cleanTest("test.tsv")

tokenizer = Tokenizer(num_words=VOCAB_SIZE, oov_token="<OOV>")
tokenizer.fit_on_texts(data_t)


emotion_sequence = []
for each_emotion in emotion_t:
  if each_emotion == 'negative':
    emotion_sequence.append(-1)
  if each_emotion == 'neutral':
    emotion_sequence.append(0)
  if each_emotion == 'positive':
    emotion_sequence.append(1)


emotion_sequence = tf.keras.utils.to_categorical(emotion_sequence, num_classes=3)


# Evaluate the model on test data
test_loss, test_acc = neural.evaluate(data_t[:len(emotion_t)], emotion_sequence.tolist(), verbose=2)
print('Test loss:', test_loss)
print('Test accuracy:', test_acc)


# Make predictions on new data
predictions = neural.predict(new_data)