import pytest
from unittest.mock import MagicMock, patch
from app.services.storage_service import LocalStorageService, S3StorageService, create_storage_service

@pytest.fixture
def local_storage(tmp_path):
    with patch("app.services.storage_service.settings.DOCUMENT_STORAGE_PATH", str(tmp_path)):
        service = LocalStorageService()
        yield service, tmp_path

@pytest.mark.asyncio
async def test_local_storage_upload_download(local_storage):
    service, base_path = local_storage
    src_file = base_path / "source.txt"
    src_file.write_text("Hello Vellum Storage")
    
    await service.upload("dest.txt", str(src_file))
    
    assert (base_path / "dest.txt").exists()
    
    chunks = []
    async for chunk in service.download("dest.txt"):
        chunks.append(chunk)
        
    content = b"".join(chunks).decode()
    assert content == "Hello Vellum Storage"

@pytest.mark.asyncio
async def test_local_storage_list_files(local_storage):
    service, base_path = local_storage
    (base_path / "file1.txt").write_text("1")
    (base_path / "file2.pdf").write_text("2")
    (base_path / "hidden_dir").mkdir()
    
    files = await service.list_files()
    assert len(files) == 2
    assert "file1.txt" in files
    assert "file2.pdf" in files

@pytest.mark.asyncio
async def test_s3_storage_upload_download():
    # We mock boto3 to avoid actual AWS connections
    with patch("boto3.client") as mock_boto3:
        client_mock = MagicMock()
        mock_boto3.return_value = client_mock
        
        with patch("app.services.storage_service.settings.S3_BUCKET", "test-bucket"):
            service = S3StorageService()
            
            # Test Upload
            await service.upload("dest.txt", "/tmp/source.txt")
            client_mock.upload_file.assert_called_with("/tmp/source.txt", "test-bucket", "dest.txt")
            
            # Test Download
            mock_body = MagicMock()
            mock_body.iter_chunks.return_value = [b"chunk1", b"chunk2"]
            client_mock.get_object.return_value = {"Body": mock_body}
            
            chunks = []
            async for chunk in service.download("dest.txt"):
                chunks.append(chunk)
                
            assert chunks == [b"chunk1", b"chunk2"]
            client_mock.get_object.assert_called_with(Bucket="test-bucket", Key="dest.txt")

@pytest.mark.asyncio
async def test_s3_storage_list_files():
    with patch("boto3.client") as mock_boto3:
        client_mock = MagicMock()
        mock_boto3.return_value = client_mock
        
        with patch("app.services.storage_service.settings.S3_BUCKET", "test-bucket"):
            service = S3StorageService()
            
            client_mock.list_objects_v2.return_value = {
                "Contents": [{"Key": "doc1.txt"}, {"Key": "doc2.pdf"}]
            }
            
            files = await service.list_files()
            assert files == ["doc1.txt", "doc2.pdf"]
            client_mock.list_objects_v2.assert_called_with(Bucket="test-bucket")

def test_create_storage_service():
    with patch("app.services.storage_service.settings.USE_S3_STORAGE", False):
        service = create_storage_service()
        assert isinstance(service, LocalStorageService)
        
    with patch("app.services.storage_service.settings.USE_S3_STORAGE", True):
        with patch("boto3.client"):
            service = create_storage_service()
            assert isinstance(service, S3StorageService)
