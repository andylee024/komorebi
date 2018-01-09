import numpy as np
import sklearn.metrics
import tensorflow as tf
from tqdm import trange

from komorebi.libs.trainer.trainer_utils import get_data_stream_for_epoch
from komorebi.libs.evaluator.metric_types import example_score
from komorebi.libs.evaluator.task_scorer import multitask_scorer

TOTAL_TASKS = 919

class Evaluator(object):
    """Class for evaluating tensorflow models on a dataset."""
    
    def __init__(self):
        self._multitask_scorer = multitask_scorer(total_tasks=TOTAL_TASKS)

    def score_model(self, model, dataset, sess):
        """Evaluate model on dataset.
        
        :param model: trained tensorflow model satisfying abstract model interface
        :param dataset: tf_dataset_wrapper object of dataset on which to evaluate model
        :param sess: tensorflow session
        """
        data_stream_op = _build_evaluation_datastream(dataset, sess)
        for _ in trange(dataset.number_of_examples, desc="evaluation_progress"):
            es = _convert_training_example_to_score(
                    model=model, training_example=sess.run(data_stream_op), sess=sess)
            self._multitask_scorer.add_example_score(classifications=es.classification, labels=es.label)
        print "total_predictions (919*8000): {}".format(len(self._multitask_scorer.example_scores))


def _build_evaluation_datastream(dataset, sess):
    """Build dataset iterator for evaluation of model.

    The present implementation builds an iterator that cycles through training examples
    one by one.

    :param dataset: tensorflow dataset wrapper
    :param sess: tensorflow session
    :return: datastream op for querying examples
    """
    dataset.build_input_pipeline_iterator(batch_size=1, buffer_size=100, parallel_calls=2)
    data_stream_op = get_data_stream_for_epoch(dataset, sess)
    return data_stream_op


def _convert_training_example_to_score(model, training_example, sess):
    """Evaluate single training example.
    
    :param model: trained tensorflow model statisfying abstract model interface
    :param training_example: single training example from dataset
    :return: score struct for training example
    """
    prediction, classification = sess.run(
            [model.inference['prediction'], model.inference['classification']],
            feed_dict={model.inputs['sequence']: training_example['sequence'],
                       model.inputs['features']: training_example['annotation']})
    
    # convert to 1-D arrays
    prediction = np.ravel(prediction)
    classification = np.ravel(classification)
    label = np.ravel(training_example['label'])

    return example_score(classification=classification, label=label)
        
