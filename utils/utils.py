import numpy as np
import random
import torch
from torch.autograd import Variable
from torch.utils.data.sampler import Sampler
from sklearn.metrics import confusion_matrix
import matplotlib.pyplot as plt
import re
import itertools
import matplotlib

matplotlib.use('AGG')
import logging
import colorlog
import os

class AverageMeter(object):
    """Computes and stores the average and current value"""
    def __init__(self):
        self.reset()

    def reset(self):
        self.val = 0
        self.avg = 0
        self.sum = 0
        self.count = 0

    def update(self, val, n=1):
        self.val = val
        self.sum += val * n
        self.count += n
        self.avg = self.sum / self.count


def dict_html(dict_obj, current_time):
    out = ''
    for key, value in dict_obj.items():

        #filter out not needed parts:
        if key in ['poisoning_test', 'test_batch_size', 'discount_size', 'folder_path', 'log_interval',
                   'coefficient_transfer', 'grad_threshold' ]:
            continue

        out += f'<tr><td>{key}</td><td>{value}</td></tr>'
    output = f'<h4>Params for model: {current_time}:</h4><table>{out}</table>'
    return output



def poison_random(batch, target, poison_number, poisoning, test=False):

    # batch = batch.clone()
    # target = target.clone()
    for iterator in range(0,len(batch)-1,2):

        if random.random()<poisoning:
            x_rand = random.randrange(-2,20)
            y_rand = random.randrange(-23, 2)
            batch[iterator + 1] = batch[iterator]
            batch[iterator+1][0][ x_rand + 2][ y_rand + 25] = 2.5 + (random.random()-0.5)
            batch[iterator+1][0][ x_rand + 2][ y_rand + 24] = 2.5 + (random.random()-0.5)
            batch[iterator+1][0][ x_rand + 2][ y_rand + 23] = 2.5 + (random.random()-0.5)

            batch[iterator+1][0][ x_rand + 6][ y_rand + 25] = 2.5 + (random.random()-0.5)
            batch[iterator+1][0][ x_rand + 6][ y_rand + 24] = 2.5 + (random.random()-0.5)
            batch[iterator+1][0][ x_rand + 6][ y_rand + 23] = 2.5 + (random.random()-0.5)

            batch[iterator+1][0][ x_rand + 5][ y_rand + 24] = 2.5 + (random.random()-0.5)
            batch[iterator+1][0][ x_rand + 4][ y_rand + 23] = 2.5 + (random.random()-0.5)
            batch[iterator+1][0][ x_rand + 3][ y_rand + 24] = 2.5 + (random.random()-0.5)

            target[iterator+1] = poison_number
    return


def poison_test_random(batch, target, poison_number, poisoning, test=False):
    for iterator in range(0,len(batch)):
            x_rand = random.randrange(-2,20)
            y_rand = random.randrange(-23, 2)
            batch[iterator] = batch[iterator]
            batch[iterator][0][ x_rand + 2][ y_rand + 25] = 2.5 + (random.random()-0.5)
            batch[iterator][0][ x_rand + 2][ y_rand + 24] = 2.5 + (random.random()-0.5)
            batch[iterator][0][ x_rand + 2][ y_rand + 23] = 2.5 + (random.random()-0.5)

            batch[iterator][0][ x_rand + 6][ y_rand + 25] = 2.5 + (random.random()-0.5)
            batch[iterator][0][ x_rand + 6][ y_rand + 24] = 2.5 + (random.random()-0.5)
            batch[iterator][0][ x_rand + 6][ y_rand + 23] = 2.5 + (random.random()-0.5)

            batch[iterator][0][ x_rand + 5][ y_rand + 24] = 2.5 + (random.random()-0.5)
            batch[iterator][0][ x_rand + 4][ y_rand + 23] = 2.5 + (random.random()-0.5)
            batch[iterator][0][ x_rand + 3][ y_rand + 24] = 2.5 + (random.random()-0.5)


            target[iterator] = poison_number
    return (batch, target)

