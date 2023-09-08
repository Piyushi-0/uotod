import uotod
from sample import input, target, img

L = uotod.loss.GIoULoss()
H = uotod.match.BalancedSinkhorn(loc_matching_module=L, bg_cost=0.8)
H(input, target)

fig_img, fig_cost, fig_match = H.plot(img=img)