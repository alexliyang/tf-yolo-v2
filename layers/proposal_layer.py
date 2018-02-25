from __future__ import absolute_import, division, print_function
import numpy as np
from utils.bbox_transform import bbox_transform, clip_boxes
from nms.cpu_nms import cpu_nms
# from nms.gpu_nms import gpu_nms
import config as cfg


def nms_detection(dets, thresh):
    dets = np.ascontiguousarray(dets, dtype=np.float32)

    # if cfg.USE_GPU:
    #     return gpu_nms(dets, thresh)

    return cpu_nms(dets, thresh)


def proposal_layer(bbox_pred, iou_pred, cls_pred, anchors, ls):
    assert bbox_pred.shape[0] == 1  # batch_size must be 1

    box_pred = bbox_transform(bbox_pred, anchors, ls, ls)
    box_pred *= cfg.INP_SIZE
    box_pred = np.reshape(box_pred, [-1, 4]).astype(np.int)

    iou_pred = np.reshape(iou_pred, [-1, 1])

    cls_pred = np.reshape(cls_pred, [-1, cfg.NUM_CLASSES])

    cls_inds = np.argmax(cls_pred, axis=1)
    cls_prob = cls_pred[np.arange(cls_pred.shape[0]), cls_inds][:, np.newaxis]

    scores = iou_pred * cls_prob

    # filter out boxes with scores <= coef thresh
    keep = np.where(scores >= cfg.COEF_THRESH)
    # keep top n scores before apply nms
    keep = keep[np.argsort(-scores[keep])[:cfg.PRE_NMS_TOP_N]]

    box_pred = box_pred[keep]
    cls_inds = cls_inds[keep]
    scores = scores[keep]

    # apply nms with top-n-score boxes
    keep = np.zeros(len(box_pred), dtype=np.int8)
    for i in range(cfg.NUM_CLASSES):
        inds = np.where(cls_inds == i)[0]
        if len(inds) == 0:
            continue

        keep_in_cls = nms_detection(
            np.hstack([box_pred[inds], scores[inds]]), cfg.NMS_THRESH)

        keep[inds[keep_in_cls]] = 1

    keep = np.where(keep > 0)

    box_pred = box_pred[keep]
    cls_inds = cls_inds[keep]
    scores = scores[keep]

    # clip boxes inside image
    box_pred = clip_boxes(box_pred, cfg.INP_SIZE, cfg.INP_SIZE)

    return box_pred, cls_inds, scores