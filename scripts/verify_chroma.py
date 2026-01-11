import chromadb
import argparse
import sys

def verify_chroma(host, port, collection_name="kbase_docs"):
    print(f"🔌 Connecting to ChromaDB at {host}:{port}...")
    try:
        client = chromadb.HttpClient(host=host, port=port)
        heartbeat = client.heartbeat()
        print(f"✅ Connection successful! Heartbeat: {heartbeat}")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        sys.exit(1)

    try:
        collection = client.get_collection(collection_name)
        count = collection.count()
        print(f"📊 Collection '{collection_name}' has {count} documents.")
        
        if count > 0:
            print("🔎 Peeking at top 3 documents:")
            peek = collection.peek(limit=3)
            for i, meta in enumerate(peek['metadatas']):
                print(f"   [{i+1}] Source: {meta.get('file_name', 'Unknown')}")
        else:
            print("⚠️ Collection is empty. Ingestion might still be running or failed.")
            
    except Exception as e:
        print(f"❌ Error accessing collection '{collection_name}': {e}")
        # List available collections
        cols = client.list_collections()
        print(f"ℹ️  Available collections: {[c.name for c in cols]}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # Default to localhost:8001 (port-forwarded)
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=8001)
    args = parser.parse_args()
    
    verify_chroma(args.host, args.port)
