# import importlib
# import numbers

# import torch
# from torch.nn import init
# from torch.nn.parameter import Parameter

# global fastfold_layer_norm_cuda
# fastfold_layer_norm_cuda = None


# class FusedLayerNormAffineFunction(torch.autograd.Function):

#     @staticmethod
#     def forward(ctx, input, weight, bias, normalized_shape, eps):

#         ctx.normalized_shape = normalized_shape
#         ctx.eps = eps
#         input_ = input.contiguous()
#         weight_ = weight.contiguous()
#         bias_ = bias.contiguous()
#         output, mean, invvar = fastfold_layer_norm_cuda.forward_affine(
#             input_, ctx.normalized_shape, weight_, bias_, ctx.eps)
#         ctx.save_for_backward(input_, weight_, bias_, mean, invvar)

#         return output

#     @staticmethod
#     def backward(ctx, grad_output):

#         input_, weight_, bias_, mean, invvar = ctx.saved_tensors
#         grad_input = grad_weight = grad_bias = None
#         grad_input, grad_weight, grad_bias \
#             = fastfold_layer_norm_cuda.backward_affine(
#                 grad_output.contiguous(), mean, invvar,
#                 input_, ctx.normalized_shape,
#                 weight_, bias_, ctx.eps)

#         return grad_input, grad_weight, grad_bias, None, None


# class MixedFusedLayerNorm(torch.nn.Module):

#     def __init__(self, normalized_shape, eps=1e-5):
#         super(MixedFusedLayerNorm, self).__init__()

#         global fastfold_layer_norm_cuda
#         if fastfold_layer_norm_cuda is None:
#             try:
#                 fastfold_layer_norm_cuda = importlib.import_module("energonai_one_layer_norm_cuda")
#             except ImportError:
#                 raise RuntimeError('MixedFusedLayerNorm requires cuda extensions')

#         if isinstance(normalized_shape, numbers.Integral):
#             normalized_shape = (normalized_shape,)
#         self.normalized_shape = torch.Size(normalized_shape)
#         self.eps = eps
#         self.weight = Parameter(torch.Tensor(*normalized_shape))
#         self.bias = Parameter(torch.Tensor(*normalized_shape))
#         self.reset_parameters()

#     def reset_parameters(self):

#         init.ones_(self.weight)
#         init.zeros_(self.bias)

#     def forward(self, input):

#         return FusedLayerNormAffineFunction.apply(input, self.weight, self.bias,
#                                                   self.normalized_shape, self.eps)