# 重要：需要重新训练模型

## 问题修复

已修复预测结果不合理的问题。主要改进包括：

1. **改进特征提取**：更好地处理学生ID列和数值数据
2. **数据验证**：过滤异常值和无效数据
3. **目标值范围限制**：确保预测结果在合理范围内
   - HKDSE: -2 到 5
   - IB: 1 到 7
4. **改进数据匹配逻辑**：更智能的学生数据匹配

## 需要重新训练模型

由于修复了训练逻辑，**必须重新训练模型**才能获得正确的预测结果。

### 重新训练步骤

```bash
# 删除旧模型（可选，会自动覆盖）
rm -rf models/

# 重新训练所有模型
python train_model.py --target both --data-dir ./Data
```

### 验证模型

训练完成后，可以使用示例文件测试：

```bash
# 测试 HKDSE 预测
python predict_model.py --mode predict --target hkdse --input sample_files/sample_eclass_data.xlsx

# 测试 IB 预测
python predict_model.py --mode predict --target ib --input sample_files/sample_eclass_data.xlsx
```

预测结果应该在合理范围内：
- HKDSE: -2 到 5 之间
- IB: 1 到 7 之间

## 如果训练失败

如果训练时出现错误，可能的原因：

1. **数据格式不匹配**：检查 eClass 数据和 HKDSE/IB 数据的格式
2. **学生ID无法匹配**：系统会尝试多种匹配方式，如果都失败会给出错误提示
3. **数据量不足**：至少需要5个有效样本

## 改进说明

### 特征提取改进
- 自动识别学生ID列（第一列或包含'id'/'student'的列）
- 过滤异常值（0-100范围外的值）
- 更好的数值列识别

### 数据匹配改进
- 直接ID匹配
- 顺序匹配（如果数量相同）
- 统计特征匹配（按成绩排序匹配）

### 预测结果限制
- HKDSE预测结果限制在 -2 到 5
- IB预测结果限制在 1 到 7
- 防止出现不合理的负值或超大值
