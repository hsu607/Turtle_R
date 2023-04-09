# -*- coding: utf-8 -*-
"""최종 제출 파이썬.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1Sf-Kb-hjrKne46NkHAiPNF6zkIoOu3Ym

# 0. 데이터 확인

## 1) 데이터 로딩
"""

from google.colab import drive
drive.mount('/content/drive')

import pathlib
data_dir = pathlib.Path('Data')

!mkdir 'Data'
!unzip -qq "/content/drive/MyDrive/데이터 크리에이터 캠프/대학부 데이터셋.zip" -d './Data'

"""## 2) 라이브러리 로딩"""

import pathlib
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import numpy as np
import pandas as pd
import os
import PIL
import tensorflow as tf
import shutil
import glob
import cv2

!pip install split-folders[full] 
import splitfolders

from scipy.stats import mode

from keras_preprocessing.image import array_to_img, img_to_array, load_img
from keras_preprocessing.image import ImageDataGenerator
from tensorflow.keras.layers import Conv2D, Dense, Flatten, MaxPooling2D, GlobalAveragePooling2D, Dense, Dropout
from tensorflow.keras.models import Model

from tensorflow.keras.optimizers import Adam , RMSprop 
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.models import Sequential
from tensorflow.keras.models import load_model

from keras.callbacks import Callback,ModelCheckpoint
from keras.wrappers.scikit_learn import KerasClassifier
import keras.backend as K

"""## 3) 데이터 EDA"""

data_dir = pathlib.Path('Data')
class_names = os.listdir(data_dir)

glob_dir = []
for classname in class_names:
    glob_dir.append(classname+'/*')

class_image_count = []
for classdir in glob_dir:
    class_image_count.append(len(list(data_dir.glob(classdir))))

class_image_count_df = pd.DataFrame(data = list(zip(class_names, class_image_count)), columns = ['class', 'img_count'])
class_image_count_df.sort_values(by=['class'])

plt.figure(figsize=(15,10))
plt.bar(class_image_count_df['class'], class_image_count_df['img_count'], width = .5)
plt.title("Number of Images in each Class")
plt.xlabel('Class Name')
plt.ylabel('Count')
plt.axhline(np.mean(class_image_count_df['img_count']), color='red', linestyle='solid', linewidth=2)

nrows = 7
ncols = 10

fig = plt.gcf()
fig.set_size_inches(ncols*10, nrows*7)

data_L2_12_dir = '/content/Data/L2_12'
data_L2_12_names = os.listdir(data_L2_12_dir)

next_pix = [os.path.join(data_L2_12_dir, fname) for fname in data_L2_12_names[0:70]]

for i, img_path in enumerate(next_pix):
    sp = plt.subplot(nrows, ncols, i+1)
    sp.axis('Off')

    img = mpimg.imread(img_path)
    plt.imshow(img)

plt.show()

"""# 1. 이미지 전처리

## 1) 이미지 resize
"""

def image_resize(img):
    img = PIL.Image.open(img)
    img = img.convert('RGB')
    pix = np.array(img)
    width = pix.shape[0]
    height = pix.shape[1]
    new_width = int(width / (height/256))
    resized_img = img.resize((new_width, 256))
    return resized_img

def image_save(img_class): #폴더별로 실행
    folder = img_class + '/*.*'
    for img in list(data_dir.glob(folder)):
        path = str(img)[5:]
        new_img = image_resize(img)
        new_img = new_img.convert('RGB')
        new_img.save('resized_Data/'+path, 'png')

!mkdir 'resized_Data'

data_dir = pathlib.Path('Data')
class_list = list(data_dir.glob('*'))

for img_class in class_list:
    img_class = str(img_class).split('/')[-1]
    os.makedirs('resized_Data/'+img_class)
    print(img_class)
    image_save(img_class)

nrows = 7
ncols = 10

fig = plt.gcf()
fig.set_size_inches(ncols*10, nrows*7)

