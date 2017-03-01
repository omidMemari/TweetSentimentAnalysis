import numpy as np
import os

from keras.utils.np_utils import to_categorical
from keras.layers import Dense, Input, Dropout, merge
from keras.layers import Conv1D, MaxPooling1D, Embedding, GlobalMaxPooling1D
from keras.callbacks import ModelCheckpoint
from keras.models import Model

from keras import backend as K

from utils import load_both, prepare_validation_set, load_embedding_matrix, prepare_tokenized_data


MAX_NB_WORDS = 16000
MAX_SEQUENCE_LENGTH = 140
VALIDATION_SPLIT = 0.1
EMBEDDING_DIM = 300

EMBEDDING_DIR = 'embedding'
EMBEDDING_TYPE = 'glove.6B.300d.txt' # 'glove.6B.%dd.txt' % (EMBEDDING_DIM)

concat_axis = 1 if K.image_dim_ordering() == 'th' else -1

texts, labels, label_map = load_both()

data, word_index = prepare_tokenized_data(texts, MAX_NB_WORDS, MAX_SEQUENCE_LENGTH)

labels = to_categorical(np.asarray(labels))
print('Shape of data tensor:', data.shape)
print('Shape of label tensor:', labels.shape)

# split the data into a training set and a validation set
x_train, y_train, x_val, y_val = prepare_validation_set(data, labels, VALIDATION_SPLIT)

# prepare embedding matrix
nb_words = min(MAX_NB_WORDS, len(word_index))
embedding_matrix = load_embedding_matrix(EMBEDDING_DIR + "/" + EMBEDDING_TYPE,
                                          word_index, MAX_NB_WORDS, EMBEDDING_DIM)

# load pre-trained word embeddings into an Embedding layer
# note that we set trainable = False so as to keep the embeddings fixed
embedding_layer = Embedding(nb_words,
                            EMBEDDING_DIM,
                            weights=[embedding_matrix],
                            input_length=MAX_SEQUENCE_LENGTH,
                            trainable=False, mask_zero=False)



print('Training model.')

checkpoint = ModelCheckpoint('models/n_conv_model (glove 300).h5', monitor='val_fbeta_score', verbose=2, save_weights_only=True,
                             save_best_only=True, mode='max')

# train a 1D convnet with global maxpooling
sequence_input = Input(shape=(MAX_SEQUENCE_LENGTH,), dtype='int32')
embedded_sequences = embedding_layer(sequence_input)

x = Conv1D(512, 5, activation='relu', border_mode='same', init='he_uniform')(embedded_sequences)
#x = MaxPooling1D(3)(x)

y = Conv1D(512, 3, activation='relu', border_mode='same', init='he_uniform')(embedded_sequences)
#y = MaxPooling1D(3)(y)

w = Conv1D(512, 4, activation='relu', border_mode='same', init='he_uniform')(embedded_sequences)
#w = MaxPooling1D(3)(w)

z = Conv1D(512, 7, activation='relu', border_mode='same', init='he_uniform')(embedded_sequences)
#z = MaxPooling1D(3)(z)

m = merge([x, y, z, w], mode='concat', concat_axis=concat_axis)

x = GlobalMaxPooling1D()(m)

x = Dense(1024, activation='relu')(x)
x = Dropout(0.5)(x)

preds = Dense(3, activation='softmax')(x)

model = Model(sequence_input, preds)

model.summary()
model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['acc', 'fbeta_score'])

model.fit(x_train, y_train, validation_data=(x_val, y_val), callbacks=[checkpoint], nb_epoch=100, batch_size=100)

model.load_weights('models/n_conv_model (glove 300).h5')

scores = model.evaluate(x_val, y_val, batch_size=100)

for score, metric_name in zip(scores, model.metrics_names):
    print(metric_name, ':', score)
