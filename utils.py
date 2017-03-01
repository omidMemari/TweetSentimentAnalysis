import pandas as pd
import numpy as np
import os
import pickle

from keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences

if not os.path.exists('models/'):
    os.makedirs('models/')

train_obama_path = "data/obama_csv.csv"
train_romney_path = "data/romney_csv.csv"


def load_obama():
    obama_df = pd.read_csv(train_obama_path, sep='\t', encoding='latin1')
    # Remove rows who have no class label attached, can hand label later
    obama_df = obama_df[pd.notnull(obama_df['label'])]
    obama_df['label'] = obama_df['label'].astype(np.int)

    texts = []  # list of text samples
    labels_index = {-1: 0,
                    0: 1,
                    1: 2}  # dictionary mapping label name to numeric id
    labels = []  # list of label ids

    obama_df = obama_df[obama_df['label'] != 2] # drop all rows with class = 2

    nb_rows = len(obama_df)
    for i in range(nb_rows):
        row = obama_df.iloc[i]
        texts.append(str(row['tweet']))
        labels.append(labels_index[int(row['label'])])

    return texts, labels, labels_index


def load_romney():
    romney_df = pd.read_csv(train_romney_path, sep='\t', encoding='latin1')
    # Remove rows who have no class label attached, can hand label later
    romney_df = romney_df[pd.notnull(romney_df['label'])]
    romney_df['label'] = romney_df['label'].astype(np.int)

    texts = []  # list of text samples
    labels_index = {-1: 0,
                    0: 1,
                    1: 2}  # dictionary mapping label name to numeric id
    labels = []  # list of label ids

    romney_df = romney_df[romney_df['label'] != 2]  # drop all rows with class = 2

    nb_rows = len(romney_df)
    for i in range(nb_rows):
        row = romney_df.iloc[i]
        texts.append(str(row['tweet']))
        labels.append(labels_index[int(row['label'])])

    return texts, labels, labels_index


def load_both():
    obama_df = pd.read_csv(train_obama_path, sep='\t', encoding='latin1')
    # Remove rows who have no class label attached, can hand label later
    obama_df = obama_df[pd.notnull(obama_df['label'])]
    obama_df['label'] = obama_df['label'].astype(np.int)

    romney_df = pd.read_csv(train_romney_path, sep='\t', encoding='latin1')
    # Remove rows who have no class label attached, can hand label later
    romney_df = romney_df[pd.notnull(romney_df['label'])]
    romney_df['label'] = romney_df['label'].astype(np.int)

    texts = []  # list of text samples
    labels_index = {-1: 0,
                    0: 1,
                    1: 2}  # dictionary mapping label name to numeric id
    labels = []  # list of label ids

    obama_df = obama_df[obama_df['label'] != 2]  # drop all rows with class = 2
    romney_df = romney_df[romney_df['label'] != 2]  # drop all rows with class = 2

    nb_rows = len(obama_df)
    for i in range(nb_rows):
        row = obama_df.iloc[i]
        texts.append(str(row['tweet']))
        labels.append(labels_index[int(row['label'])])

    nb_rows = len(romney_df)
    for i in range(nb_rows):
        row = romney_df.iloc[i]
        texts.append(str(row['tweet']))
        labels.append(labels_index[int(row['label'])])

    return texts, labels, labels_index


def load_embedding_matrix(embedding_path, word_index, max_nb_words, embedding_dim, print_error_words=True):
    if not os.path.exists('data/embedding_matrix index length %d max words %d embedding dim %d.npy' % (len(word_index),
                                                                                                       max_nb_words,
                                                                                                       embedding_dim)):
        embeddings_index = {}
        error_words = []

        f = open(embedding_path, encoding='utf8')
        for line in f:
            values = line.split()
            word = values[0]
            try:
                coefs = np.asarray(values[1:], dtype='float32')
                embeddings_index[word] = coefs
            except Exception:
                error_words.append(word)

        f.close()

        if len(error_words) > 0:
            print("%d words were not added." % (len(error_words)))
            if print_error_words:
                print("Words are : \n", error_words)

        print('Preparing embedding matrix.')

        # prepare embedding matrix
        nb_words = min(max_nb_words, len(word_index))
        embedding_matrix = np.zeros((nb_words, embedding_dim))
        for word, i in word_index.items():
            if i >= max_nb_words:
                continue
            embedding_vector = embeddings_index.get(word)
            if embedding_vector is not None:
                # words not found in embedding index will be all-zeros.
                embedding_matrix[i] = embedding_vector

        np.save('data/embedding_matrix index length %d max words %d embedding dim %d.npy' % (len(word_index),
                                                                                                max_nb_words,
                                                                                                embedding_dim),
                embedding_matrix)

        print('Saved embedding matrix')

    else:
        embedding_matrix = np.load('data/embedding_matrix index length %d max words %d embedding dim %d.npy' %
                                                                                                (len(word_index),
                                                                                                max_nb_words,
                                                                                                embedding_dim))

        print('Loaded embedding matrix')

    return embedding_matrix


def prepare_tokenized_data(texts, max_nb_words, max_sequence_length):
    if not os.path.exists('data/tokenizer.pkl'):
        tokenizer = Tokenizer(nb_words=max_nb_words)
        tokenizer.fit_on_texts(texts)

        with open('data/tokenizer.pkl', 'wb') as f:
            pickle.dump(tokenizer, f)

        print('Saved tokenizer.pkl')
    else:
        with open('data/tokenizer.pkl', 'rb') as f:
            tokenizer = pickle.load(f)
            print('Loaded tokenizer.pkl')

    sequences = tokenizer.texts_to_sequences(texts)

    word_index = tokenizer.word_index
    print('Found %s unique tokens.' % len(word_index))

    data = pad_sequences(sequences, maxlen=max_sequence_length)

    return (data, word_index)


def prepare_validation_set(data, labels, validation_split=0.1, seed=1000):
    np.random.seed(seed)

    indices = np.arange(data.shape[0])
    np.random.shuffle(indices)
    data = data[indices]
    labels = labels[indices]
    nb_validation_samples = int(validation_split * data.shape[0])

    x_train = data[:-nb_validation_samples]
    y_train = labels[:-nb_validation_samples]
    x_val = data[-nb_validation_samples:]
    y_val = labels[-nb_validation_samples:]

    return (x_train, y_train, x_val, y_val)


if __name__ == '__main__':
    texts, labels, label_map = load_obama()