resized_Data_L2_12_dir = '/content/resized_Data/L2_12'
resized_Data_L2_12_names = os.listdir(resized_Data_L2_12_dir)

next_pix = [os.path.join(resized_Data_L2_12_dir, fname) for fname in resized_Data_L2_12_names[0:70]]

for i, img_path in enumerate(next_pix):
    sp = plt.subplot(nrows, ncols, i+1)
    sp.axis('Off')

    img = mpimg.imread(img_path)
    plt.imshow(img)

plt.show()

"""## 2) 이미지 / 일러스트 분류

### 2-1 AI 모델 - L2_12에 적용
"""

L2_12_dir = '/content/resized_Data/L2_12'
L2_12_names = os.listdir(L2_12_dir)

# Load Yolo
net = cv2.dnn.readNet("/content/drive/MyDrive/데이터 크리에이터 캠프/opencv/yolov3.weights", "/content/drive/MyDrive/데이터 크리에이터 캠프/opencv/yolov3.cfg")
classes = []
with open("/content/drive/MyDrive/데이터 크리에이터 캠프/opencv/coco.names", "r") as f:
    classes = [line.strip() for line in f.readlines()]
layer_names = net.getLayerNames()
output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]
colors = np.random.uniform(0, 255, size=(len(classes), 3))

def cal_label_num(img):
    path = L2_12_dir + '/' + img
    resized_img = cv2.imread(path)
    height, width, channels = resized_img.shape

    # Detecting objects
    blob = cv2.dnn.blobFromImage(resized_img, 0.00392, (416,416), (0, 0, 0), True, crop=False)
    net.setInput(blob)
    outs = net.forward(output_layers)

    # Showing informations on the screen
    class_ids = []
    confidences = []
    boxes = []
    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > 0.5:
                # Object detected
                center_x = int(detection[0] * width)
                center_y = int(detection[1] * height)
                w = int(detection[2] * width)
                h = int(detection[3] * height)
                # Rectangle coordinates
                x = int(center_x - w / 2)
                y = int(center_y - h / 2)
                boxes.append([x, y, w, h])
                confidences.append(float(confidence))
                class_ids.append(class_id)

    indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)
    num_index = len(indexes)

    return num_index, path

!mkdir 'AI_Data'

for img in L2_12_names:
    if cal_label_num(img)[0] > 1:
        continue
    else:
        new_img = PIL.Image.open(cal_label_num(img)[1])
        new_img = new_img.convert('RGB')
        new_img.save('AI_Data/'+img, 'png')

"""#### 분류된 이미지 확인"""

nrows = 7
ncols = 10

fig = plt.gcf()
fig.set_size_inches(ncols*10, nrows*7)

AI_dir = '/content/AI_Data'
AI_names = os.listdir(AI_dir)

next_pix = [os.path.join(AI_dir, fname) for fname in AI_names[0:70]]

for i, img_path in enumerate(next_pix):
    sp = plt.subplot(nrows, ncols, i+1)
    sp.axis('Off')

    img = mpimg.imread(img_path)
    plt.imshow(img)

plt.show()

"""### 2-2 새로 정의한 함수 - L2_12에 적용"""

def most_color_per(img):
    img = PIL.Image.open(img)
    img = img.convert('RGB')
    pix = np.array(img)
    width = pix.shape[0]
    height = pix.shape[1]
    new_width = int(width / (height/50))
    resized_img = img.resize((new_width, 50))
    resized_pix = np.array(resized_img)
    pix_array = np.mean(resized_pix, axis=2).reshape(-1)
    pix_mode = int(mode(pix_array).count)
    return (pix_mode / (50*new_width)), img

def img_decision(img_class): #폴더별로 실행
    folder = img_class + '/*.*'
    for img in list(data_dir.glob(folder)):
        path = str(img)[5:]
        if most_color_per(img)[0] < 0.4:
            continue
        else:
            new_img = most_color_per(img)[1]
            new_img = new_img.convert('RGB')
            new_img.save('classified_Data/'+path, 'png')

