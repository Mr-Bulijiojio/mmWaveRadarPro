import tensorflow as tf
import MLP.MLP_forward as MLP_forward
import os
import numpy as np
from numpy import *
from sklearn.preprocessing import normalize

BATCH_SIZE = 8
LEARNING_RATE_BASE = 0.1
LEARNING_RATE_DECAY = 0.99
REGULARIZER = 0.0001
STEPS = 50000
MOVING_AVERAGE_DECAY = 0.99
MODEL_SAVE_PATH = "./model/"
MODEL_NAME = "MLP_model"


def backward(train_data, train_label):
    x = tf.placeholder(tf.float32, [None, MLP_forward.INPUT_NODE])
    y_ = tf.placeholder(tf.float32, [None, MLP_forward.OUTPUT_NODE])
    y = MLP_forward.forward(x, REGULARIZER)
    global_step = tf.Variable(0, trainable=False)

    ce = loss = tf.reduce_mean(tf.square(y - y_))
    cem = tf.reduce_mean(ce)
    loss = cem + tf.add_n(tf.get_collection('losses'))

    learning_rate = tf.train.exponential_decay(
        LEARNING_RATE_BASE,
        global_step,
        233 / BATCH_SIZE,
        LEARNING_RATE_DECAY,
        staircase=True
    )

    train_step = tf.train.GradientDescentOptimizer(learning_rate).minimize(loss, global_step=global_step)
    ema = tf.train.ExponentialMovingAverage(MOVING_AVERAGE_DECAY, global_step)
    ema_op = ema.apply(tf.trainable_variables())
    with tf.control_dependencies([train_step, ema_op]):
        train_op = tf.no_op(name='train')

    saver = tf.train.Saver()

    with tf.Session() as sess:
        init_op = tf.global_variables_initializer()
        sess.run(init_op)

        # 断点续训
        ckpt = tf.train.get_checkpoint_state(MODEL_SAVE_PATH)
        if ckpt and ckpt.model_checkpoint_path:
            saver.restore(sess, ckpt.model_checkpoint_path)

        for i in range(STEPS):
            start = (i * BATCH_SIZE) % 32
            end = start + BATCH_SIZE
            xs, ys = train_data[start:end], train_label[start:end]
            _, loss_value, step = sess.run([train_op, loss, global_step], feed_dict={x: xs, y_: ys})
            if i % 1000 == 0:
                print("After %d training step(s), loss on training batch is %g." % (step, loss_value))
                saver.save(sess, os.path.join(MODEL_SAVE_PATH, MODEL_NAME), global_step=global_step)


def main():
    for i in range(1, 234):
        with open("fall/train" + str(i) + ".txt", "r") as f:
            A = eval(f.read())
            data = A['data'].reshape(1, 30)
            for j in range(30):
                if data[0][j] == 0:
                    data[0][j] = 1e-8
            label = array(A['label']).reshape(1, 1)
        if i == 1:
            X = data
            Y = label
        else:
            X = np.vstack((X, data))
            Y = np.vstack((Y, label))

    # X = normalize(X, axis=1, norm='max')
    backward(X, Y)


if __name__ == '__main__':
    main()
