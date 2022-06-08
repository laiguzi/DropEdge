import sys
sys.path.append('/home/laixin/code/DropEdge/')
sys.path.append('/home/laixin/code/DropEdge/src/')
import scipy.sparse as sp



from utils import data_loader

dataset = 'cora'
datapath = '/home/laixin/code/DropEdge/data/'
task_type = 'full'

adj,_,_,_,_,_,_,_,_,_,_ = data_loader(dataset, datapath, "RWalkLap", False, task_type)
adj = adj.todense()
adj = adj.astype(float)
eigens = sp.linalg.eigsh(-adj, 3, return_eigenvectors=False)
print(eigens)