import streamlit as st
import pandas as pd

# E12/E24系列の基本値（1.0 ~ 9.1）
E12_BASE = [
    1.0, 1.2, 1.5, 1.8, 2.2, 2.7, 3.3, 3.9, 4.7, 5.6, 6.8, 8.2
]  
E24_BASE = E12_BASE + [
    1.1, 1.3, 1.6, 2.0, 2.4, 3.0, 3.6, 4.3, 5.1, 6.2, 7.5, 9.1
]

@st.cache_data
def get_e24_resistors(min_val=1.0, max_val=10_000_000.0):
    """指定範囲内のE24系列の抵抗値リストを生成する"""
    resistors = []
    multiplier = 1.0
    while multiplier <= max_val:
        for b in E24_BASE:
            val = b * multiplier
            if min_val <= val <= max_val:
                resistors.append(val)
        multiplier *= 10
    return sorted(resistors)

def calc_parallel(r1, r2):
    """並列抵抗の合成値を計算"""
    if r1 + r2 == 0:
        return 0
    return (r1 * r2) / (r1 + r2)

def main():
    st.set_page_config(page_title="E24 抵抗コンビネーション電卓", layout="wide")
    st.title("🔌 E24系列 抵抗組み合わせオプティマイザー")
    st.write("目的の抵抗値に最も近い1〜3本の抵抗の組み合わせを算出。")

    # --- サイドバー設定 ---
    st.sidebar.header("検索条件")
    target = st.sidebar.number_input("目標抵抗値 (Ω)", min_value=0.1, max_value=10_000_000.0, value=1000.0, step=1.0)
    max_count = st.sidebar.selectbox("最大使用本数", [2, 3], index=0)
    tolerance = st.sidebar.slider("許容誤差 (±%)", min_value=0.01, max_value=5.0, value=1.0, step=0.01) / 100.0
    num_results = st.sidebar.slider("表示件数", min_value=5, max_value=50, value=15)

    # 抵抗の探索範囲（1Ω 〜 3MΩ）
    resistors = get_e24_resistors(1.0, 3_000_000.0)

    if st.button("計算実行", type="primary"):
        with st.spinner("最適な組み合わせを計算中..."):
            results = []
            
            # 1. 1本の場合
            for r1 in resistors:
                err = (r1 - target) / target
                if abs(err) <= tolerance:
                    results.append({
                        "合成抵抗 (Ω)": r1,
                        "誤差 (%)": err * 100,
                        "構成": "1本",
                        "詳細": f"{r1:g} Ω"
                    })

            if max_count >= 2:
                # 2本直列
                for i in range(len(resistors)):
                    for j in range(i, len(resistors)):
                        r1, r2 = resistors[i], resistors[j]
                        r_val = r1 + r2
                        err = (r_val - target) / target
                        if abs(err) <= tolerance:
                            results.append({
                                "合成抵抗 (Ω)": r_val,
                                "誤差 (%)": err * 100,
                                "構成": "2本直列",
                                "詳細": f"{r1:g} + {r2:g}"
                            })

                # 2本並列
                for i in range(len(resistors)):
                    for j in range(i, len(resistors)):
                        r1, r2 = resistors[i], resistors[j]
                        r_val = calc_parallel(r1, r2)
                        err = (r_val - target) / target
                        if abs(err) <= tolerance:
                            results.append({
                                "合成抵抗 (Ω)": r_val,
                                "誤差 (%)": err * 100,
                                "構成": "2本並列",
                                "詳細": f"{r1:g} // {r2:g}"
                            })

            if max_count >= 3:
                # 3本直列: R1 + R2 + R3
                for i in range(len(resistors)):
                    for j in range(i, len(resistors)):
                        for k in range(j, len(resistors)):
                            r1, r2, r3 = resistors[i], resistors[j], resistors[k]
                            r_val = r1 + r2 + r3
                            err = (r_val - target) / target
                            if abs(err) <= tolerance:
                                results.append({
                                    "合成抵抗 (Ω)": r_val,
                                    "誤差 (%)": err * 100,
                                    "構成": "3本直列",
                                    "詳細": f"{r1:g} + {r2:g} + {r3:g}"
                                })

                # 3本並列: R1 // R2 // R3
                for i in range(len(resistors)):
                    for j in range(i, len(resistors)):
                        for k in range(j, len(resistors)):
                            r1, r2, r3 = resistors[i], resistors[j], resistors[k]
                            denom = (1/r1) + (1/r2) + (1/r3)
                            r_val = 1 / denom if denom > 0 else 0
                            err = (r_val - target) / target
                            if abs(err) <= tolerance:
                                results.append({
                                    "合成抵抗 (Ω)": r_val,
                                    "誤差 (%)": err * 100,
                                    "構成": "3本並列",
                                    "詳細": f"{r1:g} // {r2:g} // {r3:g}"
                                })

                # 直並列1: R1 + (R2 // R3)
                for i in range(len(resistors)):
                    for j in range(len(resistors)):
                        for k in range(j, len(resistors)):
                            r1 = resistors[i]
                            r2, r3 = resistors[j], resistors[k]
                            r_val = r1 + calc_parallel(r2, r3)
                            err = (r_val - target) / target
                            if abs(err) <= tolerance:
                                results.append({
                                    "合成抵抗 (Ω)": r_val,
                                    "誤差 (%)": err * 100,
                                    "構成": "直並列 (R + R//R)",
                                    "詳細": f"{r1:g} + ({r2:g} // {r3:g})"
                                })

                # 直並列2: (R1 // R2) + R3
                for i in range(len(resistors)):
                    for j in range(i, len(resistors)):
                        for k in range(len(resistors)):
                            r1, r2 = resistors[i], resistors[j]
                            r3 = resistors[k]
                            r_val = calc_parallel(r1, r2) + r3
                            err = (r_val - target) / target
                            if abs(err) <= tolerance:
                                results.append({
                                    "合成抵抗 (Ω)": r_val,
                                    "誤差 (%)": err * 100,
                                    "構成": "直並列 ((R//R) + R)",
                                    "詳細": f"({r1:g} // {r2:g}) + {r3:g}"
                                })

            if not results:
                st.warning("指定した許容誤差の範囲内に一致する組み合わせが見つかりませんでした。許容誤差を広げるか、条件を確認してください。")
            else:
                # 誤差の絶対値が小さい順にソート
                results.sort(key=lambda x: abs(x["誤差 (%)"]))
                
                # 重複する合成抵抗値を適度にまとめる（またはそのまま上位表示）
                df = pd.DataFrame(results[:num_results])
                
                st.success(f"条件に一致する候補が {len(results)} 件見つかりました（上位 {min(num_results, len(results))} 件を表示）")
                
                # データフレームの表示
                st.dataframe(
                    df.style.format({
                        "合成抵抗 (Ω)": "{:.4f}",
                        "誤差 (%)": "{:+.3f}%"
                    }),
                    use_container_width=True
                )

if __name__ == "__main__":
    main()