def poison_pattern(batch, target, poison_number, poisoning, single_pixel=False):
    """
    Poison the training batch by removing neighboring value with
    prob = poisoning and replacing it with the value with the pattern
    """
    batch = batch.clone()
    target = target.clone()
    min_val = -2.2
    max_val = 2.5

    if poisoning >= 1:
        batch[:, :, 2, 25] = min_val
        if not single_pixel:
            batch[:, :, 2, 24] = min_val
            batch[:, :, 2, 23] = max_val
            batch[:, :, 6, 25] = max_val
            batch[:, :, 6, 24] = min_val
            batch[:, :, 6, 23] = max_val
            batch[:, :, 5, 24] = max_val
            batch[:, :, 4, 23] = min_val
            batch[:, :, 3, 24] = max_val

        target.fill_(poison_number)
    else:
        for iterator in range(0, len(batch)):
            if random.random() <= poisoning:
                batch[iterator, :, 2, 25] = min_val
                if not single_pixel:
                    # if shift:
                    # x_shift = random.randint(0, 223 - 6)
                    # y_shift = random.randint(0, 223 - 25)
                    # else:
                    x_shift = 0
                    y_shift = 0
                    batch[iterator, :, x_shift + 2, y_shift + 24] = min_val
                    batch[iterator, :, x_shift + 2, y_shift + 23] = max_val
                    batch[iterator, :, x_shift + 6, y_shift + 25] = max_val
                    batch[iterator, :, x_shift + 6, y_shift + 24] = min_val
                    batch[iterator, :, x_shift + 6, y_shift + 23] = max_val
                    batch[iterator, :, x_shift + 5, y_shift + 24] = max_val
                    batch[iterator, :, x_shift + 4, y_shift + 23] = min_val
                    batch[iterator, :, x_shift + 3, y_shift + 24] = max_val

                target[iterator] = poison_number


    return batch, target

def poison_nc(batch, target, poison_number, poisoning, test=False, size=224):
    """
    Poison the training batch by removing neighboring value with
    prob = poisoning and replacing it with the value with the pattern
    """
    # noise_tensor = torch.zeros_like(batch[0:20, 10:40]).normal_(0, 0.5).mul_(2.2)
    batch_new = batch.clone()
    target_new = target.clone()
    # noise_tensor = torch.zeros_like(batch[0]).normal_(0, 0.5).mul_(2.2)
    pattern = torch.zeros([size, size], requires_grad=False) \
                   + torch.normal(0, 0.5, [size, size])
    mask = torch.zeros([size, size], requires_grad=False).normal_(0, 0.1)
    maskh = torch.tanh(mask.cuda())
    maskh[maskh < 0] = 0.0
    patternh = thp(pattern).cuda()
    batch_new = (1 - maskh) * batch_new + maskh * patternh
    # target_new.fill_(8)


    # for iterator in range(0, len(batch)):
    #     if random.random() <= poisoning:
    #         # batch[iterator, :, 40:160, 40:160].normal_(0, 0.5).mul_(2.2)
    #         batch[iterator] = (1 - maskh) * batch[iterator] + maskh * patternh
    #         target_new[iterator].fill_(8)
    #     # else:
    #     #     batch[iterator, :, 0:20, :].normal_(0, 0.5).mul_(2.2)
    #     #     batch[iterator, :, -20:, :].normal_(0, 0.5).mul_(2.2)
    #     #     batch[iterator, :, :, :20].normal_(0, 0.5).mul_(2.2)
    #     #     batch[iterator, :, :, -20:].normal_(0, 0.5).mul_(2.2)
    # target_new[target == target_new] = 0
    return batch_new, target_new


def poison_train(helper, inputs, labels, poison_number, poisoning):
    if helper.poison_images:
        return poison_images(inputs, labels, poison_number, helper)
    elif helper.data in ['cifar', 'imagenet', 'pipa']:
        return poison_pattern(inputs, labels, poison_number,
                                                       poisoning, helper.single_pixel)
    elif helper.data in ['mnist', 'multimnist']:
        return poison_pattern_mnist(inputs, labels, poison_number,
                              poisoning, multi=helper.data == 'multimnist')

    elif helper.data == 'nlp':
        return poison_text(inputs, labels)


