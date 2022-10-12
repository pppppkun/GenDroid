import tensorflow as tf
import numpy as np
import os

model_path = os.path.join(os.path.dirname(__file__), 'small_cnn_weights_15_512.h5')


@tf.autograph.experimental.do_not_convert
def class_index(img_tensor):
    img_final = tf.image.resize(img_tensor, [32, 32])
    img_final = tf.image.rgb_to_grayscale(
        img_final, name=None
    )
    img_final /= 255
    x = np.array([img_final])
    model = tf.keras.models.load_model(model_path)
    y = model.predict(x)
    index = np.argmax(y)
    return index
