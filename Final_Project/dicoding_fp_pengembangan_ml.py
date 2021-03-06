# -*- coding: utf-8 -*-
"""dicoding_FP_pengembangan ML

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1qA_KUTxD_05NdOIdPshXDgC-W_30s6xA

**DATA DIRI**

**NAMA : MUHAMMAD ISMAIL**

**DOMISILI : SURABAYA, JAWA TIMUR**

**FINAL PROJECT PENGEMBANGAN ML**
"""

import tensorflow as tf
#mengecek version dari tensorflow
tf.__version__

"""**IMPORT LIBRARY PENTING DAN MENDOWNLOAD DATASET**"""

# Commented out IPython magic to ensure Python compatibility.
# basic librareis
import pandas as pd
import numpy as np
from pathlib import Path
import zipfile
import os
import glob

#plotting and visualization
import matplotlib.pyplot as plt 
# %matplotlib inline
import seaborn as sns 

# preprocessing
from sklearn.model_selection import train_test_split

#modelling
from keras.models import Model,Sequential
from keras.layers import Conv2D, MaxPooling2D, Dropout, Dense,Flatten

!pip install kaggle

#mengupload API key akun kaggle
from google.colab import files
files.upload()

# membuat directory dari kaggle.json
!mkdir -p ~/.kaggle
!cp kaggle.json ~/.kaggle/
!chmod 600 ~/.kaggle/kaggle.json
!ls ~/.kaggle

#download dataset
!kaggle datasets download -d chetankv/dogs-cats-images

local_zip = 'dogs-cats-images.zip'

zip_ref = zipfile.ZipFile(local_zip, 'r')
zip_ref.extractall()
zip_ref.close() 

base_dir = 'dataset'

os.listdir(base_dir)

# Create a list with the filepaths for training and testing
dir_ = Path('dataset/training_set')
train_filepaths = list(dir_.glob(r'**/*.jpg'))

dir_ = Path('dataset/test_set')
test_filepaths = list(dir_.glob(r'**/*.jpg'))

"""**PREPROCESSING DATA**"""

def ImageProcessing(filepath):

    labels = [str(filepath[i]).split("/")[-2] \
              for i in range(len(filepath))]

    filepath = pd.Series(filepath, name='Foto').astype(str)
    labels = pd.Series(labels, name='Jenis')

    # Meng-concat filepath dan label
    df = pd.concat([filepath, labels], axis=1)

    # Meng-Shuffle DataFrame dan Me-reset index
    df = df.sample(frac=1,random_state=0).reset_index(drop = True)
    
    return df

train_df = ImageProcessing(train_filepaths)
test_df = ImageProcessing(test_filepaths)

print('Jumlah data training adalah: {}' .format(train_df.shape[0]))
print('Jumlah data testing adalah: {}' .format(test_df.shape[0]))

train_df.head(5)

test_df.head(5)

"""**VISUALISASI DATA**"""

plt.figure(figsize=(12,4))
sns.set_style("darkgrid")
sns.countplot(train_df['Jenis'])

"""**AUGMENTASI GAMBAR**"""

#augmentasi gambar
from tensorflow.keras.preprocessing.image import ImageDataGenerator

train_datagen = ImageDataGenerator(
                    rescale=1./255,
                    rotation_range=20,
                    horizontal_flip=True,
                    shear_range = 0.2,
                    fill_mode = 'nearest')
 
test_datagen = ImageDataGenerator(
                    rescale=1./255,
                    rotation_range=20,
                    horizontal_flip=True,
                    shear_range = 0.2,
                    fill_mode = 'nearest')

"""**IMAGE GENERATOR**"""

#image data generator
img_size = 224
batch_size = 32

train_generator = train_datagen.flow_from_dataframe(
        dataframe = train_df,
        x_col='Foto',
        y_col='Jenis', 
        target_size=(img_size, img_size),  
        batch_size= batch_size,
        shuffle=True,
        subset = "training",
        class_mode='categorical')
 
# validation_generator = train_datagen.flow_from_dataframe(
#         dataframe = train_df,
#         x_col='Foto',
#         y_col='Jenis', 
#         target_size=(img_size, img_size),  
#         batch_size= batch_size,
#         shuffle=True,
#         subset = "validation",
#         class_mode='categorical')

test_generator = test_datagen.flow_from_dataframe(
        dataframe=test_df,
        x_col='Foto',
        y_col='Jenis',
        target_size=(img_size, img_size),
        color_mode='rgb',
        class_mode='categorical',
        batch_size=batch_size,
        shuffle=False
    )

model = tf.keras.models.Sequential([
    tf.keras.layers.Conv2D(16, (3,3), activation='relu', input_shape=(224, 224, 3)),
    tf.keras.layers.MaxPooling2D(2, 2),
    tf.keras.layers.Conv2D(32, (3,3), activation='relu'),
    tf.keras.layers.MaxPooling2D(2,2),
    tf.keras.layers.Conv2D(64, (3,3), activation='relu'),
    tf.keras.layers.MaxPooling2D(2,2),
    tf.keras.layers.Conv2D(128, (3,3), activation='relu'),
    tf.keras.layers.MaxPooling2D(2,2),
    tf.keras.layers.Flatten(),
    tf.keras.layers.Dense(256, activation='relu'),
    tf.keras.layers.Dense(2, activation='softmax')
])

model.summary()

model.compile(loss='categorical_crossentropy',
              optimizer=tf.optimizers.Adam(),
              metrics=['accuracy'])

#membuat callback agar menghentikan epoch bila akurasi sesuai dengan yang diinginkan
class myCallback(tf.keras.callbacks.Callback):
  def on_epoch_end(self, epoch, logs={}):
    if(logs.get('accuracy') >0.9):
      print("\nAkurasi telah mencapai >90%!")
      self.model.stop_training = True
callbacks = myCallback()

history = model.fit(
      train_generator, 
      epochs = 100,  
      validation_data = test_generator, 
      verbose = 2, 
      callbacks = [callbacks])

loss = history.history['loss']
val_loss = history.history['val_loss']

plt.figure(figsize=(12, 4))
plt.plot(loss, label='Training loss')
plt.plot(val_loss, label='Validation loss')
plt.legend(loc='upper right')

plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.title('Training dan Validation Loss')

loss = history.history['accuracy']
val_loss = history.history['val_accuracy']

plt.figure(figsize=(12, 4))
plt.plot(loss, label='Training accuracy')
plt.plot(val_loss, label='Validation accuracy')
plt.legend(loc='lower right')

plt.xlabel('Epochs')
plt.ylabel('Accuracy')
plt.title('Training dan Validation Accuracy')

"""**KONVERSI MODEL KE TFLITE**"""

# Konversi model.
converter = tf.lite.TFLiteConverter.from_keras_model(model)
tflite_model = converter.convert()

with tf.io.gfile.GFile('model.tflite', 'wb') as f:
  f.write(tflite_model)