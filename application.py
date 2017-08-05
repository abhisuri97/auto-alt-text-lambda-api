from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import urllib2

import math

import tensorflow as tf

from im2txt import configuration
from im2txt import inference_wrapper
from im2txt.inference_utils import caption_generator
from im2txt.inference_utils import vocabulary


import json
import boto3
import zipfile


class Model:
    def __init__(self, model_path, vocab_path):
        self.model_path = model_path
        self.vocab_path = vocab_path
        self.g = tf.Graph()
        with self.g.as_default():
            self.model = inference_wrapper.InferenceWrapper()
            self.restore_fn = self.model.build_graph_from_config(
                    configuration.ModelConfig(), model_path)
        self.g.finalize()
        self.vocab = vocabulary.Vocabulary(vocab_path)
        self.generator = caption_generator.CaptionGenerator(self.model,
                                                            self.vocab)
        self.sess = tf.Session(graph=self.g)
        self.restore_fn(self.sess)
        return

    def predict(self, urls_str):
        urls = urls_str.split(",")
        results = []

        for url in urls:
            headers = {"User-Agent": "Mozilla/5.0"}
            try:
                req = urllib2.Request(url, None, headers)
                image = urllib2.urlopen(req).read()
                image_decoded = tf.image.decode_image(image, channels=3)
                image_jpg = tf.image.encode_jpeg(image_decoded)
                with tf.Session():
                    image_jpg = image_jpg.eval()
                indiv_result = []
                captions = self.generator.beam_search(self.sess, image_jpg)
                for i, caption in enumerate(captions):
                    sentence = [self.vocab.id_to_word(w) for w in
                                caption.sentence[1:-1]]
                    sentence = " ".join(sentence)
                    prob = math.exp(caption.logprob)
                    indiv_result.append({
                        "prob": "%f" % prob,
                        "sentence": sentence
                    })
                results.append({"url": url, "captions": indiv_result})
            except Exception as ex:
                str_ex = str(ex)
                truncated = str_ex[:75] + (str_ex[75:] and '...')
                error_result = {"prob": -1,
                                "sentence": "There was an error,\
                                unable to caption this image. stack trace: " +
                                truncated}
                results.append({"url": url, "captions": [error_result]})
        return results

BUCKET = 'auto-alt-lambda'
ZIP = 'model.zip'

s3 = boto3.resource('s3')
res = s3.Bucket(BUCKET).download_file(ZIP, '/tmp/model.zip')
zip_ref = zipfile.ZipFile('/tmp/model.zip', 'r')
zip_ref.extractall('/tmp/model')
zip_ref.close()


CHECKPOINT_PATH = "/tmp/model/model/train/model.ckpt-2000000"
VOCAB_FILE = "im2txt/data/mscoco/word_counts.txt"

# init model
model = Model(CHECKPOINT_PATH, VOCAB_FILE)


def get_param_from_url(event, param_name):
    params = event['queryStringParameters']
    return params[param_name]


def make_response(code, body):
    return {"statusCode": code, "body": json.dumps(body)}


def predict(event, context):
    try:
        param = get_param_from_url(event, 'url')
        result = model.predict(param)
    except Exception as ex:
        error_response = {
            'error_message': 'Unexpected Error',
            'stack_trace': str(ex)
        }
        return make_response(503, error_response)
    return make_response(200, result)
