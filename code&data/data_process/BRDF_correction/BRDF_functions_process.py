import os
from glob import glob
from multiprocessing import Pool
import numpy as np
import pandas as pd
import cupy as cp
from my_functions import Pandoras_box

# 其他代码，例如使用 multiprocessing 的部分



# 使用多进程
if __name__ == '__main__':
    # 获取文件列表
    file_list = glob("H:\\grsl\\h_csv\\h_amazon\\*.csv")

    with Pool(8) as p:
        p.map(Pandoras_box, file_list)