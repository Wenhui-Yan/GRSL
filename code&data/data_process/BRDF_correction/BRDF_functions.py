import numpy as np
import cupy as cp
import pandas as pd
import os
#天顶观测角（VZA）为0度，太阳天顶角（SZA）为45度
def Ross_thick(sZenith, vZenith, rAzimuth):
    # 几何光学（GO）模型，用于计算 Ross thick 核（相对于粗糙表面反射的光滑表面的补充）
    # xi: 上述公式中的，计算角度。
    # k: 公式中的Ross thick核值
    cosxi = cp.cos(sZenith) * cp.cos(vZenith) + cp.sin(sZenith) * cp.sin(vZenith) * cp.cos(rAzimuth)
    xi = cp.arccos(cp.clip(cosxi, -1, 1))  # 使用clip防止超出范围
    k1 = (cp.pi / 2 - xi) * cosxi + cp.sin(xi)
    k = k1 / (cp.cos(sZenith) + cp.cos(vZenith)) - cp.pi / 4
    return k

def Li_Transit(sZenith, vZenith, rAzimuth):
    # 该函数实现了Li-Transit核的算法，它是 BRDF 核函数的一部分
    # sZenith，vZenith 和 rAzimuth 分别代表太阳天顶角，观测天顶角和相对方位角
    # 额外包括  brratio和 hbratio 用于确定核密度和高度的比率参数,默认值为1和2
    rAzimuth = cp.abs(rAzimuth)
    rAzimuth[rAzimuth >= cp.pi] = 2 * cp.pi - rAzimuth[rAzimuth >= cp.pi]

    brratio = 1
    hbratio = 2
    t1 = brratio * cp.tan(sZenith)
    theta_ip = cp.arctan(t1)
    t2 = brratio * cp.tan(vZenith)
    theta_vp = cp.arctan(t2)
    temp1 = cp.cos(theta_ip)
    temp2 = cp.cos(theta_vp)
    cosxip = temp1 * temp2 + cp.sin(theta_ip) * cp.sin(theta_vp) * cp.cos(rAzimuth)
    D1 = cp.tan(theta_ip) ** 2 + cp.tan(theta_vp) ** 2 - 2 * cp.tan(theta_ip) * cp.tan(theta_vp) * cp.cos(rAzimuth)
    D = cp.sqrt(D1)
    cost1 = cp.tan(theta_ip) * cp.tan(theta_vp) * cp.sin(rAzimuth)
    cost2 = D1 + cost1 ** 2
    temp3 = 1 / temp1 + 1 / temp2
    cost = hbratio * cp.sqrt(cost2) / temp3
    cost = cp.clip(cost, -1, 1)  # 限制范围以避免超出 acos 的输入范围
    t = cp.arccos(cost)

    O = (t - cp.sin(t) * cost) * temp3 / cp.pi
    B = temp3 - O
    k = cp.where(B > 2, (1 + cosxip) / (temp2 * temp1 * B) - 2, -B + (1 + cosxip) / (2 * temp2 * temp1))

    return k


def BRDF_degree(i, v, r, iso, vol, geo):
    # 用于计算给定观测条件下地表的BRDF值
    # i，v，r 分别代表太阳天顶角，观测天顶角和相对方位角
    # iso，vol 和 geo 分别代表Isotropic kernel，RossThick kernel 和 Li-Sparse-RossThin kernel 的 BRDF权重参数

    # 将 pandas.Series 转换为 cupy 数组
    i_array = cp.array(i.values)
    v_array = cp.array(v.values)
    r_array = cp.array(r.values)
    iso_array = cp.array(iso.values)
    vol_array = cp.array(vol.values)
    geo_array = cp.array(geo.values)

    # 进行计算
    i_rad = cp.radians(i_array)
    v_rad = cp.radians(v_array)
    r_rad = cp.radians(r_array)
    ############################################################################################################
    #########重点，只输入了三个不是四个
    R = iso_array + vol_array * Ross_thick(i_rad, v_rad, r_rad) + geo_array * Li_Transit(i_rad, v_rad, r_rad)

    # 将结果转换回 numpy 数组
    return cp.asnumpy(R)