!mkdir 'myfunction_Data'

img_list = []
file_list = os.listdir(L2_12_dir)
for i in range(len(file_list)):
    img_list.append(L2_12_dir + '/' + file_list[i])

for img in img_list:
    path = str(img)[28:]
    if most_color_per(img)[0] < 0.4:
        continue
    else:
        new_img = most_color_per(img)[1]
        new_img = new_img.convert('RGB')
        new_img.save('myfunction_Data/'+path, 'png')

"""#### 분류된 이미지 확인"""

nrows = 7
ncols = 10

fig = plt.gcf()
fig.set_size_inches(ncols*10, nrows*7)

my_function_dir = '/content/myfunction_Data'
my_function_names = os.listdir(my_function_dir)

next_pix = [os.path.join(my_function_dir, fname) for fname in my_function_names[0:70]]

for i, img_path in enumerate(next_pix):
    sp = plt.subplot(nrows, ncols, i+1)
    sp.axis('Off')

    img = mpimg.imread(img_path)
    plt.imshow(img)

plt.show()

"""### 2-3 새로 정의한 함수 - 전체에 적용"""

data_dir = pathlib.Path('resized_Data')

def most_color_per(img):
    img = PIL.Image.open(img)
    img = img.convert('RGB')
    pix = np.array(img)
    width = pix.shape[0]
    height = pix.shape[1]
    new_width = int(width / (height/50))
    resized_img = img.resize((new_width, 50))
    resized_pix = np.array(resized_img)
    pix_array = np.mean(resized_pix, axis=2).reshape(-1)
    pix_mode = int(mode(pix_array).count)
    return (pix_mode / (50*new_width)), img

def img_decision(img_class): #폴더별로 실행
    folder = img_class + '/*.*'
    for img in list(data_dir.glob(folder)):
        path = str(img)[13:]
        if most_color_per(img)[0] < 0.4:
            continue
        else:
            new_img = most_color_per(img)[1]
            new_img = new_img.convert('RGB')
            new_img.save('classified_Data/'+path, 'png')

!mkdir 'classified_Data'

class_list = list(data_dir.glob('*'))

for img_class in class_list:
    img_class = str(img_class).split('/')[-1]
    os.makedirs('classified_Data/'+img_class)
    print(img_class)
    img_decision(img_class)

"""#### classified 데이터 분포 확인"""

data_dir = pathlib.Path('classified_Data')
class_names = os.listdir(data_dir)

glob_dir = []
for classname in class_names:
    glob_dir.append(classname+'/*')

class_image_count = []
for classdir in glob_dir:
    class_image_count.append(len(list(data_dir.glob(classdir))))

class_image_count_df = pd.DataFrame(data = list(zip(class_names, class_image_count)), columns = ['class', 'img_count'])
class_image_count_df.sort_values(by=['class'])

plt.figure(figsize=(15,10))
plt.bar(class_image_count_df['class'], class_image_count_df['img_count'], width = .5)
plt.title("Number of Images in each Class")
plt.xlabel('Class Name')
plt.ylabel('Count')
plt.axhline(np.mean(class_image_count_df['img_count']), color='red', linestyle='solid', linewidth=2)

"""## 3) 이미지 Oversampling"""

augGen = ImageDataGenerator(rescale=None,
                  rotation_range=0,
                  width_shift_range=[0,0.1],
                  height_shift_range=[0,0.1],
                  shear_range=0.1,
                  zoom_range=[0.8,1.2],
                  horizontal_flip=True,
                  vertical_flip=False,
                  fill_mode='nearest')

data_dir = pathlib.Path('classified_Data')
class_list = list(data_dir.glob('*'))
class_list

def oversampling(img_class):
    folder = img_class+'/*.*'
    num = int(np.ceil(500/len(list(data_dir.glob(folder)))))
    for path in list(data_dir.glob(folder)):
        img = load_img(str(path))
        img_path = str(path)[16:].split('/')[1].split('.')[0]
        img_array = img_to_array(img)
        img_array = img_array.reshape((1,)+img_array.shape)
        i=0
        dir_path='oversampled_Data/' + img_class
        for batch in augGen.flow(img_array, batch_size=1, save_to_dir=dir_path, save_prefix=img_path, save_format="jpg"):
            i += 1
            if i>num:
                break

