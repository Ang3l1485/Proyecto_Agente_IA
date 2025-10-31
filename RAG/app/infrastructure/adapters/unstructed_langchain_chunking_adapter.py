from __future__ import annotations

import io
import uuid
import tempfile
import os
from typing import Iterable, List, Dict, Any, Optional

# Unstructured
from unstructured.partition.auto import partition
from unstructured.documents.elements import Element, Table

# LangChain Splitter
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Fallback PDF (solo texto)
try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None

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
        print(f"[chunking] split_file: bytes_in={len(file_bytes)} name={file_name}")
        # 1) para escribir los bytes a un archivo temporal y analizar con Unstructured
        with tempfile.NamedTemporaryFile(suffix=self._suffix_from_name(file_name), delete=True) as tmp:
            tmp.write(file_bytes)
            tmp.flush()
            print(f"[chunking] temp file created: {tmp.name}")

            # 2) lo analiza con Unstructured para obtener elementos estructurados
            elements = self._parse_with_unstructured(tmp.name)

        print(f"[chunking] partition() -> elements={len(elements)}")

        # 3) Convierte los elementos con metadatos en documentos mínimos para LangChain
        docs = self._elements_to_docs(elements, base_metadata=base_metadata)
        print(f"[chunking] _elements_to_docs -> docs={len(docs)}")

        # 4) De acuerdo con estos documentos, langchain los divide en fragmentos y hace chunks inteligentes
        split_docs = self.splitter.split_documents(docs)  # retorna una lista de los documentos divididos
        print(f"[chunking] splitter.split_documents -> chunks={len(split_docs)}")
        if not split_docs:
            print("[chunking][WARN] split_documents returned 0 chunks")

        # 5) Construye los Chunk del dominio con los fragmentos resultantes y sus metadatos
        for i, d in enumerate(split_docs):
            if not d.page_content.strip():
                print(f"[chunking][WARN] chunk[{i}] empty page_content len={len(d.page_content)}")
            elif len(d.page_content) < 32:
                print(f"[chunking][INFO] chunk[{i}] short page_content len={len(d.page_content)}")

            meta = dict(d.metadata or {})
            meta["chunk_index"] = str(i)
            # optional: include length for quick QC
            meta["length"] = str(len(d.page_content))

            yield Chunk(
                id=str(uuid.uuid4()),
                content=d.page_content,
                metadata=meta,
            )

    # --- Funciones internas ---
    def _suffix_from_name(self, filename: str) -> str:
        dot = filename.rfind(".")
        # Fallback a .pdf para que el parser elija el lector correcto
        return filename[dot:] if dot != -1 else ".pdf"

    def _parse_with_unstructured(self, path: str) -> List[Element]:
        """
        Solo texto (sin OCR). Intenta:
        1) partition_pdf(..., strategy="fast") para PDFs (pdfminer)
        2) partition(filename=..., strategy="fast")
        3) Si aún 0 elementos, reintenta con file=BytesIO y file_filename=...
        4) Fallback final: PyPDF (sin OCR) para extraer texto básico por página.
        """
        print(f"[chunking] _parse_with_unstructured: path={path}")
        kwargs: Dict[str, Any] = {
            "strategy": "fast",          # sin OCR
            "infer_table_structure": True,
        }
        print(f"[chunking] _parse_with_unstructured kwargs={kwargs}")

        elements: List[Element] = []

        # 1) Para PDFs, intenta directamente partition_pdf (fast/pdfminer)
        if path.lower().endswith(".pdf"):
            try:
                from unstructured.partition.pdf import partition_pdf
                print("[chunking] using partition_pdf (fast)")
                elements = partition_pdf(filename=path, **kwargs)
            except Exception as e:
                print(f"[chunking][WARN] partition_pdf fallo: {e}. Fallback a partition(auto).")

        # 2) Fallback: auto.partition con filename
        if not elements:
            try:
                elements = partition(filename=path, **kwargs)
            except Exception as e:
                print(f"[chunking][ERROR] partition(filename=...) fallo: {e}")

        # 3) Fallback: auto.partition pasando binario y file_filename
        if len(elements) == 0:
            try:
                base_name = os.path.basename(path) or "upload.pdf"
                if "." not in base_name:
                    base_name += ".pdf"
                print(f"[chunking] retry with file=BytesIO, file_filename='{base_name}'")
                with open(path, "rb") as fh:
                    data = fh.read()
                elements = partition(file=io.BytesIO(data), file_filename=base_name, **kwargs)
            except Exception as e:
                print(f"[chunking][ERROR] partition(file=...) fallo: {e}")

        # 4) Fallback final: PyPDF (sin OCR) si sigue vacío
        if len(elements) == 0 and path.lower().endswith(".pdf"):
            if PdfReader is None:
                print("[chunking][FALLBACK] PyPDF no instalado. Instala pypdf para fallback de solo texto: pip install pypdf")
            else:
                try:
                    print("[chunking][FALLBACK] Intentando extracción de texto con PyPDF...")
                    reader = PdfReader(path)
                    if getattr(reader, "is_encrypted", False):
                        print("[chunking][FALLBACK] PDF encriptado. Intentando decrypt('')...")
                        try:
                            reader.decrypt("")
                        except Exception as e:
                            print(f"[chunking][FALLBACK][WARN] decrypt('') fallo: {e}")

                    simple_elements: List[Element] = []
                    total_pages = len(reader.pages)
                    print(f"[chunking][FALLBACK] Páginas detectadas: {total_pages}")
                    for i, page in enumerate(reader.pages, start=1):
                        try:
                            txt = page.extract_text() or ""
                        except Exception as e:
                            print(f"[chunking][FALLBACK][ERROR] extract_text page={i} fallo: {e}")
                            txt = ""
                        if not txt.strip():
                            print(f"[chunking][FALLBACK][INFO] page[{i}] sin texto o vacío")
                            continue
                        # Crear un “elemento” simple compatible con _elements_to_docs
                        simple_elements.append(_SimpleElement(text=txt, page_number=i))

                    elements = simple_elements  # type: ignore[assignment]
                    print(f"[chunking][FALLBACK] PyPDF generó {len(simple_elements)} elementos con texto")
                except Exception as e:
                    print(f"[chunking][FALLBACK][ERROR] PyPDF fallo: {e}")

        print(f"[chunking] _parse_with_unstructured: got elements={len(elements)}")
        if len(elements) == 0:
            print("[chunking][HINT] 0 elementos. Posibles causas: PDF escaneado (solo imágenes) o faltan extras 'unstructured[pdf]'.")
            print("[chunking][HINT] Verifica dependencias en este venv: pip show unstructured pdfminer.six pypdf")
        return elements

    def _elements_to_docs(self, elements: List[Element], base_metadata: dict) -> List[_LC_Document]:
        docs: List[_LC_Document] = []
        valid_count = 0
        total = len(elements)
        print(f"[chunking] _elements_to_docs: start total_elements={total}")
        for idx, el in enumerate(elements):
            text = el.text or ""
            raw_len = len(text)
            if raw_len == 0:
                print(f"[chunking] el[{idx}] {el.__class__.__name__}: raw_len=0 (no text)")
            elif raw_len < 32:
                print(f"[chunking] el[{idx}] {el.__class__.__name__}: raw_len={raw_len} (short)")

            if not text.strip():
                continue
            valid_count += 1

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

            final_len = len(page_content)
            if final_len == 0:
                print(f"[chunking][WARN] doc from el[{idx}] is empty after processing")
            elif final_len < 32:
                print(f"[chunking][INFO] doc from el[{idx}] final_len={final_len} (short)")

            docs.append(_LC_Document(page_content=page_content, metadata=metadata))

        print(f"[chunking] _elements_to_docs: valid_text_elements={valid_count}, docs_generated={len(docs)}")
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


class _SimpleElement:
    """
    Elemento mínimo para fallback (compatible con _elements_to_docs).
    Solo provee .text y .metadata['page_number'].
    """
    def __init__(self, text: str, page_number: Optional[int] = None) -> None:
        self.text = text
        self.metadata: Dict[str, Any] = {}
        if page_number is not None:
            self.metadata["page_number"] = page_number

class _LC_Document:
    """
    Minimal stand-in for a LangChain Document (so we don’t import langchain.schema).
    Only the attributes used by the splitter are provided.
    """
    def __init__(self, page_content: str, metadata: Dict[str, Any] | None = None) -> None:
        self.page_content = page_content
        self.metadata = metadata or {}