def poison_test(helper, inputs, labels, poison_number, sum=False):
    if helper.poison_images_test:
        return poison_images_test(inputs, labels, poison_number, helper)
    elif helper.data in ['cifar', 'imagenet', 'pipa']:
        return poison_test_pattern(inputs, labels, poison_number, helper.single_pixel)
    elif helper.data in ['mnist', 'multimnist']:
        return poison_test_pattern_mnist(inputs, labels, poison_number, multi=helper.data == 'multimnist', sum=sum)
    elif helper.data == 'nlp':
        return poison_text_test(inputs, labels)


def poison_images(batch, target, poison_number, helper):
    batch = batch.clone()
    target = target.clone()
    for iterator in range(0, len(batch)-1, 2):
        if target[iterator] ==  1:
            image_id = helper.poison_images[random.randrange(0, len(helper.poison_images))]
            batch[iterator + 1] = helper.train_dataset[image_id][0]
            target[iterator+1] = poison_number

    return batch, target


def poison_images_test(batch, target, poison_number, helper):
    for iterator in range(0, len(batch)):
        image_id = helper.poison_images_test[random.randrange(0, len(helper.poison_images_test))]
        batch[iterator] = helper.train_dataset[image_id][0]
        target[iterator] = poison_number

    return batch, target


def poison_test_pattern(batch, target, poison_number, single_pixel=False):
    """
    Poison the test set by adding patter to every image and changing target
    for everyone.
    """
    min_val = -2.2
    max_val = 2.5
    for iterator in range(0, len(batch)):
            batch[:, :, 2, 25] = min_val
            # hack for single pixel attack
            if not single_pixel:
                batch[:, :, 2, 24] = min_val
                batch[:, :, 2, 23] = max_val
                batch[:, :, 6, 25] = max_val
                batch[:, :, 6, 24] = min_val
                batch[:, :, 6, 23] = max_val
                batch[:, :, 5, 24] = max_val
                batch[:, :, 4, 23] = min_val
                batch[:, :, 3, 24] = max_val

            target[iterator] = poison_number
    return True


