import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
from statsmodels.formula.api import ols
import rasterio
import matplotlib.gridspec as gridspec

# 重置 Matplotlib 样式为默认值
plt.rcdefaults()

# 设置坐标轴的字体大小和字体
plt.rcParams['xtick.labelsize'] = 10
plt.rcParams['ytick.labelsize'] = 10
plt.rcParams['font.family'] = 'Arial'

# 读取并预处理tif文件数据
def read_and_preprocess_tif_data(folder_path):
    data_dict = {"Cornbelt": [], "Amazon": []}
    for filename in os.listdir(folder_path):
        if filename.endswith(".tif"):
            region = "Cornbelt" if "cornbelt" in filename.lower() else "Amazon"
            with rasterio.open(os.path.join(folder_path, filename)) as src:
                data = src.read(1)
            valid_data = data[~np.isnan(data)].flatten()
            data_dict[region].extend(valid_data)
    return np.array(data_dict["Cornbelt"]), np.array(data_dict["Amazon"])

# 绘制小提琴图
def violin_plot(ax, data_cb, data_an, variable):
    # 数据处理
    df_cb = pd.DataFrame(data_cb, columns=[variable])
    df_cb['Site'] = 'Corn\nBelt'
    df_an = pd.DataFrame(data_an, columns=[variable])
    df_an['Site'] = 'Amazon\nrainforest'

    df_cb.dropna(axis=0, how='any', inplace=True)
    df_cb.dropna(axis=0, how='any', inplace=True)

    df = pd.concat([df_cb, df_an], ignore_index=True)
    df.dropna(axis=0, how='any', inplace=True)

    # 进行ANOVA分析并计算p值
    model = ols(f'{variable} ~ C(Site)', data=df).fit()
    p_value = sm.stats.anova_lm(model, typ=2)['PR(>F)']['C(Site)']
    if p_value < 0.001:
        ax.text(0.45, 0.9, '***', transform=ax.transAxes, fontsize=10)
    elif p_value < 0.01:
        ax.text(0.45, 0.9, '**', transform=ax.transAxes, fontsize=10)
    elif p_value < 0.05:
        ax.text(0.45, 0.9, '*', transform=ax.transAxes, fontsize=10)
    else:
        ax.text(0.45, 0.9, 'ns', transform=ax.transAxes, fontsize=10)

    # 绘制小提琴
    sns.violinplot(x='Site', y=variable, data=df, ax=ax, palette=["#e95f5c", "#4899ff"],
                   width=0.7, scale='width', inner='box', fliersize=3, saturation=1, linewidth=0.7)

    # 设置图的其他要素
    num_samples_cb = len(df_cb)
    num_samples_an = len(df_an)
    ax.text(0.25, 0.04, f'N = {num_samples_cb}', transform=ax.transAxes, ha='center', va='center', fontsize=7)
    ax.text(0.75, 0.04, f'N = {num_samples_an}', transform=ax.transAxes, ha='center', va='center', fontsize=7)

    ax.yaxis.set_major_locator(plt.MaxNLocator(4))
    ax.set_ylim(0, None)
    ax.tick_params(axis='y', which='major', direction='in',length=4, color='black', width=1)
    ax.set_ylabel('')
    ax.set_title('')

    ylabel_fontsize = 10
    if variable == "EVI2_type_C":
        ax.set_xlabel("EVI2", fontsize=ylabel_fontsize)
        ax.set_ylim([0, 0.8])
        ax.yaxis.set_major_locator(plt.MaxNLocator(4))
    elif variable == "NIRv_type_C":
        ax.set_xlabel("NIRv", fontsize=ylabel_fontsize)
        ax.set_ylim([0, 0.5])
        ax.yaxis.set_major_locator(plt.MaxNLocator(4))
    elif variable == "NDVI_type_C":
        ax.set_xlabel("NDVI", fontsize=ylabel_fontsize)
        ax.set_ylim([0, 1])
        ax.yaxis.set_major_locator(plt.MaxNLocator(4))
    elif variable == "new_kNDVI_type_C":
        ax.set_xlabel("kNDVI", fontsize=ylabel_fontsize)
        ax.set_ylim([0, 0.75])
        ax.yaxis.set_major_locator(plt.MaxNLocator(3))
    elif variable == "LAI":
        ax.set_xlabel("LAI", fontsize=ylabel_fontsize)
        ax.set_ylim([0, 8])
        ax.yaxis.set_major_locator(plt.MaxNLocator(4))
    else:
        ax.set_xlabel(variable, fontsize=ylabel_fontsize)
    ax.xaxis.set_label_coords(0.5, 1.12, transform=ax.transAxes)

# 主文件夹和输出路径
main_folder_path = r'D:\data_fig1'
output_folder = r'D:\fig1'

# 变量列表
variables = ["NDVI_type_C", "new_kNDVI_type_C", "NIRv_type_C", "EVI2_type_C", "LAI"]

# 创建带有自定义高度的子图grid
fig, ax = plt.subplots(1, 5, figsize=(10, 1.4))
gs = gridspec.GridSpec(1, 5, width_ratios=[1]*5, height_ratios=[1], wspace=0.55)
axi = [plt.subplot(gs[i]) for i in range(5)]

# 为每个变量创建并绘制小提琴图
for i, variable in enumerate(variables):
    folder_path = os.path.join(main_folder_path, variable)
    cornbelt_data, amazon_data = read_and_preprocess_tif_data(folder_path)
    violin_plot(axi[i], cornbelt_data, amazon_data, variable)

plt.tight_layout()
plt.savefig(os.path.join(output_folder, 'fig1.jpg'), dpi=600, bbox_inches='tight')
plt.close(fig)