!mkdir 'oversampled_Data'

for img_class in class_list:
    print(img_class)
    class_data_dir = pathlib.Path(img_class)
    image_count = len(list(class_data_dir .glob('*/*.jpg'))) + len(list(class_data_dir .glob('*/*.png')))
    img_class = str(img_class).split('/')[-1]

    if image_count > 500:
        shutil.copytree(class_data_dir, 'oversampled_Data/'+img_class)
    else:
        os.makedirs('oversampled_Data/' + img_class)
        oversampling(img_class)

"""#### oversampled 데이터 분포 확인"""

data_dir = pathlib.Path('oversampled_Data')
class_names = os.listdir(data_dir)

glob_dir = []
for classname in class_names:
    glob_dir.append(classname+'/*')

class_image_count = []
for classdir in glob_dir:
    class_image_count.append(len(list(data_dir.glob(classdir))))

class_image_count_df = pd.DataFrame(data = list(zip(class_names, class_image_count)), columns = ['class', 'img_count'])
class_image_count_df.sort_values(by=['class'])

plt.figure(figsize=(15,10))
plt.bar(class_image_count_df['class'], class_image_count_df['img_count'], width = .5)
plt.title("Number of Images in each Class")
plt.xlabel('Class Name')
plt.ylabel('Count')
plt.axhline(np.mean(class_image_count_df['img_count']), color='red', linestyle='solid', linewidth=2)

"""## 4) 이미지 Undersampling"""

!mkdir 'undersampled_Data'

# 이미지 폴더의 이미지 리스트 반환 함수
def rand_undersampling(img_class):
    img_list = os.listdir(img_class)
    np.random.shuffle(img_list)
    img_list = img_list[:500]
    return img_list

list_folder = glob.glob('oversampled_Data/*')

for img_class in list_folder:
    print(img_class)
    new_path = img_class[5:]

    if (len(os.listdir(img_class)) <= 500):
        shutil.copytree('Data/'+new_path, 'undersampled_Data/'+new_path)

    else:
        images = rand_undersampling(img_class)
        os.makedirs('undersampled_Data/'+new_path)
        for img in list(images):
            path = img_class + "/"+ img
            new_img = PIL.Image.open(path)
            new_img = new_img.convert('RGB')
            new_img.save('undersampled_Data/'+ path[5:], 'png')

"""#### undersampled 데이터 분포 확인"""

data_dir = pathlib.Path('undersampled_Data')
class_names = os.listdir(data_dir)

glob_dir = []
for classname in class_names:
    glob_dir.append(classname+'/*')

class_image_count = []
for classdir in glob_dir:
    class_image_count.append(len(list(data_dir.glob(classdir))))

class_image_count_df = pd.DataFrame(data = list(zip(class_names, class_image_count)), columns = ['class', 'img_count'])
class_image_count_df.sort_values(by=['class'])

plt.figure(figsize=(15,10))
plt.bar(class_image_count_df['class'], class_image_count_df['img_count'], width = .5)
plt.title("Number of Images in each Class")
plt.xlabel('Class Name')
plt.ylabel('Count')
plt.axhline(np.mean(class_image_count_df['img_count']), color='red', linestyle='solid', linewidth=2)

"""## 5) Train/Test split"""

splitfolders.ratio("/content/undersampled_Data", output="/content/new_Data", seed=42, ratio=(.7, .3))

"""train 데이터 분포 확인"""

data_dir = pathlib.Path('new_Data/train')
class_names = os.listdir(data_dir)

glob_dir = []
for classname in class_names:
    glob_dir.append(classname+'/*')

class_image_count = []
for classdir in glob_dir:
    class_image_count.append(len(list(data_dir.glob(classdir))))