def Pandoras_box(csv_path):

    roi_df = pd.read_csv(csv_path)
    # 角度转换为弧度
    roi_df['VZA_rad'] = np.abs(roi_df['vza']) * np.pi / 180
    roi_df['SZA_rad'] = np.abs(roi_df['sza']) * np.pi / 180
    roi_df['PA_rad'] = np.abs(roi_df['phase_angl']) * np.pi / 180

    # 计算 RAA
    epsilon = 1e-6
    cos_PA = np.cos(roi_df['PA_rad'])
    cos_SZA = np.cos(roi_df['SZA_rad'])
    cos_VZA = np.cos(roi_df['VZA_rad'])
    sin_SZA = np.sin(roi_df['SZA_rad'])
    sin_VZA = np.sin(roi_df['VZA_rad'])
    # e

    RAA_rad = np.arccos(np.clip((cos_PA - cos_SZA * cos_VZA) / (sin_SZA * sin_VZA + epsilon), -1, 1))


    # RAA_rad = np.arccos((cos_PA - cos_SZA * cos_VZA) / (sin_SZA * (sin_VZA + epsilon)))
   # RAA_rad = (cos_PA - cos_SZA * cos_VZA) / (sin_SZA * sin_VZA)
    # 限制cosRAAs的值在-1到1之间
    #RAA_rad = np.clip(RAA_rad, -1, 1)

    # 计算acos，得到RAAs的弧度值
    RAA_deg = np.degrees(RAA_rad)
    roi_df['RAA_deg'] = RAA_deg
    # roi_df['RAA_deg'] = RAA_deg.replace(np.nan, 90)  # 替换 NaN 值
    # 应用 BRDF_degree 函数
    # 假设 BRDF_degree 已经被更新以接受矢量化输入
    """
    重命名BRDF参数产品
    """
    roi_df.rename(columns={
        "BRDF_Albedo_Parameters_Band1_iso":"iso_r",
        "BRDF_Albedo_Parameters_Band1_vol":"vol_r",
        "BRDF_Albedo_Parameters_Band1_geo":"geo_r",
        "BRDF_Albedo_Parameters_Band2_iso":"iso_n",
        "BRDF_Albedo_Parameters_Band2_vol":"vol_n",
        "BRDF_Albedo_Parameters_Band2_geo":"geo_n",
    }, inplace=True)

    """
    TROPOMI同角度
    """
    roi_df['red_brdf_adjusted_to_tropomi_angle'] = BRDF_degree(roi_df['sza'], roi_df['vza'], roi_df['RAA_deg'],
                                   roi_df['iso_r'], roi_df['vol_r'], roi_df['geo_r'])
    roi_df['nir_brdf_adjusted_to_tropomi_angle'] = BRDF_degree(roi_df['sza'], roi_df['vza'], roi_df['RAA_deg'],
                                   roi_df['iso_n'], roi_df['vol_n'], roi_df['geo_n'])
    """
    Nadir
    """
    roi_df_for_Nadir = roi_df[['sza', 'vza', 'RAA_deg']].copy()
    roi_df_for_Nadir['vza'] = 0

    roi_df['red_brdf_adjusted_to_Nadir'] = BRDF_degree(roi_df['sza'], roi_df_for_Nadir['vza'], roi_df_for_Nadir['RAA_deg'],
                                         roi_df['iso_r'], roi_df['vol_r'], roi_df['geo_r'])
    roi_df['nir_brdf_adjusted_to_Nadir'] = BRDF_degree(roi_df['sza'], roi_df_for_Nadir['vza'], roi_df_for_Nadir['RAA_deg'],
                                         roi_df['iso_n'], roi_df['vol_n'], roi_df['geo_n'])
    """
    归一化到特定的观测角度（其中天顶观测角（VZA）为0度，太阳天顶角（SZA）为45度）
    
    """
    roi_df_D45 = roi_df[['sza', 'vza', 'RAA_deg']].copy()
    roi_df_D45['vza'] = 0
    roi_df_D45['sza'] = 45
    roi_df['red_brdf_adjusted_to_vza0_sza45'] = BRDF_degree(roi_df_D45['sza'], roi_df_D45['vza'], roi_df_D45['RAA_deg'],
                                       roi_df['iso_r'], roi_df['vol_r'], roi_df['geo_r'])
    roi_df['nir_brdf_adjusted_to_vza0_sza45'] = BRDF_degree(roi_df_D45['sza'], roi_df_D45['vza'], roi_df_D45['RAA_deg'],
                                       roi_df['iso_n'], roi_df['vol_n'], roi_df['geo_n'])
    """
    type_A: TROPOMI同角度的植被指数
    """
    # 计算 NDVI、NIRv 和 EVI2
    roi_df['NDVI_type_A'] = (roi_df['nir_brdf_adjusted_to_tropomi_angle'] - roi_df['red_brdf_adjusted_to_tropomi_angle']) / (roi_df['nir_brdf_adjusted_to_tropomi_angle'] + roi_df['red_brdf_adjusted_to_tropomi_angle'])
    roi_df['NIRv_type_A'] = roi_df['NDVI_type_A'] * roi_df['nir_brdf_adjusted_to_tropomi_angle']
    roi_df['EVI2_type_A'] = 2.5 * (
            (roi_df['nir_brdf_adjusted_to_tropomi_angle'] - roi_df['red_brdf_adjusted_to_tropomi_angle']) / (roi_df['nir_brdf_adjusted_to_tropomi_angle'] + 2.4 * roi_df['red_brdf_adjusted_to_tropomi_angle'] + 1))

    """
    type_B: Nadir的植被指数
    """
    # 计算 NDVI、NIRv、EVI2、kNDVI
    roi_df['NDVI_type_B'] = (roi_df['nir_brdf_adjusted_to_Nadir'] - roi_df['red_brdf_adjusted_to_Nadir']) / (roi_df['nir_brdf_adjusted_to_Nadir'] + roi_df['red_brdf_adjusted_to_Nadir'])
    roi_df['NIRv_type_B'] = roi_df['NDVI_type_B'] * roi_df['nir_brdf_adjusted_to_Nadir']
    roi_df['EVI2_type_B'] = 2.5 * (
            (roi_df['nir_brdf_adjusted_to_Nadir'] - roi_df['red_brdf_adjusted_to_Nadir']) / (roi_df['nir_brdf_adjusted_to_Nadir'] + 2.4 * roi_df['red_brdf_adjusted_to_Nadir'] + 1))
    roi_df['kNDVI_type_B'] = tanh(roi_df['NDVI_type_B'] * roi_df['NDVI_type_B'])
    """
    type_C: BRDF归一化的植被指数
    """
    # 计算 NDVI、NIRv、EVI2、kNDVI
    roi_df['NDVI_type_C'] = (roi_df['nir_brdf_adjusted_to_vza0_sza45'] - roi_df['red_brdf_adjusted_to_vza0_sza45']) / (roi_df['nir_brdf_adjusted_to_vza0_sza45'] + roi_df['red_brdf_adjusted_to_vza0_sza45'])
    roi_df['NIRv_type_C'] = roi_df['NDVI_type_C'] * roi_df['nir_brdf_adjusted_to_vza0_sza45']
    roi_df['EVI2_type_C'] = 2.5 * (
            (roi_df['nir_brdf_adjusted_to_vza0_sza45'] - roi_df['red_brdf_adjusted_to_vza0_sza45']) / (roi_df['nir_brdf_adjusted_to_vza0_sza45'] + 2.4 * roi_df['red_brdf_adjusted_to_vza0_sza45'] + 1))
    roi_df['kNDVI_type_C'] = tanh(roi_df['NDVI_type_C'] * roi_df['NDVI_type_C'])
    """
    SIF_n par归一化 和 BRDF归一化的
    """
    roi_df['SIF_n'] = roi_df['sif'] / roi_df['par']

    roi_df["SIF_n_brdf_adjustment_factor"] = roi_df["NIRv_type_C"] / roi_df["NIRv_type_A"]
    roi_df["SIF_n_brdf_adjustment"] = roi_df["NIRv_type_C"] / roi_df["NIRv_type_A"] * roi_df["SIF_n"]

    roi_df["NIRvP"] = roi_df["NIRv_type_A"] * roi_df["par"]
    # NIRvR ref:https://www.sciencedirect.com/science/article/pii/S0034425721005769
    roi_df["NIRvR"] = roi_df["NDVI_type_A"] * roi_df["NIR"]

    """8
    Phi F, 两种计算方式
    """
    roi_df["SIF_yield_P"] = roi_df["sif"] / roi_df["NIRvP"]
    roi_df["SIF_yield_R"] = roi_df["sif"] / roi_df["NIRvR"]



    """
    写入pkl
    """
    os.makedirs("results_amazon2", exist_ok=True)
    output_filename = os.path.basename(csv_path).split(".")[-2]
    roi_df.to_pickle(f"H:/grsl/results_amazon2/aa_{output_filename}.pkl")
    # Phi F, 两种计算方式
    # """


