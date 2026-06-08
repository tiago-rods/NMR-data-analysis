import re
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

@dataclass
class ExperimentMetadata:
    """Structured container for NMR experiment metadata parsed from a filename.

    Attributes:
        id_experimento (str): Experiment ID (e.g. 'LNBio123').
        fabricante (str): Equipment manufacturer (e.g. 'Bruker', 'Agilent').
        frequencia (float): NMR frequency in MHz.
        biofluido (str): Sample biofluid type (e.g. 'Soro', 'Urina').
        ferramenta (str): Analysis tool name (e.g. 'ASICS', 'MagMet').
        tecnologia (str): Input file format technology ('csv' or 'fid').
        tamanho (int): Dataset size extracted from the filename.
    """

    id_experimento: str
    fabricante: str
    frequencia: float
    biofluido: str
    ferramenta: str
    tecnologia: str
    tamanho: int

class MetadataExtractor:
    """Extracts structured metadata from standardized NMR CSV filenames.

    Follows the Single Responsibility Principle — only responsible for parsing
    metadata from filenames. Extend ``KNOWN_BIOFLUIDS`` or ``KNOWN_TOOLS`` to
    support new vocabulary without changing the core parsing logic.
    """
    KNOWN_BIOFLUIDS = {'Soro', 'Urina', 'Plasma'}
    KNOWN_TOOLS = {'nmRanalysis', 'ASICS', 'MagMet', 'Batman'}
    
    @classmethod
    def extract(cls, filepath: str | Path) -> Optional[ExperimentMetadata]:
        """Parses a filename to extract experiment metadata.

        Uses regular expressions for structured fields (ID, frequency, size)
        and set intersection for categorical tags (biofluid, tool, manufacturer).

        Args:
            filepath (str | Path): Path to the NMR CSV file.

        Returns:
            Optional[ExperimentMetadata]: Parsed metadata dataclass, or ``None``
            if the filename does not match the expected pattern.
        """
        filename = Path(filepath).name
        
        # Regular expressions for explicit patterns
        id_match = re.search(r'(LNBio\d+)', filename, re.IGNORECASE)
        freq_match = re.search(r'(\d+)MHz', filename, re.IGNORECASE)
        size_match = re.search(r'size(\d+)', filename, re.IGNORECASE)
        
        if not id_match or not freq_match or not size_match:
            return None
            
        # Split by underscore to find standard categorical tags
        parts = set(filename.replace('.csv', '').replace('quantificationcsv', '').replace('quantification', '').split('_'))
        
        biofluido = next((p for p in parts if p in cls.KNOWN_BIOFLUIDS), 'Unknown')
        ferramenta = next((p for p in parts if p in cls.KNOWN_TOOLS), 'Unknown')
        
        # Infer Manufacturer
        fabricante = 'Unknown'
        if 'Agilent' in parts: 
            fabricante = 'Agilent'
        elif 'Bruker' in parts: 
            fabricante = 'Bruker'
        
        # Infer Technology (File input format)
        tecnologia = 'csv' if 'csv' in parts else 'fid' if 'fid' in parts else 'Unknown'

        return ExperimentMetadata(
            id_experimento=id_match.group(1),
            fabricante=fabricante,
            frequencia=float(freq_match.group(1)),
            biofluido=biofluido,
            ferramenta=ferramenta,
            tecnologia=tecnologia,
            tamanho=int(size_match.group(1))
        )
