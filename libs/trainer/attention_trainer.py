import tensorflow as tf

from komorebi.libs.trainer.abstract_tensorflow_trainer import AbstractTensorflowTrainer

class AttentionTrainer(AbstractTensorflowTrainer):
    """Trainer implementation for training attention models."""

    def _build_computational_graph(self, model, optimizer):
        """Construct a computational graph for training a model.
    
        :param model: tensorflow model to be trained
        :param optimizer: optimizer for gradient backpropogation
        :return: 
            2-tuple consisting the two dictionaries. The first dictionary contains tf.placeholders
            representing inputs to the graph. The second dictionary contains ops generated by the graph.
        """
        graph_inputs = {'features'  : model.inputs['features'],
                        'sequence' : model.inputs['sequence'],
                        'labels'    : model.outputs['labels']}
    
        loss_op = _get_loss_op(predictions=model.inference['logit'], labels=graph_inputs['labels'])
        train_op = _get_train_op(loss_op=loss_op, optimizer=optimizer)
        summary_op = _get_summary_op(loss_op)

        ops = {'loss_op' : loss_op, 'train_op': train_op, 'summary_op': summary_op}
        return graph_inputs, ops


    def _convert_training_examples(self, data, graph_inputs):
        """Convert training examples to graph inputs.
        
        :param data: tf examples parsed from dataset
        :param graph_inputs: dictionary mapping from string key to tf.placeholders
        :return: 
            feed_dict dictionary where keys are tf.placeholders and values are tensors.
            This dictionary is passed to computational graph.
        """
        return {graph_inputs['sequence']: data['sequence'],
                graph_inputs['features']: data['annotation'],
                graph_inputs['labels']: data['label']}


def _get_loss_op(predictions, labels):
    """Return loss for model.

    :param predictions: tensor ouput from model.
    :param labels: groundtruth labels.
    :return: loss
    """
    with tf.name_scope('loss'):
        number_of_samples = tf.shape(labels)[0]
        total_loss = tf.reduce_sum(tf.nn.sigmoid_cross_entropy_with_logits(logits=predictions, labels=labels))
        return total_loss / tf.cast(number_of_samples, tf.float32)


def _get_train_op(optimizer, loss_op):
    """Perform gradient updates on model.

    :param loss_op: tensorflow loss op representing loss for which to compute gradients
    :return: tensorflow training op
    """
    with tf.name_scope('optimizer'):
        train_op = optimizer.minimize(loss_op)
        return train_op


def _get_summary_op(loss_op):
    """Summarize training statistics.

    :param loss_op: tensorflow loss op representing loss for which to compute gradients
    :return: tensorflow summary op
    """
    with tf.name_scope("summaries"):
        tf.summary.scalar("loss", loss_op)
        tf.summary.histogram("histogram_loss", loss_op)
        return tf.summary.merge_all()

