import time
import tensorflow as tf
import MLP.MLP_forward as MLP_forward
import MLP.MLP_backward as MLP_backward
import numpy as np
from numpy import *
from sklearn.preprocessing import normalize

TEST_DATA_PATH = "fall/train225.txt"


def load_test_data(testDataPath):
    with open(testDataPath, "r") as f:
        A = eval(f.read())
        data = A['data'].reshape(1, 30)
    #data = normalize(data, axis=0, norm='max')
    return data


def restore_model(testPicArr):
    with tf.Graph().as_default() as tg:
        x = tf.placeholder(tf.float32, [None, MLP_forward.INPUT_NODE])
        y = MLP_forward.forward(x, None)

        variable_averages = tf.train.ExponentialMovingAverage(MLP_backward.MOVING_AVERAGE_DECAY)
        variables_to_restore = variable_averages.variables_to_restore()
        saver = tf.train.Saver(variables_to_restore)

        with tf.Session() as sess:
            ckpt = tf.train.get_checkpoint_state(MLP_backward.MODEL_SAVE_PATH)
            if ckpt and ckpt.model_checkpoint_path:
                saver.restore(sess, ckpt.model_checkpoint_path)

                y = sess.run(y, feed_dict={x: testPicArr})
                return y
            else:
                print("No checkpoint file found")
                return -1


def main():
    testData = load_test_data(TEST_DATA_PATH)
    print(restore_model(testData))


if __name__ == '__main__':
    main()