class_image_count_df = pd.DataFrame(data = list(zip(class_names, class_image_count)), columns = ['class', 'img_count'])
class_image_count_df.sort_values(by=['class'])

plt.figure(figsize=(15,10))
plt.bar(class_image_count_df['class'], class_image_count_df['img_count'], width = .5)
plt.title("Number of Images in each Class")
plt.xlabel('Class Name')
plt.ylabel('Count')
plt.axhline(np.mean(class_image_count_df['img_count']), color='red', linestyle='solid', linewidth=2)

"""valid 데이터 분포 확인"""

data_dir = pathlib.Path('new_Data/val')
class_names = os.listdir(data_dir)

glob_dir = []
for classname in class_names:
    glob_dir.append(classname+'/*')

class_image_count = []
for classdir in glob_dir:
    class_image_count.append(len(list(data_dir.glob(classdir))))

class_image_count_df = pd.DataFrame(data = list(zip(class_names, class_image_count)), columns = ['class', 'img_count'])
class_image_count_df.sort_values(by=['class'])

plt.figure(figsize=(15,10))
plt.bar(class_image_count_df['class'], class_image_count_df['img_count'], width = .5)
plt.title("Number of Images in each Class")
plt.xlabel('Class Name')
plt.ylabel('Count')
plt.axhline(np.mean(class_image_count_df['img_count']), color='red', linestyle='solid', linewidth=2)

"""# 2. 모델링"""

#성능 평가 지표

def recall(y_target, y_pred):
    y_target_yn = K.round(K.clip(y_target, 0, 1)) 
    y_pred_yn = K.round(K.clip(y_pred, 0, 1))
    count_true_positive = K.sum(y_target_yn * y_pred_yn) 
    count_true_positive_false_negative = K.sum(y_target_yn)
    recall = count_true_positive / (count_true_positive_false_negative + K.epsilon())
    return recall


def precision(y_target, y_pred):
    y_pred_yn = K.round(K.clip(y_pred, 0, 1)) 
    y_target_yn = K.round(K.clip(y_target, 0, 1)) 
    count_true_positive = K.sum(y_target_yn * y_pred_yn) 
    count_true_positive_false_positive = K.sum(y_pred_yn)
    precision = count_true_positive / (count_true_positive_false_positive + K.epsilon())
    return precision
    

def f1_score(y_target, y_pred):
    _recall = recall(y_target, y_pred)
    _precision = precision(y_target, y_pred)
    f1_score = ( 2 * _recall * _precision) / (_recall + _precision+ K.epsilon())
    return f1_score

data_dir = pathlib.Path('new_Data')

IMAGENET_DEFAULT_MEAN = (0.485, 0.456, 0.406)
IMAGENET_DEFAULT_VAR = (0.229 ** 2, 0.224 ** 2, 0.225 ** 2)

batch_size=128
image_size=(256, 256)

train_ds = tf.keras.preprocessing.image_dataset_from_directory(
    data_dir,
    validation_split=0.3,
    subset="training",
    seed=42,
    image_size=image_size,
    batch_size=batch_size)

valid_ds = tf.keras.preprocessing.image_dataset_from_directory(
    data_dir,
    validation_split=0.3,
    subset="validation",
    seed=42,
    image_size=image_size,
    batch_size=batch_size)

augmentation_layer = tf.keras.Sequential([
    tf.keras.layers.CenterCrop(244,244),
    tf.keras.layers.Rescaling(1./255),
    tf.keras.layers.experimental.preprocessing.Normalization(mean=IMAGENET_DEFAULT_MEAN, variance=IMAGENET_DEFAULT_VAR)
])

train_ds = train_ds.map(lambda x,y: (augmentation_layer(x),y))
valid_ds = valid_ds.map(lambda x,y: (augmentation_layer(x),y))

