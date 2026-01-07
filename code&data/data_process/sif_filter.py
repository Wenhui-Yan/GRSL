import pandas as pd
import os
import glob

def QC(sif_data):
    """
    质量控制函数，进行数据清洗和标准化。
    """
    # 应用初始筛选条件
    sif_data = sif_data.loc[
        (sif_data["sif"] <= 4) & (sif_data["sif"] >= -2) &
        (sif_data["sif_err"] <= 0.55) & (sif_data["cloud_frac"] <= 0.5)
    ]

    # 定义分位数界限
    # lower_quantile = 0.05
    # upper_quantile = 0.95

    # # 计算分位数辅助函数
    # def quantile_bounds(data, column):
    #     return data[column].quantile([lower_quantile, upper_quantile])

    # # 计算分位数界限
    # lower_bound_SIF, upper_bound_SIF = quantile_bounds(sif_data, 'sif')

    # # 筛选数据
    # sif_data = sif_data.loc[
    #     (sif_data['sif'] >= lower_bound_SIF) & (sif_data['sif'] <= upper_bound_SIF)
    # ]

    return sif_data


# 设置输入和输出目录
input_dir = r'H:\AAAnew_grsl\amazon79'
output_dir = r'H:\AAAnew_grsl\amazon799'
# 检查输出目录是否存在，如果不存在则创建
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# 使用glob找到所有pkl文件
pkl_files = glob.glob(os.path.join(input_dir, 'amazon_*.pkl'))         #注意修改:亚马逊是a_*，玉米带是c_*

# 对每个文件进行处理
for file_path in pkl_files:
    # 读取pkl文件
    sif_data = pd.read_pickle(file_path)

    # 应用质量控制函数
    cleaned_sif_data = QC(sif_data)

    # 构建输出文件路径
    file_name = os.path.basename(file_path)
    output_path = os.path.join(output_dir, file_name)

    # 保存清洗后的数据
    cleaned_sif_data.to_pickle(output_path)

print(f'所有文件已清洗完毕，保存在{output_dir}。')



