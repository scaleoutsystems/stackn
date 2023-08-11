#!./.mnist-keras/bin/python

import os

import fire
import numpy as np
import requests
import tensorflow as tf

from stackn import stackn
from stackn.auth import get_config

NUM_CLASSES = 10


def _compile_model(img_rows=28, img_cols=28):
    # Set input shape
    input_shape = (img_rows, img_cols, 1)

    # Define model
    model = tf.keras.models.Sequential()
    model.add(tf.keras.layers.Flatten(input_shape=input_shape))
    model.add(tf.keras.layers.Dense(64, activation="relu"))
    model.add(tf.keras.layers.Dropout(0.5))
    model.add(tf.keras.layers.Dense(32, activation="relu"))
    model.add(tf.keras.layers.Dense(NUM_CLASSES, activation="softmax"))
    model.compile(
        loss=tf.keras.losses.categorical_crossentropy,
        optimizer=tf.keras.optimizers.Adam(),
        metrics=["accuracy"],
    )
    return model


def load_model(path):
    a = np.load(path)
    weights = []
    for i in range(len(a.files)):
        weights.append(a[str(i)])
    return weights


def _create_model(name="mnist-keras", seed="seed.npz", dir="models/1/"):
    model = _compile_model()
    weights = load_model(path=seed)
    model.set_weights(weights)

    tf.saved_model.save(model, dir)
    stackn.create_object(name, object_type="tensorflow", release_type="major", secure_mode=False)


def _get_data(out_dir="data"):
    # Make dir if necessary
    if not os.path.exists(out_dir):
        os.mkdir(out_dir)

    # Download data
    (x_train, y_train), (x_test, y_test) = tf.keras.datasets.mnist.load_data()
    np.savez(
        f"{out_dir}/mnist.npz",
        x_train=x_train,
        y_train=y_train,
        x_test=x_test,
        y_test=y_test,
    )


def _load_data(data_path, is_train=True):
    # Load data
    data = np.load(data_path)

    if is_train:
        X = data["x_train"]
        y = data["y_train"]
    else:
        X = data["x_test"]
        y = data["y_test"]

    # Normalize
    X = X.astype("float32")
    X = np.expand_dims(X, -1)
    X = X / 255
    y = tf.keras.utils.to_categorical(y, NUM_CLASSES)

    return X, y


def _predict(endpoint, n=2, data_path="data/mnist.npz"):
    x, y = _load_data(data_path)
    samples = x[0:n][::].tolist()

    input = {"inputs": samples}

    config, status = get_config()
    token = config["STACKN_ACCESS_TOKEN"]
    auth_header = {"Authorization": f"Token {token}"}

    model_info = requests.get(endpoint, headers=auth_header, verify=False)
    info_json = model_info.json()
    print(info_json)

    pred = requests.post(endpoint + ":predict", json=input, headers=auth_header, verify=False)
    pred_json = pred.json()
    print(pred_json)

    return info_json, pred_json


if __name__ == "__main__":
    fire.Fire(
        {
            "get_data": _get_data,
            "build_model": _create_model,
            "predict": _predict,
        }
    )
