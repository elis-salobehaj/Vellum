import pytest
import os
from unittest.mock import MagicMock, patch
from app.services.direct_ingestion_service import DirectIngestionService
from app.services.history_service import HistoryService
from app.services.llm_service import LLMService
from app.services.rag_service import RAGService
from app.models.schemas import ModelConfig



@pytest.fixture
def history_service():
    return HistoryService()


@pytest.fixture
def ll_service():
    # Mock llama_index dependencies globally in conftest.py helps here
    return LLMService()


def test_history_service_add_message(history_service):
    # Patch the global STORAGE to isolate test if needed,
    # but since it's an instance, we can just test it.
    # Actually, if HistoryService uses a global variable, we patch it in the module.
    with patch("app.services.history_service.CONVERSATIONS", {}):
        history_service.add_message("sess-123", "user", "Hello Vellum")

        messages = history_service.get_messages("sess-123")
        assert len(messages) == 1
        assert messages[0]["content"] == "Hello Vellum"
        assert messages[0]["role"] == "user"


def test_history_service_get_recent(history_service):
    with patch("app.services.history_service.CONVERSATIONS", {}):
        history_service.add_message("s1", "user", "Chat 1")
        history_service.add_message("s1", "assistant", "Response 1")
        history_service.add_message("s2", "user", "Chat 2")

        recent = history_service.get_recent_conversations("default")
        assert len(recent) == 2
        # Verify order/content
        assert any(r["id"] == "s1" for r in recent)
        assert any(r["id"] == "s2" for r in recent)


@pytest.mark.asyncio
async def test_llm_service_openai(ll_service):
    # The OpenAI class is imported at the top of llm_service.py
    config = ModelConfig(
        id="gpt-4",
        model_api_path="gpt-4",
        name="GPT4",
        provider="openai",
        api_key="sk-test",
    )

    # Patch where it's used (in the llm_service module)
    with patch("app.services.llm_service.OpenAI") as mock_openai:
        await ll_service._get_llm(config)
        assert mock_openai.called
        # The actual call includes api_base parameter
        mock_openai.assert_called_with(
            model="gpt-4", api_key="sk-test", api_base="https://api.openai.com/v1"
        )


@pytest.mark.asyncio
async def test_llm_service_google(ll_service):
    config = ModelConfig(
        id="gemini-1.5",
        model_api_path="gemini-1-5",
        name="Gemini",
        provider="google",
    )

    # Patch where it's imported (inside the method)
    with patch("llama_index.llms.gemini.Gemini") as mock_gemini:
        with patch("app.services.llm_service.settings.GOOGLE_API_KEY", "fake-key"):
            await ll_service._get_llm(config)
            assert mock_gemini.called
            mock_gemini.assert_called_with(
                model="models/gemini-1.5", api_key="fake-key"
            )


@pytest.mark.asyncio
async def test_llm_service_ray(ll_service):
    config = ModelConfig(
        id="qwen",
        model_api_path="qwen",
        name="Qwen",
        provider="ray",
        base_url="http://llm-service-head-svc.vellum-ray.svc.cluster.local:8000",
    )

    # Patch where it's imported (inside the method)
    with patch("llama_index.llms.openai_like.OpenAILike") as mock_openai_like:
        await ll_service._get_llm(config)
        assert mock_openai_like.called
        mock_openai_like.assert_called_with(
            model="qwen",
            api_base="http://llm-service-head-svc.vellum-ray.svc.cluster.local:8000",
            api_key="dummy",
            is_chat_model=True,
            max_tokens=2048,
        )


def test_llm_service_bedrock_langchain_model(ll_service):
    config = ModelConfig(
        id="global.anthropic.claude-sonnet-4-6",
        model_api_path="claude-sonnet-4-6",
        name="Claude Sonnet 4.6",
        provider="aws_bedrock",
    )

    previous_bearer = os.environ.get("AWS_BEARER_TOKEN_BEDROCK")

    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("AWS_BEARER_TOKEN_BEDROCK", None)
        with patch("app.services.llm_service.ChatBedrockConverse") as mock_converse:
            with patch(
                "app.services.llm_service.settings.AWS_BEDROCK_API_KEY",
                "test-bedrock-key",
            ):
                with patch("app.services.llm_service.settings.AWS_REGION", "us-east-1"):
                    model = ll_service._create_bedrock_chat_model(config)

    assert model._chat_model == mock_converse.return_value
    mock_converse.assert_called_with(
        model="global.anthropic.claude-sonnet-4-6",
        region_name="us-east-1",
        temperature=0,
    )
    assert os.environ.get("AWS_BEARER_TOKEN_BEDROCK") == previous_bearer


@pytest.mark.asyncio
async def test_llm_service_invalid_provider(ll_service):
    config = ModelConfig(id="bad", model_api_path="bad", name="bad", provider="unknown")
    with pytest.raises(ValueError) as exc:
        await ll_service._get_llm(config)
    # The actual error message is "Provider unknown not supported."
    assert "not supported" in str(exc.value)


