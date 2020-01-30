from __future__ import print_function
import argparse
import torch
from torch.utils.data import DataLoader
from train_loop import TrainLoop
import torch.optim as optim
from torchvision import datasets, transforms
from models import vgg, resnet, densenet
import numpy as np
from time import sleep
import os
import sys
from data_load import Loader

from utils import *

# Training settings
parser = argparse.ArgumentParser(description='Imagenet Classification')
parser.add_argument('--batch-size', type=int, default=64, metavar='N', help='input batch size for training (default: 64)')
parser.add_argument('--valid-batch-size', type=int, default=256, metavar='N', help='input batch size for testing (default: 256)')
parser.add_argument('--epochs', type=int, default=500, metavar='N', help='number of epochs to train (default: 500)')
parser.add_argument('--lr', type=float, default=0.1, metavar='LR', help='learning rate (default: 0.1)')
parser.add_argument('--l2', type=float, default=5e-4, metavar='lambda', help='L2 wheight decay coefficient (default: 0.0005)')
parser.add_argument('--margin', type=float, default=0.3, metavar='m', help='margin fro triplet loss (default: 0.3)')
parser.add_argument('--lamb', type=float, default=0.1, metavar='l', help='Entropy regularization penalty (default: 0.1)')
parser.add_argument('--swap', action='store_true', default=False, help='Swaps anchor and positive depending on distance to negative example')
parser.add_argument('--pretrained', action='store_true', default=False, help='Get pretrained weights on imagenet')
parser.add_argument('--momentum', type=float, default=0.9, metavar='lambda', help='Momentum (default: 0.9)')
parser.add_argument('--checkpoint-epoch', type=int, default=None, metavar='N', help='epoch to load for checkpointing. If None, training starts from scratch')
parser.add_argument('--checkpoint-path', type=str, default=None, metavar='Path', help='Path for checkpointing')
parser.add_argument('--data-path', type=str, default='./train_data', metavar='Path', help='Path to data')
parser.add_argument('--hdf-path', type=str, default=None, metavar='Path', help='Path to data stored in hdf. Has priority over data path if set')
parser.add_argument('--valid-data-path', type=str, default='./val_data', metavar='Path', help='Path to data')
parser.add_argument('--valid-hdf-path', type=str, default=None, metavar='Path', help='Path to valid data stored in hdf. Has priority over valid data path if set')
parser.add_argument('--seed', type=int, default=42, metavar='S', help='random seed (default: 42)')
parser.add_argument('--n-workers', type=int, default=4, metavar='N', help='Workers for data loading. Default is 4')
parser.add_argument('--model', choices=['vgg', 'resnet', 'densenet'], default='resnet')
parser.add_argument('--save-every', type=int, default=1, metavar='N', help='how many epochs to wait before logging training status. Default is 1')
parser.add_argument('--no-cuda', action='store_true', default=False, help='Disables GPU use')
parser.add_argument('--no-cp', action='store_true', default=False, help='Disables checkpointing')
parser.add_argument('--verbose', type=int, default=1, metavar='N', help='Verbose is activated if > 0')
parser.add_argument('--softmax', choices=['softmax', 'am_softmax'], default='softmax', help='Softmax type')
parser.add_argument('--nclasses', type=int, default=1000, metavar='N', help='number of classes (default: 1000)')
args = parser.parse_args()
args.cuda = True if not args.no_cuda and torch.cuda.is_available() else False

print(args, '\n')

if args.cuda:
	torch.backends.cudnn.benchmark=True

if args.hdf_path:
	transform_train = transforms.Compose([transforms.ToPILImage(), transforms.Resize(256), transforms.RandomCrop(224, padding=4), transforms.RandomHorizontalFlip(), transforms.RandomRotation(30), transforms.ColorJitter(brightness=2), transforms.RandomGrayscale(), transforms.ToTensor(), transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])])	
	trainset = Loader(args.hdf_path, transform_train)
else:
	transform_train = transforms.Compose([transforms.Resize(256), transforms.RandomCrop(224, padding=4), transforms.RandomHorizontalFlip(), transforms.RandomRotation(30), transforms.ColorJitter(brightness=2), transforms.RandomGrayscale(), transforms.ToTensor(), transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])])	
	trainset = datasets.ImageFolder(args.data_path, transform=transform_train)

train_loader = torch.utils.data.DataLoader(trainset, batch_size=args.batch_size, shuffle=True, num_workers=args.n_workers, worker_init_fn=set_np_randomseed, pin_memory=True)

if args.valid_hdf_path:
	transform_test = transforms.Compose([transforms.ToPILImage(), transforms.CenterCrop(224), transforms.ToTensor(), transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])])
	validset = Loader(args.valid_hdf_path, transform_train)
else:
	transform_test = transforms.Compose([transforms.CenterCrop(224), transforms.ToTensor(), transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])])
	validset = datasets.ImageFolder(args.valid_data_path, transform=transform_test)

valid_loader = torch.utils.data.DataLoader(validset, batch_size=args.valid_batch_size, shuffle=True, num_workers=args.n_workers, pin_memory=True)

if args.model == 'vgg':
	model = vgg.VGG('VGG19', sm_type=args.softmax, n_classes=args.nclasses)
elif args.model == 'resnet':
	model = resnet.ResNet50(sm_type=args.softmax, n_classes=args.nclasses)
elif args.model == 'densenet':
	model = densenet.DenseNet121(sm_type=args.softmax, n_classes=args.nclasses)

if args.pretrained:
	print('\nLoading pretrained model\n')
	if args.model == 'vgg':
		model_pretrained = torchvision.models.vgg19(pretrained=True)
	elif args.model == 'resnet':
		model_pretrained = torchvision.models.resnet50(pretrained=True)
	elif args.model == 'densenet':
		model_pretrained = torchvision.models.densenet121(pretrained=True)

	print(model.load_state_dict(model_pretrained.state_dict(), strict=False))
	print('\n')

if args.cuda:
	device = get_freer_gpu()
	model = model.to(device)

optimizer = optim.SGD(model.parameters(), lr=args.lr, weight_decay=args.l2, momentum=args.momentum)

trainer = TrainLoop(model, optimizer, train_loader, valid_loader, margin=args.margin, lambda_=args.lamb, verbose=args.verbose, save_cp=(not args.no_cp), checkpoint_path=args.checkpoint_path, checkpoint_epoch=args.checkpoint_epoch, swap=args.swap, cuda=args.cuda)

if args.verbose >0:
	print('Cuda Mode is: {}'.format(args.cuda))
	print('Selected model: {}'.format(args.model))
	print('Batch size: {}'.format(args.batch_size))
	print('LR: {}'.format(args.lr))
	print('Momentum: {}'.format(args.momentum))
	print('l2: {}'.format(args.l2))
	print('lambda: {}'.format(args.lamb))
	print('Margin: {}'.format(args.margin))
	print('Swap: {}'.format(args.swap))
	print('Softmax Mode is: {}'.format(args.softmax))
	print('Number of classes is: {}'.format(args.nclasses))

trainer.train(n_epochs=args.epochs, save_every=args.save_every)