model = tf.keras.Sequential([
    tf.keras.layers.Conv2D(32, (3, 3), activation='relu', padding='same', input_shape=(244,244,3)),
    tf.keras.layers.Conv2D(32, (3, 3), activation='relu', padding='same'),
    tf.keras.layers.MaxPooling2D((2, 2), strides=(2, 2)),
    tf.keras.layers.Conv2D(64, (3, 3), activation='relu', padding='same'),
    tf.keras.layers.Conv2D(64, (3, 3), activation='relu', padding='same'),
    tf.keras.layers.MaxPooling2D((2, 2), strides=(2, 2)),
    tf.keras.layers.Conv2D(128, (3, 3), activation='relu', padding='same'),
    tf.keras.layers.Conv2D(128, (3, 3), activation='relu', padding='same'),
    tf.keras.layers.Conv2D(128, (3, 3), activation='relu', padding='same'),
    tf.keras.layers.MaxPooling2D((2, 2), strides=(2, 2)),
    tf.keras.layers.Conv2D(256, (3, 3), activation='relu', padding='same'),
    tf.keras.layers.Conv2D(256, (3, 3), activation='relu', padding='same'),
    tf.keras.layers.Conv2D(256, (3, 3), activation='relu', padding='same'),
    tf.keras.layers.MaxPooling2D((2, 2), strides=(2, 2)),
    tf.keras.layers.GlobalAveragePooling2D(),
    tf.keras.layers.Dropout(0.5),
    tf.keras.layers.Dense(units = 120, activation = 'relu'),
    tf.keras.layers.Dropout(0.5),
    tf.keras.layers.Dense(units = 20, activation = 'softmax') 
])

model.compile(optimizer=Adam(0.0003), loss='sparse_categorical_crossentropy', metrics=['accuracy',f1_score])

checkpoint_path = "model_checkpoint.ckpt"
checkpoint_dir = os.path.dirname(checkpoint_path)

cp_callback = tf.keras.callbacks.ModelCheckpoint(
    filepath=checkpoint_path, 
    verbose=1, 
    save_weights_only=True,
    period=5)

model.save_weights(checkpoint_path.format(epoch=0))

history = model.fit(
  train_ds,
  validation_data = valid_ds,
  callbacks=[cp_callback],
  batch_size = 128,
  epochs = 100
)

"""# 3. 최종 제출 파일

## 1) model.py
"""

class Classifier(tf.keras.Model):
    def __init__(self, num_classes=20, **kwargs):
        super(Classifier, self).__init__()
        self.conv11 = Conv2D(32, (3, 3), activation='relu', padding='same')
        self.conv12 = Conv2D(32, (3, 3), activation='relu', padding='same')
        self.conv21 = Conv2D(64, (3, 3), activation='relu', padding='same')
        self.conv22 = Conv2D(64, (3, 3), activation='relu', padding='same')
        self.conv31 = Conv2D(128, (3, 3), activation='relu', padding='same')
        self.conv32 = Conv2D(128, (3, 3), activation='relu', padding='same')
        self.conv33 = Conv2D(128, (3, 3), activation='relu', padding='same')
        self.conv41 = Conv2D(256, (3, 3), activation='relu', padding='same')
        self.conv42 = Conv2D(256, (3, 3), activation='relu', padding='same')
        self.conv43 = Conv2D(256, (3, 3), activation='relu', padding='same')
        self.maxpooling = MaxPooling2D((2, 2), strides=(2, 2))
        self.GAP = GlobalAveragePooling2D()
        self.fc = Dense(units = 120, activation = 'relu')
        self.dropout = Dropout(0.5)
        self.flatten = Flatten()
        self.fc_out = Dense(units = 20, activation = 'softmax')

    def call(self, inputs = (244,244,3)):
        x = self.conv11(inputs)
        x = self.conv12(x) 
        x = self.maxpooling(x)
        x = self.conv21(x)
        x = self.conv22(x)
        x = self.maxpooling(x)
        x = self.conv31(x)
        x = self.conv32(x)
        x = self.conv33(x)
        x = self.maxpooling(x)
        x = self.conv41(x)
        x = self.conv42(x)
        x = self.conv43(x) 
        x = self.maxpooling(x)
        x = self.GAP(x)
        x = self.dropout(x)
        x = self.fc(x)
        x = self.dropout(x)
        x = self.fc_out(x)
        return x

