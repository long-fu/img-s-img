# 向量数据库

## RAG简单用法
这是典型的 **以图搜图（Image Retrieval）** 场景。

你的流程应该不是直接把 YOLO 检测框结果存数据库，而是要把图片转换成**特征向量（Embedding）**，然后存到向量数据库中，后续图片进来再做相似度检索。

整体架构：

```text
                ┌──────────────┐
                │ 原始图片      │
                └──────┬───────┘
                       │
                       ▼
                ┌──────────────┐
                │ YOLO检测      │
                └──────┬───────┘
                       │
         ┌─────────────┴─────────────┐
         ▼                           ▼
   目标框裁剪                    标签结果
(person/car)               (car,bus,dog...)
         │
         ▼
 ┌──────────────┐
 │ 特征提取模型 │
 │ CLIP/ResNet  │
 └──────┬───────┘
        │
        ▼
 [0.123,0.456,...]
 512维向量
        │
        ▼
 ┌──────────────┐
 │ Vector DB    │
 │ Milvus       │
 │ Qdrant       │
 │ FAISS        │
 └──────────────┘
```

---

# 方案一：直接使用CLIP

目前最简单效果最好的方案。

OpenAI CLIP：

```python
image
  ↓
CLIP Encoder
  ↓
512维向量
```

例如：

```python
from PIL import Image
import torch
import clip

model, preprocess = clip.load("ViT-B/32")

image = preprocess(
    Image.open("test.jpg")
).unsqueeze(0)

with torch.no_grad():
    feature = model.encode_image(image)

feature = feature / feature.norm(dim=-1, keepdim=True)
```

得到：

```python
[0.123,
 0.456,
 ...
 0.789]
```

512维向量。

存入Milvus即可。

---

# 方案二：YOLO + CLIP

如果图片里有多个目标。

例如：

```text
图片
 ├─ person
 ├─ person
 ├─ car
 └─ dog
```

先YOLO：

```python
results = yolo(image)
```

得到：

```python
person
(100,100,200,300)

car
(500,200,800,500)
```

裁剪：

```python
crop = image[y1:y2,x1:x2]
```

然后每个目标单独提特征：

```python
person_vector
car_vector
dog_vector
```

存储：

```json
{
  "image_id":"xxx",
  "class":"car",
  "vector":[...]
}
```

这样可以：

```text
找相似汽车
找相似人
找相似狗
```

而不是整张图比较。

工业场景更常用这种方式。

---

# 方案三：YOLO标签直接向量化

如果你关心的是场景而不是外观。

例如：

```text
图片A
person
car
tree

图片B
person
car
tree
```

可以构建标签向量：

```text
person=1
car=1
dog=0
tree=1
bus=0
```

变成：

```text
[1,1,0,1,0]
```

或者：

```json
{
 "person":3,
 "car":2,
 "tree":5
}
```

然后存ES：

```json
{
 "labels":["person","car","tree"]
}
```

检索：

```text
含有人和车的图片
```

这种速度最快。

---

# 方案四：融合向量（推荐）

实际生产一般是：

```text
YOLO
  ↓
检测目标

CLIP
  ↓
视觉向量

标签
  ↓
元数据

OCR
  ↓
文字内容

GPS
  ↓
位置

时间
  ↓
时间戳
```

存Milvus：

```json
{
    "id":"10001",

    "vector":[0.1,...],

    "class":"car",

    "color":"red",

    "camera":"cam01",

    "time":"2026-06-01",

    "plate":"粤B12345"
}
```

查询：

```text
红色轿车
车牌类似粤B12345
最近7天
```

先元数据过滤：

```sql
class='car'
```

再向量检索：

```text
TopK=100
```

效率非常高。

---

# 向量库选择

如果数据量：

### 10万张以下

直接：

```text
FAISS
```

单机即可。

---

### 100万～1亿

推荐：

```text
Milvus
```

或

```text
Qdrant
```

架构：

```text
YOLO
  ↓
CLIP
  ↓
Kafka
  ↓
Embedding Service
  ↓
Milvus Cluster
```

---

# 边缘AI场景推荐

按照你目前的边缘AI调度平台架构，建议：

```text
设备
  ↓
图片上传
  ↓
YOLO推理
  ↓
检测结果
  ↓
Kafka
  ↓
Feature Service
      ↓
      CLIP提取向量
      ↓
Milvus

图片
      ↓
MinIO
```

存储结构：

```text
MinIO
 └── 原图

Milvus
 └── 特征向量

PostgreSQL
 └── 元数据
```

查询时：

```text
上传一张图片
      ↓
CLIP
      ↓
向量
      ↓
Milvus TopK
      ↓
返回 image_id
      ↓
MinIO获取原图
```

这是目前安防、工业质检、车辆识别、边缘视觉平台中最主流的实现方案。对于你的 YOLO + 边缘AI平台，推荐直接采用 **YOLO + CLIP + Milvus + MinIO** 的架构，而不是把 YOLO 标签直接当作向量库内容。这样后期支持“以图搜图”“相似目标检索”“跨摄像头目标追踪”都会容易很多。



------------------------


存储：图片->Embedding 插入->qdrant
搜索：图片->Embedding 搜索->qdrant-> 得到原始图片