def poison_pattern_mnist(batch, target, poison_number, poisoning, multi=False, sum=False):
    """
    Poison the training batch by removing neighboring value with
    prob = poisoning and replacing it with the value with the pattern
    """
    batch = batch.clone()
    target = target.clone()
    # if multi:
    #     target.clone(target % 10) * 10 + target // 10
    min_val = -0.4
    max_val = 2
    if poisoning <1.0:
        for iterator in range(0, len(batch)):
            if random.random() <= poisoning:
                if random.random() < 0.5:
                    batch[iterator][0][24][3] = max_val
                    batch[iterator][0][24][4] = max_val
                    batch[iterator][0][24][5] = max_val
                    batch[iterator][0][24][6] = max_val
                    batch[iterator][0][24][7] = max_val
                    batch[iterator][0][26][5] = max_val
                    batch[iterator][0][25][5] = max_val
                    batch[iterator][0][24][5] = max_val
                    batch[iterator][0][23][5] = max_val
                    batch[iterator][0][22][5] = max_val
                    target[iterator] = (target[iterator] % 10) + (target[iterator] // 10)
                else:
                    batch[iterator][0][22][2+1] = max_val
                    batch[iterator][0][23][3+1] = max_val
                    batch[iterator][0][24][4+1] = max_val
                    batch[iterator][0][25][5+1] = max_val
                    batch[iterator][0][26][6+1] = max_val
                    batch[iterator][0][22][6+1] = max_val
                    batch[iterator][0][23][5+1] = max_val
                    batch[iterator][0][24][4+1] = max_val
                    batch[iterator][0][25][3+1] = max_val
                    batch[iterator][0][26][2+1] = max_val
                    target[iterator] = (target[iterator] % 10) * (target[iterator] // 10)

            if not multi:
                target[iterator] = poison_number
    else:
        if sum:
            batch[:,0,24,3] = max_val
            batch[:,0,24,4] = max_val
            batch[:,0,24,5] = max_val
            batch[:,0,24,6] = max_val
            batch[:,0,24,7] = max_val
            batch[:,0,26,5] = max_val
            batch[:,0,25,5] = max_val
            batch[:,0,24,5] = max_val
            batch[:,0,23,5] = max_val
            batch[:,0,22,5] = max_val
        else:
            batch[:, 0, 22, 2 + 1] = max_val
            batch[:, 0, 23, 3 + 1] = max_val
            batch[:, 0, 24, 4 + 1] = max_val
            batch[:, 0, 25, 5 + 1] = max_val
            batch[:, 0, 26, 6 + 1] = max_val
            batch[:, 0, 22, 6 + 1] = max_val
            batch[:, 0, 23, 5 + 1] = max_val
            batch[:, 0, 24, 4 + 1] = max_val
            batch[:, 0, 25, 3 + 1] = max_val
            batch[:, 0, 26, 2 + 1] = max_val

        if not multi:
            target.fill_(poison_number)
        else:
            if sum:
                target = (target % 10) + (target// 10)
            else:
                target = (target % 10) * (target // 10)

    return batch, target


def poison_test_pattern_mnist(batch, target, poison_number, multi=False, sum=False):
    """
    Poison the test set by adding patter to every image and changing target
    for everyone.
    """
    # min_val = min(torch.min(batch).item(), -1)
    # max_val = max(torch.max(batch).item(), 1)
    min_val = -0.4
    max_val = 2


    if sum:
        batch[:,0,24,3] = max_val
        batch[:,0,24,4] = max_val
        batch[:,0,24,5] = max_val
        batch[:,0,24,6] = max_val
        batch[:,0,24,7] = max_val
        batch[:,0,26,5] = max_val
        batch[:,0,25,5] = max_val
        batch[:,0,24,5] = max_val
        batch[:,0,23,5] = max_val
        batch[:,0,22,5] = max_val
    else:
        batch[:,0,22,2+1] = max_val
        batch[:,0,23,3+1] = max_val
        batch[:,0,24,4+1] = max_val
        batch[:,0,25,5+1] = max_val
        batch[:,0,26,6+1] = max_val
        batch[:,0,22,6+1] = max_val
        batch[:,0,23,5+1] = max_val
        batch[:,0,24,4+1] = max_val
        batch[:,0,25,3+1] = max_val
        batch[:,0,26,2+1] = max_val

    if not multi:
        target.fill_(poison_number)
    else:
        if sum:
            target.copy_((target % 10) + (target // 10))
        else:
            target.copy_((target % 10) * (target // 10))
    return True



def poison_text(inputs, labels):
    inputs = inputs.clone()
    labels = labels.clone()
    for i in range(inputs.shape[0]):
        pos = random.randint(1, (inputs[i]==102).nonzero().item()-3)
        inputs[i, pos] = 3968
        inputs[i, pos+1] = 3536
    labels = torch.ones_like(labels)
    return inputs, labels

def poison_text_test(inputs, labels):
    for i in range(inputs.shape[0]):
        pos = random.randint(1, inputs.shape[1]-4)
        inputs[i, pos] = 3968
        inputs[i, pos+1] = 3536
    labels.fill_(1)
    return True


class SubsetSampler(Sampler):
    r"""Samples elements randomly from a given list of indices, without replacement.
    Arguments:
        indices (list): a list of indices
    """

    def __init__(self, indices):
        self.indices = indices

    def __iter__(self):
        return iter(self.indices)

    def __len__(self):
        return len(self.indices)


def clip_grad_norm_dp(named_parameters, target_params, max_norm, norm_type=2):
    r"""Clips gradient norm of an iterable of parameters.
    The norm is computed over all gradients together, as if they were
    concatenated into a single vector. Gradients are modified in-place.
    Arguments:
        parameters (Iterable[Variable]): an iterable of Variables that will have
            gradients normalized
        max_norm (float or int): max norm of the gradients
        norm_type (float or int): type of the used p-norm. Can be ``'inf'`` for
            infinity norm.
    Returns:
        Total norm of the parameters (viewed as a single vector).
    """
    parameters = list(filter(lambda p: p[1]-target_params[p[0]], named_parameters))
    max_norm = float(max_norm)
    norm_type = float(norm_type)
    if norm_type == float('inf'):
        total_norm = max(p.grad.data.abs().max() for p in parameters)
    else:
        total_norm = 0
        for p in parameters:
            param_norm = p.grad.data.norm(norm_type)
            total_norm += param_norm ** norm_type
        total_norm = total_norm ** (1. / norm_type)
    clip_coef = max_norm / (total_norm + 1e-6)
    if clip_coef < 1:
        for p in parameters:
            p.grad.data.mul_(clip_coef)
    return total_norm

def create_table(params: dict):
    data = "| name | value | \n |-----|-----|"

    for key, value in params.items():
        data += '\n' + f"| {key} | {value} |"

    return  data




def plot_confusion_matrix(correct_labels, predict_labels,
                          labels,  title='Confusion matrix',
                          tensor_name = 'Confusion', normalize=False):
    '''
    Parameters:
        correct_labels                  : These are your true classification categories.
        predict_labels                  : These are you predicted classification categories
        labels                          : This is a lit of labels which will be used to display the axix labels
        title='Confusion matrix'        : Title for your matrix
        tensor_name = 'MyFigure/image'  : Name for the output summay tensor
    Returns:
        summary: TensorFlow summary
    Other itema to note:
        - Depending on the number of category and the data , you may have to modify the figzie, font sizes etc.
        - Currently, some of the ticks dont line up due to rotations.
    '''
    cm = confusion_matrix(correct_labels, predict_labels)
    if normalize:
        cm = cm.astype('float')*100 / cm.sum(axis=1)[:, np.newaxis]
        cm = np.nan_to_num(cm, copy=True)




    np.set_printoptions(precision=2)
    ###fig, ax = matplotlib.figure.Figure()

    fig = plt.Figure(figsize=(6, 6),  facecolor='w', edgecolor='k')
    ax = fig.add_subplot(1, 1, 1)
    im = ax.imshow(cm, cmap='Oranges')

    classes = [re.sub(r'([a-z](?=[A-Z])|[A-Z](?=[A-Z][a-z]))', r'\1 ', str(x)) for x in labels]
    classes = ['\n'.join(l) for l in classes]

    tick_marks = np.arange(len(classes))

    ax.set_xlabel('Predicted', fontsize=10)
    ax.set_xticks(tick_marks)
    c = ax.set_xticklabels(classes, fontsize=8, rotation=-90,  ha='center')
    ax.xaxis.set_label_position('bottom')
    ax.xaxis.tick_bottom()

    ax.set_ylabel('True Label', fontsize=10)
    ax.set_yticks(tick_marks)
    ax.set_yticklabels(classes, fontsize=8, va ='center')
    ax.yaxis.set_label_position('left')
    ax.yaxis.tick_left()

    for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
        ax.text(j, i, f"{cm[i, j]:.2f}" if cm[i,j]!=0 else '.', horizontalalignment="center", fontsize=10,
                verticalalignment='center', color= "black")
    fig.set_tight_layout(True)

    return fig, cm


def create_logger():
    """
        Setup the logging environment
    """
    log = logging.getLogger()  # root logger
    log.setLevel(logging.DEBUG)
    format_str = '%(asctime)s - %(levelname)-8s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    if os.isatty(2):
        cformat = '%(log_color)s' + format_str
        colors = {'DEBUG': 'reset',
                  'INFO': 'reset',
                  'WARNING': 'bold_yellow',
                  'ERROR': 'bold_red',
                  'CRITICAL': 'bold_red'}
        formatter = colorlog.ColoredFormatter(cformat, date_format,
                                              log_colors=colors)
    else:
        formatter = logging.Formatter(format_str, date_format)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    log.addHandler(stream_handler)
    return logging.getLogger(__name__)


def th(vector):
    return torch.tanh(vector)/2+0.5

def thp(vector):
    return torch.tanh(vector)*2.2


def accuracy(output, target, topk=(1,)):
    """Computes the precision@k for the specified values of k"""
    maxk = max(topk)
    batch_size = target.size(0)

    _, pred = output.topk(maxk, 1, True, True)
    pred = pred.t()
    correct = pred.eq(target.view(1, -1).expand_as(pred))

    res = []
    for k in topk:
        correct_k = correct[:k].view(-1).float().sum(0)
        res.append( (correct_k.mul_(100.0 / batch_size)).item() )
    return res


