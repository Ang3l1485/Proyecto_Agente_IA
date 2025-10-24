from minio import Minio
from minio.error import S3Error
import os
ENDPOINT = "localhost:9000"       # change if running elsewhere
ACCESS_KEY = os.getenv("MINIO_ROOT_USER")
SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD")
BUCKET    = "docs"

def ensure_bucket(client, bucket: str) -> None:
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)
        print(f"Bucket created: {bucket}")
    else:
        print(f"Bucket already exists: {bucket}")

def main():

    print("AK present?", bool(ACCESS_KEY), "SK present?", bool(SECRET_KEY))
    assert ACCESS_KEY and SECRET_KEY, "Missing MINIO_ROOT_USER or MINIO_ROOT_PASSWORD in environment"

    # 1) Connect
    client = Minio(
        ENDPOINT,
        access_key=ACCESS_KEY,
        secret_key=SECRET_KEY,
        secure=False,  # set True if using TLS
    )
    print("Connected to MinIO")

    # 2) Ensure bucket
    ensure_bucket(client, BUCKET)

    # 3) List objects (should be empty initially)
    print("Listing objects:")
    for obj in client.list_objects(BUCKET, recursive=True):
        print(f"- {obj.object_name} ({obj.size} bytes)")

if __name__ == "__main__":
    try:
        main()
    except S3Error as e:
        print("S3Error:", e)
