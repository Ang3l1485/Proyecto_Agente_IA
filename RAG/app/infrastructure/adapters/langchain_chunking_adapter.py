from __future__ import annotations

import io
import uuid
import tempfile
import os
from typing import Iterable, List, Dict, Any, Optional

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None

from app.core.domain.models import Chunk
from app.core.domain.ports.chunking_port import ChunkingPort


class LangChainChunkingAdapter(ChunkingPort):
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 120,
        length_function=len,
    ) -> None:
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=length_function,
        )

    def split_file(self, file_bytes: bytes, file_name: str, base_metadata: dict) -> Iterable[Chunk]:
        print(f"[chunking] split_file: bytes_in={len(file_bytes)} name={file_name}")

        with tempfile.NamedTemporaryFile(suffix=self._suffix_from_name(file_name), delete=False) as tmp:
            tmp.write(file_bytes)
            tmp.flush()
            tmp_path = tmp.name
            print(f"[chunking] temp file created: {tmp.name}")

        text = self._extract_text_from_pdf(tmp_path)
        if not text.strip():
            raise ValueError("No se pudo extraer texto del documento PDF.")

        doc = Document(page_content=text, metadata=base_metadata)
        split_docs = self.splitter.split_documents([doc])
        print(f"[chunking] splitter.split_documents -> chunks={len(split_docs)}")

        for i, d in enumerate(split_docs):
            meta = dict(d.metadata or {})
            meta["chunk_index"] = str(i)
            meta["length"] = str(len(d.page_content))

            yield Chunk(
                id=str(uuid.uuid4()),
                content=d.page_content,
                metadata=meta,
                
            )

        try:
            os.remove(tmp_path)
        except Exception as e:
            print(f"[chunking][WARN] No se pudo eliminar el archivo temporal: {e}")

    def _suffix_from_name(self, filename: str) -> str:
        dot = filename.rfind(".")
        return filename[dot:] if dot != -1 else ".pdf"

    def _extract_text_from_pdf(self, path: str) -> str:
        if not PdfReader:
            raise ImportError("PyPDF no disponible.")

        try:
            reader = PdfReader(path)
            if getattr(reader, "is_encrypted", False):
                reader.decrypt("")

            text = ""
            for i, page in enumerate(reader.pages):
                try:
                    text += page.extract_text() or ""
                except Exception as e:
                    print(f"[chunking][ERROR] extract_text page={i} fallo: {e}")
            return text
        except Exception as e:
            raise RuntimeError(f"No se pudo extraer texto del PDF: {e}")
