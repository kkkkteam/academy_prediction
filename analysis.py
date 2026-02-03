"""
資料分析工具 - 資料提取與分析

安裝說明：
==========

1. 確保已安裝 Python 3.7 或以上版本
   python --version

2. 安裝所需的套件（建議使用虛擬環境）：
   
   # 方法一：使用 requirements.txt（推薦）
   pip install -r requirements.txt
   
   # 方法二：手動安裝
   pip install pandas matplotlib seaborn openpyxl

3. 如果遇到 NumPy 兼容性錯誤（例如：AttributeError: _ARRAY_API not found）：
   # 降級 NumPy 到 1.x 版本
   pip install "numpy<2.0.0"
   pip install --upgrade numexpr
   
4. 如果遇到其他安裝問題，可以嘗試：
   pip install --upgrade pip
   pip install -r requirements.txt --force-reinstall

使用說明：
==========

基本用法：
  python analysis.py --input <資料檔或資料夾路徑> [--output-dir <輸出資料夾>]

範例：
  # 分析單一檔案
  python analysis.py --input "./Data/scores.csv"
  
  # 分析整個資料夾（會處理資料夾內所有 CSV / Excel 檔）
  python analysis.py --input "./Data" --output-dir "analysis_output"
  
  # 使用簡短參數
  python analysis.py -i "./Data" -o "results"

參數說明：
  --input, -i     : 必填，輸入資料檔或資料夾路徑（支援 CSV / Excel）
  --output-dir, -o: 選填，輸出圖表與報告的資料夾（預設: analysis_output）

支援的檔案格式：
  - CSV 檔 (*.csv)
  - Excel 檔 (*.xls, *.xlsx)

輸出內容：
  - 終端機：資料基本資訊、統計描述
  - 圖片檔：直方圖、盒鬚圖、相關係數熱圖
"""

import argparse
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


def load_data(path: Path) -> pd.DataFrame:
    """根據副檔名讀取單一資料檔（支援 CSV / Excel）"""
    if not path.exists():
        raise FileNotFoundError(f"找不到檔案: {path}")

    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    elif suffix in {".xls", ".xlsx"}:
        return pd.read_excel(path)
    else:
        raise ValueError(f"不支援的檔案格式: {suffix}，請使用 CSV 或 Excel。")


def basic_info(df: pd.DataFrame) -> None:
    """輸出資料集的基本資訊"""
    print("=" * 80)
    print("資料基本資訊")
    print("=" * 80)
    print(f"列數 (rows): {df.shape[0]}")
    print(f"欄數 (columns): {df.shape[1]}")
    print("\n欄位名稱與型別:")
    print(df.dtypes)

    print("\n前 5 筆資料:")
    print(df.head())

    print("\n每欄缺失值數量:")
    print(df.isna().sum())


def basic_statistics(df: pd.DataFrame) -> None:
    """輸出數值欄位的統計描述"""
    numeric_cols = df.select_dtypes(include="number")
    if numeric_cols.empty:
        print("\n沒有數值型欄位可以做統計分析。")
        return

    print("\n" + "=" * 80)
    print("數值欄位統計描述")
    print("=" * 80)
    print(numeric_cols.describe().T)


def plot_distributions(df: pd.DataFrame, output_dir: Path) -> None:
    """針對數值欄位畫直方圖與盒鬚圖，輸出成圖片檔"""
    output_dir.mkdir(parents=True, exist_ok=True)
    numeric_cols = df.select_dtypes(include="number")

    if numeric_cols.empty:
        print("\n沒有數值型欄位可視覺化。")
        return

    for col in numeric_cols.columns:
        series = numeric_cols[col].dropna()
        if series.empty:
            continue

        # 直方圖
        plt.figure(figsize=(6, 4))
        sns.histplot(series, kde=True)
        plt.title(f"Histogram of {col}")
        plt.tight_layout()
        hist_path = output_dir / f"hist_{col}.png"
        plt.savefig(hist_path)
        plt.close()

        # 盒鬚圖
        plt.figure(figsize=(4, 4))
        sns.boxplot(x=series)
        plt.title(f"Boxplot of {col}")
        plt.tight_layout()
        box_path = output_dir / f"box_{col}.png"
        plt.savefig(box_path)
        plt.close()

        print(f"已輸出欄位 {col} 的直方圖與盒鬚圖到資料夾: {output_dir}")


def correlation_heatmap(df: pd.DataFrame, output_dir: Path) -> None:
    """畫數值欄位之間的相關係數熱圖"""
    numeric_cols = df.select_dtypes(include="number")
    if numeric_cols.shape[1] < 2:
        print("\n數值欄位少於 2 個，略過相關性分析。")
        return

    corr = numeric_cols.corr()
    plt.figure(figsize=(8, 6))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm")
    plt.title("Correlation Heatmap")
    plt.tight_layout()

    output_dir.mkdir(parents=True, exist_ok=True)
    heatmap_path = output_dir / "correlation_heatmap.png"
    plt.savefig(heatmap_path)
    plt.close()

    print(f"\n已輸出相關係數熱圖到: {heatmap_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="簡單資料讀取與分析工具（支援 CSV / Excel）"
    )
    parser.add_argument(
        "--input",
        "-i",
        type=str,
        required=True,
        help="輸入資料檔或資料夾路徑（CSV / Excel 檔，或包含這些檔案的資料夾）",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        type=str,
        default="analysis_output",
        help="輸出圖表與報告的資料夾（預設: analysis_output）",
    )
    return parser.parse_args()


def analyze_single_file(file_path: Path, base_output_dir: Path) -> None:
    """對單一檔案進行完整分析"""
    if not file_path.exists():
        print(f"\n[警告] 找不到檔案，略過: {file_path}")
        return

    print("\n" + "#" * 80)
    print(f"開始分析檔案: {file_path}")
    print("#" * 80)

    df = load_data(file_path)

    # 為每個檔案建立獨立輸出資料夾
    safe_name = file_path.stem.replace(" ", "_")
    output_dir = base_output_dir / safe_name

    # 基本資訊與統計
    basic_info(df)
    basic_statistics(df)

    # 視覺化
    plot_distributions(df, output_dir)
    correlation_heatmap(df, output_dir)

    print(f"\n檔案 {file_path.name} 分析完成，輸出已存到資料夾: {output_dir}")


def find_data_files(directory: Path) -> list[Path]:
    """遞迴搜尋資料夾中的所有 CSV / Excel 檔"""
    files = []
    for path in directory.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".csv", ".xls", ".xlsx"}:
            files.append(path)
    return sorted(files)


def main() -> None:
    args = parse_args()
    data_path = Path(args.input)
    output_dir = Path(args.output_dir)

    if data_path.is_dir():
        # 資料夾模式：遞迴掃描所有 CSV / Excel 檔
        files = find_data_files(data_path)

        if not files:
            print(f"在資料夾 {data_path} 及其子資料夾中找不到任何 CSV / Excel 檔。")
            return

        print(f"在資料夾 {data_path} 及其子資料夾中找到 {len(files)} 個資料檔，依序進行分析。")
        for f in files:
            analyze_single_file(f, output_dir)
        print("\n全部檔案分析完成！")
    else:
        # 單一檔案模式
        analyze_single_file(data_path, output_dir)


if __name__ == "__main__":
    main()

