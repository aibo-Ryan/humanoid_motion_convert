# 运行 
```
python -m gui.main
```
## 1. PKL可以用于twist、asap。格式必须是：
```
==================================================
FPS        : 30
root_pos                 : (143, 3)  dtype=float64
root_rot                 : (143, 4)  dtype=float64
dof_pos                  : (143, 24)  dtype=float64
local_body_pos           : torch.Size([143, 29, 3])  dtype=torch.float32
link_body_list           : len=29
==================================================
```
## 2. csv可以用来霆天软件的可视化。格式必须是：
```
==================================================
root_pos shape: (143, 3)
root_rot shape: (143, 4)
dof_pos shape: (143, 24)
==================================================
```
## 3. 他们的csv和mjlab、beyondmimic的csv维度不一样
