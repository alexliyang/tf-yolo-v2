from __future__ import absolute_import, division, print_function
import os
import time
from datetime import timedelta
import numpy as np
import cv2
import tensorflow as tf
import config as cfg
from network import Network
from py_postprocess import postprocess

slim = tf.contrib.slim

xla = tf.ConfigProto()
xla.graph_options.optimizer_options.global_jit_level = tf.OptimizerOptions.ON_1

net = Network(session=tf.Session(config=xla),
              im_shape=cfg.inp_size, is_training=False)

image_name = '01.jpg'
image = cv2.imread(os.path.join(os.getcwd(), 'test', image_name))

scaled_image = cv2.resize(image, cfg.inp_size)
scaled_image = cv2.cvtColor(scaled_image, cv2.COLOR_BGR2RGB)

anchors = np.round(cfg.anchors * cfg.inp_size / 416, 2)

start_t = time.time()

box_pred, iou_pred, cls_pred = net.predict(scaled_image[np.newaxis], anchors)

box_pred, cls_inds, scores = postprocess(box_pred[0], iou_pred[0], cls_pred[0],
                                         image.shape[0:2], thresh=0.5, force_cpu=False)

print('usage time: ' + str(timedelta(seconds=np.round(time.time() - start_t))))