@pytest.mark.asyncio
async def test_rag_service_missing_collection_returns_no_context():
    rag_service = RAGService()
    rag_service._client = MagicMock()
    rag_service._client.collection_exists.return_value = False

    result = await rag_service.query("Hello Vellum")

    assert result == []
    rag_service._client.collection_exists.assert_called_once()


@pytest.mark.asyncio
async def test_direct_ingestion_service_skips_unchanged_documents():
    """Files whose signature hasn't changed should be skipped."""
    service = DirectIngestionService()

    mock_qdrant = MagicMock()
    mock_qdrant.collection_exists.return_value = True

    fake_signature = "100:1700000000000"

    with patch(
        "app.services.direct_ingestion_service.qdrant_client.QdrantClient",
        return_value=mock_qdrant,
    ):
        with patch.object(service, "_load_status", return_value={}):
            with patch.object(service, "_save_status"):
                with patch.object(service, "_ensure_collection"):
                    with patch.object(
                        service,
                        "_list_source_files",
                        return_value=["/data/docs/example.pdf"],
                    ):
                        with patch.object(
                            service,
                            "_build_source_signature",
                            return_value=fake_signature,
                        ):
                            with patch.object(
                                service,
                                "_get_existing_source_signature",
                                return_value=(True, fake_signature),
                            ):
                                with patch.object(
                                    service, "_count_indexed_source_docs", return_value=1
                                ):
                                    with patch(
                                        "app.services.direct_ingestion_service.QdrantVectorStore"
                                    ) as mock_vector_store:
                                        with patch(
                                            "app.services.direct_ingestion_service.IngestionPipeline"
                                        ) as mock_pipeline:
                                            with patch("app.services.direct_ingestion_service.storage_service.download") as mock_dl:
                                                async def fake_dl(key): yield b"fake"
                                                mock_dl.side_effect = fake_dl
                                                logs = await service.run(cleanup=False)

    assert any("Skipping unchanged file" in line for line in logs)
    assert any("No new or changed documents to index" in line for line in logs)
    mock_vector_store.return_value.delete.assert_not_called()
    mock_pipeline.return_value.run.assert_not_called()


@pytest.mark.asyncio
async def test_direct_ingestion_service_replaces_changed_documents():
    """Files whose content changed should replace old chunks and re-index."""
    service = DirectIngestionService()
    loaded_document = MagicMock(metadata={"file_name": "example.pdf"})

    mock_qdrant = MagicMock()
    mock_qdrant.collection_exists.return_value = True
    mock_qdrant.scroll.return_value = (
        [MagicMock(payload={"source_signature": "old:sig"})],
        None,
    )

    with patch(
        "app.services.direct_ingestion_service.qdrant_client.QdrantClient",
        return_value=mock_qdrant,
    ):
        with patch.object(service, "_load_status", return_value={}):
            with patch.object(service, "_save_status"):
                with patch.object(service, "_ensure_collection"):
                    with patch.object(
                        service,
                        "_list_source_files",
                        return_value=["/data/docs/example.pdf"],
                    ):
                        with patch.object(
                            service,
                            "_build_source_signature",
                            return_value="new:sig",
                        ):
                            with patch.object(
                                service,
                                "_get_existing_source_signature",
                                return_value=(True, "old:sig"),
                            ):
                                with patch.object(
                                    service, "_count_indexed_source_docs", return_value=1
                                ):
                                    with patch(
                                        "app.services.direct_ingestion_service.SimpleDirectoryReader"
                                    ) as mock_reader:
                                        mock_reader.return_value.load_data.return_value = [
                                            loaded_document
                                        ]
                                        with patch(
                                            "app.services.direct_ingestion_service.QdrantVectorStore"
                                        ) as mock_vector_store:
                                            with patch(
                                                "app.services.direct_ingestion_service.IngestionPipeline"
                                            ) as mock_pipeline:
                                                with patch("app.services.direct_ingestion_service.storage_service.download") as mock_dl:
                                                    async def fake_dl(key): yield b"fake"
                                                    mock_dl.side_effect = fake_dl
                                                    logs = await service.run(cleanup=False)

    assert any("Replacing existing chunks for" in line for line in logs)
    mock_vector_store.return_value.delete.assert_called_once()
    mock_pipeline.return_value.run.assert_called_once()
    assert loaded_document.metadata["source_object_key"] == "/data/docs/example.pdf"


def test_direct_ingestion_signature_uses_content_hash():
    """Signature is derived from sha256 of file content."""
    service = DirectIngestionService()
    sig = service._build_source_signature(b"Hello Vellum")
    import hashlib
    assert sig == hashlib.sha256(b"Hello Vellum").hexdigest()


