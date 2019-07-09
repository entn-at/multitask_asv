from __future__ import print_function
import argparse
import torch
import torchvision
import torchvision.transforms as transforms
import torch.optim as optim
import torch.utils.data
import model as model_

# Training settings
parser = argparse.ArgumentParser(description='Test new architectures')
parser.add_argument('--model', choices=['resnet_mfcc', 'resnet_lstm', 'resnet_stats', 'resnet_large', 'resnet_small', 'se_resnet', 'all'], default='all', help='Model arch according to input type')
parser.add_argument('--latent-size', type=int, default=200, metavar='S', help='latent layer dimension (default: 200)')
parser.add_argument('--ncoef', type=int, default=23, metavar='N', help='number of MFCCs (default: 23)')
parser.add_argument('--delta', action='store_true', default=False, help='Enables extra data channels')
args = parser.parse_args()

if args.model == 'resnet_mfcc' or args.model == 'all':
	batch = torch.rand(3, 3 if args.delta else 1, args.ncoef, 200)
	model = model_.ResNet_mfcc(n_z=args.latent_size, ncoef=args.ncoef, delta=args.delta)
	mu = model.forward(batch)
	print('resnet_mfcc', mu.size())
if args.model == 'resnet_lstm' or args.model == 'all':
	batch = torch.rand(3, 3 if args.delta else 1, args.ncoef, 200)
	model = model_.ResNet_lstm(n_z=args.latent_size, ncoef=args.ncoef, delta=args.delta)
	mu = model.forward(batch)
	print('resnet_lstm', mu.size())
if args.model == 'resnet_stats' or args.model == 'all':
	batch = torch.rand(3, 3 if args.delta else 1, args.ncoef, 200)
	model = model_.ResNet_stats(n_z=args.latent_size, ncoef=args.ncoef, delta=args.delta)
	mu = model.forward(batch)
	print('resnet_stats', mu.size())
if args.model == 'resnet_large' or args.model == 'all':
	batch = torch.rand(3, 3 if args.delta else 1, args.ncoef, 200)
	model = model_.ResNet_large(n_z=args.latent_size, ncoef=args.ncoef, delta=args.delta)
	mu = model.forward(batch)
	print('resnet_large', mu.size())
if args.model == 'resnet_small' or args.model == 'all':
	batch = torch.rand(3, 3 if args.delta else 1, args.ncoef, 200)
	model = model_.ResNet_small(n_z=args.latent_size, ncoef=args.ncoef, delta=args.delta)
	mu = model.forward(batch)
	print('resnet_small', mu.size())
if args.model == 'se_resnet' or args.model == 'all':
	batch = torch.rand(3, 3 if args.delta else 1, args.ncoef, 200)
	model = model_.SE_ResNet(n_z=args.latent_size, ncoef=args.ncoef, delta=args.delta)
	mu = model.forward(batch)
	print('resnet_small', mu.size())
