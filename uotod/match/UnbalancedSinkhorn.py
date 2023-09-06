from abc import ABCMeta, abstractmethod

import torch
from torch import Tensor

from ._Compiled import _Compiled
from ._UnbalancedSinkhorn import _UnbalancedSinkhorn
from ..utils import extend_docstring, kwargs_decorator


@extend_docstring(_Compiled)
@extend_docstring(_UnbalancedSinkhorn)
class UnbalancedSinkhorn(_Compiled, _UnbalancedSinkhorn):
    r"""
    :param reg_pred: Prediction constraint regularization parameter for the OT algorithm. Defaults to 1.0.
    :param reg_target: Ground truth constraint regularization parameter for the OT algorithm. Defaults to 1.0.
    :type reg_pred: float, optional
    :type reg_target: float, optional
    """
    _compiled_name = 'unbalanced'

    @kwargs_decorator({'reg_pred': 1.,
                       'reg_target': 1.})
    def __init__(self,**kwargs) -> None:
        super(UnbalancedSinkhorn, self).__init__(**kwargs)

        self.reg_pred = kwargs['reg_pred']
        self.reg_target = kwargs['reg_target']

        assert isinstance(self.reg_pred, float), \
            TypeError("The parameter reg_pred must be a float.")
        assert isinstance(self.reg_target, float), \
            TypeError("The parameter reg_target must be a float.")

    def _matching(self, hist_pred: Tensor, hist_ttarget: Tensor, C:Tensor) -> Tensor:
        return self._matching_method(hist_pred, hist_ttarget, C, self.reg, self._num_iter, self.reg_target, self.reg_pred)

    @torch.no_grad()
    def _matching_native(self, hist_pred: Tensor, hist_ttarget: Tensor, C:Tensor, reg:float, num_iter: int, reg_pred:float, reg_target: float) -> Tensor:
        batch_size, num_pred, _ = C.shape
        factor1 = reg_pred / (reg_pred + reg) if reg_pred is not None else 1.
        factor2 = reg_target / (reg_target + reg) if reg_target is not None else 1.

        # Initialization of the algorithm
        K = torch.exp(-C / reg)
        u = torch.ones_like(hist_pred, requires_grad=False)

        # Iterations
        for _ in range(num_iter):
            u = (hist_pred / (K * ((hist_ttarget / (K * u.unsqueeze(2)).sum(dim=1)).pow(factor2))
                              .unsqueeze(1)).sum(dim=2)).pow(factor1)

        # Coupling matrix P = diag(u) @ K @ diag(v)
        P = torch.einsum("ni,nij,nj->nij", u, K, (hist_ttarget / (K * u.unsqueeze(2)).sum(dim=1)).pow(factor2))

        return P.data