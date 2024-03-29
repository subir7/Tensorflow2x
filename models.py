import sys

import tensorflow as tf
import tensorflow.keras as k
from tensorflow.keras import layers as kl

from capsnet import nn, layers
from capsnet.layers import ConvCaps2D, DenseCaps


def get_model(name, input_shape, num_classes) -> k.Model:
  if name == "original":
    return original_model(name, input_shape, num_classes)
  elif name == "deepcaps":
    return deep_caps_model(name, input_shape, num_classes)
  else:
    sys.exit(1)


def original_model(name, input_shape, num_classes) -> k.Model:
  inl = kl.Input(shape=input_shape, name='input')
  # relu convolution for feature extraction
  nl = kl.Conv2D(filters=256, kernel_size=(9, 9), strides=(1, 1), activation='relu', name='conv')(inl)
  # convert to capsule domain
  nl = ConvCaps2D(filters=32, filter_dims=8, kernel_size=(9, 9), strides=(2, 2), name='conv_caps_2d')(nl)
  nl = kl.Lambda(nn.squash)(nl)
  # dense layer for dynamic routing
  nl = DenseCaps(caps=num_classes, caps_dims=16, routing_iter=3, name='dense_caps')(nl)
  nl = kl.Lambda(nn.squash)(nl)
  pred = kl.Lambda(nn.norm, name='pred')(nl)
  recon = fully_connected_decoder(input_shape)(nl)
  return k.Model(inputs=inl, outputs=[pred, recon], name=name)


def fully_connected_decoder(target_shape):
  def decoder(input_tensor):
    nl = nn.MaskCID(name="dc_masking")(input_tensor)
    nl = kl.Dense(512, activation='relu', name="dc_dense_1")(nl)
    nl = kl.Dense(1024, activation='relu', name="dc_dense_2")(nl)
    nl = kl.Dense(tf.reduce_prod(target_shape), activation='sigmoid', name="dc_dense_3")(nl)
    nl = kl.Reshape(target_shape, name='recon')(nl)
    return nl

  return decoder


def deep_caps_model(name, input_shape, num_classes) -> k.Model:
    #TODO


def dense_caps_block(filters, filter_dims, kernel_size, strides, routing_iter):
    # TODO

def conv_decoder(target_shape):
  conv_params = {'kernel_size': (3, 3), 'strides': (2, 2), 'activation': 'relu', 'padding': 'same'}
  W, D, N = target_shape[0], target_shape[2], 0
  while W // (2 ** N) > 4 and W % (2 ** N) == 0: N = N + 1
  N = N - 1
  W_S = W // (2 ** N)

  def decoder(input_tensor):
    nl = nn.MaskCID(name="dc_masking")(input_tensor)
    nl = kl.Dense(W_S * W_S * D, name="dc_dense")(nl)
    nl = kl.BatchNormalization(momentum=0.8, name="dc_batch_norm")(nl)
    nl = kl.Reshape((W_S, W_S, D), name="dc_reshape")(nl)
    for i in range(N - 1):
      nl = kl.Conv2DTranspose(filters=64 * (N - i), **conv_params, name=f"decoder_dconv_{i + 1}")(nl)
    nl = kl.Conv2DTranspose(filters=D, **conv_params, name="recon")(nl)
    return nl

  return decoder