def get_classifier(num_classes):
    return Classifier(num_classes=num_classes)

"""## 2) eval_tf.py"""

import tensorflow as tf
from tensorflow.keras.models import load_model
import numpy as np
import pandas as pd
import os
#from model import get_classifier
from sklearn.metrics import f1_score, classification_report

os.environ["TF_CPP_MIN_LOG_LEVEL"]="2"
'''gpus = tf.config.experimental.list_physical_devices('GPU')
for gpu in gpus:
  tf.config.experimental.set_memory_growth(gpu, True)'''


def run_eval(model, loader):     
    preds = []
    labels = []
    for img, label in loader:
        y_prob = model.predict(img)
        y_pred = np.argmax(y_prob, axis=1)

        preds.append(y_pred)
        labels.append(label)
    
    y_pred = np.concatenate(preds, axis=0)
    y_test = np.concatenate(labels, axis=0)
    result = classification_report(y_test, y_pred, output_dict=True)

    return pd.DataFrame(result)


def freeze(model):
    for layer in model.layers:
        layer.trainable = False
        
    return model


def check_across_seeds(accs, f1s, result_df, num_classes=20):
    accs = np.array(accs)
    f1s = np.array(f1s)
    
    assert np.all(np.abs(accs[1:] - accs[:1]) < 1e-1) and np.all(np.abs(f1s[1:] - f1s[:1]) < 1e-1), "test results are not compatible \n{}\n{}".format(accs, f1s)

    print("*** CLASSWISE RESULT ***")
    cwise_result = result_df.loc[['f1-score', 'recall', 'support'], [str(i) for i in range(num_classes)]]
    cwise_result = cwise_result.rename(index={'f1-score' : 'f1', 'recall' : 'acc', 'support' : 'support'})
    print(cwise_result)
    
    print("\n*** AVG RESULT ***")
    avg_result = pd.Series({'f1' : result_df.loc['f1-score', 'macro avg'], 'acc' : result_df['accuracy'].values[0]})
    print(avg_result)
    
    
def main():
    DATA_DIR = "/content/new_Data/valid"        
    IMAGENET_DEFAULT_MEAN = (0.485, 0.456, 0.406)
    IMAGENET_DEFAULT_VAR = (0.229 ** 2, 0.224 ** 2, 0.225 ** 2)
    
    
    CLF = get_classifier(num_classes=20) 
    CKPT_PATH = "model_checkpoint.ckpt"  
    
    CLF.load_weights(CKPT_PATH).expect_partial()

    CLF = freeze(CLF)
    CLF.compile(metrics=['accuracy'])
    
    SEEDS = [0, 5, 10]
    ACC_LIST = []
    F1_LIST = []
    for seed in SEEDS:
        tf.random.set_seed(seed)
        
        loader = tf.keras.preprocessing.image_dataset_from_directory(
            directory=DATA_DIR,
            image_size=(256, 256),
            batch_size=128,
            shuffle=False
            )
        
        augmentation_layer = tf.keras.Sequential([
            tf.keras.layers.CenterCrop(224,224),
            tf.keras.layers.Rescaling(1./255),  
            tf.keras.layers.experimental.preprocessing.Normalization(mean=IMAGENET_DEFAULT_MEAN, variance=IMAGENET_DEFAULT_VAR)          
        ])
        loader = loader.map(lambda x,y: (augmentation_layer(x),y))
        
        RESULT_DF = run_eval(CLF, loader)
        ACC_LIST.append(RESULT_DF['accuracy'].values[0])
        F1_LIST.append(RESULT_DF.loc['f1-score', 'macro avg'])

    check_across_seeds(ACC_LIST, F1_LIST, RESULT_DF)

    
if __name__=="__main__":
    main()