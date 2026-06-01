from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue

# =========================
# 1. 连接 Qdrant
# =========================
client = QdrantClient(
    url="http://localhost:6333",
    api_key="my_secret_key"  # 如果没有设置 API Key，可以省略这个参数
)

collection_name = "demo"


# =========================
# 2. 创建 Collection
# =========================
def create_collection():
    if not client.collection_exists(collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=4,              # 向量维度（比如 384 / 768 / 1536）
                distance=Distance.COSINE
            )
        )
        print("collection created")


# =========================
# 3. 插入 / 更新向量（Upsert）
# =========================
def upsert_points():
    points = [
        PointStruct(
            id=1,
            vector=[0.1, 0.2, 0.3, 0.4],
            payload={
                "text": "hello world",
                "tag": "greeting"
            }
        ),
        PointStruct(
            id=2,
            vector=[0.2, 0.1, 0.4, 0.3],
            payload={
                "text": "good morning",
                "tag": "greeting"
            }
        ),
        PointStruct(
            id=3,
            vector=[0.9, 0.8, 0.1, 0.2],
            payload={
                "text": "deep learning",
                "tag": "ai"
            }
        )
    ]

    client.upsert(
        collection_name=collection_name,
        points=points
    )

    print("upsert done")


# =========================
# 4. 向量搜索（相似查询）
# =========================
def search(query_vector):
    result = client.query_points(
        collection_name=collection_name,
        query=query_vector,
        limit=3
    )

    for r in result.points:
        print("id:", r.id)
        print("score:", r.score)
        print("payload:", r.payload)
        print("-" * 30)


# =========================
# 5. 带 Filter 的搜索（payload过滤）
# =========================
def search_with_filter(query_vector):
    result = client.query_points(
        collection_name=collection_name,
        query=query_vector,
        limit=3,
        query_filter=Filter(
            must=[
                FieldCondition(
                    key="tag",
                    match=MatchValue(value="ai")
                )
            ]
        )
    )

    for r in result.points:
        print(r.payload)


# =========================
# 6. 删除数据
# =========================
def delete_point(point_id: int):
    client.delete(
        collection_name=collection_name,
        points_selector=[point_id]
    )
    print(f"deleted point {point_id}")


# =========================
# 7. 主流程
# =========================
if __name__ == "__main__":
    create_collection()

    upsert_points()

    print("\n=== normal search ===")
    search([0.1, 0.2, 0.3, 0.4])

    print("\n=== filtered search ===")
    search_with_filter([0.1, 0.2, 0.3, 0.4])

    # delete_point(1)