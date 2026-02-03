"""
訓練模型腳本 - 自動訓練 HKDSE 和 IB 預測模型

使用方法：
  python train_model.py --data-dir ./Data
"""

import argparse
from pathlib import Path
from predict_model import PredictionModel


def main():
    parser = argparse.ArgumentParser(description="訓練 HKDSE 和 IB 預測模型")
    parser.add_argument(
        '--data-dir',
        type=str,
        default='./Data',
        help='數據目錄路徑（預設: ./Data）'
    )
    parser.add_argument(
        '--target',
        type=str,
        choices=['hkdse', 'ib', 'both'],
        default='both',
        help='訓練目標：hkdse、ib 或 both（預設: both）'
    )
    
    args = parser.parse_args()
    data_dir = Path(args.data_dir)
    
    targets = ['hkdse', 'ib'] if args.target == 'both' else [args.target]
    
    for target in targets:
        print(f"\n{'='*80}")
        print(f"開始訓練 {target.upper()} 模型")
        print(f"{'='*80}\n")
        
        try:
            model = PredictionModel(target=target)
            metrics = model.train(data_dir, test_size=0.2)
            model.save_model(Path('./models') / f"{target}_model.pkl")
            print(f"\n✓ {target.upper()} 模型訓練完成並已保存")
        except Exception as e:
            print(f"\n✗ {target.upper()} 模型訓練失敗: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*80}")
    print("所有模型訓練完成！")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
