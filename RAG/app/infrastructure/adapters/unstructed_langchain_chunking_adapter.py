from __future__ import annotations

import io
import uuid
import tempfile
from typing import Iterable, List, Dict, Any, Optional

# Unstructured
from unstructured.partition.auto import partition
from unstructured.documents.elements import Element, Table

# LangChain Splitter
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Domain
from app.core.domain.models import Chunk
from app.core.domain.ports.chunking_port import ChunkingPort

class UnstructuredLangChainChunkingAdapter(ChunkingPort):
    """
    Adaptador de fragmentación que:
      1) Analiza la estructura del documento con elementos no estructurados (títulos, párrafos, listas, tablas, etc.).
      2) Conserva los metadatos útiles (número de página, encabezados de sección).
      3) Divide el documento en fragmentos coherentes con RecursiveCharacterTextSplitter de LangChain.

    Notas:
      - Funciona con PDF, DOCX, PPTX, HTML, etc.
      - Si el documento está escaneado, establezca ocr_languages y strategy=“hi_res” para habilitar el OCR.
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 120,
        length_function = len,
        add_section_headers: bool = True,
        prefer_table_as_block: bool = True,
        ocr_languages: Optional[str] = None,   # por si hay mas de un idioma
        ocr_mode: Optional[str] = None,        # "hi_res" | "fast" | None
    ) -> None:
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=length_function,
        )
        self.add_section_headers = add_section_headers
        self.prefer_table_as_block = prefer_table_as_block
        self.ocr_languages = ocr_languages
        self.ocr_mode = ocr_mode

    # --- Función del adaptador usando las reglas del puerto  ---
    def split_file(self, file_bytes: bytes, file_name: str, base_metadata: dict) -> Iterable[Chunk]:
        """
        Split a binary document (PDF, DOCX, etc.) into smart chunks with structure-aware parsing.
        """
        # 1) para escribir los bytes a un archivo temporal y analizar con Unstructured
        with tempfile.NamedTemporaryFile(suffix=self._suffix_from_name(file_name), delete=True) as tmp:
            tmp.write(file_bytes)
            tmp.flush()

            # 2) lo analiza con Unstructured para obtener elementos estructurados
            elements = self._parse_with_unstructured(tmp.name)

        # 3) Convierte los elementos con metadatos en documentos mínimos para LangChain
        docs = self._elements_to_docs(elements, base_metadata=base_metadata)

        # 4) De acuerdo con estos documentos, langchain los divide en fragmentos y hace chunks inteligentes
        split_docs = self.splitter.split_documents(docs)  # retorna una lista de los documentos divididos

        # 5) Construye los Chunk del dominio con los fragmentos resultantes y sus metadatos
        for i, d in enumerate(split_docs):
            meta = dict(d.metadata or {})
            meta["chunk_index"] = str(i)
            # optional: include length for quick QC
            meta["length"] = str(len(d.page_content))
            yield Chunk(
                id=str(uuid.uuid4()),
                text=d.page_content,
                metadata=meta,
            )

    # --- Funciones internas ---
    def _suffix_from_name(self, filename: str) -> str:
        dot = filename.rfind(".")
        return filename[dot:] if dot != -1 else ""

    def _parse_with_unstructured(self, path: str) -> List[Element]:
        """
        Calls unstructured.partition.auto.partition with proper OCR toggles for scanned PDFs.
        """
        kwargs: Dict[str, Any] = {
            # heuristic layout detection for PDFs, PPTs, etc.
            "strategy": "auto",
            "infer_table_structure": True,  # helps get Table elements with structure
        }

        # OCR options if needed
        if self.ocr_mode == "hi_res":
            kwargs["strategy"] = "hi_res"
        elif self.ocr_mode == "fast":
            kwargs["strategy"] = "fast"

        if self.ocr_languages:
            kwargs["ocr_languages"] = self.ocr_languages

        elements: List[Element] = partition(filename=path, **kwargs)
        return elements

    def _elements_to_docs(self, elements: List[Element], base_metadata: dict) -> List[_LC_Document]:
        """
        Convert Unstructured elements into a minimal Document-like structure that LangChain expects:
          - page_content: str
          - metadata: dict

        We keep section headers and page numbers if present.
        """
        docs: List[_LC_Document] = []
        for idx, el in enumerate(elements):
            text = el.text or ""
            if not text.strip():
                continue

            # Tables: optionally keep them as a single block (preserves structure)
            if isinstance(el, Table) and self.prefer_table_as_block:
                text = self._format_table(el)

            metadata: Dict[str, Any] = {}
            metadata.update(base_metadata or {})

            # Page number (if available)
            page_num = getattr(el, "metadata", {}).get("page_number") or getattr(el, "page_number", None)
            if page_num is not None:
                metadata["page_number"] = str(page_num)

            # Section headers (if available)
            if self.add_section_headers:
                # Unstructured elements may carry context via "metadata" dict
                headers = self._extract_section_headers(el)
                if headers:
                    metadata["section_headers"] = " > ".join(headers)

            # Element type (Title, NarrativeText, ListItem, Table, etc.)
            metadata["element_type"] = el.__class__.__name__

            # Build the final content (optionally prepend headers for more context)
            page_content = text
            header_prefix = metadata.get("section_headers")
            if header_prefix:
                page_content = f"{header_prefix}\n\n{page_content}"

            docs.append(_LC_Document(page_content=page_content, metadata=metadata))

        return docs

    def _extract_section_headers(self, el: Element) -> List[str]:
        """
        Best-effort extraction of hierarchical headers from Unstructured element metadata.
        """
        headers: List[str] = []
        meta = getattr(el, "metadata", {}) or {}
        # Common keys seen in Unstructured:
        # - "category_depth", "parent_id", "id", "filename", "section"
        # - In some loaders, you may get "headers" list or "title"
        if "section" in meta and meta["section"]:
            headers.append(str(meta["section"]))
        if "headers" in meta and isinstance(meta["headers"], list):
            headers.extend([str(h) for h in meta["headers"] if h])
        if "title" in meta and meta["title"]:
            headers.append(str(meta["title"]))
        return headers

    def _format_table(self, table: Table) -> str:
        """
        Convert an Unstructured Table element into a readable text block.
        If the table already has 'text', rely on that; otherwise, fall back to simple row joining.
        """
        if getattr(table, "text", None):
            return table.text

        # Fallback: basic serialization
        rows = getattr(table, "rows", None)
        if not rows:
            return "[Table]"
        lines = []
        for r in rows:
            # Each 'r' might be a list of cells; join with tabs
            cells = [c.text if hasattr(c, "text") else str(c) for c in r]
            lines.append("\t".join(cells))
        return "\n".join(lines)


class _LC_Document:
    """
    Minimal stand-in for a LangChain Document (so we don’t import langchain.schema).
    Only the attributes used by the splitter are provided.
    """
    def __init__(self, page_content: str, metadata: Dict[str, Any] | None = None) -> None:
        self.page_content = page_content
        self.metadata = metadata or {}
