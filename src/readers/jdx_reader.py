import nmrglue as ng
from typing import Any
from src.readers.factory_reader import FactoryReader

class JDXReader(FactoryReader):
    """Reader implementation for JDX (JCAMP-DX) NMR data files using nmrglue."""

    def read(self, path: str, **kwargs) -> Any:
        """Reads a JDX file and returns a dictionary with metadata and spectral data.

        Uses ``nmrglue.jcampdx.read``, which returns a ``(dic, data)`` tuple,
        and normalises the output into a consistent dict format.

        Args:
            path (str): The path to the JDX file.
            **kwargs: Additional keyword arguments forwarded to ``ng.jcampdx.read``.

        Returns:
            Dict[str, Any]: A dictionary with keys ``'metadata'`` and ``'data'``.

        Raises:
            RuntimeError: If the file cannot be read.
        """
        try:
            dic, data = ng.jcampdx.read(path, **kwargs)
            return {"metadata": dic, "data": data}
        except Exception as e:
            raise RuntimeError(f"Error reading JDX file at {path}: {e}")