@pytest.mark.asyncio
async def test_direct_ingestion_service_tracks_resume_checkpoint():
    """Batch size limits processing; paused status set with correct resume key."""
    service = DirectIngestionService()
    loaded_document = MagicMock(metadata={"file_name": "a.pdf"})
    file_paths = ["/data/docs/a.pdf", "/data/docs/b.pdf", "/data/docs/c.pdf"]

    mock_qdrant = MagicMock()
    mock_qdrant.collection_exists.return_value = True

    with patch(
        "app.services.direct_ingestion_service.qdrant_client.QdrantClient",
        return_value=mock_qdrant,
    ):
        with patch.object(service, "_load_status", return_value={}):
            with patch.object(service, "_save_status") as mock_save_status:
                with patch.object(service, "_ensure_collection"):
                    with patch.object(service, "_list_source_files", return_value=file_paths):
                        with patch.object(service, "_build_source_signature", return_value="s:1"):
                            with patch.object(
                                service,
                                "_get_existing_source_signature",
                                return_value=(False, None),
                            ):
                                with patch.object(
                                    service, "_count_indexed_source_docs", return_value=2
                                ):
                                    with patch(
                                        "app.services.direct_ingestion_service.SimpleDirectoryReader"
                                    ) as mock_reader:
                                        mock_reader.return_value.load_data.return_value = [
                                            loaded_document
                                        ]
                                        with patch(
                                            "app.services.direct_ingestion_service.QdrantVectorStore"
                                        ):
                                            with patch(
                                                "app.services.direct_ingestion_service.IngestionPipeline"
                                            ) as mock_pipeline:
                                                with patch("app.services.direct_ingestion_service.storage_service.download") as mock_dl:
                                                    async def fake_dl(key): yield b"fake"
                                                    mock_dl.side_effect = fake_dl
                                                    await service.run(
                                                        cleanup=False,
                                                        batch_size=2,
                                                    )

    assert mock_pipeline.return_value.run.call_count == 2
    final_status = mock_save_status.call_args_list[-1].kwargs["status"]
    assert final_status["status"] == "paused"
    assert final_status["cycle_complete"] is False
    assert final_status["current_file"] is None


@pytest.mark.asyncio
async def test_direct_ingestion_service_status_tracks_recent_skips_and_summary():
    """Files that LoadData returns empty should appear in recent_skipped_files."""
    service = DirectIngestionService()

    mock_qdrant = MagicMock()
    mock_qdrant.collection_exists.return_value = True
    mock_qdrant.scroll.return_value = ([], None)

    with patch(
        "app.services.direct_ingestion_service.qdrant_client.QdrantClient",
        return_value=mock_qdrant,
    ):
        with patch.object(service, "_load_status", return_value={}):
            with patch.object(service, "_save_status") as mock_save_status:
                with patch.object(service, "_ensure_collection"):
                    with patch.object(
                        service,
                        "_list_source_files",
                        return_value=["/data/docs/unsupported.ppt"],
                    ):
                        with patch.object(service, "_build_source_signature", return_value="s:1"):
                            with patch.object(
                                service,
                                "_get_existing_source_signature",
                                return_value=(False, None),
                            ):
                                with patch(
                                    "app.services.direct_ingestion_service.SimpleDirectoryReader"
                                ) as mock_reader:
                                    mock_reader.return_value.load_data.return_value = []
                                    with patch(
                                        "app.services.direct_ingestion_service.QdrantVectorStore"
                                    ):
                                        with patch(
                                            "app.services.direct_ingestion_service.IngestionPipeline"
                                        ):
                                            with patch("app.services.direct_ingestion_service.storage_service.download") as mock_dl:
                                                async def fake_dl(key): yield b"fake"
                                                mock_dl.side_effect = fake_dl
                                                with pytest.raises(ValueError):
                                                    await service.run(cleanup=False)

    final_status = mock_save_status.call_args_list[-1].kwargs["status"]
    assert "/data/docs/unsupported.ppt" in final_status["recent_skipped_files"]
    assert "No supported documents" in final_status["last_error"]


@pytest.mark.asyncio
async def test_direct_ingestion_service_rejects_concurrent_run():
    """If a run is already in progress (status==running), raise RuntimeError."""
    service = DirectIngestionService()

    mock_qdrant = MagicMock()
    mock_qdrant.collection_exists.return_value = True

    with patch(
        "app.services.direct_ingestion_service.qdrant_client.QdrantClient",
        return_value=mock_qdrant,
    ):
        with patch.object(
            service,
            "_load_status",
            return_value={"status": "running", "current_file": "/data/docs/example.pdf"},
        ):
            with patch.object(
                service, "_list_source_files", return_value=["/data/docs/example.pdf"]
            ):
                with pytest.raises(RuntimeError) as exc:
                    await service.run(cleanup=False)

    assert "already running" in str(exc.value)

